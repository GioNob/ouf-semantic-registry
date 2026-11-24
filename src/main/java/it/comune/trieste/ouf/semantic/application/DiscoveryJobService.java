package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Transactional;
import static it.comune.trieste.ouf.semantic.application.WorkflowAction.*;

/** Native job access. MCP delegation and HUMAN governance are separate boundaries. */
@Service
public class DiscoveryJobService {
  private static final long MIN_POLL_SECONDS=5;
  enum State { PENDING, RUNNING, SUCCEEDED, FAILED, CANCELLED }
  enum RecoveryState { ACTIVE, RETRY_WAIT, PAUSED_EXHAUSTED, BLOCKED, CANCELLED }
  private final JdbcClient db;
  private final DiscoveryService discovery;
  private final List<SemanticDiscoveryProvider> providers;
  private final ObjectMapper json;
  public DiscoveryJobService(JdbcClient db,DiscoveryService discovery,List<SemanticDiscoveryProvider> providers,ObjectMapper json){
    this.db=db;this.discovery=discovery;this.providers=List.copyOf(providers);this.json=json;
  }
  @Transactional
  public Map<String,Object> request(String type,String intent,List<String> languages,String actor,String key){
    if(type==null || !Set.of("CLASS","PROPERTY","RELATIONSHIP","VOCABULARY","CONCEPT","ONTOLOGY").contains(type)
        || intent==null || intent.isBlank() || intent.length()>2000 || languages==null || languages.size()>5
        || languages.stream().anyMatch(x->x==null || !x.matches("[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8}){0,3}")))
      throw new IllegalArgumentException("SEM_DISCOVERY_REQUEST_INVALID");
    if(actor==null || actor.isBlank())throw new IllegalArgumentException("SEM_DISCOVERY_ACTOR_REQUIRED");
    intent=intent.strip();
    languages=languages.stream().map(x->x.toLowerCase(Locale.ROOT)).distinct().toList();
    if(key==null)return status(discovery.request(type,intent,languages,actor),actor);
    if(!key.matches("[A-Za-z0-9._:-]{16,128}"))throw new IllegalArgumentException("SEM_DISCOVERY_IDEMPOTENCY_KEY_INVALID");
    String keyHash=hash(key);
    String fingerprint=hash(write(List.of(type,intent,languages,providers.stream().map(SemanticDiscoveryProvider::providerId).sorted().toList())));
    var previous=existing(actor,keyHash);
    if(!previous.isEmpty())return replay(previous.getFirst(),fingerprint,actor);
    if(providers.stream().noneMatch(SemanticDiscoveryProvider::enabled))throw new DiscoveryService.ProviderUnavailable();
    UUID id=UUID.randomUUID();
    var inserted=db.sql("insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,preferred_languages,state,created_by_subject,idempotency_key_hash,request_fingerprint) values(:id,:type,:intent,:languages,'PENDING',:actor,:key,:fingerprint) on conflict(created_by_subject,idempotency_key_hash) where idempotency_key_hash is not null do nothing returning request_id")
      .param("id",id).param("type",type).param("intent",intent).param("languages",languages.toArray(String[]::new))
      .param("actor",actor).param("key",keyHash).param("fingerprint",fingerprint).query(UUID.class).list();
    return inserted.isEmpty()?replay(existing(actor,keyHash).getFirst(),fingerprint,actor):status(id,actor);
  }
  private List<Map<String,Object>> existing(String actor,String key){
    return db.sql("select request_id,request_fingerprint from ouf_sem.discovery_request where created_by_subject=:actor and idempotency_key_hash=:key")
      .param("actor",actor).param("key",key).query().listOfRows();
  }
  private Map<String,Object> replay(Map<String,Object> row,String fingerprint,String actor){
    if(!fingerprint.equals(row.get("request_fingerprint")))throw new ArtifactService.Conflict("SEM_DISCOVERY_IDEMPOTENCY_CONFLICT");
    return status((UUID)row.get("request_id"),actor);
  }
  public Map<String,Object> status(UUID id,String actor){
    var rows=db.sql("""
        select r.request_id,r.state,r.attempt_count,r.recovery_state,r.next_attempt_at,r.budget_deadline,
          r.created_at,r.completed_at,r.last_error_code,r.rdf_invalid_count,r.rdf_bound_count,r.fetch_denied_count,
          coalesce((r.provider_policy->>'namespaceExcluded')::integer,0) as namespace_excluded_count,
          (select count(*) from ouf_sem.discovery_candidate c
           where c.request_id=r.request_id and c.expires_at>transaction_timestamp()) as candidate_count,
          ceil(extract(epoch from r.next_attempt_at-transaction_timestamp()))::bigint as seconds_until_retry
        from ouf_sem.discovery_request r where r.request_id=:id and r.created_by_subject=:actor
        """)
      .param("id",id).param("actor",actor).query().listOfRows();
    if(rows.isEmpty())throw new NoSuchElementException("SEM_DISCOVERY_REQUEST_NOT_FOUND");
    var row=rows.getFirst();var out=new LinkedHashMap<String,Object>();
    out.put("requestId",row.get("request_id"));out.put("state",row.get("state"));out.put("attemptCount",row.get("attempt_count"));
    out.put("recoveryState",row.get("recovery_state"));out.put("nextAttemptAt",row.get("next_attempt_at"));out.put("budgetDeadline",row.get("budget_deadline"));
    out.put("createdAt",row.get("created_at"));out.put("completedAt",row.get("completed_at"));out.put("candidateCount",row.get("candidate_count"));
    out.put("excludedCandidates",Map.of("CANDIDATE_RDF_INVALID",row.get("rdf_invalid_count"),
        "CANDIDATE_RDF_BOUND",row.get("rdf_bound_count"),"CANDIDATE_FETCH_DENIED",row.get("fetch_denied_count"),
        "CANDIDATE_NAMESPACE_EXCLUDED",row.get("namespace_excluded_count")));
    // Provider exception text may contain endpoint/credential details; never expose it.
    if(row.get("last_error_code") instanceof String code)out.put("errorCode",switch(code){
      case "SEM_DISCOVERY_NO_ENABLED_PROVIDER" -> code;
      case "PROVIDER_HTTP_429","PROVIDER_HTTP_429_RETRY_AFTER_INVALID" -> "SEM_DISCOVERY_RATE_LIMITED";
      default -> "SEM_DISCOVERY_PROVIDER_FAILED";
    });
    var state=State.valueOf((String)row.get("state"));
    var recovery=RecoveryState.valueOf((String)row.get("recovery_state"));
    WorkflowAction action=switch(state) {
      case PENDING, RUNNING -> switch(recovery) {
        case ACTIVE, RETRY_WAIT -> POLL_DISCOVERY;
        case PAUSED_EXHAUSTED, BLOCKED, CANCELLED -> NONE;
      };
      case SUCCEEDED -> ((Number)row.get("candidate_count")).longValue()>0 ? LIST_CANDIDATES : NONE;
      case FAILED, CANCELLED -> NONE;
    };
    out.put("allowedActions",List.of(action));
    if(action==POLL_DISCOVERY)
      out.put("pollAfterSeconds",Math.max(MIN_POLL_SECONDS,((Number)row.get("seconds_until_retry")).longValue()));
    return out;
  }
  public Map<String,Object> providerStatus(String provider,boolean enabled,String actor){
    var rows=db.sql("select state,attempts,cumulative_attempts,next_attempt_at,budget_deadline,incident_id from ouf_sem.discovery_dependency where scope_subject=:a and provider_id=:p")
      .param("a",actor).param("p",provider).query().listOfRows();
    var out=new LinkedHashMap<String,Object>();out.put("providerId",provider);out.put("enabled",enabled);
    out.put("recoveryState",rows.isEmpty()?"NOT_OBSERVED":rows.getFirst().get("state"));
    if(!rows.isEmpty())out.putAll(rows.getFirst());return out;
  }
  public List<Map<String,Object>> candidates(UUID id,String actor){status(id,actor);return discovery.candidates(id);}
  long trafficTotal(String metric,String route,String origin){
    return db.sql("""
        select coalesce(sum(amount),0) from ouf_sem.discovery_job_traffic
        where metric=:metric and route=:route and origin=:origin
        """).param("metric",metric).param("route",route).param("origin",origin).query(Long.class).single();
  }
  @Transactional(readOnly=true,isolation=Isolation.REPEATABLE_READ)
  public Map<String,Object> candidatesWithState(UUID id,String actor) {
    var response=status(id,actor);
    var candidates=discovery.candidates(id,true);
    var adoptable=new ArrayList<UUID>();
    for(var candidate:candidates) {
      if(candidate.remove("adopted_artifact_id")==null && State.SUCCEEDED.name().equals(response.get("state")))
        adoptable.add((UUID)candidate.get("candidate_id"));
    }
    if(State.SUCCEEDED.name().equals(response.get("state")))
      response.put("allowedActions",List.of(adoptable.isEmpty()?NONE:ADOPT_CANDIDATE));
    response.put("candidates",candidates);
    response.put("adoptableCandidateIds",adoptable);
    return response;
  }
  private String write(Object value){try{return json.writeValueAsString(value);}catch(Exception e){throw new IllegalArgumentException("SEM_DISCOVERY_REQUEST_INVALID");}}
  static String hash(String value){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8)));}catch(Exception e){throw new IllegalStateException("SEM_DISCOVERY_HASH_UNAVAILABLE");}}
}

package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Native job access. MCP delegation and HUMAN governance are separate boundaries. */
@Service
public class DiscoveryJobService {
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
    var rows=db.sql("select r.request_id,r.state,r.attempt_count,r.created_at,r.completed_at,r.last_error_code,(select count(*) from ouf_sem.discovery_candidate c where c.request_id=r.request_id and c.expires_at>transaction_timestamp()) as candidate_count from ouf_sem.discovery_request r where r.request_id=:id and r.created_by_subject=:actor")
      .param("id",id).param("actor",actor).query().listOfRows();
    if(rows.isEmpty())throw new NoSuchElementException("SEM_DISCOVERY_REQUEST_NOT_FOUND");
    var row=rows.getFirst();var out=new LinkedHashMap<String,Object>();
    out.put("requestId",row.get("request_id"));out.put("state",row.get("state"));out.put("attemptCount",row.get("attempt_count"));
    out.put("createdAt",row.get("created_at"));out.put("completedAt",row.get("completed_at"));out.put("candidateCount",row.get("candidate_count"));
    // Provider exception text may contain endpoint/credential details; never expose it.
    if(row.get("last_error_code")!=null)out.put("errorCode","SEM_DISCOVERY_NO_ENABLED_PROVIDER".equals(row.get("last_error_code"))?"SEM_DISCOVERY_NO_ENABLED_PROVIDER":"SEM_DISCOVERY_PROVIDER_FAILED");
    return out;
  }
  public List<Map<String,Object>> candidates(UUID id,String actor){status(id,actor);return discovery.candidates(id);}
  private String write(Object value){try{return json.writeValueAsString(value);}catch(Exception e){throw new IllegalArgumentException("SEM_DISCOVERY_REQUEST_INVALID");}}
  private static String hash(String value){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8)));}catch(Exception e){throw new IllegalStateException("SEM_DISCOVERY_HASH_UNAVAILABLE");}}
}

package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import it.comune.trieste.ouf.semantic.adapters.discovery.ProviderFailurePolicy;
import java.time.OffsetDateTime;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.util.*;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class DiscoveryService {
  private final JdbcClient db;private final List<SemanticDiscoveryProvider> providers;private final SafeRdfParser parser;private final ObjectMapper json;
  public DiscoveryService(JdbcClient db,List<SemanticDiscoveryProvider> providers,SafeRdfParser parser,ObjectMapper json){this.db=db;this.providers=List.copyOf(providers);this.parser=parser;this.json=json;}
  public static final class ProviderUnavailable extends RuntimeException {
    public ProviderUnavailable(){super("SEM_DISCOVERY_NO_ENABLED_PROVIDER");}
  }
  @Transactional public UUID request(String type,String intent,List<String> languages,String actor){
    if(providers.stream().noneMatch(SemanticDiscoveryProvider::enabled))throw new ProviderUnavailable();
    UUID id=UUID.randomUUID();db.sql("insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,preferred_languages,state,created_by_subject) values(:i,:t,:n,:l,'PENDING',:a)").param("i",id).param("t",type).param("n",intent).param("l",languages.toArray(String[]::new)).param("a",actor).update();return id;
  }
  public List<Map<String,Object>> candidates(UUID request){return db.sql("select candidate_id,provider_id,canonical_uri,artifact_type,provider_trust,score,match_reasons,gaps,expires_at from ouf_sem.discovery_candidate where request_id=:r and expires_at>transaction_timestamp() order by score desc,canonical_uri").param("r",request).query().listOfRows();}
  @Transactional public UUID adopt(UUID candidate,String semanticId,String namespace,String localName,String owner,String authority,String actor){return db.sql("select ouf_sem.adopt_candidate(:c,:s,:n,:l,:o,:u,:a)").param("c",candidate).param("s",semanticId).param("n",namespace).param("l",localName).param("o",owner).param("u",authority).param("a",actor).query(UUID.class).single();}
  @Transactional public UUID adopt(UUID request,UUID candidate,String semanticId,String namespace,String localName,String owner,String authority,String actor){
    var rows=db.sql("select candidate_id from ouf_sem.discovery_candidate where candidate_id=:c and request_id=:r for update").param("c",candidate).param("r",request).query(UUID.class).list();
    if(rows.size()!=1)throw new NoSuchElementException("SEMANTIC_CANDIDATE_NOT_FOUND");
    return adopt(candidate,semanticId,namespace,localName,owner,authority,actor);
  }
  /** Remote I/O is outside a DB transaction. Only the final generation CAS publishes bytes. */
  public int executeOne(){
    var jobs=db.sql("select * from ouf_sem.claim_discovery_job('semantic-discovery-worker',120)").query().listOfRows();
    if(jobs.isEmpty())return 0;
    var job=jobs.getFirst();UUID id=(UUID)job.get("request_id");long generation=((Number)job.get("worker_generation")).longValue();
    var candidates=new ArrayList<Map<String,Object>>();
    var enabled=providers.stream().filter(SemanticDiscoveryProvider::enabled).toList();
    if(enabled.isEmpty()){finish(id,generation,"BLOCKED","SEM_DISCOVERY_NO_ENABLED_PROVIDER",List.of(),null);return 1;}
    // Provider identity must be unique: sharing tokens between adapters is unsafe.
    if(enabled.stream().map(SemanticDiscoveryProvider::providerId).distinct().count()!=enabled.size()){
      finish(id,generation,"BLOCKED","SEM_DISCOVERY_PROVIDER_IDENTITY_INVALID",List.of(),null);return 1;
    }
    for(var p:enabled){
      if(Thread.currentThread().isInterrupted()){finish(id,generation,"CANCELLED","PROVIDER_INTERRUPTED",List.of(),null);return 1;}
      var admission=read(db.sql("select ouf_sem.reserve_discovery_dependency(:r,:g,:p)::text")
        .param("r",id).param("g",generation).param("p",p.providerId()).query(String.class).single());
      if(!Boolean.TRUE.equals(admission.get("admitted"))){
        String state=admission.get("state").toString();
        if(!"STALE".equals(state))finish(id,generation,state,"SEM_DISCOVERY_DEPENDENCY_PAUSED",List.of(),admission.get("next"));
        return 1;
      }
      long token=((Number)admission.get("generation")).longValue();
      try{
        var query=new SemanticDiscoveryProvider.Query(job.get("requested_artifact_type").toString(),job.get("intent").toString(),languages(job.get("preferred_languages")));
        var result=p.search(query);
        if(result.size()>64 || candidates.size()+result.size()>256)throw new IllegalArgumentException("candidate bound");
        for(var c:result){
          var parsed=parser.parse(c.content(),c.mediaType());
          var item=new LinkedHashMap<String,Object>();
          item.put("provider",p.providerId());item.put("uri",c.canonicalUri());item.put("source",c.sourceLocation());
          item.put("type",c.artifactType());item.put("trust",c.trust());item.put("score",c.score());
          item.put("reasons",c.reasons());item.put("gaps",c.gaps());item.put("hash",parsed.contentHash());
          item.put("mediaType",c.mediaType());item.put("bytes",Base64.getEncoder().encodeToString(c.content()));candidates.add(item);
        }
      }catch(RuntimeException error){
        var decision=ProviderFailurePolicy.exception(error);
        if(decision.kind()==ProviderFailurePolicy.Kind.CANCELLED)Thread.currentThread().interrupt();
        if(!providerFinished(id,generation,p.providerId(),token,decision.kind().name(),decision.code(),decision.retryAfter().toSeconds()))return 1;
        var dependency=db.sql("select state,next_attempt_at from ouf_sem.discovery_dependency where scope_subject=:a and provider_id=:p")
          .param("a",job.get("created_by_subject")).param("p",p.providerId()).query().singleRow();
        String state=decision.kind()==ProviderFailurePolicy.Kind.CANCELLED?"CANCELLED":dependency.get("state").toString();
        finish(id,generation,state,decision.code(),List.of(),dependency.get("next_attempt_at"));return 1;
      }
      if(!providerFinished(id,generation,p.providerId(),token,"SUCCESS",null,0))return 1;
    }
    finish(id,generation,"SUCCESS",null,candidates,null);return 1;
  }
  private boolean providerFinished(UUID id,long generation,String provider,long token,String kind,String code,long delay){
    return db.sql("select ouf_sem.finish_discovery_dependency(:r,:g,:p,:t,:k,:c,:d)")
      .param("r",id).param("g",generation).param("p",provider).param("t",token).param("k",kind).param("c",code).param("d",(double)delay).query(Boolean.class).single();
  }
  private boolean finish(UUID id,long generation,String outcome,String code,List<Map<String,Object>> candidates,Object next){
    OffsetDateTime nextAt=next==null?null:next instanceof OffsetDateTime value?value:next instanceof java.sql.Timestamp value?value.toInstant().atOffset(java.time.ZoneOffset.UTC):OffsetDateTime.parse(next.toString());
    return db.sql("select ouf_sem.finish_discovery_job(:r,:g,:o,:c,cast(:b as jsonb),:n)")
      .param("r",id).param("g",generation).param("o",outcome).param("c",code).param("b",write(candidates)).param("n",nextAt).query(Boolean.class).single();
  }
  private Map<String,Object> read(String value){try{return json.readValue(value,new com.fasterxml.jackson.core.type.TypeReference<Map<String,Object>>(){});}catch(Exception e){throw new IllegalStateException("SEM_DISCOVERY_STATE_INVALID");}}
  private static List<String> languages(Object value){if(value instanceof String[] a)return List.of(a);if(value instanceof java.sql.Array a){try{return List.of((String[])a.getArray());}catch(Exception ignored){return List.of();}}return List.of();}
  private String write(Object v){try{return json.writeValueAsString(v);}catch(Exception e){throw new IllegalArgumentException(e);}}
}


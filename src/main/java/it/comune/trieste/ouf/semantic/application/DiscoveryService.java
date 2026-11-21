package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import it.comune.trieste.ouf.semantic.adapters.discovery.ProviderFailurePolicy;
import java.time.OffsetDateTime;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.util.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.info.BuildProperties;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class DiscoveryService {
  private static final Logger log=LoggerFactory.getLogger(DiscoveryService.class);
  private final String workerVersion;
  private final JdbcClient db;private final List<SemanticDiscoveryProvider> providers;private final SafeRdfParser parser;private final ObjectMapper json;
  public DiscoveryService(JdbcClient db,List<SemanticDiscoveryProvider> providers,SafeRdfParser parser,ObjectMapper json){
    this(db,providers,parser,json,null);
  }
  @Autowired
  public DiscoveryService(JdbcClient db,List<SemanticDiscoveryProvider> providers,SafeRdfParser parser,ObjectMapper json,
      BuildProperties build){
    String workerVersion=build==null?null:build.getVersion();
    if(build!=null && (workerVersion==null || !workerVersion.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,63}")))
      throw new IllegalArgumentException("DISCOVERY_WORKER_VERSION_INVALID");
    this.db=db;this.providers=List.copyOf(providers);this.parser=parser;this.json=json;this.workerVersion=workerVersion;
  }
  public static final class ProviderUnavailable extends RuntimeException {
    public ProviderUnavailable(){super("SEM_DISCOVERY_NO_ENABLED_PROVIDER");}
  }
  @Transactional public UUID request(String type,String intent,List<String> languages,String actor){
    if(providers.stream().noneMatch(SemanticDiscoveryProvider::enabled))throw new ProviderUnavailable();
    UUID id=UUID.randomUUID();db.sql("insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,preferred_languages,state,created_by_subject) values(:i,:t,:n,:l,'PENDING',:a)").param("i",id).param("t",type).param("n",intent).param("l",languages.toArray(String[]::new)).param("a",actor).update();return id;
  }
  public List<Map<String,Object>> candidates(UUID request){return db.sql("""
      select candidate_id,provider_id,canonical_uri,artifact_type,provider_trust,score,match_reasons,gaps,expires_at
      from ouf_sem.discovery_candidate where request_id=:r and expires_at>transaction_timestamp()
      order by score desc,canonical_uri collate "C"
      """).param("r",request).query().listOfRows();}
  @Transactional public UUID adopt(UUID candidate,String semanticId,String namespace,String localName,String owner,String authority,String actor){
    UUID request=db.sql("select request_id from ouf_sem.discovery_candidate where candidate_id=:c")
        .param("c",candidate).query(UUID.class).optional().orElseThrow(()->new NoSuchElementException("SEMANTIC_CANDIDATE_NOT_FOUND"));
    return adopt(request,candidate,semanticId,namespace,localName,owner,authority,actor);
  }
  @Transactional public UUID adopt(UUID request,UUID candidate,String semanticId,String namespace,String localName,String owner,String authority,String actor){
    var rows=db.sql("""
        select c.canonical_uri,c.media_type,c.content_hash,c.content_bytes,c.ontology_rdf,c.ontology_sha256,c.adopted_artifact_id,
               c.expires_at<=clock_timestamp() expired
        from ouf_sem.discovery_candidate c join ouf_sem.discovery_request j using(request_id)
        where c.candidate_id=:c and j.request_id=:r and j.created_by_subject=:actor
          and j.created_by_subject not like 'mcp-discovery-v1:%' for update of c
        """).param("c",candidate).param("r",request).param("actor",actor).query().listOfRows();
    if(rows.size()!=1)throw new NoSuchElementException("SEMANTIC_CANDIDATE_NOT_FOUND");
    var row=rows.getFirst();
    if(Boolean.TRUE.equals(row.get("expired")))throw new GovernanceService.Conflict("CANDIDATE_EXPIRED");
    if(row.get("adopted_artifact_id") instanceof UUID artifact)return artifact;
    var model=new PublishedRdfSnapshot().verifiedModel((byte[])row.get("content_bytes"),
        (String)row.get("media_type"),(String)row.get("content_hash"));
    try {
      var metadata=CandidateAdoptionService.metadata(model.getResource((String)row.get("canonical_uri")),
          (byte[])row.get("ontology_rdf"),(String)row.get("ontology_sha256"));
      return db.sql("select ouf_sem.adopt_candidate(:c,:s,:n,:l,:o,:u,:a,:publisher,:license,'{}'::jsonb,cast(:description as jsonb))")
          .param("c",candidate).param("s",semanticId).param("n",namespace).param("l",localName)
          .param("o",owner).param("u",authority).param("a",actor)
          .param("publisher",metadata.publisher()).param("license",metadata.license())
          .param("description",write(metadata.descriptions())).query(UUID.class).single();
    } finally {model.close();}
  }
  /** Remote I/O is outside a DB transaction. Only the final generation CAS publishes bytes. */
  public int executeOne(){
    var enabled=providers.stream().filter(SemanticDiscoveryProvider::enabled).toList();
    var jobs=db.sql("select * from ouf_sem.claim_discovery_job('semantic-discovery-worker',120)").query().listOfRows();
    if(jobs.isEmpty() && workerVersion!=null && !enabled.isEmpty()){
      jobs=db.sql("select * from ouf_sem.claim_discovery_version_probe(:v,:providers)")
          .param("v",workerVersion).param("providers",enabled.stream().map(SemanticDiscoveryProvider::providerId).toArray(String[]::new))
          .query().listOfRows();
    }
    if(jobs.isEmpty())return 0;
    var job=jobs.getFirst();UUID id=(UUID)job.get("request_id");long generation=((Number)job.get("worker_generation")).longValue();
    var candidates=new ArrayList<Map<String,Object>>();
    int invalid=0, bound=0, fetchDenied=0;
    if(enabled.isEmpty()){finish(id,generation,"BLOCKED","SEM_DISCOVERY_NO_ENABLED_PROVIDER",List.of(),null);return 1;}
    // Provider identity must be unique: sharing tokens between adapters is unsafe.
    if(enabled.stream().map(SemanticDiscoveryProvider::providerId).distinct().count()!=enabled.size()){
      finish(id,generation,"BLOCKED","SEM_DISCOVERY_PROVIDER_IDENTITY_INVALID",List.of(),null);return 1;
    }
    for(var p:enabled){
      if(Thread.currentThread().isInterrupted()){finish(id,generation,"CANCELLED","PROVIDER_INTERRUPTED",List.of(),null);return 1;}
      var admission=read(db.sql("select ouf_sem.reserve_discovery_dependency(:r,:g,:p,:v)::text")
        .param("r",id).param("g",generation).param("p",p.providerId()).param("v",workerVersion).query(String.class).single());
      if(!Boolean.TRUE.equals(admission.get("admitted"))){
        String state=admission.get("state").toString();
        if(!"STALE".equals(state))finish(id,generation,state,"SEM_DISCOVERY_DEPENDENCY_PAUSED",List.of(),admission.get("next"));
        return 1;
      }
      long token=((Number)admission.get("generation")).longValue();
      try{
        var started=java.time.Instant.now();
        var remaining=db.sql("select floor(extract(epoch from (busy_until-clock_timestamp()))*1000)::bigint from ouf_sem.discovery_dependency where scope_subject=:a and provider_id=:p and generation=:g")
            .param("a",job.get("created_by_subject")).param("p",p.providerId()).param("g",token)
            .query(Long.class).optional();
        if(remaining.isEmpty())return 1;
        var query=new SemanticDiscoveryProvider.Query(job.get("requested_artifact_type").toString(),job.get("intent").toString(),
            languages(job.get("preferred_languages")),started.plusMillis(remaining.get()));
        var result=p.searchWithExclusions(query);
        long attempted=(long)result.candidates().size()+result.fetchDenied()+result.rdfInvalid()+result.rdfBound();
        if(attempted>64 || candidates.size()+invalid+bound+fetchDenied+attempted>256)throw new IllegalArgumentException("candidate bound");
        fetchDenied+=result.fetchDenied();
        invalid+=result.rdfInvalid();
        bound+=result.rdfBound();
        for(var c:result.candidates()){
          SafeRdfParser.Parsed parsed;
          try{parsed=parser.parse(c.content(),c.mediaType());}
          catch(SafeRdfParser.UnsafeRdf rejected){
            if("RDF_SIZE_LIMIT".equals(rejected.getMessage()))bound++;
            else invalid++;
            continue;
          }
          var item=new LinkedHashMap<String,Object>();
          item.put("provider",p.providerId());item.put("uri",c.canonicalUri());item.put("source",c.sourceLocation());
          item.put("type",c.artifactType());item.put("trust",c.trust());item.put("score",c.score());
          item.put("reasons",c.reasons());item.put("gaps",c.gaps());item.put("hash",parsed.contentHash());
          item.put("labels",c.labels());
          if(c.ontologyProvenance()!=null)item.put("ontology",Base64.getEncoder().encodeToString(c.ontologyProvenance()));
          item.put("mediaType",c.mediaType());item.put("bytes",Base64.getEncoder().encodeToString(c.content()));candidates.add(item);
        }
      }catch(RuntimeException error){
        var decision=ProviderFailurePolicy.exception(error);
        if("PROVIDER_UNKNOWN".equals(decision.code()))logUnknown(error);
        if(decision.kind()==ProviderFailurePolicy.Kind.CANCELLED)Thread.currentThread().interrupt();
        if(!providerFinished(id,generation,p.providerId(),token,decision.kind().name(),decision.code(),decision.retryAfter().toSeconds()))return 1;
        var dependency=db.sql("select state,next_attempt_at from ouf_sem.discovery_dependency where scope_subject=:a and provider_id=:p")
          .param("a",job.get("created_by_subject")).param("p",p.providerId()).query().singleRow();
        String state=decision.kind()==ProviderFailurePolicy.Kind.CANCELLED?"CANCELLED":dependency.get("state").toString();
        finish(id,generation,state,decision.code(),List.of(),dependency.get("next_attempt_at"));return 1;
      }
      if(!providerFinished(id,generation,p.providerId(),token,"SUCCESS",null,0))return 1;
    }
    db.sql("select ouf_sem.publish_discovery_candidates(:r,:g,cast(:b as jsonb),:invalid,:bound,:denied)")
      .param("r",id).param("g",generation).param("b",write(candidates)).param("invalid",invalid).param("bound",bound)
      .param("denied",fetchDenied).query(Boolean.class).single();
    return 1;
  }
  private static void logUnknown(Throwable error){
    String location="unavailable";
    Throwable cause=error, innermost=error;
    for(int depth=0;cause!=null && depth<16;depth++,cause=cause.getCause()){
      innermost=cause;
      for(var frame:cause.getStackTrace()){
        if(frame.getClassName().startsWith("it.comune.trieste.ouf.semantic.")){
          location=frame.getClassName()+":"+frame.getLineNumber();
          break;
        }
      }
    }
    log.warn("Unclassified discovery exception type={} frame={}",innermost.getClass().getName(),location);
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

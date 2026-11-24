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
import org.springframework.transaction.support.TransactionTemplate;

@Service
@org.springframework.boot.context.properties.EnableConfigurationProperties(ProviderCapacityProfile.class)
public class DiscoveryService {
  private static final Logger log=LoggerFactory.getLogger(DiscoveryService.class);
  private final String workerVersion;
  private final ProviderCapacityProfile capacity;
  private final TransactionTemplate transactions;
  private final JdbcClient db;private final List<SemanticDiscoveryProvider> providers;private final SafeRdfParser parser;private final ObjectMapper json;
  public DiscoveryService(JdbcClient db,List<SemanticDiscoveryProvider> providers,SafeRdfParser parser,ObjectMapper json,
      TransactionTemplate transactions){
    this(db,providers,parser,json,transactions,null);
  }
  public DiscoveryService(JdbcClient db,List<SemanticDiscoveryProvider> providers,SafeRdfParser parser,ObjectMapper json,
      TransactionTemplate transactions,BuildProperties build){
    this(db,providers,parser,json,transactions,build,ProviderCapacityProfile.defaults());
  }
  @Autowired
  public DiscoveryService(JdbcClient db,List<SemanticDiscoveryProvider> providers,SafeRdfParser parser,ObjectMapper json,
      TransactionTemplate transactions,BuildProperties build,ProviderCapacityProfile capacity){
    this.capacity=capacity;
    String workerVersion=build==null?null:build.getVersion();
    if(build!=null && (workerVersion==null || !workerVersion.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,63}")))
      throw new IllegalArgumentException("DISCOVERY_WORKER_VERSION_INVALID");
    this.db=db;this.providers=List.copyOf(providers);this.parser=parser;this.json=json;this.workerVersion=workerVersion;
    this.transactions=transactions;
  }
  public static final class ProviderUnavailable extends RuntimeException {
    public ProviderUnavailable(){super("SEM_DISCOVERY_NO_ENABLED_PROVIDER");}
  }
  @Transactional public UUID request(String type,String intent,List<String> languages,String actor){
    if(providers.stream().noneMatch(SemanticDiscoveryProvider::enabled))throw new ProviderUnavailable();
    UUID id=UUID.randomUUID();db.sql("insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,preferred_languages,state,created_by_subject) values(:i,:t,:n,:l,'PENDING',:a)").param("i",id).param("t",type).param("n",intent).param("l",languages.toArray(String[]::new)).param("a",actor).update();return id;
  }
  public List<Map<String,Object>> candidates(UUID request){return candidates(request,false);}
  List<Map<String,Object>> candidates(UUID request,boolean includeAdoption){return db.sql("""
      select candidate_id,provider_id,canonical_uri,artifact_type,provider_trust,score,match_reasons,gaps,expires_at%s
      from ouf_sem.discovery_candidate where request_id=:r and expires_at>transaction_timestamp()
      order by score desc,canonical_uri collate "C"
      """.formatted(includeAdoption?",adopted_artifact_id":"")).param("r",request).query().listOfRows();}
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
  private record Claim(Map<String,Object> job,Map<String,Long> tokens){}
  private Claim claim(List<SemanticDiscoveryProvider> enabled,org.springframework.transaction.TransactionStatus tx) {
    String[] ids=enabled.stream().map(SemanticDiscoveryProvider::providerId).toArray(String[]::new);
    var jobs=db.sql("select * from ouf_sem.claim_discovery_owner_job(?)").param(ids).query().listOfRows();
    if(jobs.isEmpty() && workerVersion!=null && !enabled.isEmpty()){
      jobs=db.sql("select * from ouf_sem.claim_discovery_version_probe(:v,:providers)")
          .param("v",workerVersion).param("providers",ids)
          .query().listOfRows();
    }
    if(jobs.isEmpty())return null;
    var job=jobs.getFirst();
    UUID id=(UUID)job.get("request_id");
    long generation=((Number)job.get("worker_generation")).longValue();
    var tokens=new LinkedHashMap<String,Long>();
    var claimed=new Claim(job,tokens);
    if(enabled.isEmpty() || enabled.stream().map(SemanticDiscoveryProvider::providerId).distinct().count()!=enabled.size()){
      finish(id,generation,"BLOCKED",enabled.isEmpty()?"SEM_DISCOVERY_NO_ENABLED_PROVIDER":
          "SEM_DISCOVERY_PROVIDER_IDENTITY_INVALID",List.of(),null);
      return claimed;
    }
    // A claim and all its subject leases become visible together. Roll back partial
    // admission if any dependency is already owned or paused.
    Object savepoint=tx.createSavepoint();
    for(var p:enabled){
      String provider=p.providerId();
      boolean owner=db.sql("select ouf_sem.bind_discovery_owner(?,?,?)").param(id)
          .param(job.get("created_by_subject")).param(provider).query(Boolean.class).single();
      var admission=owner?read(db.sql("select ouf_sem.reserve_owner_dependency(:r,:g,:p,:v)::text")
          .param("r",id).param("g",generation).param("p",provider).param("v",workerVersion).query(String.class).single())
          :Map.<String,Object>of("admitted",false,"state","RETRY_WAIT");
      if(!Boolean.TRUE.equals(admission.get("admitted"))){
        tx.rollbackToSavepoint(savepoint);
        tx.releaseSavepoint(savepoint);
        tokens.clear();
        String state=admission.get("state").toString();
        if("PAUSED_EXHAUSTED".equals(state)){
          // Keep V15's exhaustion transition even if a previous adapter in this
          // multi-provider claim had to be rolled back.
          db.sql("""
              update ouf_sem.discovery_dependency set state='PAUSED_EXHAUSTED'
              where scope_subject=? and provider_id=? and state in ('ACTIVE','RETRY_WAIT')
                and (attempts>=128 or budget_deadline<=clock_timestamp())
              """).param(job.get("created_by_subject")).param(provider).update();
        }
        if(!"STALE".equals(state))finish(id,generation,state,"SEM_DISCOVERY_DEPENDENCY_PAUSED",List.of(),admission.get("next"));
        return claimed;
      }
      tokens.put(provider,((Number)admission.get("generation")).longValue());
    }
    tx.releaseSavepoint(savepoint);
    return claimed;
  }

  /** All remote work is outside the claim and publication transactions. */
  @Transactional(propagation=org.springframework.transaction.annotation.Propagation.NEVER)
  public int executeOne(){
    db.sql("select ouf_sem.reconcile_discovery_slots()").query().singleRow();
    var enabled=providers.stream().filter(SemanticDiscoveryProvider::enabled)
        .sorted(Comparator.comparing(SemanticDiscoveryProvider::providerId)).toList();
    var claim=transactions.execute(tx->claim(enabled,tx));
    if(claim==null)return 0;
    if(claim.tokens().isEmpty())return 1;
    var job=claim.job();UUID id=(UUID)job.get("request_id");long generation=((Number)job.get("worker_generation")).longValue();
    var candidates=new ArrayList<Map<String,Object>>();
    var results=new LinkedHashMap<String,ProviderFailurePolicy.Decision>();
    int invalid=0, bound=0, fetchDenied=0, namespaceExcluded=0;
    for(var p:enabled){
      long token=claim.tokens().get(p.providerId());
      try{
        if(Thread.currentThread().isInterrupted())
          throw new it.comune.trieste.ouf.semantic.adapters.discovery.BoundedGatewayClient.ProviderFailure("PROVIDER_INTERRUPTED");
        var started=java.time.Instant.now();
        var remaining=db.sql("select floor(extract(epoch from (busy_until-clock_timestamp()))*1000)::bigint from ouf_sem.discovery_dependency where scope_subject=:a and provider_id=:p and generation=:g")
            .param("a",job.get("created_by_subject")).param("p",p.providerId()).param("g",token)
            .query(Long.class).optional();
        if(remaining.isEmpty() || remaining.get()<=0)return 1;
        var query=new SemanticDiscoveryProvider.Query(job.get("requested_artifact_type").toString(),job.get("intent").toString(),
            languages(job.get("preferred_languages")),started.plusMillis(remaining.get()));
        SemanticDiscoveryProvider.SearchResult result;
        if(p instanceof NamespaceFilteredDiscoveryProvider filtered){
          var traffic=new JobDiscoveryTraffic(db,transactions,capacity,id,generation,p.providerId(),token);
          var response=filtered.searchWithNamespaceFilter(query,traffic);
          results.put(p.providerId(),traffic.optionalFailure());
          namespaceExcluded=Math.addExact(namespaceExcluded,response.namespaceExcluded());
          result=response.fetched();
        }else{
          result=p.searchWithExclusions(query);
          results.put(p.providerId(),null);
        }
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
      }catch(JobDiscoveryTraffic.Stale stale){
        return 1;
      }catch(JobDiscoveryTraffic.SlotWaitExpired timeout){
        complete(claim,results,p.providerId(),true,List.of(),0,0,0,0);
        return 1;
      }catch(RuntimeException error){
        var decision=error instanceof JobDiscoveryTraffic.ProfileDrift
            ?new ProviderFailurePolicy.Decision(ProviderFailurePolicy.Kind.BLOCKED,"DISCOVERY_CAPACITY_CONFIG_DRIFT",java.time.Duration.ZERO)
            :ProviderFailurePolicy.exception(error);
        if("PROVIDER_UNKNOWN".equals(decision.code()))logUnknown(error);
        if(decision.kind()==ProviderFailurePolicy.Kind.CANCELLED)Thread.currentThread().interrupt();
        results.put(p.providerId(),decision);
        complete(claim,results,p.providerId(),false,List.of(),0,0,0,0);
        return 1;
      }
    }
    complete(claim,results,null,false,candidates,invalid,bound,fetchDenied,namespaceExcluded);
    return 1;
  }

  private void complete(Claim claim,Map<String,ProviderFailurePolicy.Decision> results,String failed,
      boolean busy,List<Map<String,Object>> candidates,int invalid,int bound,int denied,int namespaceExcluded){
    UUID id=(UUID)claim.job().get("request_id");
    long generation=((Number)claim.job().get("worker_generation")).longValue();
    String actor=(String)claim.job().get("created_by_subject");
    String payload=write(candidates);
    transactions.executeWithoutResult(tx->{
      OffsetDateTime deadline=null;
      for(var lease:claim.tokens().entrySet()){
        String provider=lease.getKey();
        var until=db.sql("select ouf_sem.discovery_owner_deadline(?,?,?,?)")
            .param(id).param(generation).param(provider).param(lease.getValue()).query(OffsetDateTime.class).optional();
        if(until.isEmpty()){tx.setRollbackOnly();return;}
        if(deadline==null || until.get().isBefore(deadline))deadline=until.get();
        if(busy && !results.containsKey(provider)){
          // Park the same attempt across the short wait. Its next execution
          // receives a fresh worker generation and keeps its original budget.
          db.sql("""
              update ouf_sem.discovery_dependency set busy_until=null where scope_subject=?
              and provider_id=? and generation=? and active_request=? and request_generation=?
              """).param(actor).param(provider).param(lease.getValue()).param(id).param(generation).update();
        }else if(!closeDependency(id,generation,actor,provider,lease.getValue(),results)){
          tx.setRollbackOnly();return;
        }
      }
      boolean finished=failed==null
          ?publish(id,generation,actor,payload,candidates.size(),invalid,bound,denied,namespaceExcluded)
          :finishUnpublished(id,generation,actor,failed,busy,results.get(failed));
      if(!finished){tx.setRollbackOnly();return;}
      db.sql("""
          delete from ouf_sem.discovery_provider_owner o using ouf_sem.discovery_request r
          where o.request_id=r.request_id and r.request_id=? and r.state in ('SUCCEEDED','FAILED','CANCELLED')
          """).param(id).update();
      if(!db.sql("select clock_timestamp()<cast(? as timestamptz)").param(deadline).query(Boolean.class).single())
        tx.setRollbackOnly();
    });
  }

  private boolean closeDependency(UUID job,long generation,String actor,String provider,long token,
      Map<String,ProviderFailurePolicy.Decision> results){
    if(!results.containsKey(provider)){
      // Contention or an unvisited adapter provides no evidence about provider health.
      db.sql("""
          update ouf_sem.discovery_dependency set active_request=null,request_generation=null,busy_until=null
          where scope_subject=? and provider_id=? and generation=?
          """).param(actor).param(provider).param(token).update();
      db.sql("""
          update ouf_sem.discovery_attempt set completed_at=clock_timestamp(),outcome='DEFERRED'
          where scope_subject=? and provider_id=? and generation=?
          """).param(actor).param(provider).param(token).update();
      return true;
    }
    var failure=results.get(provider);
    if(failure==null)return providerFinished(job,generation,provider,token,"SUCCESS",null,0);
    var delay=failure.retryAfter();
    double seconds=delay.getSeconds()+(delay.getNano()==0?0d:1d);
    return providerFinished(job,generation,provider,token,failure.kind().name(),failure.code(),seconds);
  }

  private boolean finishUnpublished(UUID job,long generation,String actor,String provider,boolean busy,
      ProviderFailurePolicy.Decision decision){
    if(busy){
      return db.sql("""
          with pause as (select clock_timestamp()+make_interval(secs=>1+random()*0.2) as resume_at)
          update ouf_sem.discovery_request set state='PENDING',lease_until=null,
            recovery_state=case when resume_at>=budget_deadline then 'PAUSED_EXHAUSTED' else 'RETRY_WAIT' end,
            next_attempt_at=resume_at,last_error_code='SEM_DISCOVERY_PROVIDER_SLOT_BUSY'
          from pause where request_id=? and worker_generation=? and state='RUNNING'
            and recovery_state='ACTIVE' and lease_until>clock_timestamp() and budget_deadline>clock_timestamp()
          """).param(job).param(generation).update()==1;
    }
    var dependency=db.sql("select state,next_attempt_at from ouf_sem.discovery_dependency where scope_subject=? and provider_id=?")
        .param(actor).param(provider).query().singleRow();
    String state=decision.kind()==ProviderFailurePolicy.Kind.CANCELLED?"CANCELLED":dependency.get("state").toString();
    return finish(job,generation,state,decision.code(),List.of(),dependency.get("next_attempt_at"));
  }

  private boolean publish(UUID id,long generation,String actor,String payload,int count,
      int invalid,int bound,int denied,int namespaceExcluded){
      int completed=db.sql("""
          insert into ouf_sem.audit_event(event_id,event_type,subject_ref,resource_type,resource_id,detail_json)
          select :r,'DISCOVERY_COMPLETED',:actor,'DISCOVERY_REQUEST',cast(:r as text),
                 jsonb_build_object('completedCandidateCount',cast(:count as integer))
          from ouf_sem.publish_discovery_candidates(:r,:g,cast(:b as jsonb),:invalid,:bound,:denied) as p(succeeded)
          where p.succeeded
          """)
          .param("r",id).param("g",generation).param("b",payload).param("invalid",invalid).param("bound",bound)
          .param("denied",denied).param("actor",actor).param("count",count).update();
      if(completed==1 && namespaceExcluded>0){
        db.sql("""
            update ouf_sem.discovery_request
            set provider_policy=jsonb_set(provider_policy,'{namespaceExcluded}',to_jsonb(cast(:count as integer)))
            where request_id=:r
            """).param("count",namespaceExcluded).param("r",id).update();
      }
      return completed==1;
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
  private boolean providerFinished(UUID id,long generation,String provider,long token,String kind,String code,double delay){
    return db.sql("select ouf_sem.finish_owner_dependency(:r,:g,:p,:t,:k,:c,:d)")
      .param("r",id).param("g",generation).param("p",provider).param("t",token).param("k",kind).param("c",code).param("d",delay).query(Boolean.class).single();
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

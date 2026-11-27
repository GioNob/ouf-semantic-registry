package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import it.comune.trieste.ouf.semantic.adapters.discovery.ProviderFailurePolicy;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.util.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.info.BuildProperties;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionTemplate;

@Service
public class DiscoveryService {
  private static final Logger log=LoggerFactory.getLogger(DiscoveryService.class);
  private static final int COMPACT_TEXT_BYTES=160;
  private final String workerVersion;
  private final TransactionTemplate transactions;
  private final JdbcClient db;private final List<SemanticDiscoveryProvider> providers;private final SafeRdfParser parser;private final ObjectMapper json;
  public DiscoveryService(JdbcClient db,List<SemanticDiscoveryProvider> providers,SafeRdfParser parser,ObjectMapper json,
      TransactionTemplate transactions){
    this(db,providers,parser,json,transactions,null);
  }
  @Autowired
  public DiscoveryService(JdbcClient db,List<SemanticDiscoveryProvider> providers,SafeRdfParser parser,ObjectMapper json,
      TransactionTemplate transactions,BuildProperties build){
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

  public record CandidatePosition(long evidenceVersion, UUID candidateId, Instant expiresAt) {}
  public record CandidatePage(long evidenceVersion, long candidateCount, Instant evidenceExpiresAt,
      DiscoveryJobService.State state, DiscoveryJobService.RecoveryState recoveryState, long pollAfterSeconds,
      List<Map<String,Object>> candidates) {}

  // Negating the descending component gives PostgreSQL a single tuple range
  // in the index, including when an entire request has the same score.
  private static final String CANDIDATE_PAGE_ORDER = " order by (-score),canonical_uri collate \"C\",candidate_id limit :fetch";
  private static final String CANDIDATE_PAGE_SEEK =
      " and ((-score),canonical_uri collate \"C\",candidate_id) > (:rank,:uri,:candidate)";
  private static final String CANDIDATE_PAGE_FROM =
      " from ouf_sem.discovery_candidate where request_id=:request and expires_at>transaction_timestamp()";

  @Transactional(readOnly=true,isolation=Isolation.REPEATABLE_READ)
  public CandidatePage candidatePage(UUID request,String actor,int limit,boolean compact,CandidatePosition after) {
    var head=db.sql("""
        select r.state,r.recovery_state,r.preferred_languages,
          coalesce(h.evidence_version,0) as version,live.expires_at,
          coalesce(transaction_timestamp()>=:cursor_expiry,false) as cursor_expired,
          case when live.expires_at is null then 0 else h.candidate_count-(
            select count(*) from ouf_sem.discovery_candidate c
            where c.request_id=r.request_id and c.expires_at<=transaction_timestamp()
          ) end as total,
          greatest(5,ceil(extract(epoch from r.next_attempt_at-transaction_timestamp())))::bigint as poll_after
        from ouf_sem.discovery_request r left join ouf_sem.discovery_candidate_page_head h using(request_id)
        left join lateral (
          select c.expires_at
          from ouf_sem.discovery_candidate c where c.request_id=r.request_id and c.expires_at>transaction_timestamp()
          order by c.expires_at limit 1
        ) live on true
        where r.request_id=:request and r.created_by_subject=:actor
        """).param("request",request).param("actor",actor)
        .param("cursor_expiry",after==null?null:after.expiresAt().atOffset(ZoneOffset.UTC))
        .query((rs,n)->new CandidateHead(rs.getLong("version"),rs.getLong("total"),
            rs.getObject("expires_at",OffsetDateTime.class),rs.getBoolean("cursor_expired"),
            DiscoveryJobService.State.valueOf(rs.getString("state")),
            DiscoveryJobService.RecoveryState.valueOf(rs.getString("recovery_state")),rs.getLong("poll_after"),
            Arrays.asList((String[])rs.getArray("preferred_languages").getArray())))
        .optional().orElseThrow(()->new NoSuchElementException("SEM_DISCOVERY_REQUEST_NOT_FOUND"));
    // Use the original snapshot deadline with the same clock as the per-row filter.
    if(head.cursorExpired())throw new ArtifactService.Conflict("SEM_DISCOVERY_CURSOR_EXPIRED");
    boolean available=head.state()==DiscoveryJobService.State.SUCCEEDED && head.expiresAt()!=null;
    if(after!=null && (!available || head.version()!=after.evidenceVersion()))
      throw new ArtifactService.Conflict("SEM_DISCOVERY_CURSOR_STALE");
    List<Map<String,Object>> rows=available?candidateRows(request,limit,compact,after,head.languages()):List.of();
    return new CandidatePage(head.version(),available?head.total():0,available?head.expiresAt().toInstant():null,
        head.state(),head.recoveryState(),head.pollAfterSeconds(),rows);
  }

  private record CandidateHead(long version,long total,OffsetDateTime expiresAt,boolean cursorExpired,
      DiscoveryJobService.State state,DiscoveryJobService.RecoveryState recoveryState,long pollAfterSeconds,
      List<String> languages) {}

  static String candidatePageSql(boolean compact,boolean continuation) {
    String fields=compact?"candidate_id,canonical_uri,score,adopted_artifact_id,discovery_labels::text as labels":
        "candidate_id,provider_id,canonical_uri,artifact_type,provider_trust,score,match_reasons,gaps,expires_at,adopted_artifact_id";
    return "select "+fields+CANDIDATE_PAGE_FROM+(continuation?CANDIDATE_PAGE_SEEK:"")+CANDIDATE_PAGE_ORDER;
  }

  private List<Map<String,Object>> candidateRows(UUID request,int limit,boolean compact,CandidatePosition after,List<String> languages) {
    var query=db.sql(candidatePageSql(compact,after!=null)).param("request",request).param("fetch",limit+1);
    if(after!=null) {
      var anchor=db.sql("""
          select (-score) as rank,canonical_uri from ouf_sem.discovery_candidate
          where candidate_id=:candidate and request_id=:request
          """).param("candidate",after.candidateId()).param("request",request)
          .query((rs,n)->new CandidateKey(rs.getBigDecimal("rank"),rs.getString("canonical_uri")))
          .optional().orElseThrow(()->new ArtifactService.Conflict("SEM_DISCOVERY_CURSOR_STALE"));
      query.param("rank",anchor.rank()).param("uri",anchor.uri()).param("candidate",after.candidateId());
    }
    var rows=query.query().listOfRows();
    return compact?rows.stream().map(row->compactCandidate(row,languages)).toList():rows;
  }

  private record CandidateKey(java.math.BigDecimal rank,String uri) {}

  private Map<String,Object> compactCandidate(Map<String,Object> row,List<String> languages) {
    var out=new LinkedHashMap<String,Object>();
    String uri=(String)row.get("canonical_uri");
    String local=org.apache.jena.rdf.model.ResourceFactory.createResource(uri).getLocalName();
    String term=local==null || local.isEmpty()?uri:local;
    var labels=read((String)row.get("labels"));
    String label=languages.stream().map(labels::get).filter(String.class::isInstance).map(String.class::cast)
        .filter(value->!value.isBlank()).findFirst().orElseGet(()->new TreeMap<>(labels).values().stream()
            .filter(String.class::isInstance).map(String.class::cast).filter(value->!value.isBlank()).findFirst().orElse(term));
    var truncated=new ArrayList<String>();
    out.put("candidateId",row.get("candidate_id"));
    out.put("canonicalUri",uri);
    out.put("term",shortText(term,"term",truncated));
    out.put("label",shortText(label,"label",truncated));
    out.put("score",row.get("score"));
    out.put("state",row.get("adopted_artifact_id")==null?"AVAILABLE":"ADOPTED");
    if(!truncated.isEmpty())out.put("truncatedFields",truncated);
    return out;
  }

  private String shortText(String value,String field,List<String> truncated) {
    int low=0,high=Math.min(COMPACT_TEXT_BYTES,value.codePointCount(0,value.length()));
    try {
      while(low<high) {
        int middle=(low+high+1)/2;
        String prefix=value.substring(0,value.offsetByCodePoints(0,middle));
        // Count the escaped UTF-8 bytes, excluding the two JSON quotes.
        if(json.writeValueAsBytes(prefix).length<=COMPACT_TEXT_BYTES+2)low=middle;
        else high=middle-1;
      }
    }catch(JsonProcessingException e){throw new IllegalStateException("SEM_DISCOVERY_PAGE_SERIALIZATION_FAILED",e);}
    int end=value.offsetByCodePoints(0,low);
    if(end<value.length())truncated.add(field);
    return value.substring(0,end);
  }
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
    int invalid=0, bound=0, fetchDenied=0, namespaceExcluded=0;
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
        SemanticDiscoveryProvider.SearchResult result;
        if(p instanceof NamespaceFilteredDiscoveryProvider filtered){
          var response=filtered.searchWithNamespaceFilter(query,new JobDiscoveryTraffic(db,id));
          namespaceExcluded=Math.addExact(namespaceExcluded,response.namespaceExcluded());
          result=response.fetched();
        }else{
          result=p.searchWithExclusions(query);
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
      }catch(RuntimeException error){
        var decision=ProviderFailurePolicy.exception(error);
        if("PROVIDER_UNKNOWN".equals(decision.code()))logUnknown(error);
        if(decision.kind()==ProviderFailurePolicy.Kind.CANCELLED)Thread.currentThread().interrupt();
        var delay=decision.retryAfter();
        long seconds=delay.getSeconds()+(delay.getNano()==0?0:1);
        if(!providerFinished(id,generation,p.providerId(),token,decision.kind().name(),decision.code(),seconds))return 1;
        var dependency=db.sql("select state,next_attempt_at from ouf_sem.discovery_dependency where scope_subject=:a and provider_id=:p")
          .param("a",job.get("created_by_subject")).param("p",p.providerId()).query().singleRow();
        String state=decision.kind()==ProviderFailurePolicy.Kind.CANCELLED?"CANCELLED":dependency.get("state").toString();
        finish(id,generation,state,decision.code(),List.of(),dependency.get("next_attempt_at"));return 1;
      }
      if(!providerFinished(id,generation,p.providerId(),token,"SUCCESS",null,0))return 1;
    }
    publish(id,generation,(String)job.get("created_by_subject"),candidates,invalid,bound,fetchDenied,namespaceExcluded);
    return 1;
  }
  private void publish(UUID id,long generation,String actor,List<Map<String,Object>> candidates,
      int invalid,int bound,int denied,int namespaceExcluded){
    String payload=write(candidates);
    transactions.executeWithoutResult(tx->{
      // V17 inserts every supplied candidate or rolls back. A failed generation CAS emits no evidence.
      int completed=db.sql("""
          insert into ouf_sem.audit_event(event_id,event_type,subject_ref,resource_type,resource_id,detail_json)
          select :r,'DISCOVERY_COMPLETED',:actor,'DISCOVERY_REQUEST',cast(:r as text),
                 jsonb_build_object('completedCandidateCount',cast(:count as integer))
          from ouf_sem.publish_discovery_candidates(:r,:g,cast(:b as jsonb),:invalid,:bound,:denied) as p(succeeded)
          where p.succeeded
          """)
          .param("r",id).param("g",generation).param("b",payload).param("invalid",invalid).param("bound",bound)
          .param("denied",denied).param("actor",actor).param("count",candidates.size()).update();
      if(completed==1 && namespaceExcluded>0){
        db.sql("""
            update ouf_sem.discovery_request
            set provider_policy=jsonb_set(provider_policy,'{namespaceExcluded}',to_jsonb(cast(:count as integer)))
            where request_id=:r
            """).param("count",namespaceExcluded).param("r",id).update();
      }
    });
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

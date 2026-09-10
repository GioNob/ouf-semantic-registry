package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.util.*;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class DiscoveryService {
  private final JdbcClient db;private final List<SemanticDiscoveryProvider> providers;private final SafeRdfParser parser;private final ObjectMapper json;
  public DiscoveryService(JdbcClient db,List<SemanticDiscoveryProvider> providers,SafeRdfParser parser,ObjectMapper json){this.db=db;this.providers=List.copyOf(providers);this.parser=parser;this.json=json;}
  @Transactional public UUID request(String type,String intent,List<String> languages,String actor){UUID id=UUID.randomUUID();db.sql("insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,preferred_languages,state,created_by_subject) values(:i,:t,:n,:l,'PENDING',:a)").param("i",id).param("t",type).param("n",intent).param("l",languages.toArray(String[]::new)).param("a",actor).update();return id;}
  public List<Map<String,Object>> candidates(UUID request){return db.sql("select candidate_id,provider_id,canonical_uri,artifact_type,provider_trust,score,match_reasons,gaps,expires_at from ouf_sem.discovery_candidate where request_id=:r and expires_at>transaction_timestamp() order by score desc,canonical_uri").param("r",request).query().listOfRows();}
  @Transactional public UUID adopt(UUID candidate,String semanticId,String namespace,String localName,String owner,String authority,String actor){return db.sql("select ouf_sem.adopt_candidate(:c,:s,:n,:l,:o,:u,:a)").param("c",candidate).param("s",semanticId).param("n",namespace).param("l",localName).param("o",owner).param("u",authority).param("a",actor).query(UUID.class).single();}
  public int executeOne(){var jobs=db.sql("select * from ouf_sem.claim_discovery_job('semantic-discovery-worker',30)").query().listOfRows();if(jobs.isEmpty())return 0;var job=jobs.get(0);UUID id=(UUID)job.get("request_id");List<String> failures=new ArrayList<>();int successfulProviders=0;for(var p:providers){try{var q=new SemanticDiscoveryProvider.Query(job.get("requested_artifact_type").toString(),job.get("intent").toString(),languages(job.get("preferred_languages")));for(var c:p.search(q)){var parsed=parser.parse(c.content(),c.mediaType());db.sql("insert into ouf_sem.discovery_candidate(candidate_id,request_id,provider_id,canonical_uri,source_location,artifact_type,provider_trust,score,match_reasons,gaps,normalized_payload,content_hash,media_type,content_bytes,expires_at) values(:i,:r,:p,:u,:s,:t,:x,:n,cast(:m as jsonb),cast(:g as jsonb),'{}',:h,:y,:b,transaction_timestamp()+interval '24 hours') on conflict do nothing").param("i",UUID.randomUUID()).param("r",id).param("p",p.providerId()).param("u",c.canonicalUri()).param("s",c.sourceLocation()).param("t",c.artifactType()).param("x",c.trust()).param("n",c.score()).param("m",write(c.reasons())).param("g",write(c.gaps())).param("h",parsed.contentHash()).param("y",c.mediaType()).param("b",c.content()).update();}successfulProviders++;}catch(RuntimeException e){failures.add(p.providerId()+":"+safeCode(e));}}
    boolean success=providers.isEmpty()||successfulProviders>0;String error=failures.isEmpty()?null:String.join(",",failures);db.sql("select ouf_sem.complete_discovery_job(:r,:s,:e)").param("r",id).param("s",success).param("e",error).query().singleRow();return 1;}
  private static List<String> languages(Object value){if(value instanceof String[] a)return List.of(a);if(value instanceof java.sql.Array a){try{return List.of((String[])a.getArray());}catch(Exception ignored){return List.of();}}return List.of();}
  private static String safeCode(RuntimeException e){String m=e.getMessage();return m==null?e.getClass().getSimpleName():m.substring(0,Math.min(m.length(),120));}
  private String write(Object v){try{return json.writeValueAsString(v);}catch(Exception e){throw new IllegalArgumentException(e);}}
}

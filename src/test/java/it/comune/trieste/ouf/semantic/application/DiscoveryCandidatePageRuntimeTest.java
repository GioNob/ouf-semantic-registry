package it.comune.trieste.ouf.semantic.application;

import static org.assertj.core.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import java.sql.DriverManager;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestReporter;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.jdbc.support.JdbcTransactionManager;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.support.TransactionTemplate;

class DiscoveryCandidatePageRuntimeTest {
  private static final String ACTOR="discovery-page-fixture";
  private static final int LIMIT=17;
  private static final int TOTAL=1000;
  private static final ObjectMapper JSON=new ObjectMapper();

  @Test void v24EvidenceSurvivesUpgradeAndBothEndsOfPagingUseIndex(TestReporter reporter) throws Exception {
    String url=System.getenv("OUF_SEM_DB_URL"), user=System.getenv("OUF_SEM_DB_USER"), password=System.getenv("OUF_SEM_DB_PASSWORD");
    String database="candidate_page_"+UUID.randomUUID().toString().replace("-","");
    try(var control=DriverManager.getConnection(url,user,password); var ddl=control.createStatement()) {
      ddl.execute("create database "+database);
      try {
        var source=new DriverManagerDataSource(url.substring(0,url.lastIndexOf('/')+1)+database,user,password);
        var flyway=Flyway.configure().dataSource(source).schemas("ouf_sem").defaultSchema("ouf_sem");
        flyway.target("24").load().migrate();
        var db=JdbcClient.create(source);
        var tx=new TransactionTemplate(new JdbcTransactionManager(source));
        tx.setReadOnly(true);
        tx.setIsolationLevel(TransactionDefinition.ISOLATION_REPEATABLE_READ);
        var service=new DiscoveryService(db,List.of(),new SafeRdfParser(),JSON,tx);
        UUID request=seed(db,TOTAL);
        seed(db,2000);
        var predecessor=service.candidates(request);
        assertThat(predecessor).hasSize(TOTAL);
        assertThat(flyway.target("25").load().migrate().migrationsExecuted).isOne();
        db.sql("analyze ouf_sem.discovery_candidate").update();

        assertThat(service.candidates(request)).containsExactlyInAnyOrderElementsOf(predecessor);
        var expected=db.sql("""
            select candidate_id from ouf_sem.discovery_candidate where request_id=:request
            order by score desc,canonical_uri collate "C",candidate_id
            """).param("request",request).query(UUID.class).list();
        var actual=new ArrayList<UUID>();
        DiscoveryService.CandidatePosition after=null;
        UUID lastAnchor=null;
        for(int pageNumber=0;pageNumber<(TOTAL+LIMIT-1)/LIMIT;pageNumber++) {
          var position=after;
          var page=tx.execute(status->service.candidatePage(request,ACTOR,LIMIT,true,position));
          assertThat(page.candidateCount()).isEqualTo(TOTAL);
          assertThat(page.candidates()).hasSize(Math.min(LIMIT+1,TOTAL-actual.size()));
          for(var row:page.candidates().stream().limit(LIMIT).toList()) {
            assertThat(row).containsOnlyKeys("candidateId","canonicalUri","term","label","score","state")
                .containsEntry("label","Preferred English").containsEntry("state","AVAILABLE");
            actual.add((UUID)row.get("candidateId"));
          }
          after=new DiscoveryService.CandidatePosition(page.evidenceVersion(),actual.getLast());
          if(page.candidates().size()<=LIMIT)lastAnchor=position.candidateId();
        }
        assertThat(actual).containsExactlyElementsOf(expected).doesNotHaveDuplicates();
        assertPlan(db,request,null,reporter);
        assertPlan(db,request,lastAnchor,reporter);

        // A predecessor-style write changes the durable evidence version on the new schema.
        var originalPosition=after;
        db.sql("update ouf_sem.discovery_candidate set score=0.90000 where candidate_id=:candidate")
            .param("candidate",expected.getLast()).update();
        assertThatThrownBy(()->tx.execute(status->service.candidatePage(request,ACTOR,LIMIT,true,originalPosition)))
            .isInstanceOf(ArtifactService.Conflict.class).hasMessage("SEM_DISCOVERY_CURSOR_STALE");
        assertThatThrownBy(()->tx.execute(status->service.candidatePage(request,"different-owner",LIMIT,true,null)))
            .isInstanceOf(java.util.NoSuchElementException.class).hasMessage("SEM_DISCOVERY_REQUEST_NOT_FOUND");

        var afterUpgrade=publishThroughV24Signature(db);
        assertThat(service.candidates(afterUpgrade)).hasSize(2);
        var current=tx.execute(status->service.candidatePage(afterUpgrade,ACTOR,LIMIT,true,null));
        assertThat(current.candidateCount()).isEqualTo(2);
        db.sql("""
            update ouf_sem.discovery_candidate set expires_at=now()-interval '1 second'
            where request_id=:request and canonical_uri='https://fixture.test/1'
            """).param("request",afterUpgrade).update();
        assertThat(service.candidates(afterUpgrade)).hasSize(1);
        var expired=tx.execute(status->service.candidatePage(afterUpgrade,ACTOR,LIMIT,true,null));
        assertThat(expired.candidates()).isEmpty();
        assertThat(expired.candidateCount()).isZero();
        db.sql("delete from ouf_sem.discovery_request where request_id=:request").param("request",afterUpgrade).update();
        assertThat(db.sql("select count(*) from ouf_sem.discovery_candidate_page_head where request_id=:request")
            .param("request",afterUpgrade).query(Long.class).single()).isZero();
      } finally {
        ddl.execute("drop database "+database+" with (force)");
      }
    }
  }

  private static UUID publishThroughV24Signature(JdbcClient db) {
    UUID request=UUID.randomUUID();
    db.sql("""
        insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,state,created_by_subject,
          worker_generation,lease_until,budget_deadline)
        values(:request,'CLASS','term','RUNNING',:actor,1,now()+interval '60 seconds',now()+interval '1 hour')
        """).param("request",request).param("actor",ACTOR).update();
    boolean published=db.sql("""
        select ouf_sem.publish_discovery_candidates(:request,1,jsonb_agg(jsonb_build_object(
          'provider','fixture','uri','https://fixture.test/'||i,'source','https://fixture.test/',
          'type','CLASS','trust','HIGH','score',0.85,'reasons','[]'::jsonb,'gaps','[]'::jsonb,
          'hash',repeat('a',64),'mediaType','text/turtle','bytes','Zml4dHVyZQ==')),0,0,0)
        from generate_series(1,2) i
        """).param("request",request).query(Boolean.class).single();
    assertThat(published).isTrue();
    return request;
  }

  private static UUID seed(JdbcClient db,int count) {
    UUID request=UUID.randomUUID();
    db.sql("""
        insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,state,created_by_subject,preferred_languages,completed_at)
        values(:request,'CLASS','term','SUCCEEDED',:actor,array['en','it'],now())
        """).param("request",request).param("actor",ACTOR).update();
    db.sql("""
        insert into ouf_sem.discovery_candidate(candidate_id,request_id,provider_id,canonical_uri,source_location,
          artifact_type,provider_trust,score,match_reasons,normalized_payload,content_hash,media_type,content_bytes,expires_at,discovery_labels)
        select gen_random_uuid(),:request,'fixture','https://fixture.test/terms/T'||lpad((i/4)::text,4,'0'),
          'https://fixture.test/terms','CLASS','HIGH',case when i<=:count-20 then 0.85 else 0.84 end,
          '["detailed evidence"]'::jsonb,'{}',encode(sha256(convert_to(i::text,'UTF8')),'hex'),'text/turtle',
          convert_to('fixture','UTF8'),now()+interval '24 hours','{"it":"Italiano","en":"Preferred English"}'::jsonb
        from generate_series(1,:count) i order by i desc
        """).param("request",request).param("count",count).update();
    return request;
  }

  private static void assertPlan(JdbcClient db,UUID request,UUID after,TestReporter reporter) throws Exception {
    var query=db.sql("explain (analyze,buffers,format json) "+DiscoveryService.candidatePageSql(true,after!=null))
        .param("request",request).param("fetch",LIMIT+1);
    if(after!=null) {
      var key=db.sql("select (-score) as rank,canonical_uri from ouf_sem.discovery_candidate where candidate_id=:id")
          .param("id",after).query().singleRow();
      query.param("rank",key.get("rank")).param("uri",key.get("canonical_uri")).param("candidate",after);
    }
    String measured=query.query(String.class).single();
    reporter.publishEntry(after==null?"first page":"last page",measured);
    var plan=JSON.readTree(measured).get(0).required("Plan");
    assertThat(plan.required("Node Type").asText()).isEqualTo("Limit");
    JsonNode scan=plan.required("Plans").get(0);
    assertThat(scan.required("Index Name").asText()).isEqualTo("discovery_candidate_page_idx");
    assertThat(scan.required("Actual Rows").asInt()).isBetween(1,LIMIT+1);
    assertThat(scan.path("Rows Removed by Filter").asInt()).isZero();
    if(after!=null)assertThat(scan.required("Index Cond").asText()).contains("ROW(",">");
  }
}

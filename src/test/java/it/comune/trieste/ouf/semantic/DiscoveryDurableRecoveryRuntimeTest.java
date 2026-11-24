package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.application.*;
import it.comune.trieste.ouf.semantic.adapters.discovery.BoundedGatewayClient;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.transaction.support.TransactionTemplate;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
class DiscoveryDurableRecoveryRuntimeTest {
  @Autowired TransactionTemplate publicationTx;
  @Autowired JdbcClient db; @Autowired ObjectMapper json; @Autowired SafeRdfParser parser;
  final String actor="recovery-test-"+UUID.randomUUID();
  @AfterEach void leaveNoRunnableFixture(){db.sql("update ouf_sem.discovery_request set state='CANCELLED',lease_until=null where created_by_subject=:a and state in ('PENDING','RUNNING')").param("a",actor).update();}
  UUID request(boolean running){
    UUID id=UUID.randomUUID();
    db.sql("insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,state,created_by_subject,created_at,worker_generation,attempt_count,lease_until,budget_deadline) values(:r,'CLASS','theatre',:s,:a,timestamp '1800-01-01',1,1,clock_timestamp()+interval '120 seconds',clock_timestamp()+interval '24 hours')")
      .param("r",id).param("s",running?"RUNNING":"PENDING").param("a",actor).update();return id;
  }
  Map<String,Object> reserve(UUID id,long generation,String provider){try{return json.readValue(db.sql("select ouf_sem.reserve_discovery_dependency(:r,:g,:p)::text").param("r",id).param("g",generation).param("p",provider).query(String.class).single(),new com.fasterxml.jackson.core.type.TypeReference<Map<String,Object>>(){});}catch(Exception e){throw new AssertionError(e);}}
  long token(Map<String,Object> admission){assertThat(admission).containsEntry("admitted",true);return ((Number)admission.get("generation")).longValue();}
  Map<String,Object> reserve(UUID job,String provider,String version) throws Exception {
    String result=db.sql("select ouf_sem.reserve_discovery_dependency(:r,1,:p,:v)::text")
        .param("r",job).param("p",provider).param("v",version).query(String.class).single();
    return json.readValue(result,new com.fasterxml.jackson.core.type.TypeReference<Map<String,Object>>(){});
  }
  boolean done(UUID id,long generation,String provider,long token,String kind,String code,double delay){return db.sql("select ouf_sem.finish_discovery_dependency(:r,:g,:p,:t,:k,:c,:d)").param("r",id).param("g",generation).param("p",provider).param("t",token).param("k",kind).param("c",code).param("d",delay).query(Boolean.class).single();}
  boolean finish(UUID id,long generation,String outcome,String bytes){return db.sql("select ouf_sem.finish_discovery_job(:r,:g,:o,null,cast(:b as jsonb),null)").param("r",id).param("g",generation).param("o",outcome).param("b",bytes).query(Boolean.class).single();}
  Map<String,Object> dependency(String provider){return db.sql("select * from ouf_sem.discovery_dependency where scope_subject=:a and provider_id=:p").param("a",actor).param("p",provider).query().singleRow();}
  void ready(String provider){db.sql("update ouf_sem.discovery_dependency set next_attempt_at=clock_timestamp()-interval '1 second' where scope_subject=:a and provider_id=:p").param("a",actor).param("p",provider).update();}
  String candidate(){return "[{\"provider\":\"TEST\",\"uri\":\"urn:theatre\",\"source\":\"urn:fixture\",\"type\":\"CLASS\",\"trust\":\"HIGH\",\"score\":1,\"reasons\":[],\"gaps\":[],\"hash\":\""+"a".repeat(64)+"\",\"mediaType\":\"text/turtle\",\"bytes\":\"eA==\"}]";}
  @Test void staleGenerationAndExpiredLeaseCannotPublishOrComplete(){
    UUID id=request(true);assertThat(finish(id,0,"SUCCESS",candidate())).isFalse();
    assertThat(db.sql("select count(*) from ouf_sem.discovery_candidate where request_id=:r").param("r",id).query(Long.class).single()).isZero();
    db.sql("update ouf_sem.discovery_request set lease_until=clock_timestamp()-interval '1 second' where request_id=:r").param("r",id).update();
    assertThat(finish(id,1,"SUCCESS",candidate())).isFalse();assertThat(reserve(id,1,"TEST")).containsEntry("state","STALE");
  }
  @Test void cancellationDuringRemoteWorkRejectsLateSuccess(){
    UUID id=request(true);long t=token(reserve(id,1,"TEST"));
    db.sql("update ouf_sem.discovery_request set state='CANCELLED' where request_id=:r").param("r",id).update();
    assertThat(done(id,1,"TEST",t,"SUCCESS",null,0)).isFalse();assertThat(finish(id,1,"SUCCESS",candidate())).isFalse();
  }
  @Test void publicationAndCompletionRollbackTogetherOnInvalidSecondCandidate(){
    UUID id=request(true);String payload=candidate();
    // The first insert is valid; the second fails its trust constraint. Neither is committed.
    String invalid=payload.substring(0,payload.length()-1)+","+payload.substring(1).replace("HIGH","INVALID");
    assertThatThrownBy(()->finish(id,1,"SUCCESS",invalid)).isInstanceOf(org.springframework.dao.DataAccessException.class);
    assertThat(db.sql("select count(*) from ouf_sem.discovery_candidate where request_id=:r").param("r",id).query(Long.class).single()).isZero();
    assertThat(finish(id,1,"SUCCESS",candidate())).isTrue();assertThat(finish(id,1,"SUCCESS",candidate())).isFalse();
  }
  @Test void sameScopeJobsShareOneIncidentAndRetryAfterCannotBeShortened(){
    UUID a=request(true),b=request(true);long t=token(reserve(a,1,"TEST"));
    assertThat(done(a,1,"TEST",t,"TRANSIENT","PROVIDER_HTTP_503",7200)).isTrue();
    assertThat(db.sql("select next_attempt_at>=clock_timestamp()+interval '7199 seconds' from ouf_sem.discovery_dependency where scope_subject=:a and provider_id='TEST'").param("a",actor).query(Boolean.class).single()).isTrue();
    assertThat(reserve(b,1,"TEST")).containsEntry("state","RETRY_WAIT");ready("TEST");
    t=token(reserve(b,1,"TEST"));assertThat(done(b,1,"TEST",t,"TRANSIENT","PROVIDER_HTTP_503",0)).isTrue();
    assertThat(db.sql("select count(*) from ouf_sem.discovery_incident where scope_subject=:a").param("a",actor).query(Long.class).single()).isEqualTo(1);
    assertThat(dependency("TEST")).containsEntry("attempts",2).containsEntry("cumulative_attempts",2L);
  }
  @Test void newJobAndRestartCannotBypassExhaustionButIndependentProviderContinues() throws Exception {
    UUID a=request(true);long t=token(reserve(a,1,"TEST"));
    db.sql("update ouf_sem.discovery_dependency set attempts=128 where scope_subject=:a and provider_id='TEST'").param("a",actor).update();
    assertThat(done(a,1,"TEST",t,"TRANSIENT","PROVIDER_TIMEOUT",0)).isTrue();
    UUID b=request(true);assertThat(reserve(b,1,"TEST")).containsEntry("state","PAUSED_EXHAUSTED");
    assertThat(reserve(b,"TEST","new-image")).containsEntry("state","PAUSED_EXHAUSTED").containsEntry("admitted",false);
    assertThat(reserve(b,1,"INDEPENDENT")).containsEntry("admitted",true);
    var jobs=new DiscoveryJobService(db,new DiscoveryService(db,List.of(),parser,json,publicationTx),List.of(),json);
    assertThat(jobs.providerStatus("TEST",true,actor)).containsEntry("recoveryState","PAUSED_EXHAUSTED");
    assertThat(jobs.providerStatus("TEST",true,"other-"+actor)).containsEntry("recoveryState","NOT_OBSERVED");
  }
  @Test void retryAfterBeyondDeadlineExhaustsInsteadOfSchedulingEarly(){
    UUID id=request(true);long t=token(reserve(id,1,"TEST"));
    assertThat(done(id,1,"TEST",t,"TRANSIENT","PROVIDER_HTTP_429",90000)).isTrue();
    assertThat(dependency("TEST")).containsEntry("state","PAUSED_EXHAUSTED");
  }
  @Test void concurrentAdmissionAllowsOneCallForSharedScope() throws Exception {
    UUID a=request(true),b=request(true);var barrier=new CyclicBarrier(2);
    try(var pool=Executors.newFixedThreadPool(2)){
      var one=pool.submit(()->{barrier.await(5,TimeUnit.SECONDS);return reserve(a,1,"TEST");});
      var two=pool.submit(()->{barrier.await(5,TimeUnit.SECONDS);return reserve(b,1,"TEST");});
      assertThat(List.of(one.get(10,TimeUnit.SECONDS).get("admitted"),two.get(10,TimeUnit.SECONDS).get("admitted"))).containsExactlyInAnyOrder(true,false);
    }
  }
  @Test void expiredProviderTokenCannotResolveNewGeneration(){
    UUID a=request(true),b=request(true);long old=token(reserve(a,1,"TEST"));
    db.sql("update ouf_sem.discovery_dependency set busy_until=clock_timestamp()-interval '1 second' where scope_subject=:a and provider_id='TEST'").param("a",actor).update();
    long current=token(reserve(b,1,"TEST"));assertThat(current).isGreaterThan(old);
    assertThat(done(a,1,"TEST",old,"SUCCESS",null,0)).isFalse();assertThat(done(b,1,"TEST",current,"SUCCESS",null,0)).isTrue();
    assertThat(db.sql("select outcome from ouf_sem.discovery_attempt where scope_subject=:a and provider_id='TEST' and generation=:t").param("a",actor).param("t",old).query(String.class).single()).isEqualTo("LEASE_EXPIRED");
  }
  @Test void hoursLongIncidentRecoversWithHistoryAndNewFaultGetsNewEpisode(){
    UUID a=request(true);long t=token(reserve(a,1,"TEST"));done(a,1,"TEST",t,"TRANSIENT","PROVIDER_TIMEOUT",7200);
    Object incident=dependency("TEST").get("incident_id");
    db.sql("update ouf_sem.discovery_incident set first_seen_at=clock_timestamp()-interval '3 hours' where incident_id=:i").param("i",incident).update();
    ready("TEST");t=token(reserve(a,1,"TEST"));assertThat(done(a,1,"TEST",t,"SUCCESS",null,0)).isTrue();
    assertThat(db.sql("select state from ouf_sem.discovery_incident where incident_id=:i").param("i",incident).query(String.class).single()).isEqualTo("RESOLVED");
    assertThat(dependency("TEST")).containsEntry("attempts",0).containsEntry("cumulative_attempts",2L);
    t=token(reserve(a,1,"TEST"));done(a,1,"TEST",t,"TRANSIENT","PROVIDER_TIMEOUT",0);
    assertThat(dependency("TEST").get("incident_id")).isNotEqualTo(incident);
  }
  @Test void actualServicePausesTransientErrorAndResumesWithoutDuplicateCandidates(){
    var calls=new AtomicInteger();UUID id=request(false);
    SemanticDiscoveryProvider provider=new SemanticDiscoveryProvider(){
      public String providerId(){return "SERVICE_TEST";}
      public List<Candidate> search(Query q){if(calls.incrementAndGet()==1)throw new BoundedGatewayClient.ProviderFailure("PROVIDER_UNAVAILABLE");return List.of(new Candidate("urn:theatre","urn:fixture","CLASS","HIGH",1,List.of(),List.of(),"<urn:theatre> a <http://www.w3.org/2002/07/owl#Class> .".getBytes(java.nio.charset.StandardCharsets.UTF_8),"text/turtle"));}
    };
    var service=new DiscoveryService(db,List.of(provider),parser,json,publicationTx);service.executeOne();
    var jobs=new DiscoveryJobService(db,service,List.of(provider),json);
    assertThat(jobs.status(id,actor)).doesNotContainKey("completedCandidateCount");
    assertThat(service.candidates(id)).isEmpty();
    assertThat(db.sql("select recovery_state from ouf_sem.discovery_request where request_id=:r").param("r",id).query(String.class).single()).isEqualTo("RETRY_WAIT");
    ready("SERVICE_TEST");db.sql("update ouf_sem.discovery_request set next_attempt_at=clock_timestamp()-interval '1 second' where request_id=:r").param("r",id).update();
    // New service instance models losing all Java process state.
    new DiscoveryService(db,List.of(provider),parser,json,publicationTx).executeOne();assertThat(service.candidates(id)).hasSize(1);assertThat(calls).hasValue(2);
    assertThat(jobs.status(id,actor)).containsEntry("completedCandidateCount",1).containsEntry("candidateCount",1L);
    db.sql("update ouf_sem.discovery_candidate set expires_at=now()-interval '1 second' where request_id=:r").param("r",id).update();
    assertThat(jobs.candidatesWithState(id,actor)).containsEntry("candidateCount",0L)
        .containsEntry("completedCandidateCount",1).containsEntry("candidates",List.of());
  }
  @Test void actualLateWorkerCannotPublishAfterAnotherProcessRecovers() throws Exception {
    var entered=new CountDownLatch(1);var release=new CountDownLatch(1);var calls=new AtomicInteger();UUID id=request(false);
    SemanticDiscoveryProvider provider=new SemanticDiscoveryProvider(){
      public String providerId(){return "LATE_TEST";}
      public List<Candidate> search(Query q){
        if(calls.incrementAndGet()==1){entered.countDown();try{if(!release.await(5,TimeUnit.SECONDS))throw new AssertionError("late fixture timeout");}catch(InterruptedException e){Thread.currentThread().interrupt();throw new AssertionError(e);}}
        return List.of(new Candidate("urn:theatre","urn:fixture","CLASS","HIGH",1,List.of(),List.of(),"<urn:theatre> a <http://www.w3.org/2002/07/owl#Class> .".getBytes(java.nio.charset.StandardCharsets.UTF_8),"text/turtle"));
      }
    };
    var service=new DiscoveryService(db,List.of(provider),parser,json,publicationTx);
    try(var pool=Executors.newFixedThreadPool(1)){
      var late=pool.submit(service::executeOne);assertThat(entered.await(3,TimeUnit.SECONDS)).isTrue();
      // Native database time controls both leases; no Java singleton coordinates recovery.
      db.sql("update ouf_sem.discovery_request set lease_until=clock_timestamp()-interval '1 second' where request_id=:r").param("r",id).update();
      db.sql("update ouf_sem.discovery_dependency set busy_until=clock_timestamp()-interval '1 second' where scope_subject=:a and provider_id='LATE_TEST'").param("a",actor).update();
      new DiscoveryService(db,List.of(provider),parser,json,publicationTx).executeOne();
      release.countDown();assertThat(late.get(3,TimeUnit.SECONDS)).isEqualTo(1);
      assertThat(service.candidates(id)).hasSize(1);assertThat(calls).hasValue(2);
      assertThat(db.sql("select count(*) from ouf_sem.discovery_attempt where scope_subject=:a and outcome='SUCCESS'").param("a",actor).query(Long.class).single()).isEqualTo(1);
    }finally{release.countDown();}
  }
  @Test void jobBudgetSurvivesClaimExpiryAndOldCompletionIsFenced(){
    UUID id=request(false);
    db.sql("update ouf_sem.discovery_request set attempt_count=128 where request_id=:r").param("r",id).update();
    db.sql("select count(*) from ouf_sem.claim_discovery_job('budget-test',120)").query(Long.class).single();
    assertThat(db.sql("select recovery_state from ouf_sem.discovery_request where request_id=:r").param("r",id).query(String.class).single()).isEqualTo("PAUSED_EXHAUSTED");
    assertThat(finish(id,1,"SUCCESS",candidate())).isFalse();
  }
  @Test void unversionedCompletionIsDenied(){UUID id=request(true);assertThatThrownBy(()->db.sql("select ouf_sem.complete_discovery_job(:r,true,null)").param("r",id).query().singleRow()).isInstanceOf(org.springframework.dao.DataAccessException.class);}

  @Test void versionProbeIsOneShotAcrossConcurrentWorkersRestartsAndRollbacks() throws Exception {
    UUID first=request(true), other=request(true);
    long initial=token(reserve(first,"TEST","v1"));
    assertThat(done(first,1,"TEST",initial,"BLOCKED","PROVIDER_UNKNOWN",0)).isTrue();
    ready("TEST");
    assertThat(reserve(first,"TEST","v1")).containsEntry("state","BLOCKED");
    var start=new CyclicBarrier(2);
    try(var pool=Executors.newFixedThreadPool(2)){
      var one=pool.submit(()->{start.await(5,TimeUnit.SECONDS);return reserve(first,"TEST","v2");});
      var two=pool.submit(()->{start.await(5,TimeUnit.SECONDS);return reserve(other,"TEST","v2");});
      var left=one.get(10,TimeUnit.SECONDS);var right=two.get(10,TimeUnit.SECONDS);
      assertThat(List.of(left.get("admitted"),right.get("admitted"))).containsExactlyInAnyOrder(true,false);
    }
    var active=dependency("TEST");
    assertThat(active).containsEntry("state","BLOCKED").containsEntry("cumulative_attempts",2L);
    db.sql("update ouf_sem.discovery_dependency set busy_until=clock_timestamp()-interval '1 second' where scope_subject=:a")
        .param("a",actor).update();
    assertThat(reserve(first,"TEST","v2")).containsEntry("state","BLOCKED");
    assertThat(reserve(first,1,"TEST")).containsEntry("state","BLOCKED");
    long next=token(reserve(other,"TEST","v3"));
    assertThat(done((UUID)active.get("active_request"),1,"TEST",2,"SUCCESS",null,0)).isFalse();
    assertThat(done(other,1,"TEST",next,"BLOCKED","PROVIDER_UNKNOWN",0)).isTrue();
    ready("TEST");
    for(String used:List.of("v1","v2","v3"))assertThat(reserve(first,"TEST",used)).containsEntry("state","BLOCKED");
    assertThat(done(first,1,"TEST",token(reserve(first,"TEST","v4")),"SUCCESS",null,0)).isTrue();
    assertThat(dependency("TEST")).containsEntry("state","HEALTHY").containsEntry("cumulative_attempts",4L);
    assertThat(db.sql("select opened_worker_version from ouf_sem.discovery_incident where scope_subject=:a and state='RESOLVED'")
        .param("a",actor).query(String.class).single()).isEqualTo("v1");
    assertThat(db.sql("select attempts from ouf_sem.discovery_incident where scope_subject=:a")
        .param("a",actor).query(Integer.class).single()).isEqualTo(4);
  }
  @Test void securityAndUnrecognizedCodesStayBlockedOnUpgrade() throws Exception {
    UUID id=request(true);
    for(String code:List.of("PROVIDER_TLS_UNPROVEN","GATEWAY_TOKEN_REJECTED","GATEWAY_AUTH_REQUIRED",
        "GATEWAY_ORIGIN_VIOLATION","GATEWAY_HTTPS_REQUIRED","PROVIDER_REDIRECT_FORBIDDEN",
        "GATEWAY_CREDENTIAL_FILE_INVALID","PROVIDER_HTTP_401","PROVIDER_HTTP_403","PROVIDER_HTTP_407","FUTURE_CODE")){
      long t=token(reserve(id,code,"v1"));
      assertThat(done(id,1,code,t,"BLOCKED",code,0)).isTrue();
      ready(code);
      assertThat(reserve(id,code,"v2")).as(code).containsEntry("state","BLOCKED").containsEntry("admitted",false);
      db.sql("update ouf_sem.discovery_dependency set state='PAUSED_EXHAUSTED',budget_deadline=now() where scope_subject=:a and provider_id=:p")
          .param("a",actor).param("p",code).update();
      assertThat(reserve(id,code,"v2")).as(code).containsEntry("state","PAUSED_EXHAUSTED").containsEntry("admitted",false);
    }
  }
  @Test void transientProbeFailureKeepsTheOriginalBlockAndRespectsRetryAfter() throws Exception {
    UUID id=request(true);
    assertThat(done(id,1,"TEST",token(reserve(id,"TEST","v1")),"BLOCKED","SCHEMA_GOV_SPARQL_RESULT_INVALID",0)).isTrue();
    ready("TEST");
    assertThat(done(id,1,"TEST",token(reserve(id,"TEST","v2")),"TRANSIENT","PROVIDER_HTTP_503",7200)).isTrue();
    assertThat(dependency("TEST")).containsEntry("state","BLOCKED");
    assertThat(reserve(id,"TEST","v2")).containsEntry("state","BLOCKED");
    assertThat(reserve(id,"TEST","v3")).containsEntry("state","RETRY_WAIT").containsEntry("admitted",false);
    ready("TEST");
    assertThat(done(id,1,"TEST",token(reserve(id,"TEST","v3")),"SUCCESS",null,0)).isTrue();
  }
  @Test void exhaustedCorrectableIncidentHonorsRetryAfterAndAllowsOnlyAnUnusedVersion() throws Exception {
    UUID id=request(true),fresh=request(true);
    assertThat(done(id,1,"TEST",token(reserve(id,"TEST","v1")),"BLOCKED","PROVIDER_UNKNOWN",0)).isTrue();
    ready("TEST");
    assertThat(done(id,1,"TEST",token(reserve(id,"TEST","v2")),"TRANSIENT","PROVIDER_HTTP_503",90000)).isTrue();
    var exhausted=dependency("TEST");
    assertThat(exhausted).containsEntry("state","PAUSED_EXHAUSTED");
    assertThat(reserve(fresh,"TEST","v3")).containsEntry("state","RETRY_WAIT").containsEntry("admitted",false);
    ready("TEST");
    for(String used:List.of("v1","v2"))
      assertThat(reserve(fresh,"TEST",used)).containsEntry("state","PAUSED_EXHAUSTED").containsEntry("admitted",false);
    assertThat(dependency("TEST")).containsEntry("budget_deadline",exhausted.get("budget_deadline")).containsEntry("cumulative_attempts",2L);
    long probe=token(reserve(fresh,"TEST","v3"));
    assertThat(dependency("TEST")).containsEntry("attempts",1).containsEntry("cumulative_attempts",3L)
        .containsEntry("incident_id",exhausted.get("incident_id"));
    assertThat(done(fresh,1,"TEST",probe,"SUCCESS",null,0)).isTrue();
    assertThat(dependency("TEST")).containsEntry("state","HEALTHY");
  }
  @Test void correctableBlockOnLastAttemptCanOpenANewEpisodeBeforeDeadline() throws Exception {
    UUID old=request(true),fresh=request(true);
    assertThat(done(old,1,"TEST",token(reserve(old,"TEST","v1")),"TRANSIENT","PROVIDER_TIMEOUT",0)).isTrue();
    // Advance the fixture to the last available attempt, keeping the time budget live.
    db.sql("update ouf_sem.discovery_dependency set attempts=127,cumulative_attempts=127,next_attempt_at=now() where scope_subject=:a")
        .param("a",actor).update();
    assertThat(done(old,1,"TEST",token(reserve(old,"TEST","v1")),"BLOCKED","PROVIDER_UNKNOWN",0)).isTrue();
    ready("TEST");
    long probe=token(reserve(fresh,"TEST","v2"));
    assertThat(dependency("TEST")).containsEntry("attempts",1).containsEntry("cumulative_attempts",129L);
    assertThat(done(fresh,1,"TEST",probe,"SUCCESS",null,0)).isTrue();
    assertThat(db.sql("select attempts from ouf_sem.discovery_incident where scope_subject=:a and state='RESOLVED'")
        .param("a",actor).query(Integer.class).single()).isEqualTo(129);
  }
  @Test void invalidCandidateIsExcludedAndProviderSucceeds(){checkCandidateExclusions(true);}
  @Test void allExcludedCandidatesLeaveSuccessfulEmptyJobWithTypedCounts(){checkCandidateExclusions(false);}
  @Test void unknownFailureLogsOnlyItsTypeAndInnermostSemanticFrame(){
    UUID id=request(false);
    var cause=new IllegalArgumentException("private-provider-body");
    cause.setStackTrace(new StackTraceElement[]{
        new StackTraceElement("example.Library","parse","private-file",2),
        new StackTraceElement("it.comune.trieste.ouf.semantic.TestAdapter","fetch","private-file",42)});
    SemanticDiscoveryProvider provider=new SemanticDiscoveryProvider(){
      public String providerId(){return "UNKNOWN_TEST";}
      public List<Candidate> search(Query q){throw new IllegalStateException("private-wrapper",cause);}
    };
    var service=new DiscoveryService(db,List.of(provider),parser,json,publicationTx);
    var logger=(ch.qos.logback.classic.Logger)org.slf4j.LoggerFactory.getLogger(DiscoveryService.class);
    var logs=new ch.qos.logback.core.read.ListAppender<ch.qos.logback.classic.spi.ILoggingEvent>();
    logs.start();logger.addAppender(logs);
    try{
      service.executeOne();
      assertThat(logs.list).singleElement().satisfies(event->{
        assertThat(event.getFormattedMessage()).isEqualTo("Unclassified discovery exception type=java.lang.IllegalArgumentException frame=it.comune.trieste.ouf.semantic.TestAdapter:42");
        assertThat(event.getThrowableProxy()).isNull();
      });
      assertThat(new DiscoveryJobService(db,service,List.of(provider),json).status(id,actor))
          .containsEntry("errorCode","SEM_DISCOVERY_PROVIDER_FAILED");
    }finally{logger.detachAppender(logs);logs.stop();}
  }
  private void checkCandidateExclusions(boolean includeValid){
    UUID id=request(false);
    SemanticDiscoveryProvider provider=new SemanticDiscoveryProvider(){
      public String providerId(){return "RDF_TEST";}
      public List<Candidate> search(Query q){
        var rows=new ArrayList<Candidate>();
        rows.add(candidate("urn:bad","invalid turtle".getBytes()));
        rows.add(candidate("urn:large",new byte[SafeRdfParser.MAX_BYTES+1]));
        if(includeValid)rows.add(candidate("urn:good","<urn:good> a <urn:Class> .".getBytes()));
        return rows;
      }
      private Candidate candidate(String uri,byte[] bytes){
        return new Candidate(uri,uri,"CLASS","HIGH",1,List.of(),List.of(),bytes,"text/turtle");
      }
    };
    var service=new DiscoveryService(db,List.of(provider),parser,json,publicationTx);
    assertThat(service.executeOne()).isOne();
    var status=new DiscoveryJobService(db,service,List.of(provider),json).status(id,actor);
    assertThat(status).containsEntry("state","SUCCEEDED").containsEntry("candidateCount",includeValid?1L:0L)
        .containsEntry("excludedCandidates",Map.of("CANDIDATE_RDF_INVALID",1,"CANDIDATE_RDF_BOUND",1,"CANDIDATE_FETCH_DENIED",0,"CANDIDATE_NAMESPACE_EXCLUDED",0)).doesNotContainKey("errorCode");
    var uris=service.candidates(id).stream().map(row->row.get("canonical_uri")).toList();
    if(includeValid)assertThat(uris).containsExactly("urn:good");else assertThat(uris).isEmpty();
    assertThat(dependency("RDF_TEST")).containsEntry("state","HEALTHY");
    assertThat(db.sql("select outcome from ouf_sem.discovery_attempt where request_id=:id").param("id",id)
        .query(String.class).single()).isEqualTo("SUCCESS");
  }
}

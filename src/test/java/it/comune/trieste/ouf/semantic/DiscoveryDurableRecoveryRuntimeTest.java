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

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
class DiscoveryDurableRecoveryRuntimeTest {
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
  @Test void newJobAndRestartCannotBypassExhaustionButIndependentProviderContinues(){
    UUID a=request(true);long t=token(reserve(a,1,"TEST"));
    db.sql("update ouf_sem.discovery_dependency set attempts=128 where scope_subject=:a and provider_id='TEST'").param("a",actor).update();
    assertThat(done(a,1,"TEST",t,"TRANSIENT","PROVIDER_TIMEOUT",0)).isTrue();
    UUID b=request(true);assertThat(reserve(b,1,"TEST")).containsEntry("state","PAUSED_EXHAUSTED");
    assertThat(reserve(b,1,"INDEPENDENT")).containsEntry("admitted",true);
    var jobs=new DiscoveryJobService(db,new DiscoveryService(db,List.of(),parser,json),List.of(),json);
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
    var service=new DiscoveryService(db,List.of(provider),parser,json);service.executeOne();
    assertThat(service.candidates(id)).isEmpty();
    assertThat(db.sql("select recovery_state from ouf_sem.discovery_request where request_id=:r").param("r",id).query(String.class).single()).isEqualTo("RETRY_WAIT");
    ready("SERVICE_TEST");db.sql("update ouf_sem.discovery_request set next_attempt_at=clock_timestamp()-interval '1 second' where request_id=:r").param("r",id).update();
    // New service instance models losing all Java process state.
    new DiscoveryService(db,List.of(provider),parser,json).executeOne();assertThat(service.candidates(id)).hasSize(1);assertThat(calls).hasValue(2);
  }
  @Test void unversionedCompletionIsDenied(){UUID id=request(true);assertThatThrownBy(()->db.sql("select ouf_sem.complete_discovery_job(:r,true,null)").param("r",id).query().singleRow()).isInstanceOf(org.springframework.dao.DataAccessException.class);}
}

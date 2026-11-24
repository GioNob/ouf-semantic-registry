package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.application.*;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.util.*;
import java.util.concurrent.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.AfterEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.support.TransactionTemplate;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
@AutoConfigureMockMvc
class DiscoveryJobRuntimeTest {
  private final Set<String> fixtureIdentities=new HashSet<>();
  @AfterEach void leaveNoRunnableJobsForOtherRuntimeTests(){
    for(String subject:fixtureIdentities)
      db.sql("update ouf_sem.discovery_request set state='CANCELLED',lease_until=null where created_by_subject=:a and state in ('PENDING','RUNNING')")
        .param("a",subject).update();
  }
  @Autowired JdbcClient db;
  @Autowired ObjectMapper json;
  @Autowired SafeRdfParser parser;
  @Autowired MockMvc http;
  @Autowired TransactionTemplate transactions;
  @Autowired ArtifactService artifacts;
  private DiscoveryJobService service(boolean enabled){
    SemanticDiscoveryProvider provider=new SemanticDiscoveryProvider(){
      public String providerId(){return "JOBS_TEST";}
      public boolean enabled(){return enabled;}
      public List<Candidate> search(Query q){throw new AssertionError("No provider call in request/status");}
    };
    var providers=List.of(provider);
    return new DiscoveryJobService(db,new DiscoveryService(db,providers,parser,json,transactions),providers,json);
  }
  private String unique(){String value=UUID.randomUUID().toString();fixtureIdentities.add(value);return value;}
  private UUID id(Map<String,Object> result){return (UUID)result.get("requestId");}
  @Test void identicalKeyAndNormalizedQueryReturnsOneJob(){
    String actor=unique(),key=unique();var jobs=service(true);
    UUID first=id(jobs.request("CLASS"," teatro ",List.of("it","en","it"),actor,key));
    assertThat(id(jobs.request("CLASS","teatro",List.of("IT","EN"),actor,key))).isEqualTo(first);
    assertThat(db.sql("select count(*) from ouf_sem.discovery_request where created_by_subject=:a").param("a",actor).query(Long.class).single()).isEqualTo(1);
    assertThat(db.sql("select idempotency_key_hash from ouf_sem.discovery_request where request_id=:id").param("id",first).query(String.class).single()).hasSize(64).isNotEqualTo(key);
  }
  @Test void changedPayloadConflictsAndSameKeyIsScopedToCaller(){
    String actor=unique(),key=unique();var jobs=service(true);UUID first=id(jobs.request("CLASS","teatro",List.of("it"),actor,key));
    assertThatThrownBy(()->jobs.request("CLASS","cinema",List.of("it"),actor,key)).isInstanceOf(ArtifactService.Conflict.class);
    assertThat(id(jobs.request("CLASS","teatro",List.of("it"),unique(),key))).isNotEqualTo(first);
  }
  @Test void replayReturnsActualStateEvenIfProviderIsNowDisabled(){
    String actor=unique(),key=unique();UUID request=id(service(true).request("CLASS","teatro",List.of(),actor,key));
    db.sql("update ouf_sem.discovery_request set state='SUCCEEDED',completed_at=transaction_timestamp() where request_id=:id").param("id",request).update();
    assertThat(service(false).request("CLASS","teatro",List.of(),actor,key)).containsEntry("requestId",request)
        .containsEntry("state","SUCCEEDED").doesNotContainKey("completedCandidateCount");
  }
  @Test void workflowActionsFollowDurableJobAndCandidateState() {
    String actor=unique();
    var jobs=service(true);
    var requested=jobs.request("CLASS","teatro",List.of(),actor,unique());
    UUID request=id(requested);
    assertThat(requested).containsEntry("state","PENDING")
        .containsEntry("allowedActions",List.of(WorkflowAction.POLL_DISCOVERY)).containsEntry("pollAfterSeconds",5L);
    assertThat(jobs.candidatesWithState(request,actor)).containsEntry("candidates",List.of())
        .containsEntry("allowedActions",List.of(WorkflowAction.POLL_DISCOVERY));

    db.sql("""
        update ouf_sem.discovery_request set recovery_state='RETRY_WAIT',next_attempt_at=now()+interval '3 minutes'
        where request_id=:id
        """).param("id",request).update();
    assertThat(((Number)jobs.status(request,actor).get("pollAfterSeconds")).longValue()).isBetween(160L,180L);
    db.sql("update ouf_sem.discovery_request set recovery_state='PAUSED_EXHAUSTED' where request_id=:id")
        .param("id",request).update();
    assertThat(jobs.status(request,actor)).containsEntry("allowedActions",List.of(WorkflowAction.NONE))
        .doesNotContainKey("pollAfterSeconds");

    db.sql("update ouf_sem.discovery_request set state='SUCCEEDED',recovery_state='ACTIVE' where request_id=:id")
        .param("id",request).update();
    assertThat(jobs.candidatesWithState(request,actor)).containsEntry("allowedActions",List.of(WorkflowAction.NONE));
    UUID live=UUID.randomUUID(),expired=UUID.randomUUID();
    db.sql("""
        insert into ouf_sem.discovery_candidate(candidate_id,request_id,provider_id,canonical_uri,source_location,
          artifact_type,provider_trust,score,normalized_payload,content_hash,media_type,content_bytes,expires_at)
        values(:live,:id,'JOBS_TEST','urn:live','urn:live','CLASS','HIGH',1,'{}',repeat('a',64),
          'text/turtle',decode('00','hex'),now()+interval '1 hour'),
          (:expired,:id,'JOBS_TEST','urn:expired','urn:expired','CLASS','HIGH',1,'{}',repeat('a',64),
          'text/turtle',decode('00','hex'),now()-interval '1 hour')
        """).param("live",live).param("expired",expired).param("id",request).update();
    assertThat(jobs.status(request,actor)).containsEntry("allowedActions",List.of(WorkflowAction.LIST_CANDIDATES));
    assertThat(jobs.candidatesWithState(request,actor))
        .containsEntry("candidates",jobs.candidates(request,actor))
        .containsEntry("allowedActions",List.of(WorkflowAction.ADOPT_CANDIDATE))
        .containsEntry("adoptableCandidateIds",List.of(live));

    var artifact=artifacts.create(new it.comune.trieste.ouf.semantic.api.ArtifactApi.CreateArtifact(
        "urn:adopted:"+live,"CLASS","ouf","Adopted"+live,"owner","authority","1.0.0",Map.of(),Map.of()),
        actor,"HUMAN","test");
    db.sql("update ouf_sem.discovery_candidate set adopted_at=now(),adopted_artifact_id=:a where candidate_id=:id")
        .param("a",artifact.get("artifactId")).param("id",live).update();
    assertThat(jobs.candidatesWithState(request,actor)).containsEntry("adoptableCandidateIds",List.of())
        .containsEntry("allowedActions",List.of(WorkflowAction.NONE));
    assertThat(jobs.candidates(request,actor)).hasSize(1);
    assertThatThrownBy(()->jobs.candidatesWithState(request,unique())).isInstanceOf(NoSuchElementException.class);
  }
  @Test void concurrentRetriesCreateExactlyOneJob() throws Exception {
    String actor=unique(),key=unique();var jobs=service(true);var ready=new CountDownLatch(2);var start=new CountDownLatch(1);
    try(var pool=Executors.newFixedThreadPool(2)){
      Callable<UUID> call=()->{ready.countDown();if(!start.await(5,TimeUnit.SECONDS))throw new AssertionError("Start timeout");return transactions.execute(tx->id(jobs.request("CLASS","teatro",List.of("it"),actor,key)));};
      var one=pool.submit(call);var two=pool.submit(call);assertThat(ready.await(5,TimeUnit.SECONDS)).isTrue();start.countDown();
      assertThat(one.get(10,TimeUnit.SECONDS)).isEqualTo(two.get(10,TimeUnit.SECONDS));
    }
    assertThat(db.sql("select count(*) from ouf_sem.discovery_request where created_by_subject=:a").param("a",actor).query(Long.class).single()).isEqualTo(1);
  }
  @Test void otherCallerCannotReadStatusOrCandidatesAndProviderErrorsAreRedacted(){
    String actor=unique();var jobs=service(true);UUID request=id(jobs.request("CLASS","teatro",List.of(),actor,unique()));
    db.sql("update ouf_sem.discovery_request set state='FAILED',last_error_code='https://user:secret@private-provider' where request_id=:id").param("id",request).update();
    assertThat(jobs.status(request,actor)).containsEntry("errorCode","SEM_DISCOVERY_PROVIDER_FAILED");
    assertThat(jobs.status(request,actor).toString()).doesNotContain("secret","private-provider","intent","fingerprint");
    assertThatThrownBy(()->jobs.status(request,unique())).isInstanceOf(NoSuchElementException.class);
    assertThatThrownBy(()->jobs.candidates(request,unique())).isInstanceOf(NoSuchElementException.class);
    assertThatThrownBy(()->jobs.status(UUID.randomUUID(),actor)).isInstanceOf(NoSuchElementException.class);
  }
  @Test void invalidRequestsDoNotCreateJobs(){
    String actor=unique();var jobs=service(true);
    assertThatThrownBy(()->jobs.request("DATATYPE","misura",List.of("it"),actor,unique()))
        .hasMessage("SEM_DISCOVERY_REQUEST_INVALID");
    assertThatThrownBy(()->jobs.request("CLASS","teatro",List.of(),actor,"short")).isInstanceOf(IllegalArgumentException.class);
    assertThatThrownBy(()->jobs.request("CLASS"," ",List.of(),actor,unique())).isInstanceOf(IllegalArgumentException.class);
    assertThatThrownBy(()->jobs.request("CLASS","teatro",List.of("secret?"),actor,unique())).isInstanceOf(IllegalArgumentException.class);
    assertThatThrownBy(()->service(false).request("CLASS","teatro",List.of(),actor,unique())).isInstanceOf(DiscoveryService.ProviderUnavailable.class);
    assertThat(db.sql("select count(*) from ouf_sem.discovery_request where created_by_subject=:a").param("a",actor).query(Long.class).single()).isZero();
  }
  @Test void nativeHttpStatusIsCallerScopedAndDoesNotExposeProviderErrorText() throws Exception {
    String actor=unique();UUID request=id(service(true).request("CLASS","teatro",List.of(),actor,unique()));
    for(String path:List.of("/api/semantic/v1/discovery-requests/"+request,"/api/semantic/v1/discovery-requests/"+request+"/candidates")){
      http.perform(get(path).with(r->{it.comune.trieste.ouf.authorization.TestAuthorization.bind(r,"other","SERVICE",Set.of("ouf.semantic.discovery"));return r;}))
        .andExpect(status().isNotFound()).andExpect(jsonPath("$.code").value("SEM_DISCOVERY_REQUEST_NOT_FOUND"));
    }
    http.perform(get("/api/semantic/v1/discovery-requests/"+request).with(r->{it.comune.trieste.ouf.authorization.TestAuthorization.bind(r,actor,"SERVICE",Set.of("ouf.semantic.discovery"));return r;}))
      .andExpect(status().isOk()).andExpect(jsonPath("$.state").value("PENDING")).andExpect(jsonPath("$.candidateCount").value(0));
  }
}

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
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.transaction.PlatformTransactionManager;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
@AutoConfigureMockMvc
class DiscoveryJobRuntimeTest {
  @Autowired JdbcClient db;
  @Autowired ObjectMapper json;
  @Autowired SafeRdfParser parser;
  @Autowired MockMvc http;
  @Autowired PlatformTransactionManager transactions;
  private DiscoveryJobService service(boolean enabled){
    SemanticDiscoveryProvider provider=new SemanticDiscoveryProvider(){
      public String providerId(){return "JOBS_TEST";}
      public boolean enabled(){return enabled;}
      public List<Candidate> search(Query q){throw new AssertionError("No provider call in request/status");}
    };
    var providers=List.of(provider);
    return new DiscoveryJobService(db,new DiscoveryService(db,providers,parser,json),providers,json);
  }
  private String unique(){return UUID.randomUUID().toString();}
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
    assertThat(service(false).request("CLASS","teatro",List.of(),actor,key)).containsEntry("requestId",request).containsEntry("state","SUCCEEDED");
  }
  @Test void concurrentRetriesCreateExactlyOneJob() throws Exception {
    String actor=unique(),key=unique();var jobs=service(true);var ready=new CountDownLatch(2);var start=new CountDownLatch(1);
    try(var pool=Executors.newFixedThreadPool(2)){
      Callable<UUID> call=()->{ready.countDown();if(!start.await(5,TimeUnit.SECONDS))throw new AssertionError("Start timeout");return new TransactionTemplate(transactions).execute(tx->id(jobs.request("CLASS","teatro",List.of("it"),actor,key)));};
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

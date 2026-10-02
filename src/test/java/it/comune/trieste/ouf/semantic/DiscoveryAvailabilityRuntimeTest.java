package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.application.DiscoveryService;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
@AutoConfigureMockMvc
class DiscoveryAvailabilityRuntimeTest {
  @Autowired JdbcClient db;
  @Autowired ObjectMapper json;
  @Autowired SafeRdfParser parser;
  @Autowired MockMvc http;
  private DiscoveryService service(SemanticDiscoveryProvider... providers){return new DiscoveryService(db,List.of(providers),parser,json);}
  private SemanticDiscoveryProvider provider(boolean enabled,AtomicInteger calls,boolean fail){
    return new SemanticDiscoveryProvider(){
      public String providerId(){return "AVAILABILITY_TEST";}
      public boolean enabled(){return enabled;}
      public List<Candidate> search(Query query){calls.incrementAndGet();if(fail)throw new IllegalStateException("TEST_PROVIDER_FAILED");return List.of();}
    };
  }
  private UUID oldPendingRequest(){
    UUID id=UUID.randomUUID();
    db.sql("insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,state,created_by_subject,created_at) values(:id,'CLASS','availability-test','PENDING','availability-test',timestamp '1900-01-01')")
      .param("id",id).update();return id;
  }
  private Map<String,Object> row(UUID id){return db.sql("select state,last_error_code from ouf_sem.discovery_request where request_id=:id").param("id",id).query().singleRow();}
  @Test void noProviderRejectsBeforePersistingAJob(){
    long before=db.sql("select count(*) from ouf_sem.discovery_request").query(Long.class).single();
    assertThatThrownBy(()->service().request("CLASS","teatro",List.of("it"),"caller"))
      .isInstanceOf(DiscoveryService.ProviderUnavailable.class).hasMessage("SEM_DISCOVERY_NO_ENABLED_PROVIDER");
    var calls=new AtomicInteger();
    assertThatThrownBy(()->service(provider(false,calls,false)).request("CLASS","teatro",List.of("it"),"caller"))
      .isInstanceOf(DiscoveryService.ProviderUnavailable.class);
    assertThat(db.sql("select count(*) from ouf_sem.discovery_request").query(Long.class).single()).isEqualTo(before);
    assertThat(calls).hasValue(0);
  }
  @Test void previouslyQueuedRequestFailsExplicitlyWhenAllProvidersAreDisabled(){
    var calls=new AtomicInteger();UUID id=oldPendingRequest();
    assertThat(service(provider(false,calls,false)).executeOne()).isEqualTo(1);
    assertThat(row(id)).containsEntry("state","FAILED").containsEntry("last_error_code","SEM_DISCOVERY_NO_ENABLED_PROVIDER");
    assertThat(calls).hasValue(0);
  }
  @Test void previouslyQueuedRequestDoesNotReportSuccessWithAnEmptyProviderList(){
    UUID id=oldPendingRequest();assertThat(service().executeOne()).isEqualTo(1);
    assertThat(row(id)).containsEntry("state","FAILED").containsEntry("last_error_code","SEM_DISCOVERY_NO_ENABLED_PROVIDER");
  }
  @Test void realEmptyProviderResultRemainsDistinctFromDisabledProvider(){
    var calls=new AtomicInteger();UUID id=oldPendingRequest();
    assertThat(service(provider(true,calls,false)).executeOne()).isEqualTo(1);
    assertThat(row(id)).containsEntry("state","SUCCEEDED").containsEntry("last_error_code",null);
    assertThat(calls).hasValue(1);
  }
  @Test void oneSuccessfulProviderCanCompleteDespiteAnotherDisabledOrFailedProvider(){
    var disabled=new AtomicInteger();var failed=new AtomicInteger();var successful=new AtomicInteger();
    UUID id=oldPendingRequest();
    service(provider(false,disabled,false),provider(true,failed,true),provider(true,successful,false)).executeOne();
    assertThat(row(id)).containsEntry("state","SUCCEEDED").containsEntry("last_error_code","AVAILABILITY_TEST:TEST_PROVIDER_FAILED");
    assertThat(disabled).hasValue(0);assertThat(failed).hasValue(1);assertThat(successful).hasValue(1);
  }
  @Test void authorizedNativeRequestReturns503ForDisabledProvider() throws Exception {
    http.perform(post("/api/semantic/v1/discovery-requests").contentType("application/json")
      .content("{\"requestedArtifactType\":\"CLASS\",\"intent\":\"teatro\",\"preferredLanguages\":[\"it\"]}")
      .with(request->{it.comune.trieste.ouf.authorization.TestAuthorization.bind(request,"reader","SERVICE",Set.of("ouf.semantic.discovery"));return request;}))
      .andExpect(status().isServiceUnavailable()).andExpect(jsonPath("$.code").value("SEM_DISCOVERY_NO_ENABLED_PROVIDER"));
  }
}

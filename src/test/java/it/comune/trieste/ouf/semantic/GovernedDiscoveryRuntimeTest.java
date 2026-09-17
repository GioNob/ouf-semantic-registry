package it.comune.trieste.ouf.semantic;
import static org.assertj.core.api.Assertions.*;
import it.comune.trieste.ouf.semantic.application.*;
import it.comune.trieste.ouf.semantic.api.ArtifactApi.PatchRevision;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import it.comune.trieste.ouf.pairwise.GovernedPublicationFixture;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.simple.JdbcClient;
@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
class GovernedDiscoveryRuntimeTest {
 @Autowired JdbcClient db; @Autowired ObjectMapper json; @Autowired SafeRdfParser parser;
 @Autowired ArtifactService artifacts; @Autowired ValidationService validation; @Autowired GovernanceService governance;
 @Test void adoptedDraftCanBeVersionedAndPublishedWithoutLosingHistoricalIdentity(){
  var discovery=new DiscoveryService(db,List.of(GovernedPublicationFixture.provider()),parser,json);
  var result=GovernedPublicationFixture.run(discovery,artifacts,validation,governance);
  var binding=(Map<String,Object>)result.get("binding");UUID revision=(UUID)binding.get("revisionId"),set=(UUID)binding.get("publicationSetId");
  assertThatThrownBy(()->artifacts.patch(revision,"\"1\"",new PatchRevision(Map.of(),Map.of(),"2.0.0"),"service","SERVICE","r2c")).isInstanceOf(ArtifactService.Conflict.class);
  assertThatThrownBy(()->discovery.adopt(UUID.randomUUID(),(UUID)result.get("candidateId"),"other","n","l","o","a","s")).isInstanceOf(NoSuchElementException.class);
  assertThatThrownBy(()->validation.resolve("core",revision,UUID.randomUUID())).isInstanceOf(NoSuchElementException.class);
  governance.lifecycle(revision,"DEPRECATED","human","HUMAN","fixture:mfa","r2c");
  var historical=validation.resolve("core",revision,set);
  assertThat(historical.get("semantic_version")).isEqualTo("1.0.0");
  assertThat(historical.get("status")).isEqualTo("DEPRECATED");
 }
}

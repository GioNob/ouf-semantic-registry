package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.semantic.api.ArtifactApi.CreateArtifact;
import it.comune.trieste.ouf.semantic.application.*;
import java.util.*;
import java.util.concurrent.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.RequestPostProcessor;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
@AutoConfigureMockMvc
class ProposalCommandRuntimeTest {
  @Autowired ProposalCommandService commands;
  @Autowired ArtifactService artifacts;
  @Autowired JdbcClient db;
  @Autowired MockMvc http;
  @Autowired ObjectMapper json;
  private static final Set<String> CAPS=Set.of("ouf.semantic.propose","ouf.semantic.review.prepare","ouf.semantic.approval.request");
  private CreateArtifact command(){String id=UUID.randomUUID().toString();return new CreateArtifact("ouf:proposal:"+id,"CLASS","ouf","Place"+id.replace("-",""),"owner","authority","1.0.0",Map.of("it","Luogo"),Map.of());}
  private UUID revision(Map<String,Object> created){return UUID.fromString(created.get("revisionId").toString());}
  private String key(){return UUID.randomUUID().toString();}
  private RequestPostProcessor actor(String principal,Set<String> caps){return r->{it.comune.trieste.ouf.authorization.TestAuthorization.bind(r,principal,"AI_AGENT",caps);return r;};}
  private JsonNode postCommand(String mode,Object body,String key,Set<String> caps,int status)throws Exception{
    var result=http.perform(post("/api/semantic/v1/proposal-commands/"+mode).with(actor("agent",caps))
        .header("Idempotency-Key",key).contentType(MediaType.APPLICATION_JSON).content(json.writeValueAsBytes(body)))
        .andExpect(status().is(status)).andReturn();
    return json.readTree(result.getResponse().getContentAsByteArray());
  }
  @Test void httpChainPreservesRealValidationAndChallengeOnReplay()throws Exception{
    var c=command();String createKey=key();var created=postCommand("create",c,createKey,CAPS,200);
    assertThat(postCommand("create",c,createKey,CAPS,200)).isEqualTo(created);
    String r=created.get("revisionId").asText();String validateKey=key();
    var validate=Map.of("revisionId",r,"expectedRowVersion",0);
    var validated=postCommand("validate",validate,validateKey,CAPS,200);
    assertThat(postCommand("validate",validate,validateKey,CAPS,200)).isEqualTo(validated);
    String reviewKey=key();var review=Map.of("revisionId",r,"expectedRowVersion",0,"validationRunId",validated.get("validation_run_id").asText());
    var receipt=postCommand("review",review,reviewKey,CAPS,200);
    assertThat(receipt.get("targetContentHash").asText()).isEqualTo(validated.get("validated_content_hash").asText());
    assertThat(receipt.get("humanAuthorityRequired").asBoolean()).isTrue();
    assertThat(postCommand("review",review,reviewKey,CAPS,200)).isEqualTo(receipt);
    assertThat(db.sql("select count(*) from ouf_sem.approval_challenge where revision_id=:r").param("r",UUID.fromString(r)).query(Long.class).single()).isEqualTo(1L);
    assertThat(db.sql("select count(*) from ouf_sem.artifact_active_revision where artifact_id=:a").param("a",UUID.fromString(created.get("artifactId").asText())).query(Long.class).single()).isZero();
  }
  @Test void duplicateCreateWithChangedIntentConflicts() {
    String k=key();var c=command();commands.create("tenant-a","agent","AI_AGENT",k,c,"test");
    assertThatThrownBy(()->commands.create("tenant-a","agent","AI_AGENT",k,command(),"test")).hasMessage("IDEMPOTENCY_KEY_REUSE");
  }
  @Test void importedRdfReplayRetainsExactSnapshotAndRejectsChangedOrUnsafeShape() {
    var c=command();var ontology=new CreateArtifact(c.semanticId(),"ONTOLOGY",c.namespace(),c.localName(),c.ownerRef(),c.authorityRef(),c.semanticVersion(),c.labels(),Map.of());
    String turtle="<"+c.semanticId()+"> a <http://www.w3.org/2002/07/owl#Ontology> .",k=key();
    var first=commands.createImported("tenant-a","agent","AI_AGENT",k,ontology,turtle,"text/turtle","test");
    assertThat(commands.createImported("tenant-a","agent","AI_AGENT",k,ontology,turtle,"text/turtle","test")).isEqualTo(first);
    assertThatThrownBy(()->commands.createImported("tenant-a","agent","AI_AGENT",k,ontology,turtle+"\n","text/turtle","test")).hasMessage("IDEMPOTENCY_KEY_REUSE");
    assertThatThrownBy(()->commands.createImported("tenant-a","agent","AI_AGENT",key(),ontology,turtle,"application/ld+json","test")).hasMessage("SEM_PROPOSAL_RDF_SHAPE_INVALID");
    assertThatThrownBy(()->commands.createImported("tenant-a","agent","AI_AGENT",key(),ontology,"é".repeat(24577),"text/turtle","test")).hasMessage("SEM_PROPOSAL_RDF_SHAPE_INVALID");
    assertThatThrownBy(()->commands.createImported("tenant-a","agent","AI_AGENT",key(),c,turtle,"text/turtle","test")).hasMessage("SEM_PROPOSAL_RDF_SHAPE_INVALID");
    assertThatThrownBy(()->commands.createImported("tenant-a","agent","AI_AGENT",key(),ontology,"<urn:other> a <http://www.w3.org/2002/07/owl#Ontology> .","text/turtle","test")).hasMessage("RDF_IDENTITY_OR_TYPE_MISMATCH");
    assertThat(db.sql("select count(*) from ouf_sem.revision_interchange_snapshot where revision_id=:r").param("r",revision(first)).query(Long.class).single()).isEqualTo(1L);
  }
  @Test void receiptReadIsTenantAndPrincipalScopedAndDurable() {
    String k=key();var c=command();commands.create("tenant-a","agent","AI_AGENT",k,c,"test");
    assertThat(commands.receipt("tenant-a","agent",k).get("operation")).isEqualTo("CREATE");
    assertThatThrownBy(()->commands.receipt("tenant-b","agent",k)).hasMessage("PROPOSAL_RECEIPT_NOT_FOUND");
    assertThatThrownBy(()->commands.receipt("tenant-a","other",k)).hasMessage("PROPOSAL_RECEIPT_NOT_FOUND");
  }
  @Test void concurrentDuplicateCreatePublishesOneReceipt()throws Exception{
    String k=key();var c=command();var start=new CountDownLatch(1);
    try(var pool=Executors.newFixedThreadPool(2)){
      Callable<Map<String,Object>> call=()->{start.await();return commands.create("tenant-a","agent","AI_AGENT",k,c,"test");};
      var a=pool.submit(call);var b=pool.submit(call);start.countDown();
      assertThat(a.get(10,TimeUnit.SECONDS).get("revisionId").toString()).isEqualTo(b.get(10,TimeUnit.SECONDS).get("revisionId").toString());
    }
    assertThat(db.sql("select count(*) from ouf_sem.semantic_artifact where semantic_id=:s").param("s",c.semanticId()).query(Long.class).single()).isEqualTo(1L);
  }
  @Test void staleVersionAndStaleValidationDoNotFreezeDraft() {
    UUID r=revision(commands.create("tenant-a","agent","AI_AGENT",key(),command(),"test"));
    var run=commands.validate("tenant-a","agent",key(),r,0);
    artifacts.patch(r,"\"0\"",new it.comune.trieste.ouf.semantic.api.ArtifactApi.PatchRevision(Map.of("it","Changed"),Map.of()),"agent","AI_AGENT","test");
    UUID v=UUID.fromString(run.get("validation_run_id").toString());
    assertThatThrownBy(()->commands.review("tenant-a","agent","AI_AGENT",key(),r,0,v,"test")).hasMessage("DRAFT_VERSION_CONFLICT");
    assertThatThrownBy(()->commands.review("tenant-a","agent","AI_AGENT",key(),r,1,v,"test")).hasMessage("CURRENT_GREEN_VALIDATION_REQUIRED");
  }
  @Test void validationFailureRetainsWarningsButCannotOpenReview() {
    var c=command();var broken=new CreateArtifact(c.semanticId(),"PROPERTY",c.namespace(),c.localName(),c.ownerRef(),c.authorityRef(),c.semanticVersion(),c.labels(),Map.of("domainRefs",List.of("ouf:absent:"+key())));
    UUID r=revision(commands.create("tenant-a","agent","AI_AGENT",key(),broken,"test"));
    var run=commands.validate("tenant-a","agent",key(),r,0);
    assertThat(run.get("status")).isEqualTo("FAIL");assertThat(((Number)run.get("warning_count")).intValue()).isPositive();
    assertThatThrownBy(()->commands.review("tenant-a","agent","AI_AGENT",key(),r,0,UUID.fromString(run.get("validation_run_id").toString()),"test")).hasMessage("CURRENT_GREEN_VALIDATION_REQUIRED");
  }
  @Test void denialAndRevocationPreventFreshOrRepeatedCommands()throws Exception{
    var c=command();String k=key();postCommand("create",c,k,CAPS,200);
    postCommand("create",c,k,Set.of(),403);
    postCommand("review",Map.of("revisionId",UUID.randomUUID(),"expectedRowVersion",0,"validationRunId",UUID.randomUUID()),key(),Set.of("ouf.semantic.approval.request"),403);
  }
  @Test void failedTransactionLeavesNoReceiptAndKeyCanReconcile() {
    String k=key();UUID missing=UUID.randomUUID();
    assertThatThrownBy(()->commands.validate("tenant-a","agent",k,missing,0)).hasMessage("REVISION_NOT_FOUND");
    assertThatThrownBy(()->commands.receipt("tenant-a","agent",k)).hasMessage("PROPOSAL_RECEIPT_NOT_FOUND");
    UUID r=revision(commands.create("tenant-a","agent","AI_AGENT",key(),command(),"test"));
    assertThat(commands.validate("tenant-a","agent",k,r,0).get("status")).isEqualTo("PASS");
  }
}

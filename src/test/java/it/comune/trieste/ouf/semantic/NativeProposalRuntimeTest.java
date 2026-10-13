package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.semantic.api.*;
import it.comune.trieste.ouf.semantic.application.*;
import it.comune.trieste.ouf.authorization.TestAuthorization;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.mock.web.MockHttpServletRequest;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
class NativeProposalRuntimeTest {
  @Autowired NativeProposalService proposals;
  @Autowired ArtifactService artifacts;
  @Autowired GovernanceService governance;
  @Autowired ValidationService validation;
  @Autowired JdbcClient db;
  @Autowired ObjectMapper json;
  @TempDir Path tmp;
  List<ArtifactApi.CreateArtifact> commands(){
    String ns="urn:native-test:"+UUID.randomUUID()+":";
    return List.of(command(ns,"Teatro","CLASS",Map.of()),command(ns,"nome","PROPERTY",Map.of("domainRefs",List.of(ns+"Teatro"),"datatype","http://www.w3.org/2001/XMLSchema#string")));
  }
  ArtifactApi.CreateArtifact command(String ns,String local,String type,Map<String,Object> definition){return new ArtifactApi.CreateArtifact(ns+local,type,ns,local,"fixture-owner","fixture-authority","1.0.0",Map.of("it",local),definition);}
  @SuppressWarnings("unchecked") UUID revision(Map<String,Object> result){return UUID.fromString(((List<Map<String,Object>>)result.get("revisions")).get(0).get("revisionId").toString());}
  @Test void durableChainReconcilesAfterLostRepliesWithoutDuplicateEffects() {
    String key=UUID.randomUUID().toString();var input=commands();
    var created=proposals.create("tenant-a","author","AI_AGENT",key,input,"corr");
    var recreated=proposals.create("tenant-a","author","AI_AGENT",key,input,"retry");
    assertThat(recreated.get("proposalId").toString()).isEqualTo(created.get("proposalId").toString());
    var validated=proposals.validate("tenant-a","author",key,0);
    assertThat(validated.get("validationPassed")).isEqualTo(true);
    assertThat(proposals.validate("tenant-a","author",key,0)).isEqualTo(proposals.read("tenant-a","author",key));
    var requested=proposals.requestReview("tenant-a","author","AI_AGENT",key,1,"corr");
    assertThat(requested.get("published")).isEqualTo(false);
    assertThat(requested.get("challenges")).asList().hasSize(2);
    assertThat(proposals.requestReview("tenant-a","author","AI_AGENT",key,1,"retry")).isEqualTo(proposals.read("tenant-a","author",key));
    // A reconstructed service reads the committed receipt; no process-local authority.
    var restarted=new NativeProposalService(db,json,artifacts,validation,governance);
    assertThat(restarted.read("tenant-a","author",key)).isEqualTo(proposals.read("tenant-a","author",key));
    assertThat(db.sql("select count(*) from ouf_sem.approval_challenge where revision_id=:r").param("r",revision(created)).query(Long.class).single()).isEqualTo(1);
    assertThat(db.sql("select lifecycle_status from ouf_sem.artifact_revision where revision_id=:r").param("r",revision(created)).query(String.class).single()).isEqualTo("UNDER_REVIEW");
  }
  @Test void concurrentCreateAndReviewHaveOneOwnerEffect() throws Exception {
    String key=UUID.randomUUID().toString();var input=commands();
    try(var pool=Executors.newVirtualThreadPerTaskExecutor()) {
      var start=new CyclicBarrier(2);
      Callable<Map<String,Object>> create=()->{start.await(5,TimeUnit.SECONDS);return proposals.create("tenant-a","author","AI_AGENT",key,input,"concurrent");};
      var a=pool.submit(create);var b=pool.submit(create);
      assertThat(a.get(10,TimeUnit.SECONDS).get("proposalId").toString()).isEqualTo(b.get(10,TimeUnit.SECONDS).get("proposalId").toString());
      proposals.validate("tenant-a","author",key,0);
      var reviewStart=new CyclicBarrier(2);
      Callable<Map<String,Object>> review=()->{reviewStart.await(5,TimeUnit.SECONDS);return proposals.requestReview("tenant-a","author","AI_AGENT",key,1,"concurrent");};
      var c=pool.submit(review);var d=pool.submit(review);c.get(10,TimeUnit.SECONDS);d.get(10,TimeUnit.SECONDS);
      UUID r=revision(proposals.read("tenant-a","author",key));
      assertThat(db.sql("select count(*) from ouf_sem.approval_challenge where revision_id=:r").param("r",r).query(Long.class).single()).isEqualTo(1);
    }
  }
  @Test void changedIntentAndCrossPrincipalReadsAreBlocked() {
    String key=UUID.randomUUID().toString();proposals.create("tenant-a","author","AI_AGENT",key,commands(),"corr");
    assertThatThrownBy(()->proposals.create("tenant-a","author","AI_AGENT",key,commands(),"corr")).hasMessage("SEM_PROPOSAL_INTENT_CONFLICT");
    assertThatThrownBy(()->proposals.read("tenant-b","author",key)).isInstanceOf(NoSuchElementException.class);
    assertThatThrownBy(()->proposals.read("tenant-a","another",key)).isInstanceOf(NoSuchElementException.class);
    assertThatThrownBy(()->proposals.validate("tenant-a","author",key,1)).hasMessage("SEM_PROPOSAL_VERSION_CONFLICT");
  }
  @Test void creationRollsBackAllEffectsOnMidBatchConflict() {
    var input=commands();proposals.create("tenant-a","author","AI_AGENT",UUID.randomUUID().toString(),input,"corr");
    String key=UUID.randomUUID().toString();var first=commands().get(0);
    assertThatThrownBy(()->proposals.create("tenant-a","author","AI_AGENT",key,List.of(first,input.get(0)),"corr")).hasMessage("SEMANTIC_ID_CONFLICT");
    assertThatThrownBy(()->proposals.read("tenant-a","author",key)).isInstanceOf(NoSuchElementException.class);
    assertThat(db.sql("select count(*) from ouf_sem.semantic_artifact where semantic_id=:s").param("s",first.semanticId()).query(Long.class).single()).isZero();
  }
  @Test void changedRevisionOrFailedValidationCannotReachReview() {
    String key=UUID.randomUUID().toString();var created=proposals.create("tenant-a","author","AI_AGENT",key,commands(),"corr");
    proposals.validate("tenant-a","author",key,0);
    artifacts.patch(revision(created),"\"0\"",new ArtifactApi.PatchRevision(Map.of("it","changed"),Map.of()),"author","AI_AGENT","edit");
    assertThatThrownBy(()->proposals.requestReview("tenant-a","author","AI_AGENT",key,1,"corr")).hasMessage("SEM_PROPOSAL_REVISION_DRIFT");
    assertThat(proposals.read("tenant-a","author",key).get("phase")).isEqualTo("VALIDATED");
    String bad=UUID.randomUUID().toString();String ns="urn:bad-test:"+bad+":";
    proposals.create("tenant-a","author","AI_AGENT",bad,List.of(command(ns,"invalid","PROPERTY",Map.of("domainRefs",List.of("urn:missing:"+bad)))),"corr");
    assertThat(proposals.validate("tenant-a","author",bad,0).get("validationPassed")).isEqualTo(false);
    assertThatThrownBy(()->proposals.requestReview("tenant-a","author","AI_AGENT",bad,1,"corr")).hasMessage("SEM_PROPOSAL_VALIDATION_REQUIRED");
  }
  @Test void challengeRejectsUnvalidatedOrForgedHash() {
    String key=UUID.randomUUID().toString();var created=proposals.create("tenant-a","author","AI_AGENT",key,commands(),"corr");
    assertThatThrownBy(()->governance.challenge(revision(created),"a".repeat(64),java.time.Duration.ofMinutes(15),"author","AI_AGENT","corr")).hasMessage("SEM_REVIEW_CURRENT_VALIDATION_REQUIRED");
    proposals.validate("tenant-a","author",key,0);
    assertThatThrownBy(()->governance.challenge(revision(created),"a".repeat(64),java.time.Duration.ofMinutes(15),"author","AI_AGENT","corr")).hasMessage("SEM_REVIEW_CURRENT_VALIDATION_REQUIRED");
  }
  @Test void actualGatewayLuaToJavaOwnerRunsWholePreparationChainAndDeniesMissingPolicy() throws Exception {
    String gateway=System.getenv("OUF_SEMANTIC_GATEWAY_PAIRWISE_ROOT");
    org.junit.jupiter.api.Assumptions.assumeTrue(gateway!=null&&!gateway.isBlank());
    Path fixture=tmp.resolve("proposal-receipts.json");
    var pb=new ProcessBuilder("python3",Path.of(gateway,"scripts/export_semantic_proposal_pairwise.py").toString(),"--output",fixture.toString());pb.environment().put("PYTHONPATH",gateway);
    var process=pb.redirectErrorStream(true).start();assertThat(process.waitFor(10,TimeUnit.SECONDS)).isTrue();assertThat(process.exitValue()).isZero();
    var f=json.readTree(Files.readString(fixture));Path file=tmp.resolve("key");Files.writeString(file,"ab".repeat(32));
    var verifier=new SemanticProposalDelegation(json,file.toString(),"https://auth.test/realms/ouf","gateway","workload");
    var api=new SemanticProposalApi(verifier,proposals,json);
    for(String name:List.of("create","validate","request","read")) {
      byte[] raw=f.required(name).required("body").asText().getBytes(java.nio.charset.StandardCharsets.UTF_8);
      String cap=json.readTree(raw).required("CapabilityID").asText();String permission=name.equals("read")?"ouf.semantic.propose":cap;
      String proof=f.required(name).required("receipt").asText();
      var denied=new MockHttpServletRequest("POST","/api/internal/v1/semantic/proposals/"+name);denied.addHeader("X-OUF-Semantic-Proposal-Receipt",proof);TestAuthorization.bind(denied,"human-a","HUMAN",Set.of());
      if(name.equals("create"))assertThatThrownBy(()->api.create(raw,denied)).isInstanceOf(SecurityException.class);
      var req=new MockHttpServletRequest("POST","/api/internal/v1/semantic/proposals/"+name);req.addHeader("X-OUF-Semantic-Proposal-Receipt",proof);TestAuthorization.bind(req,"human-a","HUMAN",Set.of(permission));
      Object result=switch(name){case "create"->api.create(raw,req);case "validate"->api.validate(raw,req);case "request"->api.review(raw,req);default->api.read(raw,req);};
      assertThat(((Map<?,?>)result).get("published")).isEqualTo(false);
      if(name.equals("request"))assertThat(((Map<?,?>)result).get("challenges")).asList().hasSize(1);
      assertThatThrownBy(()->verifier.verify(proof,req.getRequestURI(),"ouf.semantic.publish",raw)).isInstanceOf(SecurityException.class);
    }
  }
}

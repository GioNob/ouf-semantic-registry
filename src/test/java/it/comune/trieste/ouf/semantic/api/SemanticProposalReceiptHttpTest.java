package it.comune.trieste.ouf.semantic.api;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import com.fasterxml.jackson.databind.JsonNode;
import it.comune.trieste.ouf.authorization.*;
import it.comune.trieste.ouf.authorization.AuthorizationPolicy.*;
import it.comune.trieste.ouf.semantic.application.GovernanceService;
import it.comune.trieste.ouf.semantic.application.ProposalCommandService;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.time.*;
import java.util.*;
import java.util.stream.IntStream;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
@AutoConfigureMockMvc
@Import(SignedProposalFixture.Fixture.class)
class SemanticProposalReceiptHttpTest extends SignedProposalFixture {
  @Autowired ProposalCommandService commands;
  @Autowired GovernanceService governance;

  @Test void signedValueMapWithTwoThousandMaximumLengthCodesStoresOnlyColumnMetadata() throws Exception {
    String root="https://example.org/signed-maps/";
    String vocabulary=root+UUID.randomUUID();
    String conceptPrefix=root+UUID.randomUUID();
    String longConcept=conceptPrefix+"c".repeat(512-conceptPrefix.length());
    String concept=root+UUID.randomUUID();
    publishTerm(vocabulary,"VOCABULARY",Map.of());
    publishTerm(longConcept,"CONCEPT",Map.of("vocabularyRef",vocabulary));
    UUID publication=publishTerm(concept,"CONCEPT",Map.of("vocabularyRef",vocabulary));
    var entries=IntStream.range(0,2000).mapToObj(i -> Map.of(
        "code","a".repeat(124)+String.format(Locale.ROOT,"%04d",i),
        "concept",i==0?longConcept:concept)).toList();
    var definition=Map.of("targetVocabulary",vocabulary+"@"+publication,"entries",entries);
    var source=Map.of("fieldName","codice_servizio","sourceId","source-1");
    String key=UUID.randomUUID().toString();
    String localName=UUID.randomUUID().toString();
    String cap="ouf.semantic.propose";
    var args=new LinkedHashMap<>(Map.<String,Object>of("semanticId",root+localName,"namespace",root,
        "localName",localName,"artifactType","VALUE_MAP","semanticVersion","1.0.0","ownerRef","owner",
        "authorityRef","authority","commandKey",key,"definition",definition,"rationale",Map.of("sourceColumn",source)));
    byte[] envelope=envelope(cap,"COMMAND",key,args);
    assertThat(envelope.length).isBetween(65537,1048576);
    var created=send("create",cap,cap,key,args,CAPS,200);
    assertThat(send("create",cap,cap,key,args,CAPS,200)).isEqualTo(created);
    args.put("rationale",Map.of("sourceColumn",Map.of("fieldName","a different column")));
    assertThat(send("create",cap,cap,key,args,CAPS,409).required("code").asText()).isEqualTo("IDEMPOTENCY_KEY_REUSE");
    for(var column:List.of(Map.of("fieldName",""),Map.of("fieldName","a".repeat(257)),
        Map.of("fieldName","codice_servizio","values",List.of("private-source-value")))){
      args.put("rationale",Map.of("sourceColumn",column));
      var problem=send("create",cap,cap,key,args,CAPS,400);
      assertThat(problem.required("code").asText()).isEqualTo("SEMANTIC_VALUE_MAP_INVALID");
      assertThat(problem.toString()).doesNotContain("private-source-value");
    }

    UUID revision=UUID.fromString(created.required("revisionId").asText());
    var review=prepareReview(revision);
    var card=governance.card(UUID.fromString(review.get("challengeId").toString()));
    var projected=json.valueToTree(card).required("valueMapReview");
    assertThat(projected.required("entryCount").asInt()).isEqualTo(2000);
    assertThat(projected.at("/entries/0/concept").asText()).isEqualTo(longConcept);
    assertThat(projected.required("sourceColumn")).isEqualTo(json.valueToTree(source));
    assertThat(projected.has("changes")).isFalse();
    JsonNode storedDefinition=json.valueToTree(card.get("definition_json"));
    assertThat(storedDefinition).isEqualTo(json.valueToTree(definition));
  }

  private UUID publishTerm(String id,String type,Map<String,Object> definition) {
    int separator=id.lastIndexOf('/')+1;
    var proposal=new ArtifactApi.CreateArtifact(id,type,id.substring(0,separator),id.substring(separator),
        "owner","authority","1.0.0",Map.of("it","Etichetta"),definition);
    UUID revision=UUID.fromString(commands.create("tenant-a","agent","AI_AGENT",UUID.randomUUID().toString(),
        proposal,"test").get("revisionId").toString());
    var review=prepareReview(revision);
    var decision=governance.decide(UUID.fromString(review.get("challengeId").toString()),"APPROVED","reviewer","HUMAN","fixture","test");
    return (UUID)governance.publish(revision,(UUID)decision.get("decisionId"),UUID.randomUUID().toString(),
        review.get("targetContentHash").toString(),"reviewer","HUMAN","test").get("publicationSetId");
  }

  private Map<String,Object> prepareReview(UUID revision) {
    var validation=commands.validate("tenant-a","agent",UUID.randomUUID().toString(),revision,0);
    assertThat(validation).containsEntry("status","PASS");
    return commands.review("tenant-a","agent","AI_AGENT",UUID.randomUUID().toString(),revision,0,
        UUID.fromString(validation.get("validation_run_id").toString()),"test");
  }

  @Test void signedEnvelopeTraversesFilterCurrentOwnerPolicyPostgresqlAndReceiptRead()throws Exception{
    String k=UUID.randomUUID().toString();String semantic="ouf:signed:"+UUID.randomUUID();
    var c=new LinkedHashMap<String,Object>();c.put("semanticId",semantic);c.put("artifactType","CLASS");c.put("namespace","ouf");c.put("localName","SignedPlace"+UUID.randomUUID().toString().replace("-",""));
    c.put("ownerRef","owner");c.put("authorityRef","authority");c.put("semanticVersion","1.0.0");c.put("labels",Map.of("it","Luogo"));c.put("definition",Map.of());c.put("commandKey",k);
    var created=send("create","ouf.semantic.propose","ouf.semantic.propose",k,c,CAPS,200);
    var read=send("read","ouf.semantic.proposal.read","ouf.semantic.proposal.read",UUID.randomUUID().toString(),Map.of("commandKey",k),CAPS,200);
    assertThat(read.get("result").get("revisionId").asText()).isEqualTo(created.get("revisionId").asText());
    send("read","ouf.semantic.proposal.read","ouf.semantic.proposal.read",UUID.randomUUID().toString(),Map.of("commandKey",k),Set.of("ouf.semantic.read","ouf.semantic.propose"),403);
    send("read","ouf.semantic.proposal.read","ouf.semantic.proposal.read",UUID.randomUUID().toString(),Map.of("commandKey",k),Set.of("ouf.semantic.proposal.read"),403);
    send("read","ouf.semantic.proposal.read","ouf.semantic.read",UUID.randomUUID().toString(),Map.of("commandKey",k),CAPS,403);
    send("create","ouf.semantic.propose","ouf.semantic.propose",k,c,Set.of(),403);
    String revision=created.get("revisionId").asText();String vk=UUID.randomUUID().toString();
    var validation=send("validate","ouf.semantic.review.prepare","ouf.semantic.review.prepare",vk,Map.of("commandKey",vk,"revisionId",revision,"expectedRowVersion",0),CAPS,200);
    String rk=UUID.randomUUID().toString();var review=send("review","ouf.semantic.approval.request","ouf.semantic.approval.request",rk,
        Map.of("commandKey",rk,"revisionId",revision,"expectedRowVersion",0,"validationRunId",validation.get("validation_run_id").asText()),CAPS,200);
    assertThat(review.get("trustedApprovalRef").asText()).startsWith("ths://semantic-approval-challenges/");
    assertThat(review.get("humanAuthorityRequired").asBoolean()).isTrue();
  }
  @Test void adoptionRequiresProposalProofDiscoveryScopeHumanDescriptorAndClosedArguments()throws Exception {
    String path="/api/semantic/v1/proposal-commands/adopt";
    String key=UUID.randomUUID().toString();
    UUID job=UUID.randomUUID(),candidate=UUID.randomUUID();
    var args=Map.<String,Object>of("commandKey",key,"requestId",job,"candidateId",candidate);
    byte[] raw=envelope(ADOPT,"COMMAND",key,args);
    var now=Instant.now();
    var human=Set.of(PrincipalContext.ActorType.HUMAN);
    var descriptor=new CapabilityDescriptor(ADOPT,"COMMAND",DISCOVERY_SCOPE,human);
    String readCap="ouf.semantic.proposal.read";
    var read=new CapabilityDescriptor(readCap,"READ",readCap,human);
    var grant=new Grant("grant",ADOPT,"tenant-a","agent",null,null,
        now.minusSeconds(60),now.plusSeconds(600));
    var readGrant=new Grant("read",readCap,"tenant-a","agent",null,null,grant.validFrom(),grant.validUntil());
    var runtime=new LocalAuthorization(Clock.systemUTC(),Duration.ofHours(1));
    TestAuthorization.install(runtime,new PolicyBundle("fixture",1,now,List.of(descriptor,read),List.of(grant,readGrant)));
    http.getDispatcherServlet().getServletContext().setAttribute(ServletAuthorization.RUNTIME,runtime);
    http.perform(post(path).header("X-OUF-Semantic-Proposal-Receipt",proof(path,ADOPT,key,raw))
        .contentType(MediaType.APPLICATION_JSON).content(raw)).andExpect(status().isNotFound())
        .andExpect(jsonPath("$.code").value("SEMANTIC_CANDIDATE_NOT_FOUND"));
    String uri="https://example.org/"+candidate;
    String actor="mcp-discovery-v1:"+HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(
        json.writeValueAsBytes(List.of("https://auth.test/realms/ouf","tenant-a","agent"))));
    db.sql("insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,state,created_by_subject) values(:j,'CLASS','place','SUCCEEDED',:actor)")
        .param("j",job).param("actor",actor).update();
    byte[] bytes=("<"+uri+"> a <http://www.w3.org/2002/07/owl#Class> ; <http://purl.org/dc/terms/publisher> <urn:publisher> .").getBytes(StandardCharsets.UTF_8);
    db.sql("""
        insert into ouf_sem.discovery_candidate(candidate_id,request_id,provider_id,canonical_uri,source_location,artifact_type,
          provider_trust,score,normalized_payload,content_hash,media_type,content_bytes,expires_at)
        values(:c,:r,'TEST',:uri,:uri,'CLASS','HIGH',1,'{}',:hash,'text/turtle',:bytes,now()+interval '1 hour')
        """).param("c",candidate).param("r",job).param("uri",uri).param("bytes",bytes)
        .param("hash",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))).update();
    var signed=post(path).header("X-OUF-Semantic-Proposal-Receipt",proof(path,ADOPT,key,raw))
        .contentType(MediaType.APPLICATION_JSON).content(raw);
    var receipt=json.readTree(http.perform(signed).andExpect(status().isOk()).andReturn().getResponse().getContentAsByteArray());
    var replay=signed.header("idempotency-key","unsigned-1","unsigned-2");
    assertThat(json.readTree(http.perform(replay).andExpect(status().isOk()).andReturn().getResponse().getContentAsByteArray())).isEqualTo(receipt);
    String readPath="/api/semantic/v1/proposal-commands/read",readKey=UUID.randomUUID().toString();
    byte[] query=envelope(readCap,"READ",readKey,Map.of("commandKey",key));
    var lookup=post(readPath).header("X-OUF-Semantic-Proposal-Receipt",proof(readPath,readCap,readKey,query))
        .contentType(MediaType.APPLICATION_JSON).content(query);
    assertThat(json.readTree(http.perform(lookup).andExpect(status().isOk()).andReturn().getResponse().getContentAsByteArray()).required("result"))
        .isEqualTo(receipt);
    http.perform(post(path).contentType(MediaType.APPLICATION_JSON).content(raw)).andExpect(status().isForbidden());
    var extra=new LinkedHashMap<>(args);extra.put("publisher","caller");
    byte[] changed=envelope(ADOPT,"COMMAND",key,extra);
    http.perform(post(path).header("X-OUF-Semantic-Proposal-Receipt",proof(path,ADOPT,key,changed))
        .contentType(MediaType.APPLICATION_JSON).content(changed)).andExpect(status().isForbidden());
    TestAuthorization.install(runtime,new PolicyBundle("fixture",2,now,List.of(descriptor,read),List.of(readGrant)));
    http.perform(signed).andExpect(status().isForbidden());
    http.perform(lookup).andExpect(status().isForbidden());
  }
  @Test void unsignedBodyAndTamperedReceiptCannotEstablishIdentity()throws Exception{
    String path="/api/semantic/v1/proposal-commands/create";byte[] raw=envelope("ouf.semantic.propose","COMMAND","intent-1",Map.of("commandKey","intent-1"));
    http.perform(post(path).header("X-OUF-Principal-ID","agent").header("Idempotency-Key","intent-1").contentType(MediaType.APPLICATION_JSON).content(raw)).andExpect(status().isForbidden());
    http.perform(post(path).header("X-OUF-Semantic-Proposal-Receipt",proof(path,"ouf.semantic.propose","intent-1",raw)).contentType(MediaType.APPLICATION_JSON).content("{}"))
        .andExpect(status().isForbidden()).andExpect(jsonPath("$.code").value("SEM_PROPOSAL_RECEIPT_INVALID"));
  }
}

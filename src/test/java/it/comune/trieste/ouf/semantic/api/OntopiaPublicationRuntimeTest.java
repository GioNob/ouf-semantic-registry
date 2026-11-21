package it.comune.trieste.ouf.semantic.api;

import static it.comune.trieste.ouf.semantic.adapters.discovery.OntopiaGatewayFixture.*;
import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.authorization.*;
import it.comune.trieste.ouf.authorization.AuthorizationPolicy.*;
import it.comune.trieste.ouf.semantic.adapters.discovery.OntopiaGatewayFixture;
import it.comune.trieste.ouf.semantic.application.DiscoveryService;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.time.*;
import java.util.*;
import org.apache.jena.vocabulary.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.*;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.context.annotation.*;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.request.RequestPostProcessor;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
@AutoConfigureMockMvc
@Import({SignedProposalFixture.Fixture.class,OntopiaPublicationRuntimeTest.ReadFixture.class})
class OntopiaPublicationRuntimeTest extends SignedProposalFixture {
  private static final String ISSUER="https://auth.test/realms/ouf";
  private static final String INTENT="punto di interesse";
  private static final String AGID="http://spcdata.digitpa.gov.it/Amministrazione/agid";
  @Autowired OntopiaGatewayFixture fixture;
  @Autowired DiscoveryService worker;
  @TestConfiguration static class ReadFixture {
    @Bean OntopiaGatewayFixture ontopiaGateway(ObjectMapper json)throws Exception{return new OntopiaGatewayFixture(json);}
    @Bean @Primary SemanticDiscoveryProvider fixtureProvider(OntopiaGatewayFixture gateway){return gateway.provider;}
    @Bean @Primary SemanticDiscoveryDelegation discoveryDelegation(ObjectMapper json)throws Exception{
      var file=Files.createTempFile("semantic-discovery-fixture",".key");
      try {Files.write(file,KEY);return new SemanticDiscoveryDelegation(json,file.toString(),ISSUER,"gateway","workload");}
      finally {Files.delete(file);}
    }
    @Bean @Primary SemanticReadDelegation reads(ObjectMapper json)throws Exception{
      var file=Files.createTempFile("semantic-read-fixture",".key");
      try {Files.write(file,KEY);return new SemanticReadDelegation(json,file.toString(),ISSUER,"gateway","workload");}
      finally {Files.delete(file);}
    }
  }

  private record Selection(UUID request,UUID candidate){}
  private Selection discover()throws Exception{
    var request=delegated("discovery/request",DISCOVERY_SCOPE,DISCOVERY_SCOPE,"COMMAND",
        Map.of("requestedArtifactType","CLASS","intent",INTENT,"preferredLanguages",List.of("it"),"idempotencyKey",UUID.randomUUID().toString()));
    UUID job=UUID.fromString(request.required("requestId").asText());
    // Give the fixture precedence over unfinished jobs from other runtime tests.
    db.sql("update ouf_sem.discovery_request set created_at=timestamp '1800-01-01' where request_id=?").param(job).update();
    assertThat(worker.executeOne()).isOne();
    var args=Map.<String,Object>of("requestId",job);
    var status=delegated("discovery/status","ouf.semantic.discovery.status",DISCOVERY_SCOPE,"READ",args);
    assertThat(status.required("state").asText()).isEqualTo("SUCCEEDED");
    var candidates=delegated("discovery/candidates","ouf.semantic.discovery.candidates",DISCOVERY_SCOPE,"READ",args);
    assertThat(candidates.size()).isEqualTo(5);
    for(var candidate:candidates)if(POI.equals(candidate.required("canonical_uri").asText()))
      return new Selection(job,UUID.fromString(candidate.required("candidate_id").asText()));
    throw new AssertionError("PointOfInterest missing from discovery");
  }

  private static String hash(byte[] bytes)throws Exception{
    return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
  }
  private RequestPostProcessor grant(String capability,String scope,String operation)throws Exception{
    var now=Instant.now();
    var descriptor=new CapabilityDescriptor(capability,operation,scope,Set.of(PrincipalContext.ActorType.HUMAN));
    var grant=new Grant("grant",capability,"tenant-a","agent",null,null,now.minusSeconds(60),now.plusSeconds(600));
    var runtime=new LocalAuthorization(Clock.systemUTC(),Duration.ofHours(1));
    TestAuthorization.install(runtime,new PolicyBundle("fixture",1,now,List.of(descriptor),List.of(grant)));
    return request->{request.getServletContext().setAttribute(ServletAuthorization.RUNTIME,runtime);return request;};
  }
  private JsonNode adopt(Selection selection,int expected)throws Exception{
    String key=UUID.randomUUID().toString(),path="/api/semantic/v1/proposal-commands/adopt";
    byte[] raw=envelope(ADOPT,"COMMAND",key,Map.of("commandKey",key,"requestId",selection.request(),"candidateId",selection.candidate()));
    return json.readTree(http.perform(post(path).with(grant(ADOPT,DISCOVERY_SCOPE,"COMMAND"))
        .header("X-OUF-Semantic-Proposal-Receipt",proof(path,ADOPT,key,raw))
        .contentType(MediaType.APPLICATION_JSON).content(raw)).andExpect(status().is(expected)).andReturn().getResponse().getContentAsByteArray());
  }
  private JsonNode delegated(String route,String capability,String scope,String operation,Map<String,Object> args)throws Exception{
    String path="/api/internal/v1/semantic/"+route;
    boolean discovery=route.startsWith("discovery/");
    String purpose=discovery?"semantic-discovery-owner":"semantic-read-owner";
    byte[] raw=json.writeValueAsBytes(Map.of("Owner","semantic","CapabilityID",capability,"GatewayBindingRef","capability://"+capability,
        "OperationClass",operation,"Arguments",args));
    long now=Instant.now().getEpochSecond();
    var receipt=new SemanticReadDelegation.Receipt(1,purpose,"POST",path,hash(raw),capability,now,now+30,
        ISSUER,"gateway","workload","agent","tenant-a","fixture","",scope);
    return json.readTree(http.perform(post(path).with(grant(capability,scope,operation))
        .header(discovery?"X-OUF-Semantic-Discovery-Receipt":"X-OUF-Semantic-Read-Receipt",sign("ouf-"+purpose+"-v1",receipt))
        .contentType(MediaType.APPLICATION_JSON).content(raw)).andExpect(status().isOk()).andReturn().getResponse().getContentAsByteArray());
  }
  private RequestPostProcessor reviewer(String capability){
    return r->{TestAuthorization.bind(r,"reviewer","HUMAN",Set.of(capability));return r;};
  }

  @Test void absentOntologyKeepsAllCandidatesAndReturnsTheExistingAdoptionConflict()throws Exception{
    fixture.ontologyAvailable(false);
    var candidate=discover();
    assertThat(adopt(candidate,409).required("code").asText()).isEqualTo("CANDIDATE_PUBLISHER_MISSING");
    fixture.verifyOntologyFetches(1);
    assertThat(db.sql("select state from ouf_sem.discovery_dependency where active_request is null and provider_id='SCHEMA_GOV_IT' and scope_subject=(select created_by_subject from ouf_sem.discovery_request where request_id=?)")
        .param(candidate.request()).query(String.class).single()).isEqualTo("HEALTHY");
  }

  @Test void realPoiIsReviewedByAHumanPublishedReadAndRediscovered()throws Exception{
    fixture.ontologyAvailable(true);
    var first=discover();
    JsonNode draft=adopt(first,200);
    assertThat(draft.required("status").asText()).isEqualTo("DRAFT");
    String revision=draft.required("revisionId").asText();
    long version=draft.required("expectedRowVersion").asLong();
    JsonNode provenance=draft.required("provenance");
    assertThat(provenance.required("publisher").asText()).isEqualTo(AGID);
    assertThat(provenance.required("license").isNull()).isTrue();
    assertThat(provenance.required("licenseWarning").asText()).isEqualTo("licenza mancante");
    String classHash=hash(fixture.poiBytes);
    assertThat(classHash).isEqualTo("8a8dd9623c5c84dd7057311cb56fa2088d9d8a4d26b1fc732906a1a057f7ec61");
    assertThat(provenance.required("rdfSha256").asText()).isEqualTo(classHash);
    byte[] companion=db.sql("select ontology_rdf from ouf_sem.immutable_semantic_snapshot where snapshot_id=?")
        .param(UUID.fromString(provenance.required("snapshotId").asText())).query(byte[].class).single();
    assertThat(provenance.required("ontologySha256").asText()).isEqualTo(hash(companion));
    var graph=new SafeRdfParser().model(companion,"application/n-triples");
    try {
      assertThat(graph.size()).isEqualTo(6L);
      graph.listStatements().forEachRemaining(s->{
        assertThat(s.getSubject().getURI()).isEqualTo(ONTOLOGY);
        assertThat(s.getPredicate()).isIn(DCTerms.publisher,DCTerms.rightsHolder,RDFS.label,OWL.versionInfo);
      });
    } finally {graph.close();}
    String key=UUID.randomUUID().toString();
    var validation=send("validate","ouf.semantic.review.prepare","ouf.semantic.review.prepare",key,
        Map.of("commandKey",key,"revisionId",revision,"expectedRowVersion",version),CAPS,200);
    assertThat(validation.required("status").asText()).isEqualTo("PASS");
    assertThat(validation.required("issues").findValuesAsText("rule_id")).doesNotContain("VAL-008");
    key=UUID.randomUUID().toString();
    var review=send("review","ouf.semantic.approval.request","ouf.semantic.approval.request",key,
        Map.of("commandKey",key,"revisionId",revision,"expectedRowVersion",version,
            "validationRunId",validation.required("validation_run_id").asText()),CAPS,200);
    String challenge=review.required("challengeId").asText(),ths="/api/trusted-human/v1/semantic-approval-challenges/"+challenge;
    assertThat(review.required("trustedApprovalRef").asText()).isEqualTo("ths://semantic-approval-challenges/"+challenge);
    var card=json.readTree(http.perform(get(ths).with(reviewer("ouf.semantic.review")))
        .andExpect(status().isOk()).andReturn().getResponse().getContentAsByteArray());
    assertThat(card.required("adoptionProvenance")).isEqualTo(provenance);
    var descriptions=card.required("description_json");
    var source=new SafeRdfParser().model(fixture.poiBytes,"text/turtle");
    try {
      var comments=source.getResource(POI).listProperties(RDFS.comment).toList();
      assertThat(comments).extracting(statement->statement.getLiteral().getLanguage()).containsExactlyInAnyOrder("it","en");
      for(var comment:comments)
        assertThat(descriptions.required(comment.getLiteral().getLanguage()).asText()).isEqualTo(comment.getString());
    } finally {source.close();}
    var approved=json.readTree(http.perform(post(ths+"/decision").with(reviewer("ouf.semantic.approve"))
        .contentType(MediaType.APPLICATION_JSON).content("{\"decision\":\"APPROVED\"}"))
        .andExpect(status().isOk()).andReturn().getResponse().getContentAsByteArray());
    var publication=json.readTree(http.perform(post(ths+"/publish").with(reviewer("ouf.semantic.publish"))
        .header("Idempotency-Key",UUID.randomUUID()).contentType(MediaType.APPLICATION_JSON)
        .content(json.writeValueAsBytes(Map.of("approvalDecisionId",approved.required("decisionId").asText(),
            "contentHash",review.required("targetContentHash").asText()))))
        .andExpect(status().isOk()).andExpect(jsonPath("$.status").value("PUBLISHED")).andReturn().getResponse().getContentAsByteArray());
    String set=publication.required("publicationSetId").asText();
    var detail=delegated("consultation/get","ouf.semantic.consultation.read","ouf.semantic.read","READ",
        Map.of("semanticId",POI,"revisionId",revision,"publicationSetId",set));
    assertThat(detail.required("rdf_snapshot").required("content_base64").binaryValue()).isEqualTo(fixture.poiBytes);
    assertThat(detail.required("rdf_snapshot").required("statements").findValuesAsText("kind")).contains("BLANK_NODE");
    var search=delegated("consultation/search","ouf.semantic.search","ouf.semantic.search","READ",
        Map.of("q",INTENT,"type","CLASS","namespace",ONTOLOGY+"/"));
    assertThat(search.size()).isOne();
    for(var row:List.of(detail,search.required(0))){
      assertThat(row.required("semantic_id").asText()).isEqualTo(POI);
      assertThat(row.required("revision_id").asText()).isEqualTo(revision);
      assertThat(row.required("publication_set_id").asText()).isEqualTo(set);
      assertThat(row.required("status").asText()).isEqualTo("ACTIVE");
      assertThat(row.required("label").required("it").asText()).isEqualTo("Punto di Interesse");
      assertThat(row.required("label").required("en").asText()).isEqualTo("Point of Interest");
    }
    var second=discover();
    assertThat(second.request()).isNotEqualTo(first.request());
    assertThat(second.candidate()).isNotEqualTo(first.candidate());
    var reused=adopt(second,200);
    assertThat(reused.required("status").asText()).isEqualTo("ACTIVE");
    assertThat(reused.required("publicationSetId").asText()).isEqualTo(set);
    for(String field:List.of("semanticId","artifactId","revisionId","provenance"))
      assertThat(reused.required(field)).isEqualTo(draft.required(field));
    fixture.verifyOntologyFetches(2);
    fixture.serveChangedOntology();
    assertThat(adopt(discover(),409).required("code").asText()).isEqualTo("SEMANTIC_IDENTITY_MISMATCH");
  }
}

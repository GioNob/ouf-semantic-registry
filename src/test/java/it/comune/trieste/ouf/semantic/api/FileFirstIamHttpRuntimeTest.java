package it.comune.trieste.ouf.semantic.api;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import com.fasterxml.jackson.databind.*;
import com.nimbusds.jose.*;
import com.nimbusds.jose.crypto.RSASSASigner;
import com.nimbusds.jose.jwk.RSAKey;
import com.nimbusds.jwt.*;
import com.sun.net.httpserver.HttpServer;
import it.comune.trieste.ouf.authorization.*;
import it.comune.trieste.ouf.authorization.AuthorizationPolicy.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.security.interfaces.*;
import java.time.*;
import java.util.*;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;

/** Actual RSA JWT decoding, owner policy, HTTP controllers and PostgreSQL. No target proof. */
@SpringBootTest(properties={"spring.profiles.active=file-first","ouf.iam.enabled=true","ouf.iam.audience=ouf-api-gateway","ouf.authorization.ths.public-origin=https://ths.example.test"})
@AutoConfigureMockMvc
@DirtiesContext
class FileFirstIamHttpRuntimeTest {
  static final Set<String> CAPS=Set.of("ouf.semantic.read","ouf.semantic.search","ouf.semantic.propose",
      "ouf.semantic.review.prepare","ouf.semantic.approval.request","ouf.semantic.review","ouf.semantic.approve","ouf.semantic.publish");
  static final java.util.concurrent.atomic.AtomicInteger IMPORT_FETCHES=new java.util.concurrent.atomic.AtomicInteger();
  static final RSAKey KEY;
  static final HttpServer ISSUER;
  static final String URL;
  static {
    try {
      var generator=KeyPairGenerator.getInstance("RSA");generator.initialize(2048);var pair=generator.generateKeyPair();
      KEY=new RSAKey.Builder((RSAPublicKey)pair.getPublic()).privateKey((RSAPrivateKey)pair.getPrivate()).keyID("fixture").build();
      ISSUER=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);
      URL="http://127.0.0.1:"+ISSUER.getAddress().getPort();
      ISSUER.createContext("/.well-known/openid-configuration",e->{
        byte[] b=("{\"issuer\":\""+URL+"\",\"jwks_uri\":\""+URL+"/jwks\"}").getBytes(StandardCharsets.UTF_8);
        e.getResponseHeaders().set("Content-Type","application/json");e.sendResponseHeaders(200,b.length);e.getResponseBody().write(b);e.close();
      });
      ISSUER.createContext("/jwks",e->{
        byte[] b=("{\"keys\":["+KEY.toPublicJWK().toJSONString()+"]}").getBytes(StandardCharsets.UTF_8);
        e.getResponseHeaders().set("Content-Type","application/json");e.sendResponseHeaders(200,b.length);e.getResponseBody().write(b);e.close();
      });
      ISSUER.createContext("/must-not-fetch",e->{IMPORT_FETCHES.incrementAndGet();e.sendResponseHeaders(500,-1);e.close();});
      ISSUER.start();
    } catch(Exception e){throw new ExceptionInInitializerError(e);}
  }
  @DynamicPropertySource static void properties(DynamicPropertyRegistry p){p.add("ouf.iam.issuer",()->URL);}
  @AfterAll static void stop(){ISSUER.stop(0);}
  @Autowired MockMvc http;
  @Autowired ObjectMapper json;
  @Autowired org.springframework.context.ApplicationContext context;

  String jwt(String actor,String audience,Instant expires,Object roles)throws Exception {
    var claims=new JWTClaimsSet.Builder().issuer(URL).subject("actual-jwt-subject").audience(audience)
        .issueTime(Date.from(Instant.now().minusSeconds(5))).expirationTime(Date.from(expires))
        .claim("tenant_id","tenant-a").claim("ouf_actor_type",actor).claim("acr","1")
        .claim("scope",String.join(" ",CAPS)).claim("externalRoleRefs",roles).build();
    var jwt=new SignedJWT(new JWSHeader.Builder(JWSAlgorithm.RS256).keyID("fixture").build(),claims);
    jwt.sign(new RSASSASigner(KEY));return jwt.serialize();
  }
  String jwt(String actor)throws Exception{return jwt(actor,"ouf-api-gateway",Instant.now().plusSeconds(300),List.of("semantic-editor"));}
  void policy(boolean allow)throws Exception {
    var now=Instant.now();
    var descriptors=CAPS.stream().sorted().map(c->new CapabilityDescriptor(c,"EXECUTE",c,
        Set.of(PrincipalContext.ActorType.HUMAN,PrincipalContext.ActorType.AI_AGENT))).toList();
    var role=new GrantConstraints("ALLOW","semantic-editor",null,null,Map.of(),Set.of(),Set.of(),null,Set.of(),null);
    var grants=allow?CAPS.stream().sorted().map(c->new Grant("grant:"+c,c,"tenant-a",null,null,null,now.minusSeconds(5),now.plusSeconds(600),role)).toList():List.<Grant>of();
    var runtime=new LocalAuthorization(Clock.systemUTC(),Duration.ofHours(1));
    TestAuthorization.install(runtime,new PolicyBundle("fresh-role-policy",1,now,descriptors,grants));
    http.getDispatcherServlet().getServletContext().setAttribute(ServletAuthorization.RUNTIME,runtime);
  }
  JsonNode command(String mode,Map<String,Object> body,String token)throws Exception {
    var response=http.perform(post("/api/semantic/v1/proposal-commands/"+mode)
        .header("Authorization","Bearer "+token).header("Idempotency-Key",UUID.randomUUID().toString())
        .contentType(MediaType.APPLICATION_JSON).content(json.writeValueAsBytes(body)))
        .andExpect(status().isOk()).andReturn().getResponse();
    return json.readTree(response.getContentAsByteArray());
  }
  @Test void freshJwtProposalValidationHumanDecisionPublicationAndCurrentSearchShareOneApplication()throws Exception {exercise(false);}
  @Test void importedOntologyReusesIdempotentCommandsAndReviewBindsExactRdfWithoutFetchingImports()throws Exception {exercise(true);}
  private void exercise(boolean imported)throws Exception {
    policy(true);String agent=jwt("AI_AGENT"),human=jwt("HUMAN");String suffix=UUID.randomUUID().toString().replace("-","");
    var draft=new LinkedHashMap<String,Object>(Map.of("semanticId","ouf:file-first:"+suffix,"artifactType",imported?"ONTOLOGY":"CLASS","namespace","ouf",
        "localName","Place"+suffix,"ownerRef","owner","authorityRef","authority","semanticVersion","1.0.0",
        "labels",Map.of("it","Teatro"+suffix),"definition",Map.of()));
    JsonNode retained=null;
    if(imported){try(var input=getClass().getResourceAsStream("/teatri-reuse-semantic-proposal-20261014.json")){retained=json.readTree(input);draft=json.convertValue(retained.get("importCommand"),new com.fasterxml.jackson.core.type.TypeReference<LinkedHashMap<String,Object>>(){});}}
    String semanticId=draft.get("semanticId").toString(),label=((Map<?,?>)draft.get("labels")).get("it").toString();
    var created=command("create",draft,agent);
    String revision=created.get("revisionId").asText();
    var valid=command("validate",Map.of("revisionId",revision,"expectedRowVersion",0),agent);
    var review=command("review",Map.of("revisionId",revision,"expectedRowVersion",0,"validationRunId",valid.get("validation_run_id").asText()),agent);
    assertThat(review.get("reviewUrl").asText()).startsWith("https://ths.example.test/trusted-human/semantic/?challenge=");
    if(imported){assertThat(review.get("interchangeSnapshot").get("content").asText()).isEqualTo(draft.get("rdfTurtle"));assertThat(review.get("definition_json").get("importedSnapshot").get("contentHash").asText()).isEqualTo(created.get("contentHash").asText());assertThat(IMPORT_FETCHES.get()).isZero();}
    String challenge=review.get("challengeId").asText(),path="/api/trusted-human/v1/semantic-approval-challenges/"+challenge;
    http.perform(get(path).header("Authorization","Bearer "+human)).andExpect(status().isOk())
        .andExpect(jsonPath("$.target_content_hash").value(review.get("targetContentHash").asText()));
    http.perform(post(path+"/decision").header("Authorization","Bearer "+agent).contentType(MediaType.APPLICATION_JSON)
        .content("{\"decision\":\"APPROVED\"}")).andExpect(status().isForbidden());
    var decision=json.readTree(http.perform(post(path+"/decision").header("Authorization","Bearer "+human)
        .contentType(MediaType.APPLICATION_JSON).content("{\"decision\":\"APPROVED\"}"))
        .andExpect(status().isOk()).andReturn().getResponse().getContentAsByteArray());
    http.perform(get(path).header("Authorization","Bearer "+human)).andExpect(status().isOk())
        .andExpect(jsonPath("$.approvalDecisionId").value(decision.get("decisionId").asText()));
    var publication=json.readTree(http.perform(post(path+"/publish").header("Authorization","Bearer "+human)
        .header("Idempotency-Key",UUID.randomUUID().toString()).contentType(MediaType.APPLICATION_JSON)
        .content(json.writeValueAsBytes(Map.of("approvalDecisionId",decision.get("decisionId").asText(),"contentHash",review.get("targetContentHash").asText()))))
        .andExpect(status().isOk()).andReturn().getResponse().getContentAsByteArray());
    http.perform(get("/api/semantic/v1/search").param("q",label).param("type",imported?"ONTOLOGY":"CLASS")
        .header("Authorization","Bearer "+human)).andExpect(status().isOk()).andExpect(jsonPath("$[0].revision_id").value(revision));
    var exact=json.readTree(http.perform(get("/api/semantic/v1/references:resolve").param("semanticId",semanticId)
        .param("revisionId",revision).param("publicationSetId",publication.get("publicationSetId").asText())
        .header("Authorization","Bearer "+human)).andExpect(status().isOk()).andExpect(jsonPath("$.label.it").value(label))
        .andReturn().getResponse().getContentAsByteArray());
    if(imported) {
      assertThat(exact.get("rdf_snapshot").get("content_hash").asText()).isEqualTo(retained.get("rdfSha256").asText());
      assertThat(exact.get("rdf_snapshot").get("partial").asBoolean()).isFalse();
      var terms=new TreeSet<String>();boolean capString=false;
      for(var statement:exact.get("rdf_snapshot").get("statements")) {
        String subject=statement.get("subject").get("value").asText(),predicate=statement.get("predicate").asText(),object=statement.get("object").get("value").asText();
        if(predicate.equals("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")&&Set.of("http://www.w3.org/2002/07/owl#Class","http://www.w3.org/2002/07/owl#DatatypeProperty","http://www.w3.org/1999/02/22-rdf-syntax-ns#Property").contains(object))terms.add(subject);
        if(subject.equals("https://api.ouf-lab.it/semantic/teatri#cap")&&predicate.equals("http://www.w3.org/2000/01/rdf-schema#range")&&object.equals("http://www.w3.org/2001/XMLSchema#string"))capString=true;
      }
      var expected=new TreeSet<String>();expected.add(retained.get("mappingBlueprint").get("targetClassIri").asText());
      for(var field:retained.get("mappingBlueprint").get("fields"))expected.add(field.get("targetPropertyIri").asText());
      assertThat(expected).hasSize(21);assertThat(terms).containsExactlyElementsOf(expected);assertThat(capString).isTrue();
    }
    http.perform(get(path).header("Authorization","Bearer "+human)).andExpect(status().isOk())
        .andExpect(jsonPath("$.lifecycleStatus").value("ACTIVE"))
        .andExpect(jsonPath("$.publicationSetId").value(publication.get("publicationSetId").asText()));
    policy(false);
    http.perform(get("/api/semantic/v1/search").param("q",label).header("Authorization","Bearer "+human)).andExpect(status().isForbidden());
    assertThat(context.getBeansOfType(it.comune.trieste.ouf.semantic.application.DiscoveryWorker.class)).isEmpty();
    assertThat(context.getEnvironment().getProperty("ouf.semantic.providers.schema-gov.enabled")).isEqualTo("false");
  }
  @Test void invalidJwtOrMissingCurrentRoleCannotReleaseReads()throws Exception {
    policy(true);
    for(String token:List.of(jwt("HUMAN","wrong-audience",Instant.now().plusSeconds(300),List.of("semantic-editor")),
        jwt("HUMAN","ouf-api-gateway",Instant.now().minusSeconds(120),List.of("semantic-editor")),
        jwt("HUMAN","ouf-api-gateway",Instant.now().plusSeconds(300),"semantic-editor"))) {
      http.perform(get("/api/semantic/v1/search").param("q","Teatro").header("Authorization","Bearer "+token)).andExpect(status().isUnauthorized());
    }
    http.perform(get("/api/semantic/v1/search").param("q","Teatro")
        .header("Authorization","Bearer "+jwt("HUMAN","ouf-api-gateway",Instant.now().plusSeconds(300),List.of())))
        .andExpect(status().isForbidden());
    http.perform(get("/api/semantic/v1/search").param("q","Teatro").header("X-OUF-Actor-Type","HUMAN")
        .header("X-OUF-External-Roles","semantic-editor")).andExpect(status().isForbidden());
  }
}

package it.comune.trieste.ouf.semantic;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.UUID;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.RequestPostProcessor;

@SpringBootTest(properties={
    "ouf.semantic.discovery-worker.enabled=false",
    "ouf.semantic.providers.schema-gov.enabled=false"
})
@AutoConfigureMockMvc
class HttpApiRuntimeTest {
  @Autowired MockMvc http;
  @Autowired ObjectMapper json;

  @Test
  void artifactLifecycleRunsThroughHttpToPostgresql() throws Exception {
    String semanticId="ouf:http:"+UUID.randomUUID();
    String localName="Place"+UUID.randomUUID().toString().replace("-","");
    JsonNode created=body(http.perform(post("/api/semantic/v1/artifacts")
        .with(actor("author","OUF_SERVICE",Set.of()))
        .contentType(MediaType.APPLICATION_JSON)
        .content(json.writeValueAsBytes(java.util.Map.of(
            "semanticId",semanticId,"artifactType","CLASS","namespace","ouf",
            "localName",localName,"ownerRef","owner","authorityRef","authority",
            "semanticVersion","1.0.0","labels",java.util.Map.of("it","Luogo"),
            "definition",java.util.Map.of()))))
        .andExpect(status().isCreated())
        .andExpect(header().string("ETag","\"0\""))
        .andReturn());
    UUID artifact=UUID.fromString(created.get("artifactId").asText());
    UUID revision=UUID.fromString(created.get("revisionId").asText());

    http.perform(get("/api/semantic/v1/artifacts/{id}",artifact))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.semantic_id").value(semanticId));

    http.perform(patch("/api/semantic/v1/revisions/{id}",revision)
        .with(actor("author","OUF_SERVICE",Set.of()))
        .header("If-Match","\"0\"").contentType(MediaType.APPLICATION_JSON)
        .content("{\"labels\":{\"it\":\"Luogo aggiornato\"},\"definition\":{}}"))
        .andExpect(status().isOk()).andExpect(header().string("ETag","\"1\""));
    http.perform(patch("/api/semantic/v1/revisions/{id}",revision)
        .with(actor("author","OUF_SERVICE",Set.of()))
        .header("If-Match","\"0\"").contentType(MediaType.APPLICATION_JSON)
        .content("{\"labels\":{\"it\":\"stale\"},\"definition\":{}}"))
        .andExpect(status().isConflict())
        .andExpect(jsonPath("$.detail").value("VERSION_CONFLICT"));

    JsonNode validation=body(http.perform(post("/api/semantic/v1/revisions/{id}:validate",revision)
        .with(actor("validator","OUF_SERVICE",Set.of()))).andExpect(status().isOk())
        .andExpect(jsonPath("$.status").value("PASS")).andReturn());
    String hash=validation.get("validated_content_hash").asText();

    JsonNode challenge=body(http.perform(post("/api/semantic/v1/approval-challenges")
        .with(actor("agent","OUF_AI_AGENT",Set.of()))
        .contentType(MediaType.APPLICATION_JSON)
        .content(json.writeValueAsBytes(java.util.Map.of("revisionId",revision,"contentHash",hash))))
        .andExpect(status().isCreated()).andExpect(jsonPath("$.status").value("OPEN")).andReturn());
    UUID challengeId=UUID.fromString(challenge.get("challengeId").asText());
    JsonNode decision=body(http.perform(post("/api/trusted-human/v1/semantic-approval-challenges/{id}/decision",challengeId)
        .with(actor("reviewer","OUF_HUMAN_USER",Set.of("ouf.semantic.approve")))
        .contentType(MediaType.APPLICATION_JSON).content("{\"decision\":\"APPROVED\"}"))
        .andExpect(status().isOk()).andReturn());
    UUID decisionId=UUID.fromString(decision.get("decisionId").asText());

    JsonNode published=body(http.perform(post("/api/trusted-human/v1/semantic-approval-challenges/{id}/publish",challengeId)
        .with(actor("reviewer","OUF_HUMAN_USER",Set.of("ouf.semantic.publish")))
        .header("Idempotency-Key","http-"+revision).header("X-Correlation-Id","test-http")
        .contentType(MediaType.APPLICATION_JSON)
        .content(json.writeValueAsBytes(java.util.Map.of(
            "approvalDecisionId",decisionId,"contentHash",hash))))
        .andExpect(status().isOk()).andExpect(jsonPath("$.status").value("PUBLISHED"))
        .andReturn());
    UUID publication=UUID.fromString(published.get("publicationSetId").asText());
    org.assertj.core.api.Assertions.assertThat(published.get("manifestHash").asText())
        .hasSize(64).isNotEqualTo(hash);

    http.perform(get("/api/semantic/v1/publication-sets/{set}/artifacts/{artifact}",publication,artifact)
        .header("Accept","text/turtle"))
        .andExpect(status().isOk()).andExpect(content().contentType("text/turtle"))
        .andExpect(content().string(org.hamcrest.Matchers.containsString(semanticId)));
  }

  @Test
  void invalidDtoAndUnsafeRdfReturnBoundedClientErrors() throws Exception {
    http.perform(post("/api/semantic/v1/artifacts")
        .with(actor("tester","OUF_SERVICE",Set.of()))
        .contentType(MediaType.APPLICATION_JSON)
        .content("{\"semanticId\":\"x\",\"artifactType\":\"INVALID\"}"))
        .andExpect(status().isBadRequest());

    http.perform(post("/api/semantic/v1/imports")
        .queryParam("semanticId","ouf:unsafe").queryParam("artifactType","ONTOLOGY")
        .queryParam("namespace","ouf").queryParam("localName","Unsafe")
        .queryParam("ownerRef","owner").queryParam("authorityRef","authority")
        .queryParam("semanticVersion","1.0.0")
        .with(actor("tester","OUF_SERVICE",Set.of()))
        .contentType("application/rdf+xml")
        .content("<!DOCTYPE rdf:RDF [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>"))
        .andExpect(status().isUnprocessableEntity())
        .andExpect(jsonPath("$.detail").value("RDF_EXTERNAL_ENTITY_FORBIDDEN"));
  }

  @Test
  void spoofedIdentityHeadersCannotCrossTrustBoundary() throws Exception {
    http.perform(post("/api/semantic/v1/revisions/{id}:validate",UUID.randomUUID())
        .header("X-OUF-Subject","attacker")
        .header("X-OUF-Principal-Type","HUMAN_USER"))
        .andExpect(status().isForbidden())
        .andExpect(jsonPath("$.detail").value("SEM_AUTHENTICATION_REQUIRED"));

    http.perform(get("/api/trusted-human/v1/semantic-approval-challenges/{id}",UUID.randomUUID())
        .with(actor("agent","OUF_AI_AGENT",Set.of("ouf.semantic.review"))))
        .andExpect(status().isForbidden())
        .andExpect(jsonPath("$.detail").value("HUMAN_IDENTITY_REQUIRED"));

    http.perform(post("/api/trusted-human/v1/semantic-approval-challenges/revisions/{id}:deprecate",UUID.randomUUID())
        .with(actor("human","OUF_HUMAN_USER",Set.of())))
        .andExpect(status().isForbidden())
        .andExpect(jsonPath("$.detail").value("SEM_CAPABILITY_REQUIRED:ouf.semantic.deprecate"));
  }

  private static RequestPostProcessor actor(String subject,String role,Set<String> capabilities) {
    return request -> {
      request.setUserPrincipal(() -> subject);
      request.addUserRole(role);
      request.setAttribute("ouf.actorType",switch(role){case "OUF_HUMAN_USER" -> "HUMAN";case "OUF_AI_AGENT" -> "AI_AGENT";default -> "SERVICE";});
      request.setAttribute("ouf.authorizedCapabilities",capabilities);
      request.setAttribute("ouf.authorizationDecisionRef","authz:test:"+subject);
      return request;
    };
  }

  private JsonNode body(org.springframework.test.web.servlet.MvcResult result) throws Exception {
    return json.readTree(result.getResponse().getContentAsByteArray());
  }
}

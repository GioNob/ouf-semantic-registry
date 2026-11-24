package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;

import ch.qos.logback.classic.Level;
import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.read.ListAppender;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import it.comune.trieste.ouf.authorization.*;
import it.comune.trieste.ouf.authorization.AuthorizationPolicy.*;
import it.comune.trieste.ouf.semantic.api.*;
import it.comune.trieste.ouf.semantic.application.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.time.*;
import java.util.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

class DelegatedReadDenialTest {
  enum Route {
    SEARCH("consultation/search", "ouf.semantic.search", "ouf.semantic.search", SemanticConsultationApi.class),
    GET("consultation/get", "ouf.semantic.consultation.read", "ouf.semantic.read", SemanticConsultationApi.class),
    BATCH("consultation/search-batch", "ouf.semantic.search.batch", "ouf.semantic.search", PublishedBatchApi.class),
    STATUS("discovery/status", "ouf.semantic.discovery.status", "ouf.semantic.discovery", SemanticDiscoveryMcpApi.class);

    final String path, capability, scope;
    final Class<?> controller;
    Route(String path, String capability, String scope, Class<?> controller) {
      this.path = "/api/internal/v1/semantic/" + path;
      this.capability = capability;
      this.scope = scope;
      this.controller = controller;
    }
    String codePrefix() { return this == STATUS ? "SEM_DISCOVERY" : "SEM_READ"; }
  }

  private static final String KEY = "ab".repeat(32);
  private static final String TENANT = "private-tenant", SUBJECT = "private-subject", ROLE = "private-role";
  private static final String INTENT = "private-intent";
  private final ObjectMapper json = new ObjectMapper();
  private final SemanticReadService reads = mock(SemanticReadService.class);
  private final PublishedBatchSearch batches = mock(PublishedBatchSearch.class);
  private final DiscoveryJobService jobs = mock(DiscoveryJobService.class);
  @TempDir Path tmp;
  private MockMvc http;
  private LocalAuthorization owner;

  @BeforeEach void setup() throws Exception {
    var key = Files.writeString(tmp.resolve("fixture-key"), KEY).toString();
    var receipts = new SemanticReadDelegation(json, key, "issuer", "audience", "workload");
    var discovery = new SemanticDiscoveryDelegation(json, key, "issuer", "audience", "workload");
    http = MockMvcBuilders.standaloneSetup(new SemanticConsultationApi(receipts, reads, json),
        new PublishedBatchApi(receipts, batches, json, 64, 3, 65536, 262144),
        new SemanticDiscoveryMcpApi(discovery, jobs, json)).setControllerAdvice(new ProblemHandler()).build();
    owner = new LocalAuthorization(Clock.systemUTC(), Duration.ofHours(1));
  }

  private byte[] body(Route route) throws Exception {
    Map<String,?> args = switch (route) {
      case SEARCH -> Map.of("q", INTENT);
      case GET -> Map.of("semanticId", INTENT, "publicationSetId", UUID.randomUUID().toString());
      case STATUS -> Map.of("requestId", UUID.randomUUID().toString());
      case BATCH -> Map.of("contract", PublishedBatchSearch.CONTRACT, "limitPerIntent", 1,
          "intents", List.of(Map.of("intentId", "i0", "intent", INTENT, "requestedArtifactType", "CLASS",
              "preferredLanguages", List.of("it"), "context", Map.of())));
    };
    return json.writeValueAsBytes(Map.of("CapabilityID", route.capability, "GatewayBindingRef", "capability://" + route.capability,
        "OperationClass", "READ", "Owner", "semantic", "Arguments", args));
  }

  private static String digest(byte[] bytes) throws Exception {
    return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
  }

  private ObjectNode claims(Route route, byte[] body) throws Exception {
    long now = Instant.now().getEpochSecond();
    return json.createObjectNode().put("v", 1).put("purpose", route == Route.STATUS ? "semantic-discovery-owner" : "semantic-read-owner")
        .put("method", "POST").put("path", route.path).put("bodyHash", digest(body)).put("capability", route.capability)
        .put("iat", now).put("exp", now + 30).put("issuer", "issuer").put("audience", "audience").put("workload", "workload")
        .put("subject", SUBJECT).put("tenant", TENANT).put("acr", "fixture-acr").put("roles", ROLE).put("scope", route.scope);
  }

  private String sign(ObjectNode claims, String key) throws Exception {
    var base64 = Base64.getUrlEncoder().withoutPadding();
    var payload = base64.encodeToString(json.writeValueAsBytes(claims));
    var mac = Mac.getInstance("HmacSHA256");
    mac.init(new SecretKeySpec(key.getBytes(StandardCharsets.US_ASCII), "HmacSHA256"));
    var input = "ouf-" + claims.required("purpose").asText() + "-v1." + payload;
    return payload + "." + base64.encodeToString(mac.doFinal(input.getBytes(StandardCharsets.US_ASCII)));
  }

  @ParameterizedTest @EnumSource(Route.class)
  void rejectsBadSignatureExpiredReceiptAndDifferentBody(Route route) throws Exception {
    byte[] raw = body(route);
    var claims = claims(route, raw);
    String code = route.codePrefix() + "_RECEIPT_INVALID";
    expect(route, raw, sign(claims, "cd".repeat(32)), code, "SIGNATURE", null);
    expect(route, raw, sign(claims.deepCopy().put("exp", 1).put("iat", 0), KEY), code, "EXPIRED", null);
    expect(route, raw, sign(claims.put("bodyHash", "0".repeat(64)), KEY), code, "BODY_HASH", null);
  }

  @ParameterizedTest @EnumSource(Route.class)
  void ownerDistinguishesAnUndeclaredCapabilityFromAnInapplicableLabelGrant(Route route) throws Exception {
    byte[] raw = body(route);
    var now = Instant.now();
    TestAuthorization.install(owner, new PolicyBundle("fixture", 1, now, List.of(), List.of()));
    expect(route, raw, sign(claims(route, raw), KEY), "CAPABILITY_NOT_DECLARED", null, route.capability, 1L);
    var descriptor = new CapabilityDescriptor(route.capability, "READ", route.scope, Set.of(PrincipalContext.ActorType.HUMAN));
    var constraint = new GrantConstraints("ALLOW", ROLE, null, null, Map.of(), Set.of("OPEN"), Set.of(), null, Set.of(), null);
    var grant = new Grant("role-grant", route.capability, TENANT, null, null, null, now.minusSeconds(30), now.plusSeconds(300), constraint);
    TestAuthorization.install(owner, new PolicyBundle("fixture", 2, now, List.of(descriptor), List.of(grant)));
    expect(route, raw, sign(claims(route, raw), KEY), "NO_APPLICABLE_GRANT", null, route.capability, 2L);
  }

  @ParameterizedTest @EnumSource(Route.class)
  void unknownMessagesCodesAndForeignCapabilitiesAreSanitized(Route route) throws Exception {
    byte[] raw = body(route);
    String proof = sign(claims(route, raw), KEY);
    String fallback = route.codePrefix() + "_POLICY_DENIED";
    owner = mock(LocalAuthorization.class);
    when(owner.currentSnapshot()).thenThrow(
        new SecurityException("unexpected " + SUBJECT),
        new SecurityException("CAPABILITY_DENIED:" + route.capability + ":" + ROLE),
        new SecurityException("CAPABILITY_DENIED:" + TENANT + ":EXPLICIT_DENY"),
        new SecurityException("CAPABILITY_DENIED:ouf.semantic.discovery.candidates:EXPLICIT_DENY"));
    expect(route, raw, proof, fallback, null, null);
    expect(route, raw, proof, fallback, null, route.capability);
    expect(route, raw, proof, "EXPLICIT_DENY", null, null);
    expect(route, raw, proof, "EXPLICIT_DENY", null, null);
  }

  private void expect(Route route, byte[] raw, String proof, String code, String receiptReason, String capability) throws Exception {
    expect(route, raw, proof, code, receiptReason, capability, null);
  }

  private void expect(Route route, byte[] raw, String proof, String code, String receiptReason, String capability,
      Long policyVersion) throws Exception {
    var logger = (Logger) LoggerFactory.getLogger(route.controller);
    var logs = new ListAppender<ILoggingEvent>();
    logs.start();
    logger.addAppender(logs);
    try {
      String header = route == Route.STATUS ? "X-OUF-Semantic-Discovery-Receipt" : "X-OUF-Semantic-Read-Receipt";
      var response = http.perform(post(route.path).contentType(MediaType.APPLICATION_JSON).content(raw).header(header, proof)
          .with(req -> { req.getServletContext().setAttribute(ServletAuthorization.RUNTIME, owner); return req; }))
          .andReturn().getResponse();
      assertThat(response.getStatus()).isEqualTo(403);
      assertThat(response.getContentType()).isEqualTo(MediaType.APPLICATION_JSON_VALUE);
      String denial = receiptReason == null ? "POLICY" : "RECEIPT";
      var expected = json.createObjectNode().put("code", code).put("denial", denial);
      if (capability != null) expected.put("capability", capability);
      if (policyVersion != null) expected.put("policyVersion", policyVersion.intValue());
      var actual = json.readTree(response.getContentAsByteArray());
      assertThat(actual.fieldNames().next()).isEqualTo("code");
      assertThat(actual).isEqualTo(expected);

      String line = "decision=DENY denial=" + denial + " capability=" + (capability == null ? route.capability : capability)
          + (receiptReason == null ? " policyCode=" + code : " reason=" + receiptReason)
          + (policyVersion == null ? "" : " policyVersion=" + policyVersion);
      if (route == Route.BATCH) {
        boolean signed = receiptReason == null || receiptReason.equals("BODY_HASH");
        line += " scope=" + (signed ? digest(TENANT.getBytes(StandardCharsets.UTF_8)) : "unverified")
            + " ranking=" + PublishedBatchSearch.CONTRACT + " batch=" + (signed ? digest(raw) : "unverified");
      }
      assertThat(logs.list).hasSize(1);
      var event = logs.list.getFirst();
      assertThat(event.getLevel()).isEqualTo(Level.INFO);
      assertThat(event.getThrowableProxy()).isNull();
      assertThat(event.getFormattedMessage()).isEqualTo(line).doesNotContain(SUBJECT, TENANT, ROLE, INTENT, proof, proof.split("\\.")[1]);
      verifyNoInteractions(reads, batches, jobs);
    } finally {
      logger.detachAppender(logs);
      logs.stop();
    }
  }
}

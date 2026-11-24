package it.comune.trieste.ouf.semantic.adapters.discovery;

import static it.comune.trieste.ouf.semantic.adapters.discovery.OriginAttestationFixture.*;
import static it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic.Origin.*;
import static org.assertj.core.api.Assertions.assertThat;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpHeaders;
import java.net.http.HttpResponse;
import java.time.Clock;
import java.util.Base64;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;

/** PET-semantic-294/307 · D-091 T2 · Gateway 55l. */
class Ed25519RateLimitOriginVerifierTest {
  private final SchemaGovProperties provider = routes("/provider/search", "/provider/fetch");
  private final URI target = GATEWAY.resolve(TARGET);
  private final RateLimitOriginVerifier verifier = verifierAt(IAT, 0);

  private RateLimitOriginVerifier verifierAt(long second, int skew) {
    return new Ed25519RateLimitOriginVerifier(provider, PUBLIC_KEY, INSTALLATION, skew, clock(second));
  }

  private record Info(int statusCode, HttpHeaders headers) implements HttpResponse.ResponseInfo {
    public HttpClient.Version version() { return HttpClient.Version.HTTP_1_1; }
  }

  private static Info response(int status, String... proofs) {
    return new Info(status, HttpHeaders.of(
        Map.of(HEADER, List.of(proofs), "X-RateLimit-Origin", List.of("APISIX")), (name, value) -> true));
  }

  @Test @DisplayName("SEM-58G-01 published 55l vector, exact raw target and exchange binding")
  void verifiesOnlyTheOriginalExchange() {
    var info = response(429, ATTESTATION);
    assertThat(verifier.verifiedOrigin("GET", target, NONCE, info)).isEqualTo(UPSTREAM);
    assertThat(verifier.verifiedOrigin("GET", target, info)).isEqualTo(UNKNOWN);
    for (String other : List.of(NONCE.replace("48da", "58da"), NONCE.toUpperCase(java.util.Locale.ROOT),
        NONCE.replace("-4b0e", "-5b0e"), NONCE.replace("-967b", "-767b"), ""))
      assertThat(verifier.verifiedOrigin("GET", target, other, info)).isEqualTo(UNKNOWN);
    for (String other : List.of(TARGET.replace("%2F", "%2f"), TARGET + "&x=1", "/provider/search",
        "http://gateway.invalid" + TARGET, "https://other.invalid" + TARGET,
        "https://gateway.invalid:8443" + TARGET, TARGET + "#fragment"))
      assertThat(verifier.verifiedOrigin("GET", GATEWAY.resolve(other), NONCE, info)).isEqualTo(UNKNOWN);
    assertThat(verifier.verifiedOrigin("POST", target, NONCE, info)).isEqualTo(UNKNOWN);
    assertThat(verifier.verifiedOrigin("GET", target, NONCE, response(503, ATTESTATION))).isEqualTo(UNKNOWN);
    var otherSite = new Ed25519RateLimitOriginVerifier(provider, PUBLIC_KEY, "Fixture.invalid", 0, clock(IAT));
    assertThat(otherSite.verifiedOrigin("GET", target, NONCE, info)).isEqualTo(UNKNOWN);

    String raw = "/provider/search?x=1&x=2&empty=";
    var search = response(429, sign("POST", raw, NONCE, "APISIX", IAT, EXP));
    assertThat(verifier.verifiedOrigin("POST", GATEWAY.resolve(raw), NONCE, search)).isEqualTo(APISIX);
    assertThat(verifier.verifiedOrigin("POST", GATEWAY.resolve(raw.replace("1&x=2", "2&x=1")), NONCE, search))
        .isEqualTo(UNKNOWN);
    var emptyQuery = response(429, sign("GET", "/provider/fetch?", NONCE, "UPSTREAM", IAT, EXP));
    assertThat(verifier.verifiedOrigin("GET", GATEWAY.resolve("/provider/fetch?"), NONCE, emptyQuery)).isEqualTo(UPSTREAM);
    assertThat(verifier.verifiedOrigin("GET", GATEWAY.resolve("/provider/fetch"), NONCE, emptyQuery)).isEqualTo(UNKNOWN);
    var wrongRoute = response(429, sign("POST", TARGET, NONCE, "APISIX", IAT, EXP));
    assertThat(verifier.verifiedOrigin("POST", target, NONCE, wrongRoute)).isEqualTo(UNKNOWN);
  }

  @Test @DisplayName("SEM-58G-02 malformed, duplicate, missing and forged attestations")
  void requiresOneCanonicalProof() {
    assertThat(verifier.verifiedOrigin("GET", target, NONCE, response(429))).isEqualTo(UNKNOWN);
    assertThat(verifier.verifiedOrigin("GET", target, NONCE, response(429, ATTESTATION, ATTESTATION))).isEqualTo(UNKNOWN);
    for (String proof : List.of(ATTESTATION + ", " + ATTESTATION, ATTESTATION.replace("v1.", "v2."),
        ATTESTATION.replace("UPSTREAM", "APISIX"), ATTESTATION.replace("UPSTREAM", "OTHER"),
        ATTESTATION.replace(".180", ".0180"), ATTESTATION.replace("1800000030", "9999999999999999999"),
        ATTESTATION.replace(".w_", ".x_"), ATTESTATION + "=", ATTESTATION.substring(0, ATTESTATION.length()-1),
        ATTESTATION.substring(0, ATTESTATION.length()-1) + "B", ""))
      assertThat(verifier.verifiedOrigin("GET", target, NONCE, response(429, proof))).isEqualTo(UNKNOWN);
  }

  @Test @DisplayName("SEM-58G-03 inclusive issue, exclusive expiry, finite lifetime and clock skew")
  void checksSignedTimeWindow() {
    var info = response(429, ATTESTATION);
    assertThat(verifierAt(IAT-1, 0).verifiedOrigin("GET", target, NONCE, info)).isEqualTo(UNKNOWN);
    assertThat(verifierAt(EXP-1, 0).verifiedOrigin("GET", target, NONCE, info)).isEqualTo(UPSTREAM);
    assertThat(verifierAt(EXP, 0).verifiedOrigin("GET", target, NONCE, info)).isEqualTo(UNKNOWN);
    assertThat(verifierAt(IAT-1, 1).verifiedOrigin("GET", target, NONCE, info)).isEqualTo(UPSTREAM);
    assertThat(verifierAt(EXP+1, 1).verifiedOrigin("GET", target, NONCE, info)).isEqualTo(UNKNOWN);
    for (long exp : List.of(IAT-1, IAT, EXP+1)) {
      var invalid = response(429, sign("GET", TARGET, NONCE, "UPSTREAM", IAT, exp));
      assertThat(verifierAt(IAT, 1).verifiedOrigin("GET", target, NONCE, invalid)).isEqualTo(UNKNOWN);
    }
  }

  @Test @DisplayName("SEM-58G-04 production bean, installation profile and predecessor fallback")
  void buildsTheVerifierFromInstallationSettings() {
    String prefix = "ouf.semantic.providers.schema-gov.origin-attestation.";
    var context = new ApplicationContextRunner().withUserConfiguration(RateLimitOriginConfiguration.class)
        .withBean(SchemaGovProperties.class, () -> provider).withBean(Clock.class, () -> clock(IAT));
    context.run(ctx -> assertThat(ctx.getBean(RateLimitOriginVerifier.class)).isSameAs(RateLimitOriginVerifier.UNATTESTED));
    String base64 = Base64.getUrlEncoder().withoutPadding().encodeToString(HexFormat.of().parseHex(PUBLIC_KEY));
    context.withPropertyValues(prefix+"public-key="+base64, prefix+"installation-id="+INSTALLATION).run(ctx ->
        assertThat(ctx.getBean(RateLimitOriginVerifier.class).verifiedOrigin("GET", target, NONCE, response(429, ATTESTATION)))
            .isEqualTo(UPSTREAM));
    context.withPropertyValues(prefix+"public-key="+PUBLIC_KEY).run(ctx -> assertThat(ctx).hasFailed());
    context.withPropertyValues(prefix+"public-key=AA", prefix+"installation-id="+INSTALLATION)
        .run(ctx -> assertThat(ctx).hasFailed());
  }
}

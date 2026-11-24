package it.comune.trieste.ouf.semantic.adapters.discovery;

import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.KeyFactory;
import java.security.Signature;
import java.security.spec.EdECPrivateKeySpec;
import java.security.spec.NamedParameterSpec;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Base64;
import java.util.HexFormat;
import java.util.List;

/** Public Gateway 55l semantic-provider-429-vector-v1.json. The ignored input folder is absent in CI. */
final class OriginAttestationFixture {
  static final URI GATEWAY = URI.create("https://gateway.invalid");
  static final String TARGET = "/provider/fetch?uri=https%3A%2F%2Fterms.invalid%2Fa%2Fb";
  static final String NONCE = "48da10fa-2476-4b0e-967b-b5d8374af715";
  static final String INSTALLATION = "fixture.invalid";
  static final String PUBLIC_KEY = "03a107bff3ce10be1d70dd18e74bc09967e4d6309ba50d5f1ddc8664125531b8";
  static final String ATTESTATION = "v1.UPSTREAM.1800000000.1800000030."
      + "w_VraC8rpA1IyMbdzjrQBA_m7FW8Hs0icwJ1m1TL6UBWW9TBKDw0QSMg0JHIcvQlEIM48ETGnljkieyBJSu5DA";
  static final long IAT = 1800000000L;
  static final long EXP = IAT + 30;
  static final String HEADER = "X-OUF-RateLimit-Attestation";

  static Clock clock(long second) {
    return Clock.fixed(Instant.ofEpochSecond(second), ZoneOffset.UTC);
  }

  static SchemaGovProperties routes(String search, String fetch) {
    return new SchemaGovProperties(true, GATEWAY, search, fetch, Duration.ofSeconds(2), Duration.ofSeconds(2),
        8192, 1, 1, Duration.ZERO, 3, Duration.ofSeconds(30), List.of("https://terms.invalid/"));
  }

  static String sign(String method, String rawTarget, String nonce, String origin, long iat, long exp) {
    byte[] seed = HexFormat.of().parseHex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f");
    try {
      var privateKey = KeyFactory.getInstance("Ed25519").generatePrivate(
          new EdECPrivateKeySpec(NamedParameterSpec.ED25519, seed));
      var signer = Signature.getInstance("Ed25519");
      signer.initSign(privateKey);
      String payload = "v1\nsemantic-provider-429-origin\n" + method + "\n" + rawTarget + "\n" + nonce + "\n"
          + origin + "\n429\n" + iat + "\n" + exp + "\n" + INSTALLATION;
      signer.update(payload.getBytes(StandardCharsets.US_ASCII));
      return "v1." + origin + "." + iat + "." + exp + "."
          + Base64.getUrlEncoder().withoutPadding().encodeToString(signer.sign());
    } catch (GeneralSecurityException error) {
      throw new AssertionError(error);
    }
  }
}

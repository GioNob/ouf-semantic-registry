package it.comune.trieste.ouf.semantic.adapters.discovery;

import it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic.Origin;
import java.net.URI;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.Signature;
import java.security.spec.X509EncodedKeySpec;
import java.time.Clock;
import java.util.Arrays;
import java.util.Base64;
import java.util.HexFormat;
import java.util.regex.Pattern;

final class Ed25519RateLimitOriginVerifier implements RateLimitOriginVerifier.ExchangeBound {
  private static final Pattern EXCHANGE_ID = Pattern.compile(
      "[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}");
  private static final String SECONDS = "(0|[1-9][0-9]{0,18})";
  private static final Pattern PROOF = Pattern.compile(
      "v1\\.(APISIX|UPSTREAM)\\." + SECONDS + "\\." + SECONDS + "\\.([A-Za-z0-9_-]{86})");
  private static final int MAX_LIFETIME_SECONDS = 30;

  private final URI gateway;
  private final String searchPath;
  private final String fetchPath;
  private final PublicKey key;
  private final String installation;
  private final int skewSeconds;
  private final Clock clock;

  Ed25519RateLimitOriginVerifier(SchemaGovProperties provider, String publicKey, String installation,
      int skewSeconds, Clock clock) {
    this.gateway = provider.gatewayBaseUrl();
    if (gateway == null || !"https".equalsIgnoreCase(gateway.getScheme()))
      throw new IllegalArgumentException("429 attestation requires an HTTPS gateway");
    this.searchPath = routePath(provider.searchPath());
    this.fetchPath = routePath(provider.fetchPath());
    if (installation == null || !installation.matches("[!-~]+"))
      throw new IllegalArgumentException("Invalid 429 attestation installation identifier");
    if (skewSeconds < 0 || skewSeconds > MAX_LIFETIME_SECONDS)
      throw new IllegalArgumentException("Invalid 429 attestation clock skew");
    this.key = publicKey(publicKey);
    this.installation = installation;
    this.skewSeconds = skewSeconds;
    this.clock = clock;
  }

  private String routePath(String configuredPath) {
    if (configuredPath == null || configuredPath.isEmpty())
      throw new IllegalArgumentException("Missing 429 attestation provider route");
    URI route = gateway.resolve(configuredPath);
    BoundedGatewayClient.requireSameOrigin(gateway, route);
    return rawPath(URI.create(route.toASCIIString()));
  }

  private static String rawPath(URI target) {
    return target.getRawPath().isEmpty() ? "/" : target.getRawPath();
  }

  private static PublicKey publicKey(String encoded) {
    // SubjectPublicKeyInfo for id-Ed25519 (RFC 8410), followed by the 32 raw key bytes.
    byte[] prefix = HexFormat.of().parseHex("302a300506032b6570032100");
    try {
      byte[] raw = encoded.matches("[0-9A-Fa-f]{64}") ? HexFormat.of().parseHex(encoded)
          : Base64.getUrlDecoder().decode(encoded);
      if (raw.length != 32) throw new IllegalArgumentException();
      byte[] spki = Arrays.copyOf(prefix, prefix.length + raw.length);
      System.arraycopy(raw, 0, spki, prefix.length, raw.length);
      return KeyFactory.getInstance("Ed25519").generatePublic(new X509EncodedKeySpec(spki));
    } catch (IllegalArgumentException | GeneralSecurityException invalid) {
      throw new IllegalArgumentException("Invalid Ed25519 public key for 429 attestation");
    }
  }

  @Override public Origin verifiedOrigin(String method, URI target, String exchangeId, HttpResponse.ResponseInfo response) {
    if (response == null || response.statusCode() != 429 || exchangeId == null
        || !EXCHANGE_ID.matcher(exchangeId).matches()) return Origin.UNKNOWN;
    try {
      BoundedGatewayClient.requireSameOrigin(gateway, target);
      String path = rawPath(target);
      if (!("POST".equals(method) && searchPath.equals(path) || "GET".equals(method) && fetchPath.equals(path)))
        return Origin.UNKNOWN;
      var values = response.headers().allValues("X-OUF-RateLimit-Attestation");
      if (values.size() != 1) return Origin.UNKNOWN;
      var proof = PROOF.matcher(values.getFirst());
      if (!proof.matches()) return Origin.UNKNOWN;
      long issued = Long.parseLong(proof.group(2));
      long expires = Long.parseLong(proof.group(3));
      long now = clock.instant().getEpochSecond();
      if (expires <= issued || expires - issued > MAX_LIFETIME_SECONDS
          || issued > now + skewSeconds || expires <= now - skewSeconds) return Origin.UNKNOWN;

      String signatureText = proof.group(4);
      byte[] signature = Base64.getUrlDecoder().decode(signatureText);
      if (!Base64.getUrlEncoder().withoutPadding().encodeToString(signature).equals(signatureText))
        return Origin.UNKNOWN;
      String rawTarget = target.getRawQuery() == null ? path : path + "?" + target.getRawQuery();
      if (!StandardCharsets.US_ASCII.newEncoder().canEncode(rawTarget)) return Origin.UNKNOWN;
      String message = String.join("\n", "v1", "semantic-provider-429-origin", method, rawTarget, exchangeId,
          proof.group(1), "429", proof.group(2), proof.group(3), installation);
      var verifier = Signature.getInstance("Ed25519");
      verifier.initVerify(key);
      verifier.update(message.getBytes(StandardCharsets.US_ASCII));
      return verifier.verify(signature) ? Origin.valueOf(proof.group(1)) : Origin.UNKNOWN;
    } catch (BoundedGatewayClient.ProviderFailure | IllegalArgumentException | GeneralSecurityException invalid) {
      return Origin.UNKNOWN;
    }
  }
}

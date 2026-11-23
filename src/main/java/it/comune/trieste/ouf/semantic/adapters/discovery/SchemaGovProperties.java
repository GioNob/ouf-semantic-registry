package it.comune.trieste.ouf.semantic.adapters.discovery;

import java.net.URI;
import java.time.Duration;
import java.util.HashSet;
import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("ouf.semantic.providers.schema-gov")
public record SchemaGovProperties(boolean enabled, URI gatewayBaseUrl, String searchPath,
                                  String fetchPath, Duration connectTimeout,
                                  Duration requestTimeout, int maxResponseBytes,
                                  int maxCandidates, int maxAttempts,
                                  Duration retryBackoff, int circuitFailureThreshold,
                                  Duration circuitOpenDuration, List<String> namespacePrefixes) {
  public SchemaGovProperties {
    if (namespacePrefixes == null || namespacePrefixes.isEmpty() || namespacePrefixes.size() > 32
        || new HashSet<>(namespacePrefixes).size() != namespacePrefixes.size()
        || namespacePrefixes.stream().anyMatch(prefix -> !validPrefix(prefix))) {
      throw new IllegalArgumentException("Invalid schema-gov namespace-prefixes");
    }
    namespacePrefixes = List.copyOf(namespacePrefixes);
  }

  private static boolean validPrefix(String prefix) {
    if (prefix == null || !(prefix.endsWith("/") || prefix.endsWith("#"))
        || prefix.codePointCount(0, prefix.length()) > 2048
        || prefix.codePoints().anyMatch(c -> Character.isISOControl(c)
            || (c >= 0xD800 && c <= 0xDFFF))) return false;
    try {
      // URI also rejects spaces, forbidden IRI delimiters and malformed percent escapes.
      URI iri = URI.create(prefix);
      return iri.isAbsolute();
    } catch (IllegalArgumentException invalid) {
      return false;
    }
  }

  boolean admits(String uri) {
    return namespacePrefixes.stream().anyMatch(prefix -> uri.startsWith(prefix) && uri.length() > prefix.length());
  }
}

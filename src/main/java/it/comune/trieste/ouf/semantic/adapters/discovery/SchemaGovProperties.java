package it.comune.trieste.ouf.semantic.adapters.discovery;

import java.net.URI;
import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("ouf.semantic.providers.schema-gov")
public record SchemaGovProperties(boolean enabled, URI gatewayBaseUrl, String searchPath,
                                  String fetchPath, Duration connectTimeout,
                                  Duration requestTimeout, int maxResponseBytes,
                                  int maxCandidates, int maxAttempts,
                                  Duration retryBackoff, int circuitFailureThreshold,
                                  Duration circuitOpenDuration) {}

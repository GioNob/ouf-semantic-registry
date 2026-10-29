package it.comune.trieste.ouf.semantic.adapters.discovery;

import java.net.URI;
import java.nio.file.Path;
import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("ouf.semantic.providers.schema-gov.gateway-auth")
public record GatewayOAuthProperties(boolean enabled, URI tokenEndpoint, String clientId,
    Path clientSecretFile, String scope, Duration requestTimeout, Duration refreshSkew,
    int maxResponseBytes) {}

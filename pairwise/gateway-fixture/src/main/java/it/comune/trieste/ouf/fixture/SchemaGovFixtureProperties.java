package it.comune.trieste.ouf.fixture;

import java.net.URI;
import java.time.Duration;
import java.util.Set;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("fixture.schema-gov")
public record SchemaGovFixtureProperties(URI sparqlUpstream,Set<String> allowedHosts,
    Duration connectTimeout,Duration requestTimeout,int maxRequestBytes,int maxResponseBytes) {}

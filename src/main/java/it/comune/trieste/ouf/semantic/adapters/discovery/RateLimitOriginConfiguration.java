package it.comune.trieste.ouf.semantic.adapters.discovery;

import java.time.Clock;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
class RateLimitOriginConfiguration {
  @Bean
  @ConditionalOnMissingBean(RateLimitOriginVerifier.class)
  RateLimitOriginVerifier rateLimitOriginVerifier(SchemaGovProperties provider, ObjectProvider<Clock> clocks,
      @Value("${ouf.semantic.providers.schema-gov.origin-attestation.public-key:}") String publicKey,
      @Value("${ouf.semantic.providers.schema-gov.origin-attestation.installation-id:}") String installation,
      @Value("${ouf.semantic.providers.schema-gov.origin-attestation.clock-skew-seconds:0}") int skewSeconds) {
    if (publicKey.isEmpty()) return RateLimitOriginVerifier.UNATTESTED;
    return new Ed25519RateLimitOriginVerifier(provider, publicKey, installation, skewSeconds,
        clocks.getIfAvailable(Clock::systemUTC));
  }
}

package it.comune.trieste.ouf.semantic.api;

import static org.assertj.core.api.Assertions.*;

import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.security.oauth2.jwt.Jwt;

class SemanticIamSecurityConfigurationTest {
  @Test
  void serviceJwtBecomesTrustedOufPrincipal() {
    var cfg=new SemanticIamSecurityConfiguration();
    var converter=cfg.trustedJwtAuthenticationConverter("ouf-api-gateway","ouf_actor_type");

    var jwt=Jwt.withTokenValue("test")
        .header("alg","none")
        .issuer("https://auth.example/realms/ouf")
        .subject("service-account-subject")
        .audience(List.of("ouf-api-gateway","account"))
        .claim("tenant_id","ouf-lab")
        .claim("ouf_actor_type","SERVICE")
        .claim("client_id","ouf-udp")
        .claim("acr","1")
        .claim("scope","ouf.semantic.read authorization.bundle.read")
        .issuedAt(Instant.parse("2026-09-25T08:00:00Z"))
        .expiresAt(Instant.parse("2030-09-25T08:00:00Z"))
        .build();

    var authentication=converter.convert(jwt);
    assertThat(authentication).isNotNull();
    assertThat(authentication.getPrincipal())
        .isInstanceOf(it.comune.trieste.ouf.authorization.TrustedPrincipal.class);

    var principal=(it.comune.trieste.ouf.authorization.TrustedPrincipal)authentication.getPrincipal();
    assertThat(principal.context().subjectId()).isEqualTo("service-account-subject");
    assertThat(principal.context().tenantId()).isEqualTo("ouf-lab");
    assertThat(principal.context().actorType().name()).isEqualTo("SERVICE");
    assertThat(principal.context().servicePrincipalId()).isEqualTo("ouf-udp");
    assertThat(principal.context().scopes()).contains("ouf.semantic.read");
  }

  @Test
  void audienceValidatorRejectsWrongAudience() {
    var validator=SemanticIamSecurityConfiguration.requiredAudienceValidator("ouf-api-gateway");
    var jwt=Jwt.withTokenValue("test")
        .header("alg","none")
        .subject("s")
        .audience(List.of("other"))
        .issuedAt(Instant.parse("2026-09-25T08:00:00Z"))
        .expiresAt(Instant.parse("2030-09-25T08:00:00Z"))
        .build();

    assertThat(validator.validate(jwt).hasErrors()).isTrue();
  }
}

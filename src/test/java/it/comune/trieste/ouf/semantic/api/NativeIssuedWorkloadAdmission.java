package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.authorization.PrincipalContext;
import it.comune.trieste.ouf.authorization.TrustedPrincipal;
import java.time.Instant;

/** Test-only invocation of the retained real IAM decoder and principal converter. */
public final class NativeIssuedWorkloadAdmission {
  public static boolean accepts(String token,String issuer,String audience) {
    try {
      var security=new SemanticIamSecurityConfiguration();
      var jwt=security.jwtDecoder(issuer,audience).decode(token);
      var authentication=security.trustedJwtAuthenticationConverter(audience,"ouf_actor_type").convert(jwt);
      if(authentication==null || !(authentication.getPrincipal() instanceof TrustedPrincipal principal))return false;
      var p=principal.context();
      return jwt.getExpiresAt()!=null && jwt.getExpiresAt().isAfter(Instant.now().plusSeconds(10))
          && !p.subjectId().isBlank() && p.actorType()==PrincipalContext.ActorType.SERVICE
          && p.servicePrincipalId().equals("native-workload") && p.tenantId().equals("native-fixture-tenant")
          && p.authenticationContextRef().equals("1") && p.issuer().equals(issuer) && p.audience().equals(audience)
          && p.scopes().contains("gateway.invoke");
    }catch(RuntimeException failure){return false;}
  }
}

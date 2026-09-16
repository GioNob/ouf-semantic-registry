package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;

import it.comune.trieste.ouf.semantic.api.TrustedActorResolver;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;

class TrustedActorResolverTest {
  private final TrustedActorResolver resolver=new TrustedActorResolver();

  @Test void authenticatedRolesMapToCanonicalAuthorizationActorTypes(){
    assertThat(resolver.actor(request("human","OUF_HUMAN_USER")).type()).isEqualTo("HUMAN");
    assertThat(resolver.actor(request("agent","OUF_AI_AGENT")).type()).isEqualTo("AI_AGENT");
    assertThat(resolver.actor(request("service","OUF_SERVICE")).type()).isEqualTo("SERVICE");
    assertThat(resolver.actor(request("mcp","OUF_MCP_SERVER")).type()).isEqualTo("SERVICE");
  }

  @Test void canonicalDecisionRefWinsAndLegacyAliasRemainsBoundedCompatibilityBridge(){
    var request=request("human","OUF_HUMAN_USER");
    request.setAttribute("ouf.authorizationDecisionRef","bundle:7:decision:42");
    request.setAttribute("ouf.authorizationContextRef","legacy:context");
    assertThat(resolver.authorizationDecisionRef(request)).isEqualTo("bundle:7:decision:42");

    var legacy=request("human","OUF_HUMAN_USER");
    legacy.setAttribute("ouf.authorizationContextRef","legacy:context");
    assertThat(resolver.authorizationDecisionRef(legacy)).isEqualTo("legacy:context");
  }

  @Test void capabilitiesRemainServerEstablished(){
    var request=request("service","OUF_SERVICE");
    request.setAttribute("ouf.authorizedCapabilities",Set.of("ouf.semantic.review"));
    assertThat(resolver.actor(request).capabilities()).containsExactly("ouf.semantic.review");
  }

  private static MockHttpServletRequest request(String subject,String role){
    var request=new MockHttpServletRequest();
    request.setUserPrincipal(()->subject);
    request.addUserRole(role);
    return request;
  }
}

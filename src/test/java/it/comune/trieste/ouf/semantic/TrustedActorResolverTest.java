package it.comune.trieste.ouf.semantic;
import static org.assertj.core.api.Assertions.*;
import it.comune.trieste.ouf.semantic.api.TrustedActorResolver;
import it.comune.trieste.ouf.authorization.TestAuthorization;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
class TrustedActorResolverTest {
 private final TrustedActorResolver resolver=new TrustedActorResolver();
 @Test void canonicalActorsComeOnlyFromAuthenticatedCommonPrincipal(){for(String type:Set.of("HUMAN","SERVICE","AI_AGENT")){var r=new MockHttpServletRequest();TestAuthorization.bind(r,"subject",type,Set.of("read"));assertThat(resolver.actor(r).type()).isEqualTo(type);}}
 @Test void decisionAndCapabilitiesComeFromLocalPinnedBundle(){var r=new MockHttpServletRequest();TestAuthorization.bind(r,"human","HUMAN",Set.of("ouf.semantic.review"));r.setAttribute("ouf.authorizedCapabilities",Set.of("ouf.semantic.publish"));r.setAttribute("ouf.authorizationContextRef","forged");assertThat(resolver.actor(r).capabilities()).containsExactly("ouf.semantic.review");assertThat(resolver.authorizationDecisionRef(r)).isEqualTo("fixture:1");assertThatThrownBy(()->resolver.require(resolver.actor(r),"ouf.semantic.publish")).hasMessageContaining("SEM_CAPABILITY_REQUIRED");}
 @Test void rolesAndLegacyContextAloneAreInsufficient(){var r=new MockHttpServletRequest();r.setUserPrincipal(()->"human");r.addUserRole("OUF_HUMAN_USER");r.setAttribute("ouf.authorizationContextRef","legacy");assertThatThrownBy(()->resolver.actor(r)).hasMessage("TRUSTED_PRINCIPAL_REQUIRED");}
}

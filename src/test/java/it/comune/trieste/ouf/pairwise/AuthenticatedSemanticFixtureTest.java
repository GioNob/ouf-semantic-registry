package it.comune.trieste.ouf.pairwise;

import static org.assertj.core.api.Assertions.*;
import it.comune.trieste.ouf.semantic.api.TrustedActorResolver;
import jakarta.servlet.http.HttpServletRequest;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.*;

class AuthenticatedSemanticFixtureTest {
  private static final String TOKEN="a".repeat(64);
  private final AuthenticatedSemanticFixture.FixtureIdentityFilter filter=new AuthenticatedSemanticFixture.FixtureIdentityFilter(TOKEN);
  @Test void noCredentialOrForgedSubjectCannotCreatePrincipal() throws Exception {
    for(String token:new String[]{"", "Bearer invalid"}) {
      var request=new MockHttpServletRequest("POST","/api/semantic/v1/discovery-requests");
      request.addHeader("X-OUF-Subject","forged-human");
      if(!token.isEmpty())request.addHeader("Authorization",token);
      var response=new MockHttpServletResponse();var called=new AtomicBoolean();
      filter.doFilter(request,response,(req,res)->called.set(true));
      assertThat(response.getStatus()).isEqualTo(401);assertThat(called).isFalse();
    }
  }
  @Test void validCredentialProducesOnlyServerEstablishedServiceIdentity() throws Exception {
    var request=new MockHttpServletRequest("POST","/api/semantic/v1/discovery-requests");
    request.addHeader("Authorization","Bearer "+TOKEN);request.addHeader("X-OUF-Subject","forged-human");
    request.setAttribute(TrustedActorResolver.ACTOR_TYPE,"HUMAN");
    var called=new AtomicBoolean();
    filter.doFilter(request,new MockHttpServletResponse(),(req,res)->{
      var trusted=(HttpServletRequest)req;var resolver=new TrustedActorResolver();
      assertThat(resolver.actor(trusted).subject()).isEqualTo("pairwise-discovery-service");
      assertThat(resolver.actor(trusted).type()).isEqualTo("SERVICE");
      assertThat(resolver.actor(trusted).capabilities()).doesNotContain("ouf.semantic.approve","ouf.semantic.publish");
      assertThat(trusted.isUserInRole("OUF_HUMAN_USER")).isFalse();called.set(true);
    });
    assertThat(called).isTrue();
  }
  @Test void serviceCannotReachHumanApprovalOrUnknownCapability() throws Exception {
    for(String path:new String[]{"/api/trusted-human/v1/semantic-approval-challenges/00000000-0000-0000-0000-000000000000/decision","/api/semantic/v1/unknown"}) {
      var request=new MockHttpServletRequest("POST",path);request.addHeader("Authorization","Bearer "+TOKEN);
      var response=new MockHttpServletResponse();var called=new AtomicBoolean();
      filter.doFilter(request,response,(req,res)->called.set(true));
      assertThat(response.getStatus()).isEqualTo(403);assertThat(called).isFalse();
    }
  }
  @Test void fixtureCannotStartWithoutExplicitCredential(){
    assertThatThrownBy(()->new AuthenticatedSemanticFixture.FixtureIdentityFilter(null)).isInstanceOf(IllegalArgumentException.class);
  }
}

package it.comune.trieste.ouf.pairwise;

import it.comune.trieste.ouf.semantic.SemanticRegistryApplication;
import it.comune.trieste.ouf.semantic.api.TrustedActorResolver;
import it.comune.trieste.ouf.authorization.*;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.Principal;
import java.util.Set;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/** Laboratory identity adapter. Never packaged in the production application. */
public class AuthenticatedSemanticFixture {
  public static void main(String[] args) {
    SpringApplication.run(new Class<?>[]{SemanticRegistryApplication.class, FixtureConfiguration.class}, args);
  }
  @Configuration(proxyBeanMethods=false)
  public static class FixtureConfiguration {
    @Bean FilterRegistrationBean<FixtureIdentityFilter> fixtureIdentityFilter() {
      var registration=new FilterRegistrationBean<>(new FixtureIdentityFilter(System.getenv("OUF_PAIRWISE_TOKEN")));
      registration.addUrlPatterns("/api/*");
      registration.setOrder(-100);
      return registration;
    }
  }
  public static final class FixtureIdentityFilter implements Filter {
    private final byte[] expected;
    private final Set<String> caps=Set.of("ouf.semantic.read","ouf.semantic.discovery","ouf.semantic.propose");
    private final LocalAuthorization runtime=TestAuthorization.runtime("pairwise-discovery-service","SERVICE",caps);
    public FixtureIdentityFilter(String token) {
      if(token==null || !token.matches("[a-f0-9]{64}")) throw new IllegalArgumentException("Pairwise fixture requires an ephemeral 256-bit token");
      expected=("Bearer "+token).getBytes(StandardCharsets.UTF_8);
    }
    @Override public void doFilter(ServletRequest input,ServletResponse output,FilterChain chain) throws IOException,ServletException {
      var request=(HttpServletRequest)input;var response=(HttpServletResponse)output;
      String credential=request.getHeader("Authorization");
      if(credential==null || !MessageDigest.isEqual(expected,credential.getBytes(StandardCharsets.UTF_8))) {
        response.sendError(401,"PAIRWISE_AUTHENTICATION_REQUIRED");return;
      }
      String path=request.getRequestURI(), method=request.getMethod();
      boolean allowed=(method.equals("POST") && path.equals("/api/semantic/v1/discovery-requests"))
          || (method.equals("GET") && path.matches("/api/semantic/v1/discovery-requests/[a-f0-9-]+/candidates"))
          || (method.equals("POST") && path.matches("/api/semantic/v1/discovery-requests/[a-f0-9-]+/candidates/[a-f0-9-]+:adopt"))
          || (method.equals("GET") && path.matches("/api/semantic/v1/artifacts/[a-f0-9-]+"));
      if(!allowed){response.sendError(403,"PAIRWISE_CAPABILITY_DENIED");return;}
      request.getServletContext().setAttribute(ServletAuthorization.RUNTIME,runtime);
      chain.doFilter(new HttpServletRequestWrapper(request) {
        @Override public Principal getUserPrincipal(){return TestAuthorization.principal("pairwise-discovery-service","SERVICE",caps);}
        @Override public String getRemoteUser(){return "pairwise-discovery-service";}
        @Override public boolean isUserInRole(String role){return "OUF_SERVICE".equals(role);}
      },response);
    }
  }
}

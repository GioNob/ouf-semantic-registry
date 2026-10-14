package it.comune.trieste.ouf.pairwise;

import it.comune.trieste.ouf.authorization.*;
import it.comune.trieste.ouf.authorization.AuthorizationPolicy.*;
import it.comune.trieste.ouf.semantic.SemanticRegistryApplication;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.time.Instant;
import java.util.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.*;

/** Disposable identity adapter only; every proposal and HUMAN decision uses the production HTTP API. */
public class ChatbotSemanticFixture {
  public static void main(String[] args){SpringApplication.run(new Class<?>[]{SemanticRegistryApplication.class,Fixture.class},args);}
  @Configuration(proxyBeanMethods=false) public static class Fixture {
    private static final Set<String> SERVICE=Set.of("ouf.semantic.read");
    private static final Set<String> HUMAN=Set.of("ouf.semantic.read","ouf.semantic.propose","ouf.semantic.review.prepare",
        "ouf.semantic.approval.request","ouf.semantic.review","ouf.semantic.approve","ouf.semantic.reject","ouf.semantic.publish");
    @Bean FilterRegistrationBean<Filter> chatbotSemanticIdentity()throws Exception{
      String serviceToken=required("OUF_PAIRWISE_TOKEN"),humanToken=required("OUF_PAIRWISE_HUMAN_TOKEN");
      var service=TestAuthorization.runtime("fixture-ingestion","SERVICE",SERVICE);
      var human=TestAuthorization.runtime("fixture-human","HUMAN",HUMAN);
      var caps=new LinkedHashMap<String,CapabilityDescriptor>();
      for(var c:service.currentSnapshot().bundle().capabilities())caps.put(c.capabilityId(),c);
      for(var c:human.currentSnapshot().bundle().capabilities()){
        var old=caps.get(c.capabilityId());
        if(old==null)caps.put(c.capabilityId(),c);
        else {var actors=new HashSet<>(old.allowedActors());actors.addAll(c.allowedActors());caps.put(c.capabilityId(),new CapabilityDescriptor(c.capabilityId(),c.operation(),c.requiredScope(),actors));}
      }
      var grants=new ArrayList<Grant>();
      for(var g:service.currentSnapshot().bundle().grants())grants.add(new Grant("service:"+g.grantId(),g.capabilityId(),g.tenantId(),g.subjectId(),g.servicePrincipalId(),g.organizationId(),g.validFrom(),g.validUntil()));
      for(var g:human.currentSnapshot().bundle().grants())grants.add(new Grant("human:"+g.grantId(),g.capabilityId(),g.tenantId(),g.subjectId(),g.servicePrincipalId(),g.organizationId(),g.validFrom(),g.validUntil()));
      TestAuthorization.install(service,new PolicyBundle("chatbot-semantic-fixture",1,Instant.now(),new ArrayList<>(caps.values()),grants));
      Filter identity=(input,output,chain)->{
        var request=(HttpServletRequest)input;var response=(HttpServletResponse)output;
        boolean workload=matches(request.getHeader("Authorization"),serviceToken),person=matches(request.getHeader("Authorization"),humanToken);
        if(!workload&&!person){response.sendError(401);return;}
        String path=request.getRequestURI(),method=request.getMethod();
        boolean reference="GET".equals(method)&&path.equals("/api/semantic/v1/references:resolve");
        boolean proposal="POST".equals(method)&&path.matches("/api/semantic/v1/proposal-commands/(create|read|validate|review)")
            &&request.getHeader("X-OUF-Semantic-Proposal-Receipt")!=null;
        boolean humanRoute=person&&path.matches("/api/trusted-human/v1/semantic-approval-challenges/[a-f0-9-]{36}(/decision|/publish)?")
            &&(("GET".equals(method)&&!path.endsWith("/decision")&&!path.endsWith("/publish"))
                ||("POST".equals(method)&&(path.endsWith("/decision")||path.endsWith("/publish"))));
        if(!reference&&!proposal&&!humanRoute){response.sendError(403);return;}
        request.getServletContext().setAttribute(ServletAuthorization.RUNTIME,service);
        chain.doFilter(new HttpServletRequestWrapper(request){@Override public Principal getUserPrincipal(){
          return TestAuthorization.principal(workload?"fixture-ingestion":"fixture-human",workload?"SERVICE":"HUMAN",workload?SERVICE:HUMAN);
        }},response);
      };
      var registration=new FilterRegistrationBean<>(identity);registration.addUrlPatterns("/api/*");registration.setOrder(-100);return registration;
    }
    private static String required(String name){String value=System.getenv(name);if(value==null||!value.matches("[a-f0-9]{64}"))throw new IllegalArgumentException("Ephemeral fixture token required");return value;}
    private static boolean matches(String value,String expected){return value!=null&&MessageDigest.isEqual(value.getBytes(StandardCharsets.UTF_8),("Bearer "+expected).getBytes(StandardCharsets.UTF_8));}
  }
}

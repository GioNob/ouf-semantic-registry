package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.authorization.*;
import it.comune.trieste.ouf.semantic.application.GovernanceService.Forbidden;
import jakarta.servlet.http.*;
import java.util.*;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.*;
import org.springframework.web.servlet.config.annotation.*;

@Configuration
public class SemanticAuthorizationBoundary implements WebMvcConfigurer {
 @Override public void addInterceptors(InterceptorRegistry registry){registry.addInterceptor(new HandlerInterceptor(){
  @Override public boolean preHandle(HttpServletRequest request,HttpServletResponse response,Object handler){
   if(!(handler instanceof HandlerMethod method))return true;
   var rule=method.getMethodAnnotation(SemanticCapability.class);
   if(rule==null)throw new Forbidden("SEM_ROUTE_CAPABILITY_UNDECLARED");
   try{
    var owner=OwnerAuthorization.bind(request);String id=null;
    Object raw=request.getAttribute(HandlerMapping.URI_TEMPLATE_VARIABLES_ATTRIBUTE);
    if(raw instanceof Map<?,?> vars){Object value=vars.get("id");if(value==null)value=vars.get("artifactId");if(value==null)value=vars.get("candidateId");if(value!=null)id=value.toString();}
    String type="semantic."+method.getBeanType().getSimpleName().replace("Api", "").toLowerCase(java.util.Locale.ROOT);
    var resource=new ResourceContext(type,id,owner.principal().tenantId(),null,Map.of("module","SEMANTIC"));
    owner.require(rule.value(),resource);request.setAttribute(ServletAuthorization.RESOURCE,resource);return true;
   }catch(SecurityException denied){throw new Forbidden(request.getUserPrincipal()==null?"SEM_AUTHENTICATION_REQUIRED":"SEM_CAPABILITY_REQUIRED:"+rule.value());}
  }
 }).addPathPatterns("/api/semantic/v1/**");}
}

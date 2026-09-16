package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.GovernanceService.Forbidden;
import jakarta.servlet.http.HttpServletRequest;
import java.security.Principal;
import java.util.*;
import org.springframework.stereotype.Component;

@Component
public class TrustedActorResolver {
  public static final String ACTOR_TYPE="ouf.actorType",CAPABILITIES="ouf.authorizedCapabilities",DECISION_REF="ouf.authorizationDecisionRef",LEGACY_CONTEXT_REF="ouf.authorizationContextRef";
  public record Actor(String subject,String type,Set<String> capabilities){}
  public Actor actor(HttpServletRequest request){Principal principal=request.getUserPrincipal();if(principal==null||principal.getName()==null||principal.getName().isBlank())throw new Forbidden("SEM_AUTHENTICATION_REQUIRED");String type=canonicalActorType(request);Set<String> capabilities=new LinkedHashSet<>();Object authorized=request.getAttribute(CAPABILITIES);if(authorized instanceof Collection<?> values)values.stream().map(String::valueOf).forEach(capabilities::add);return new Actor(principal.getName(),type,Set.copyOf(capabilities));}
  private String canonicalActorType(HttpServletRequest request){Object propagated=request.getAttribute(ACTOR_TYPE);if(propagated instanceof String type&&!type.isBlank()){if(Set.of("HUMAN","SERVICE","AI_AGENT").contains(type))return type;throw new Forbidden("SEM_ACTOR_TYPE_INVALID");}if(request.isUserInRole("OUF_HUMAN_USER"))return "HUMAN";if(request.isUserInRole("OUF_AI_AGENT"))return "AI_AGENT";if(request.isUserInRole("OUF_SERVICE")||request.isUserInRole("OUF_MCP_SERVER"))return "SERVICE";throw new Forbidden("SEM_ACTOR_ROLE_REQUIRED");}
  public String authorizationDecisionRef(HttpServletRequest request){Object value=request.getAttribute(DECISION_REF);if(!(value instanceof String ref)||ref.isBlank()){value=request.getAttribute(LEGACY_CONTEXT_REF);}if(!(value instanceof String ref)||ref.isBlank())throw new Forbidden("SEM_AUTHORIZATION_CONTEXT_REQUIRED");return ref;}
  public void require(Actor actor,String capability){if(!actor.capabilities().contains(capability))throw new Forbidden("SEM_CAPABILITY_REQUIRED:"+capability);}
}

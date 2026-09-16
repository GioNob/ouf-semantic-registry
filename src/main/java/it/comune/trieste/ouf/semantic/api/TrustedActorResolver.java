package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.GovernanceService.Forbidden;
import jakarta.servlet.http.HttpServletRequest;
import java.security.Principal;
import java.util.*;
import org.springframework.stereotype.Component;

@Component
public class TrustedActorResolver {
  public record Actor(String subject,String type,Set<String> capabilities){}
  public Actor actor(HttpServletRequest request){Principal principal=request.getUserPrincipal();if(principal==null||principal.getName()==null||principal.getName().isBlank())throw new Forbidden("SEM_AUTHENTICATION_REQUIRED");String type;if(request.isUserInRole("OUF_HUMAN_USER"))type="HUMAN";else if(request.isUserInRole("OUF_AI_AGENT"))type="AI_AGENT";else if(request.isUserInRole("OUF_SERVICE")||request.isUserInRole("OUF_MCP_SERVER"))type="SERVICE";else throw new Forbidden("SEM_ACTOR_ROLE_REQUIRED");Set<String> capabilities=new LinkedHashSet<>();Object authorized=request.getAttribute("ouf.authorizedCapabilities");if(authorized instanceof Collection<?> values)values.stream().map(String::valueOf).forEach(capabilities::add);return new Actor(principal.getName(),type,Set.copyOf(capabilities));}
  public String authorizationDecisionRef(HttpServletRequest request){Object value=request.getAttribute("ouf.authorizationDecisionRef");if(!(value instanceof String ref)||ref.isBlank())throw new Forbidden("SEM_AUTHORIZATION_DECISION_REQUIRED");return ref;}
  public void require(Actor actor,String capability){if(!actor.capabilities().contains(capability))throw new Forbidden("SEM_CAPABILITY_REQUIRED:"+capability);}
}

package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.GovernanceService.Forbidden;
import it.comune.trieste.ouf.authorization.ServletAuthorization;
import jakarta.servlet.http.HttpServletRequest;
import java.util.*;
import org.springframework.stereotype.Component;

@Component
public class TrustedActorResolver {
  public static final String ACTOR_TYPE="ouf.actorType",CAPABILITIES="ouf.authorizedCapabilities",DECISION_REF="ouf.authorizationDecisionRef",LEGACY_CONTEXT_REF="ouf.authorizationContextRef";
  public record Actor(String subject,String type,Set<String> capabilities){}
  public Actor actor(HttpServletRequest request){var c=context(request);return new Actor(c.principal().subjectId(),c.principal().actorType().name(),c.capabilities());}
  private ServletAuthorization.Context context(HttpServletRequest request){try{return ServletAuthorization.resolve(request);}catch(SecurityException e){throw new Forbidden(request.getUserPrincipal()==null?"SEM_AUTHENTICATION_REQUIRED":e.getMessage());}}
  public String authorizationDecisionRef(HttpServletRequest request){return context(request).decisionRef();}
  public void require(Actor actor,String capability){if(!actor.capabilities().contains(capability))throw new Forbidden("SEM_CAPABILITY_REQUIRED:"+capability);}
}

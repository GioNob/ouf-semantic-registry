package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.*;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Pattern;
import java.util.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController @RequestMapping("/api/trusted-human/v1/semantic-approval-challenges")
public class SemanticTrustedHumanApi {
  private final GovernanceService governance;private final ChangeGovernanceService changes;private final TrustedActorResolver actors;
  public SemanticTrustedHumanApi(GovernanceService governance,ChangeGovernanceService changes,TrustedActorResolver actors){this.governance=governance;this.changes=changes;this.actors=actors;}
  public record DecisionRequest(@Pattern(regexp="APPROVED|REJECTED") String decision){}
  public record PublishRequest(UUID approvalDecisionId,@Pattern(regexp="[0-9a-f]{64}") String contentHash){}
  public record MigrationDecisionRequest(@Pattern(regexp="APPROVED|REJECTED") String decision){}
  @GetMapping("/{id}") Map<String,Object> card(@PathVariable UUID id,HttpServletRequest request){var actor=human(request);actors.require(actor,"ouf.semantic.review");return governance.card(id);}
  @PostMapping("/{id}/decision") Map<String,Object> decide(@PathVariable UUID id,@Valid @RequestBody DecisionRequest body,HttpServletRequest request,@RequestHeader HttpHeaders headers){var actor=human(request);actors.require(actor,"APPROVED".equals(body.decision())?"ouf.semantic.approve":"ouf.semantic.reject");return governance.decide(id,body.decision(),actor.subject(),actor.type(),actors.authorizationDecisionRef(request),correlation(headers));}
  @PostMapping("/{id}/publish") Map<String,Object> publish(@PathVariable UUID id,@Valid @RequestBody PublishRequest body,@RequestHeader("Idempotency-Key") String key,HttpServletRequest request,@RequestHeader HttpHeaders headers){var actor=human(request);actors.require(actor,"ouf.semantic.publish");Map<String,Object> card=governance.card(id);return governance.publish((UUID)card.get("revision_id"),body.approvalDecisionId(),key,body.contentHash(),actor.subject(),actor.type(),correlation(headers));}
  @PostMapping("/revisions/{id}:deprecate") Map<String,Object> deprecate(@PathVariable UUID id,HttpServletRequest request,@RequestHeader HttpHeaders headers){var actor=human(request);actors.require(actor,"ouf.semantic.deprecate");return governance.lifecycle(id,"DEPRECATED",actor.subject(),actor.type(),actors.authorizationDecisionRef(request),correlation(headers));}
  @PostMapping("/artifacts/{id}:retire") Map<String,Object> retire(@PathVariable UUID id,HttpServletRequest request,@RequestHeader HttpHeaders headers){var actor=human(request);actors.require(actor,"ouf.semantic.deprecate");return governance.lifecycle(governance.retiredRevision(id),"RETIRED",actor.subject(),actor.type(),actors.authorizationDecisionRef(request),correlation(headers));}
  @GetMapping("/migration-proposals/{id}") Map<String,Object> migrationCard(@PathVariable UUID id,HttpServletRequest request){var actor=human(request);actors.require(actor,"ouf.semantic.review");return changes.proposal(id);}
  @PostMapping("/migration-proposals/{id}/decision") Map<String,Object> migrationDecision(@PathVariable UUID id,@Valid @RequestBody MigrationDecisionRequest body,HttpServletRequest request){var actor=human(request);actors.require(actor,"ouf.semantic.migration.decide");return changes.decide(id,body.decision(),actor.subject(),actor.type(),actors.authorizationDecisionRef(request));}
  private TrustedActorResolver.Actor human(HttpServletRequest request){var actor=actors.actor(request);if(!"HUMAN".equals(actor.type()))throw new GovernanceService.Forbidden("HUMAN_IDENTITY_REQUIRED");return actor;}
  private static String correlation(HttpHeaders h){return Optional.ofNullable(h.getFirst("X-Correlation-Id")).filter(x->!x.isBlank()).orElseGet(()->UUID.randomUUID().toString());}
}

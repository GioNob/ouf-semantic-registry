package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.GovernanceService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Pattern;
import java.time.Duration;
import java.util.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController @RequestMapping("/api/semantic/v1")
public class GovernanceApi {
  private final GovernanceService service;private final TrustedActorResolver actors;
  public GovernanceApi(GovernanceService service,TrustedActorResolver actors){this.service=service;this.actors=actors;}
  public record ChallengeRequest(UUID revisionId,@Pattern(regexp="[0-9a-f]{64}") String contentHash){}
  @PostMapping("/approval-challenges") ResponseEntity<Map<String,Object>> challenge(@Valid @RequestBody ChallengeRequest r,HttpServletRequest request,@RequestHeader HttpHeaders headers){var actor=actors.actor(request);Map<String,Object> out=service.challenge(r.revisionId(),r.contentHash(),Duration.ofMinutes(15),actor.subject(),actor.type(),correlation(headers));return ResponseEntity.status(HttpStatus.CREATED).body(out);}
  private static String correlation(HttpHeaders h){return Optional.ofNullable(h.getFirst("X-Correlation-Id")).filter(x->!x.isBlank()).orElseGet(()->UUID.randomUUID().toString());}
}

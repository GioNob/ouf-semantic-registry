package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.GovernanceService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Pattern;
import java.time.Duration;
import java.util.Map;
import java.util.UUID;
import org.springframework.web.bind.annotation.*;

@RestController @RequestMapping("/api/semantic/v1")
public class GovernanceApi {
  private final GovernanceService service; public GovernanceApi(GovernanceService service){this.service=service;}
  public record ChallengeRequest(UUID revisionId,@Pattern(regexp="[0-9a-f]{64}") String contentHash){}
  public record DecisionRequest(@Pattern(regexp="APPROVED|REJECTED") String decision){}
  public record PublishRequest(UUID revisionId,UUID approvalDecisionId,@Pattern(regexp="[0-9a-f]{64}") String contentHash){}
  @PostMapping("/approval-challenges") Map<String,Object> challenge(@Valid @RequestBody ChallengeRequest r,@RequestHeader("X-OUF-Subject") String actor,@RequestHeader("X-OUF-Principal-Type") String type){return service.challenge(r.revisionId(),r.contentHash(),Duration.ofMinutes(15),actor,type);}
  @PostMapping("/approval-challenges/{id}/decisions") Map<String,Object> decide(@PathVariable UUID id,@Valid @RequestBody DecisionRequest r,@RequestHeader("X-OUF-Subject") String actor,@RequestHeader("X-OUF-Principal-Type") String type){return service.decide(id,r.decision(),actor,type);}
  @PostMapping("/revisions/{id}:publish") Map<String,Object> publish(@PathVariable UUID id,@Valid @RequestBody PublishRequest r,@RequestHeader("Idempotency-Key") String key,@RequestHeader("X-OUF-Subject") String actor,@RequestHeader("X-OUF-Principal-Type") String type,@RequestHeader(value="X-Correlation-Id",defaultValue="") String correlation){if(!id.equals(r.revisionId()))throw new IllegalArgumentException("revision mismatch");return service.publish(id,r.approvalDecisionId(),key,r.contentHash(),actor,type,correlation);}
}

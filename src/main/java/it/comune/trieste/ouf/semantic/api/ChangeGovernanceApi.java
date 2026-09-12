package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.ChangeGovernanceService;
import java.util.*;
import org.springframework.web.bind.annotation.*;
import jakarta.servlet.http.HttpServletRequest;

@RestController @RequestMapping("/api/semantic/v1")
public class ChangeGovernanceApi {
  private final ChangeGovernanceService service;private final TrustedActorResolver actors;public ChangeGovernanceApi(ChangeGovernanceService service,TrustedActorResolver actors){this.service=service;this.actors=actors;}
  public record NoticeRequest(UUID changeId,String decision){}
  public record ProposalRequest(UUID changeId,List<Map<String,Object>> replacementRefs,String rationale){}
  public record DecisionRequest(String decision){}
  @PostMapping("/change-notices") Map<String,Object> notice(@RequestBody NoticeRequest r,HttpServletRequest request){return service.notice(r.changeId(),r.decision(),actors.actor(request).subject());}
  @GetMapping("/change-notices/{id}") Map<String,Object> notice(@PathVariable UUID id){return service.getNotice(id);}
  @PostMapping("/migration-proposals") Map<String,Object> propose(@RequestBody ProposalRequest r,HttpServletRequest request){return service.propose(r.changeId(),r.replacementRefs(),r.rationale(),actors.actor(request).subject());}
  @GetMapping("/migration-proposals/{id}") Map<String,Object> proposal(@PathVariable UUID id){return service.proposal(id);}
}

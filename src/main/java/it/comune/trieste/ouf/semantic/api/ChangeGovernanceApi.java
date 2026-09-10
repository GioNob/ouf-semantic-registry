package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.ChangeGovernanceService;
import java.util.*;
import org.springframework.web.bind.annotation.*;

@RestController @RequestMapping("/api/semantic/v1")
public class ChangeGovernanceApi {
  private final ChangeGovernanceService service;public ChangeGovernanceApi(ChangeGovernanceService service){this.service=service;}
  public record NoticeRequest(UUID changeId,String decision){}
  public record ProposalRequest(UUID changeId,List<Map<String,Object>> replacementRefs,String rationale){}
  public record DecisionRequest(String decision){}
  @PostMapping("/change-notices") Map<String,Object> notice(@RequestBody NoticeRequest r,@RequestHeader("X-OUF-Subject") String actor){return service.notice(r.changeId(),r.decision(),actor);}
  @GetMapping("/change-notices/{id}") Map<String,Object> notice(@PathVariable UUID id){return service.getNotice(id);}
  @PostMapping("/migration-proposals") Map<String,Object> propose(@RequestBody ProposalRequest r,@RequestHeader("X-OUF-Subject") String actor){return service.propose(r.changeId(),r.replacementRefs(),r.rationale(),actor);}
  @PostMapping("/migration-proposals/{id}:decide") Map<String,Object> decide(@PathVariable UUID id,@RequestBody DecisionRequest r,@RequestHeader("X-OUF-Subject") String actor,@RequestHeader("X-OUF-Actor-Type") String actorType){return service.decide(id,r.decision(),actor,actorType);}
  @GetMapping("/migration-proposals/{id}") Map<String,Object> proposal(@PathVariable UUID id){return service.proposal(id);}
}

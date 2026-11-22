package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;

import static it.comune.trieste.ouf.semantic.application.WorkflowAction.*;

/** Current workflow metadata, independent of the immutable command receipt. */
@Service
public class ProposalObservation {
  enum State {
    DRAFT(PREPARE_REVIEW), VALIDATED(REQUEST_APPROVAL), VALIDATION_FAILED(REVISE_PROPOSAL),
    UNDER_REVIEW(WAIT_HUMAN_DECISION), APPROVED(NONE), REJECTED(REVISE_PROPOSAL),
    EXPIRED(REVISE_PROPOSAL), ACTIVE(NONE), DEPRECATED(NONE), RETIRED(NONE), UNKNOWN(NONE);

    private final WorkflowAction action;
    State(WorkflowAction action) { this.action=action; }
  }

  private final JdbcClient db;
  private final ObjectMapper json;
  private final GovernanceService governance;

  public ProposalObservation(JdbcClient db,ObjectMapper json,GovernanceService governance) {
    this.db=db;
    this.json=json;
    this.governance=governance;
  }

  public Map<String,Object> current(UUID revision) {
    Map<String,Object> out=new LinkedHashMap<>();
    State state=State.UNKNOWN;
    if(revision!=null) {
      var row=db.sql("""
          select r.row_version,r.lifecycle_status,coalesce(c.challenge_id,h.challenge_id) challenge_id,
            coalesce(c.expires_at,h.expires_at) expires_at,
            case when c.status='OPEN' and c.expires_at<=statement_timestamp() then 'EXPIRED'
                 else coalesce(c.status,h.status) end challenge_status,
            v.validation_run_id,v.status validation_status
          from ouf_sem.artifact_revision r
          left join lateral (
            select challenge_id,status,expires_at from ouf_sem.approval_challenge
            where r.lifecycle_status='UNDER_REVIEW' and revision_id=r.revision_id
              and status in ('OPEN','APPROVED') and target_content_hash=r.content_hash
            order by created_at desc,challenge_id desc limit 1
          ) c on true
          left join lateral (
            select validation_run_id,status from ouf_sem.validation_run
            where r.lifecycle_status='DRAFT' and revision_id=r.revision_id
              and validated_row_version=r.row_version and (status='FAIL' or (status='PASS' and error_count=0))
              and validated_content_hash=encode(public.digest(
                convert_to(r.label_json::text||r.description_json::text||r.definition_json::text,'UTF8'),'sha256'),'hex')
            order by created_at desc,validation_run_id desc limit 1
          ) v on true
          left join lateral (
            select challenge_id,status,expires_at from ouf_sem.approval_challenge
            where r.lifecycle_status='DRAFT' and v.status is null and revision_id=r.revision_id
              and status in ('REJECTED','EXPIRED')
            order by created_at desc,challenge_id desc limit 1
          ) h on true
          where r.revision_id=:r
          """).param("r",revision).query().optionalRow().orElse(Map.of());
      if(!row.isEmpty()) {
        state=state(row);
        out.put("revisionId",revision);
        out.put("rowVersion",row.get("row_version"));
        if(row.get("validation_run_id")!=null)out.put("currentValidationRunId",row.get("validation_run_id"));
        if(row.get("challenge_id") instanceof UUID challengeId) {
          var challenge=new LinkedHashMap<String,Object>();
          challenge.put("challengeId",challengeId);
          challenge.put("challengeStatus",row.get("challenge_status"));
          challenge.put("expiresAt",row.get("expires_at"));
          if(state==State.UNDER_REVIEW || state==State.APPROVED)
            governance.reviewUrl(challengeId).ifPresent(url->challenge.put("reviewUrl",url));
          out.put("currentChallenge",challenge);
        }
      }
    }
    out.put("state",state);
    out.put("allowedActions",List.of(state.action));
    if(state==State.UNDER_REVIEW)out.put("pollAfterSeconds",5);
    out.put("version",version(out));
    return out;
  }

  private static State state(Map<String,Object> row) {
    String challenge=Objects.toString(row.get("challenge_status"),"");
    return switch(String.valueOf(row.get("lifecycle_status"))) {
      case "DRAFT" -> switch(Objects.toString(row.get("validation_status"),"")) {
        case "PASS" -> State.VALIDATED;
        case "FAIL" -> State.VALIDATION_FAILED;
        default -> switch(challenge) {
          case "REJECTED" -> State.REJECTED;
          case "EXPIRED" -> State.EXPIRED;
          default -> State.DRAFT;
        };
      };
      case "UNDER_REVIEW" -> switch(challenge) {
        case "OPEN" -> State.UNDER_REVIEW;
        case "APPROVED" -> State.APPROVED;
        case "EXPIRED" -> State.EXPIRED;
        default -> State.UNKNOWN;
      };
      case "ACTIVE" -> State.ACTIVE;
      case "DEPRECATED" -> State.DEPRECATED;
      case "RETIRED" -> State.RETIRED;
      default -> State.UNKNOWN;
    };
  }

  private String version(Map<String,Object> observation) {
    try {
      return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(json.writeValueAsBytes(observation)));
    } catch(NoSuchAlgorithmException | JsonProcessingException e) {
      throw new IllegalStateException("SEM_PROPOSAL_OBSERVATION_INVALID",e);
    }
  }
}

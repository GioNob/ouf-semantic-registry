package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ChangeGovernanceService {
  private final JdbcClient db;private final ObjectMapper json;public ChangeGovernanceService(JdbcClient db,ObjectMapper json){this.db=db;this.json=json;}
  @Transactional public Map<String,Object> notice(UUID change,String decision,String actor){UUID id=db.sql("select ouf_sem.create_change_notice(:c,:d,:a)").param("c",change).param("d",decision).param("a",actor).query(UUID.class).single();return getNotice(id);}
  public Map<String,Object> getNotice(UUID id){return db.sql("select change_notice_id,change_id,semantic_id,from_revision_id,to_revision_id,classification,decision,detected_at,created_by_subject from ouf_sem.semantic_change_notice where change_notice_id=:i").param("i",id).query().singleRow();}
  @Transactional public Map<String,Object> propose(UUID change,List<Map<String,Object>> replacements,String rationale,String actor){UUID id=UUID.randomUUID();db.sql("insert into ouf_sem.semantic_migration_proposal(migration_proposal_id,change_id,status,replacement_refs,rationale,proposed_by_subject) values(:i,:c,'PROPOSED',cast(:r as jsonb),:n,:a)").param("i",id).param("c",change).param("r",write(replacements)).param("n",rationale).param("a",actor).update();return proposal(id);}
  @Transactional public Map<String,Object> decide(UUID proposal,String decision,String actor,String actorType,String authorizationDecisionRef){if(!"HUMAN".equals(actorType))throw new GovernanceService.Forbidden("HUMAN_IDENTITY_REQUIRED");if(!Set.of("APPROVED","REJECTED").contains(decision))throw new IllegalArgumentException("MIGRATION_DECISION_INVALID");int n=db.sql("update ouf_sem.semantic_migration_proposal set status=:s,decided_by_subject=:a,decided_at=transaction_timestamp(),decision_actor_type=:t,decision_authorization_context_ref=:x where migration_proposal_id=:i and status='PROPOSED'").param("s",decision).param("a",actor).param("t",actorType).param("x",authorizationDecisionRef).param("i",proposal).update();if(n!=1)throw new GovernanceService.Conflict("MIGRATION_PROPOSAL_NOT_OPEN");db.sql("insert into ouf_sem.audit_event(event_id,event_type,subject_ref,resource_type,resource_id,detail_json) values(gen_random_uuid(),:e,:a,'MIGRATION_PROPOSAL',:i,jsonb_build_object('actorType',:t,'authorizationDecisionRef',:x))").param("e","SEMANTIC_MIGRATION_"+decision).param("a",actor).param("i",proposal.toString()).param("t",actorType).param("x",authorizationDecisionRef).update();return proposal(proposal);}
  public Map<String,Object> proposal(UUID id){return db.sql("select migration_proposal_id,change_id,status,replacement_refs,rationale,proposed_by_subject,proposed_at,decided_by_subject,decided_at from ouf_sem.semantic_migration_proposal where migration_proposal_id=:i").param("i",id).query().singleRow();}
  private String write(Object value){try{return json.writeValueAsString(value==null?List.of():value);}catch(Exception e){throw new IllegalArgumentException("MIGRATION_REFS_INVALID",e);}}
}

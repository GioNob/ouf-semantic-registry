package it.comune.trieste.ouf.semantic.application;

import java.time.Duration;
import java.util.Map;
import java.util.UUID;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class GovernanceService {
  private final JdbcClient db;
  public GovernanceService(JdbcClient db){this.db=db;}
  private static void human(String type){if(!"HUMAN_USER".equals(type))throw new Forbidden("HUMAN_IDENTITY_REQUIRED");}

  @Transactional public Map<String,Object> challenge(UUID revision,String hash,Duration ttl,String actor,String type){
    human(type);UUID id=UUID.randomUUID();
    int n=db.sql("update ouf_sem.artifact_revision set lifecycle_status='UNDER_REVIEW',content_hash=:h,row_version=row_version+1 where revision_id=:r and lifecycle_status='DRAFT'").param("h",hash).param("r",revision).update();
    if(n!=1)throw new Conflict("REVISION_NOT_DRAFT");
    db.sql("insert into ouf_sem.approval_challenge(challenge_id,revision_id,target_content_hash,status,expires_at,created_by_subject) values(:i,:r,:h,'OPEN',transaction_timestamp()+cast(:ttl as interval),:a)").param("i",id).param("r",revision).param("h",hash).param("ttl",ttl.toSeconds()+" seconds").param("a",actor).update();
    return Map.of("challengeId",id,"revisionId",revision,"targetContentHash",hash,"status","OPEN");
  }
  @Transactional public Map<String,Object> decide(UUID challenge,String decision,String actor,String type){
    human(type);UUID id=UUID.randomUUID();
    var row=db.sql("select target_content_hash from ouf_sem.approval_challenge where challenge_id=:i and status='OPEN' and expires_at>transaction_timestamp() for update").param("i",challenge).query().optionalValue();
    if(row.isEmpty())throw new Conflict("APPROVAL_CHALLENGE_NOT_OPEN");
    db.sql("insert into ouf_sem.approval_decision(decision_id,challenge_id,decision,target_content_hash,decided_by_subject) values(:i,:c,:d,:h,:a)").param("i",id).param("c",challenge).param("d",decision).param("h",row.get()).param("a",actor).update();
    db.sql("update ouf_sem.approval_challenge set status=:d where challenge_id=:c").param("d",decision).param("c",challenge).update();
    return Map.of("decisionId",id,"challengeId",challenge,"decision",decision);
  }
  @Transactional public Map<String,Object> publish(UUID revision,UUID decision,String key,String hash,String actor,String type,String correlation){
    human(type);UUID set=db.sql("select ouf_sem.publish_revision(:r,:d,:k,:h,:a,:c)").param("r",revision).param("d",decision).param("k",key).param("h",hash).param("a",actor).param("c",correlation).query(UUID.class).single();
    return Map.of("publicationSetId",set,"status","PUBLISHED","manifestHash",hash);
  }
  public static class Forbidden extends RuntimeException{public Forbidden(String m){super(m);}}
  public static class Conflict extends RuntimeException{public Conflict(String m){super(m);}}
}

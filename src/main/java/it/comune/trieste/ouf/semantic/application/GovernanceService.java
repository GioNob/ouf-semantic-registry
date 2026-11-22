package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.api.ProposalCommandApi.SourceColumn;
import java.time.Duration;
import java.util.*;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class GovernanceService {
  private final JdbcClient db;private final ObjectMapper json;private final String thsOrigin;
  public GovernanceService(JdbcClient db,ObjectMapper json,@org.springframework.beans.factory.annotation.Value("${ouf.authorization.ths.public-origin:}") String origin){
    this.db=db;this.json=json;this.thsOrigin=origin.replaceAll("/+$", "");
    if(!thsOrigin.isBlank()) {
      var uri=java.net.URI.create(thsOrigin);
      if(!"https".equals(uri.getScheme())||uri.getHost()==null||uri.getUserInfo()!=null||uri.getQuery()!=null||uri.getFragment()!=null||!uri.getPath().isEmpty())
        throw new IllegalArgumentException("SEM_THS_PUBLIC_ORIGIN_INVALID");
    }
  }
  private static void human(String type){if(!"HUMAN".equals(type))throw new Forbidden("HUMAN_IDENTITY_REQUIRED");}

  @Transactional public Map<String,Object> challenge(UUID revision,String hash,Duration ttl,String actor,String type,String correlation) {
    UUID id=UUID.randomUUID();
    try {
      int changed=db.sql("""
          update ouf_sem.artifact_revision set lifecycle_status='UNDER_REVIEW',content_hash=:h
          where revision_id=:r and lifecycle_status='DRAFT'
          """).param("h",hash).param("r",revision).update();
      if(changed!=1) throw new Conflict("REVISION_NOT_DRAFT");
    } catch(org.springframework.dao.DataAccessException e) {
      if(e.getMostSpecificCause() instanceof java.sql.SQLException sql && "P0841".equals(sql.getSQLState()))
        throw new Conflict("CURRENT_GREEN_VALIDATION_REQUIRED");
      throw e;
    }
    db.sql("""
        insert into ouf_sem.approval_challenge(challenge_id,revision_id,target_content_hash,status,expires_at,created_by_subject)
        values(:i,:r,:h,'OPEN',transaction_timestamp()+cast(:ttl as interval),:a)
        """).param("i",id).param("r",revision).param("h",hash).param("ttl",ttl.toSeconds()+" seconds").param("a",actor).update();
    audit("SEMANTIC_APPROVAL_CHALLENGE_CREATED",actor,type,"APPROVAL_CHALLENGE",id.toString(),correlation,
        Map.of("revisionId",revision,"contentHash",hash));
    var out=new LinkedHashMap<>(card(id,false));
    out.put("challengeId",id);
    out.put("revisionId",revision);
    out.put("targetContentHash",hash);
    out.put("trustedApprovalRef","ths://semantic-approval-challenges/"+id);
    return out;
  }
  boolean expireReview(UUID revision,long expectedVersion,String actor) {
    return db.sql("select ouf_sem.expire_review(:r,:v,:a)").param("r",revision)
        .param("v",expectedVersion).param("a",actor).query(Boolean.class).single();
  }
  @Transactional public Map<String,Object> decide(UUID challenge,String decision,String actor,String type,String authorizationDecisionRef,String correlation){
    human(type);
    if(!Set.of("APPROVED","REJECTED").contains(decision))throw new IllegalArgumentException("APPROVAL_DECISION_INVALID");
    // Same lock order as expiry. Sample the clock after acquiring the revision fence.
    var revision=db.sql("""
        select r.revision_id from ouf_sem.artifact_revision r join ouf_sem.approval_challenge c using(revision_id)
        where c.challenge_id=:c and r.lifecycle_status='UNDER_REVIEW' for update of r
        """).param("c",challenge).query(UUID.class).optional().orElseThrow(()->new Conflict("APPROVAL_CHALLENGE_NOT_OPEN"));
    var row=db.sql("""
        with instant as materialized (select clock_timestamp() as decided_at)
        update ouf_sem.approval_challenge set status=:d from instant
        where challenge_id=:c and status='OPEN' and expires_at>instant.decided_at
        returning target_content_hash,instant.decided_at
        """).param("c",challenge).param("d",decision).query().listOfRows().stream().findFirst()
        .orElseThrow(()->new Conflict("APPROVAL_CHALLENGE_NOT_OPEN"));
    UUID id=UUID.randomUUID();
    db.sql("""
        insert into ouf_sem.approval_decision(decision_id,challenge_id,decision,target_content_hash,decided_by_subject,
          actor_type,authorization_context_ref,decided_at) values(:i,:c,:d,:h,:a,:t,:x,:at)
        """).param("i",id).param("c",challenge).param("d",decision).param("h",row.get("target_content_hash"))
        .param("a",actor).param("t",type).param("x",authorizationDecisionRef).param("at",row.get("decided_at")).update();
    if("REJECTED".equals(decision))db.sql("update ouf_sem.artifact_revision set lifecycle_status='DRAFT',row_version=row_version+1 where revision_id=:r")
        .param("r",revision).update();
    audit("SEMANTIC_"+decision,actor,type,"APPROVAL_CHALLENGE",challenge.toString(),correlation,
        Map.of("decisionId",id,"revisionId",revision,"contentHash",row.get("target_content_hash"),"authorizationDecisionRef",authorizationDecisionRef));
    return Map.of("decisionId",id,"challengeId",challenge,"decision",decision);
  }
  @Transactional public Map<String,Object> publish(UUID revision,UUID decision,String key,String hash,String actor,String type,String correlation) {
    human(type);
    if(revision==null||decision==null||hash==null)throw new IllegalArgumentException("PUBLICATION_INTENT_REQUIRED");
    UUID set;
    try {
      set=db.sql("select ouf_sem.publish_revision(:r,:d,:k,:h,:a,:c)").param("r",revision).param("d",decision)
          .param("k",key).param("h",hash).param("a",actor).param("c",correlation).query(UUID.class).single();
    } catch(org.springframework.dao.DataAccessException e) {
      if(e.getMostSpecificCause() instanceof java.sql.SQLException sql) {
        if("P1501".equals(sql.getSQLState()))throw new Conflict("PUBLICATION_IDEMPOTENCY_CONFLICT");
        if("P1502".equals(sql.getSQLState()))throw new Conflict("PUBLICATION_RECONCILIATION_REQUIRED");
      }
      throw e;
    }
    String manifest=db.sql("select checksum from ouf_sem.semantic_publication_set where publication_set_id=:s")
        .param("s",set).query(String.class).single();
    return Map.of("publicationSetId",set,"status","PUBLISHED","manifestHash",manifest);
  }
  @Transactional public Map<String,Object> lifecycle(UUID revision,String target,String actor,String type,String authorizationDecisionRef,String correlation){human(type);String state=db.sql("select ouf_sem.govern_revision_lifecycle(:r,:s,:a,:x,:c)").param("r",revision).param("s",target).param("a",actor).param("x",authorizationDecisionRef).param("c",correlation).query(String.class).single();return Map.of("revisionId",revision,"status",state);}
  public UUID retiredRevision(UUID artifact){return db.sql("select revision_id from ouf_sem.artifact_revision where artifact_id=:a and lifecycle_status='DEPRECATED' order by revision_no desc limit 1").param("a",artifact).query(UUID.class).list().stream().findFirst().orElseThrow(()->new Conflict("DEPRECATED_REVISION_NOT_FOUND"));}
  public Map<String,Object> card(UUID challenge) {
    return card(challenge,true);
  }
  private Map<String,Object> card(UUID challenge,boolean includeValueMapDetails) {
    Map<String,Object> row=db.sql("select c.challenge_id,c.revision_id,c.target_content_hash,case when c.status='OPEN' and c.expires_at<=clock_timestamp() then 'EXPIRED' else c.status end status,c.expires_at,c.created_at,a.artifact_id,a.semantic_id,a.artifact_type,a.namespace,a.local_name,a.owner_ref,a.authority_ref,r.revision_no,r.semantic_version,r.row_version,r.lifecycle_status revision_status,r.label_json::text label_json,r.description_json::text description_json,r.definition_json::text definition_json from ouf_sem.approval_challenge c join ouf_sem.artifact_revision r on r.revision_id=c.revision_id join ouf_sem.semantic_artifact a on a.artifact_id=r.artifact_id where c.challenge_id=:i")
        .param("i",challenge).query().listOfRows().stream().findFirst().orElseThrow(()->new NoSuchElementException("APPROVAL_CHALLENGE_NOT_FOUND"));
    Map<String,Object> out=new LinkedHashMap<>(row);
    for(String field:List.of("label_json","description_json","definition_json"))try{out.put(field,json.readValue(String.valueOf(row.get(field)),Object.class));}catch(Exception e){throw new IllegalStateException("SEMANTIC_CARD_DECODE_FAILED",e);}
    if(out.get("definition_json") instanceof Map<?,?> definition && definition.containsKey("adoptionProvenance") && db.sql(
        "select exists(select 1 from ouf_sem.revision_adoption where revision_id=:r)")
        .param("r",row.get("revision_id")).query(Boolean.class).single()) {
      out.put("adoptionProvenance",definition.get("adoptionProvenance"));
    }
    boolean valueMap="VALUE_MAP".equals(row.get("artifact_type"));
    if (valueMap && !includeValueMapDetails) out.remove("definition_json");
    if ("DATATYPE".equals(row.get("artifact_type")) || (valueMap && includeValueMapDetails)) {
      var prior=db.sql("""
          select jsonb_build_object('semantic_version',semantic_version,'definition_json',definition_json,
            'label_json',label_json,'description_json',description_json)::text
          from ouf_sem.artifact_revision where artifact_id=:a and revision_no<:n and published_at is not null
          order by revision_no desc limit 1
          """).param("a",row.get("artifact_id")).param("n",row.get("revision_no")).query(String.class).optional();
      try {
        var previous=prior.isEmpty()?null:json.readTree(prior.get());
        if (valueMap) {
          JsonNode definition=json.valueToTree(out.get("definition_json"));
          String name=ValueMapReviewCard.name(definition,json.valueToTree(out.get("label_json")),row.get("local_name").toString());
          var sourceColumn=db.sql("""
              select field_name,source_id from ouf_sem.value_map_proposal_source where revision_id=:r
              """).param("r",row.get("revision_id"))
              .query((rs,n) -> new SourceColumn(rs.getString("field_name"),rs.getString("source_id")))
              .optional().orElse(null);
          out.put("valueMapReview",ValueMapReviewCard.build(name,definition,valueMapLabels(definition),
              sourceColumn,previous==null?null:previous.path("definition_json")));
        } else {
          var review=DatatypeReviewCard.build(json.valueToTree(out),previous);
          out.put("datatypeReview",review);
          out.put("validationFindings",review.get("avvisi"));
        }
      } catch(com.fasterxml.jackson.core.JsonProcessingException invalid) {throw new IllegalStateException("SEMANTIC_CARD_DECODE_FAILED",invalid);}
    }
    var snapshots=db.sql("select media_type,content_hash,content_bytes,statement_count from ouf_sem.revision_interchange_snapshot where revision_id=:r").param("r",row.get("revision_id")).query().listOfRows();
    if(!snapshots.isEmpty()) {
      var snapshot=snapshots.get(0);byte[] bytes=(byte[])snapshot.get("content_bytes");String hash=snapshot.get("content_hash").toString().strip();
      try {if(!HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)).equals(hash))throw new IllegalStateException("SEMANTIC_SNAPSHOT_HASH_MISMATCH");}
      catch(java.security.NoSuchAlgorithmException e){throw new IllegalStateException(e);}
      out.put("interchangeSnapshot",Map.of("mediaType",snapshot.get("media_type"),"contentHash",hash,"statementCount",snapshot.get("statement_count"),"content",new String(bytes,java.nio.charset.StandardCharsets.UTF_8)));
    }
    var decisions=db.sql("select decision_id,decision from ouf_sem.approval_decision where challenge_id=:c").param("c",challenge).query().listOfRows();
    if(decisions.size()>1)throw new IllegalStateException("SEMANTIC_DECISION_CONFLICT");
    if(!decisions.isEmpty()){out.put("approvalDecisionId",decisions.get(0).get("decision_id"));out.put("decision",decisions.get(0).get("decision"));}
    var publications=db.sql("select s.publication_set_id,s.checksum from ouf_sem.semantic_publication_member m join ouf_sem.semantic_publication_set s using(publication_set_id) where m.revision_id=:r and s.status='PUBLISHED' order by s.publication_no desc limit 1")
        .param("r",row.get("revision_id")).query().listOfRows();
    if(!publications.isEmpty()){out.put("publicationSetId",publications.get(0).get("publication_set_id"));out.put("manifestHash",publications.get(0).get("checksum"));}
    out.put("revisionStatus",row.get("revision_status"));out.put("lifecycleStatus",row.get("revision_status"));out.put("trustedApprovalRef","ths://semantic-approval-challenges/"+challenge);
    if(!thsOrigin.isBlank())out.put("reviewUrl",thsOrigin+"/trusted-human/semantic/?challenge="+challenge);
    out.put("humanAuthorityRequired",true);return out;
  }
  private Map<String,String> valueMapLabels(JsonNode definition) {
    var labels=new HashMap<String,String>();
    db.sql("""
        select m.semantic_id, coalesce(nullif(r.label_json->>'it',''),nullif(r.label_json->>'en',''),a.local_name) label
        from ouf_sem.semantic_publication_member m join ouf_sem.artifact_revision r using (revision_id)
        join ouf_sem.semantic_artifact a using (artifact_id)
        where m.publication_set_id=:publication and m.semantic_id in (:ids)
        """).param("publication",ValueMapReviewCard.publicationSetId(definition))
        .param("ids",ValueMapReviewCard.memberIds(definition))
        .query((rs,n) -> Map.entry(rs.getString("semantic_id"),rs.getString("label")))
        .list().forEach(term -> labels.put(term.getKey(),term.getValue()));
    return labels;
  }
  private void audit(String event,String actor,String type,String resourceType,String resourceId,String correlation,Object detail){try{Map<String,Object> payload=new LinkedHashMap<>();payload.put("actorType",type);payload.put("detail",detail);db.sql("insert into ouf_sem.audit_event(event_id,event_type,subject_ref,resource_type,resource_id,correlation_id,detail_json) values(:i,:e,:a,:t,:r,:c,cast(:d as jsonb))").param("i",UUID.randomUUID()).param("e",event).param("a",actor).param("t",resourceType).param("r",resourceId).param("c",correlation).param("d",json.writeValueAsString(payload)).update();}catch(RuntimeException e){throw e;}catch(Exception e){throw new IllegalStateException(e);}}
  public static class Forbidden extends RuntimeException{public Forbidden(String m){super(m);}}
  public static class Conflict extends RuntimeException {
    private final String reason;
    public Conflict(String code){this(code,null);}
    public Conflict(String code,String reason){super(code);this.reason=reason;}
    public String reason(){return reason;}
  }
}

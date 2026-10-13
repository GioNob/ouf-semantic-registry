package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.semantic.api.ArtifactApi.CreateArtifact;
import java.time.Duration;
import java.util.*;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Atomic, owner-deduplicated preparation. No approval, publication or retries. */
@Service
public class NativeProposalService {
  private final JdbcClient db;
  private final ObjectMapper json;
  private final ArtifactService artifacts;
  private final ValidationService validation;
  private final GovernanceService governance;
  public NativeProposalService(JdbcClient db,ObjectMapper json,ArtifactService artifacts,
      ValidationService validation,GovernanceService governance) {
    this.db=db;this.json=json;this.artifacts=artifacts;this.validation=validation;this.governance=governance;
  }
  private String encode(Object value){try{return json.writeValueAsString(value);}catch(Exception e){throw new IllegalArgumentException("SEM_PROPOSAL_ENCODING_INVALID");}}
  private Map<String,Object> decode(Object value){try{return json.readValue(value.toString(),new com.fasterxml.jackson.core.type.TypeReference<Map<String,Object>>(){});}catch(Exception e){throw new IllegalStateException("SEM_PROPOSAL_RECEIPT_INVALID");}}
  private Map<String,Object> row(String tenant,String subject,String key,boolean lock) {
    return db.sql("select proposal_id,phase,row_version,result_json::text result_json from ouf_sem.native_proposal where tenant_id=:t and subject_id=:s and proposal_key=:k"+(lock?" for update":""))
      .param("t",tenant).param("s",subject).param("k",key).query().listOfRows().stream().findFirst()
      .orElseThrow(()->new NoSuchElementException("SEM_PROPOSAL_NOT_FOUND"));
  }
  public Map<String,Object> read(String tenant,String subject,String key){return decode(row(tenant,subject,key,false).get("result_json"));}
  @Transactional public Map<String,Object> create(String tenant,String subject,String type,String key,List<CreateArtifact> commands,String correlation) {
    if(commands==null||commands.isEmpty()||commands.size()>21)throw new IllegalArgumentException("SEM_PROPOSAL_SIZE_INVALID");
    var seen=new HashSet<String>();
    for(var c:commands) {
      if(c==null||!Set.of("CLASS","PROPERTY","RELATIONSHIP","VOCABULARY","CONCEPT","ONTOLOGY").contains(String.valueOf(c.artifactType()))
          ||!seen.add(c.semanticId())||c.semanticId()==null||c.namespace()==null||c.localName()==null
          ||!c.semanticId().equals(c.namespace()+c.localName())||c.ownerRef()==null||c.ownerRef().isBlank()
          ||c.authorityRef()==null||c.authorityRef().isBlank()||c.semanticVersion()==null
          ||!c.semanticVersion().matches("[0-9]+\\.[0-9]+\\.[0-9]+(?:-[A-Za-z0-9.-]+)?(?:\\+[A-Za-z0-9.-]+)?"))
        throw new IllegalArgumentException("SEM_NATIVE_COMMAND_INVALID");
    }
    UUID id=UUID.randomUUID();String intent=encode(commands);
    int inserted=db.sql("insert into ouf_sem.native_proposal(proposal_id,tenant_id,subject_id,proposal_key,commands,phase,result_json) values(:i,:t,:s,:k,cast(:c as jsonb),'DRAFT','{}') on conflict(tenant_id,subject_id,proposal_key) do nothing")
      .param("i",id).param("t",tenant).param("s",subject).param("k",key).param("c",intent).update();
    var saved=row(tenant,subject,key,true);
    boolean same=db.sql("select commands=cast(:c as jsonb) from ouf_sem.native_proposal where proposal_id=:i").param("c",intent).param("i",saved.get("proposal_id")).query(Boolean.class).single();
    if(!same)throw new ArtifactService.Conflict("SEM_PROPOSAL_INTENT_CONFLICT");
    if(inserted==0)return decode(saved.get("result_json"));
    var revisions=new ArrayList<Map<String,Object>>();
    for(var c:commands)revisions.add(artifacts.create(c,subject,type,correlation));
    var result=new LinkedHashMap<String,Object>();
    result.put("proposalId",id);result.put("proposalKey",key);result.put("phase","DRAFT");
    result.put("version",0);result.put("revisions",revisions);result.put("humanAuthorityRequired",true);
    result.put("published",false);
    save(id,"DRAFT",0,result);return result;
  }
  @SuppressWarnings("unchecked") private List<Map<String,Object>> revisions(Map<String,Object> result){return (List<Map<String,Object>>)result.get("revisions");}
  private void lockUnedited(List<Map<String,Object>> revisions,String state) {
    // One fixed order per immutable proposal. Direct editor takes the same row locks.
    for(var item:revisions) {
      UUID id=UUID.fromString(item.get("revisionId").toString());
      var r=db.sql("select row_version,lifecycle_status from ouf_sem.artifact_revision where revision_id=:r for update").param("r",id).query().singleRow();
      if(((Number)r.get("row_version")).longValue()!=0||!state.equals(r.get("lifecycle_status")))
        throw new ArtifactService.Conflict("SEM_PROPOSAL_REVISION_DRIFT");
    }
  }
  @Transactional public Map<String,Object> validate(String tenant,String subject,String key,long expected) {
    var row=row(tenant,subject,key,true);var result=decode(row.get("result_json"));
    if(!"DRAFT".equals(row.get("phase")))return result;
    if(((Number)row.get("row_version")).longValue()!=expected)throw new ArtifactService.Conflict("SEM_PROPOSAL_VERSION_CONFLICT");
    lockUnedited(revisions(result),"DRAFT");
    var runs=new ArrayList<Map<String,Object>>();boolean pass=true;
    for(var r:revisions(result)) {
      var run=validation.validate(UUID.fromString(r.get("revisionId").toString()),subject);
      pass&="PASS".equals(run.get("status"))&&((Number)run.get("error_count")).intValue()==0;
      runs.add(run);
    }
    result.put("validations",runs);result.put("validationPassed",pass);result.put("phase","VALIDATED");result.put("version",1);
    save((UUID)row.get("proposal_id"),"VALIDATED",1,result);return result;
  }
  @SuppressWarnings("unchecked") @Transactional public Map<String,Object> requestReview(String tenant,String subject,String type,String key,long expected,String correlation) {
    var row=row(tenant,subject,key,true);var result=decode(row.get("result_json"));
    if("UNDER_REVIEW".equals(row.get("phase")))return result; // same receipts, even after expiry; no silent renewal
    if(!"VALIDATED".equals(row.get("phase"))||!Boolean.TRUE.equals(result.get("validationPassed")))throw new ArtifactService.Conflict("SEM_PROPOSAL_VALIDATION_REQUIRED");
    if(((Number)row.get("row_version")).longValue()!=expected)throw new ArtifactService.Conflict("SEM_PROPOSAL_VERSION_CONFLICT");
    lockUnedited(revisions(result),"DRAFT");
    var challenges=new ArrayList<Map<String,Object>>();
    for(var run:(List<Map<String,Object>>)result.get("validations")) {
      UUID revision=UUID.fromString(run.get("revision_id").toString());String hash=run.get("validated_content_hash").toString();
      var card=governance.challenge(revision,hash,Duration.ofMinutes(15),subject,type,correlation);
      var receipt=new LinkedHashMap<String,Object>();
      for(String field:List.of("challengeId","revisionId","targetContentHash","trustedApprovalRef","expires_at"))receipt.put(field,card.get(field));
      challenges.add(receipt);
    }
    result.put("challenges",challenges);result.put("phase","UNDER_REVIEW");result.put("version",2);
    save((UUID)row.get("proposal_id"),"UNDER_REVIEW",2,result);return result;
  }
  private void save(UUID id,String phase,long version,Map<String,Object> result) {
    db.sql("update ouf_sem.native_proposal set phase=:p,row_version=:v,result_json=cast(:r as jsonb),updated_at=transaction_timestamp() where proposal_id=:i")
      .param("p",phase).param("v",version).param("r",encode(result)).param("i",id).update();
  }
}

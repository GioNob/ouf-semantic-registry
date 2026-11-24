package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.authorization.PrincipalContext;
import it.comune.trieste.ouf.semantic.api.SemanticDiscoveryDelegation;
import it.comune.trieste.ouf.semantic.api.ArtifactApi.CreateArtifact;
import it.comune.trieste.ouf.semantic.api.ProposalCommandApi.SourceColumn;
import java.time.Duration;
import java.util.*;
import java.util.function.Supplier;
import java.util.function.UnaryOperator;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Fixed owner commands. Receipts are scoped to authenticated tenant and principal. */
@Service
public class ProposalCommandService {
  private final JdbcClient db;
  private final ObjectMapper json;
  private final ArtifactService artifacts;
  private final ValidationService validation;
  private final GovernanceService governance;
  private final InterchangeService interchange;
  private final CandidateAdoptionService adoption;
  public ProposalCommandService(JdbcClient db,ObjectMapper json,ArtifactService artifacts,
      ValidationService validation,GovernanceService governance,InterchangeService interchange,CandidateAdoptionService adoption) {
    this.adoption=adoption;
    this.db=db;this.json=json;this.artifacts=artifacts;this.validation=validation;this.governance=governance;this.interchange=interchange;
  }
  @Transactional(timeout=10)
  public Map<String,Object> adopt(PrincipalContext principal,String key,UUID requestId,UUID candidateId) {
    if(principal.actorType()!=PrincipalContext.ActorType.HUMAN)
      throw new GovernanceService.Forbidden("SEM_HUMAN_REQUIRED");
    String jobSubject=SemanticDiscoveryDelegation.jobSubject(principal,json);
    return execute(principal.tenantId(),principal.subjectId(),key,"ADOPT",
        Map.of("requestId",requestId,"candidateId",candidateId,"jobSubject",jobSubject),
        ()->adoption.adopt(requestId,candidateId,jobSubject,principal.subjectId()),stored->{
          var current=adoption.reference(requestId,candidateId,jobSubject,UUID.fromString((String)stored.get("artifactId")),true);
          current.put("receiptSemantics",stored.get("receiptSemantics"));
          current.put("runtimeAuthorityIssued",false);
          current.put("notReleaseAcceptance",true);
          var projection=decode(encode(current));
          if(!projection.equals(stored))projection.put("receiptSemantics","CURRENT_ADOPTION_REFERENCE");
          return projection;
        });
  }
  @Transactional(timeout=10) public Map<String,Object> createImported(String tenant,String principal,String type,String key,
      CreateArtifact command,String turtle,String mediaType,String correlation) {
    if(!"ONTOLOGY".equals(command.artifactType())||!"text/turtle".equals(mediaType)||turtle==null||turtle.isBlank()
        ||turtle.getBytes(java.nio.charset.StandardCharsets.UTF_8).length>49152
        ||(command.definition()!=null&&!command.definition().isEmpty()))throw new IllegalArgumentException("SEM_PROPOSAL_RDF_SHAPE_INVALID");
    return execute(tenant,principal,key,"CREATE",Map.of("artifact",command,"rdfTurtle",turtle,"mediaType",mediaType),()->{
      // The existing in-memory Turtle parser never resolves imports or fetches URLs.
      var result=interchange.importDraft(command.semanticId(),command.artifactType(),command.namespace(),command.localName(),
          command.ownerRef(),command.authorityRef(),command.semanticVersion(),mediaType,turtle.getBytes(java.nio.charset.StandardCharsets.UTF_8),principal);
      // Bind the immutable RDF digest into the same JSON fingerprint validated/approved by the owner.
      var definition=Map.of("importedSnapshot",Map.of("contentHash",result.get("contentHash"),"mediaType",mediaType,"statementCount",result.get("statementCount")));
      db.sql("update ouf_sem.artifact_revision set label_json=cast(:labels as jsonb),definition_json=cast(:definition as jsonb) where revision_id=:revision and lifecycle_status='DRAFT'")
          .param("labels",encode(command.labels()==null?Map.of():command.labels())).param("definition",encode(definition))
          .param("revision",result.get("revisionId")).update();
      return result;
    });
  }
  @Transactional(timeout=10) public Map<String,Object> create(String tenant,String principal,String type,String key,
      CreateArtifact command,String correlation) {
    return create(tenant,principal,type,key,command,null,correlation);
  }
  @Transactional(timeout=10) public Map<String,Object> create(String tenant,String principal,String type,String key,
      CreateArtifact command,SourceColumn sourceColumn,String correlation) {
    boolean valueMap="VALUE_MAP".equals(command.artifactType());
    if(sourceColumn!=null && !valueMap) throw new IllegalArgumentException("SEM_REQUEST_INVALID");
    Object payload=sourceColumn==null?command:Map.of("artifact",command,"sourceColumn",sourceColumn);
    try {
      return execute(tenant,principal,key,"CREATE",payload,()->{
        var result=artifacts.create(command,principal,type,correlation);
        if(sourceColumn!=null) db.sql("""
            insert into ouf_sem.value_map_proposal_source(revision_id,field_name,source_id) values(:r,:f,:s)
            """).param("r",result.get("revisionId")).param("f",sourceColumn.fieldName())
            .param("s",sourceColumn.sourceId()).update();
        return result;
      });
    } catch (DataAccessException error) {
      throw valueMap?ArtifactService.valueMapError(error):error;
    }
  }
  @Transactional(timeout=10) public Map<String,Object> validate(String tenant,String principal,String key,
      UUID revision,long expectedVersion) {
    return execute(tenant,principal,key,"VALIDATE",Map.of("revisionId",revision,"expectedRowVersion",expectedVersion),()->{
      lockDraft(revision,expectedVersion,principal);
      return validation.validate(revision,principal);
    });
  }
  @Transactional(timeout=10) public Map<String,Object> review(String tenant,String principal,String type,String key,
      UUID revision,long expectedVersion,UUID validationRun,String correlation) {
    return execute(tenant,principal,key,"REVIEW",Map.of("revisionId",revision,
        "expectedRowVersion",expectedVersion,"validationRunId",validationRun),()->{
      Map<String,Object> current=lockDraft(revision,expectedVersion,principal);
      var rows=db.sql("select validated_content_hash from ouf_sem.validation_run where validation_run_id=:v "
          +"and revision_id=:r and validated_row_version=:version and status='PASS' and error_count=0 "
          +"and validated_content_hash=:hash")
          .param("v",validationRun).param("r",revision).param("version",expectedVersion)
          .param("hash",current.get("current_hash")).query().listOfRows();
      if(rows.size()!=1)throw new GovernanceService.Conflict("CURRENT_GREEN_VALIDATION_REQUIRED");
      long version=((Number)current.get("row_version")).longValue();
      UUID currentRun=validationRun;
      if(version!=expectedVersion) {
        var refreshed=validation.validate(revision,principal);
        if(!"PASS".equals(refreshed.get("status")))throw new GovernanceService.Conflict("CURRENT_GREEN_VALIDATION_REQUIRED");
        currentRun=(UUID)refreshed.get("validation_run_id");
      }
      Map<String,Object> out=new LinkedHashMap<>(governance.challenge(revision,
          String.valueOf(current.get("current_hash")),Duration.ofMinutes(15),principal,type,correlation));
      out.put("validationRunId",currentRun);
      out.put("expectedRowVersion",version);
      out.put("humanAuthorityRequired",true);
      return out;
    });
  }
  public Map<String,Object> receipt(String tenant,String principal,String key) {
    validKey(key);
    var rows=db.sql("select operation,result_json::text result from ouf_sem.proposal_command_receipt "
        +"where tenant_id=:t and principal_id=:p and idempotency_key=:k and result_json is not null")
        .param("t",tenant).param("p",principal).param("k",key).query().listOfRows();
    if(rows.size()!=1)throw new NoSuchElementException("PROPOSAL_RECEIPT_NOT_FOUND");
    return Map.of("operation",rows.get(0).get("operation"),"result",decode(rows.get(0).get("result")),"historicalSnapshot",true,"ownerStateMustBeRechecked",true);
  }
  public record ReceiptIdentity(String operation,UUID revisionId) {}
  public ReceiptIdentity receiptIdentity(String tenant,String principal,String key) {
    validKey(key);
    return db.sql("""
        select operation,coalesce(result_json->>'revisionId',result_json->>'revision_id') revision
        from ouf_sem.proposal_command_receipt
        where tenant_id=:t and principal_id=:p and idempotency_key=:k and result_json is not null
        """).param("t",tenant).param("p",principal).param("k",key)
        .query((rs,n)->new ReceiptIdentity(rs.getString("operation"),receiptRevision(rs.getString("revision"))))
        .optional().orElseThrow(()->new NoSuchElementException("PROPOSAL_RECEIPT_NOT_FOUND"));
  }

  public static UUID receiptRevision(Object value) {
    if(value instanceof UUID id)return id;
    if(value instanceof String id && id.length()==36) {
      try { return UUID.fromString(id); }
      catch(IllegalArgumentException historical) { return null; }
    }
    return null;
  }
  private Map<String,Object> lockDraft(UUID revision,long expected,String actor) {
    var rows=db.sql("select row_version,lifecycle_status,encode(public.digest("+
        "convert_to(label_json::text||description_json::text||definition_json::text,'UTF8'),'sha256'),'hex') current_hash "
        +"from ouf_sem.artifact_revision where revision_id=:r for update")
        .param("r",revision).query().listOfRows();
    if(rows.size()!=1)throw new NoSuchElementException("REVISION_NOT_FOUND");
    var row=rows.get(0);
    if(((Number)row.get("row_version")).longValue()!=expected)throw new GovernanceService.Conflict("DRAFT_VERSION_CONFLICT");
    if("DRAFT".equals(row.get("lifecycle_status")))return row;
    if("UNDER_REVIEW".equals(row.get("lifecycle_status"))
        && governance.expireReview(revision,expected,actor)) {
      row.put("row_version",expected+1);
      row.put("lifecycle_status","DRAFT");
      return row;
    }
    throw new GovernanceService.Conflict("DRAFT_VERSION_CONFLICT");
  }
  private Map<String,Object> execute(String tenant,String principal,String key,String operation,Object payload,
      Supplier<Map<String,Object>> effects) {
    return execute(tenant,principal,key,operation,payload,effects,UnaryOperator.identity());
  }
  private Map<String,Object> execute(String tenant,String principal,String key,String operation,Object payload,
      Supplier<Map<String,Object>> effects,UnaryOperator<Map<String,Object>> replay) {
    validKey(key);
    // Unique insert fences concurrent callers; all I/O here is local and transactional.
    String hash=db.sql("select encode(public.digest(convert_to(cast(:p as jsonb)::text,'UTF8'),'sha256'),'hex')")
        .param("p",encode(payload)).query(String.class).single();
    int inserted=db.sql("insert into ouf_sem.proposal_command_receipt(tenant_id,principal_id,idempotency_key,operation,request_hash) "
        +"values(:t,:p,:k,:o,:h) on conflict do nothing")
        .param("t",tenant).param("p",principal).param("k",key).param("o",operation).param("h",hash).update();
    if(inserted==0) {
      var row=db.sql("select operation,request_hash,result_json::text result from ouf_sem.proposal_command_receipt "
          +"where tenant_id=:t and principal_id=:p and idempotency_key=:k")
          .param("t",tenant).param("p",principal).param("k",key).query().singleRow();
      if(!operation.equals(row.get("operation"))||!hash.equals(row.get("request_hash")))
        throw new GovernanceService.Conflict("IDEMPOTENCY_KEY_REUSE");
      if(row.get("result")==null)throw new GovernanceService.Conflict("PROPOSAL_RECONCILE_REQUIRED");
      return replay.apply(decode(row.get("result")));
    }
    Map<String,Object> result=new LinkedHashMap<>(effects.get());
    result.put("receiptSemantics","DURABLE_COMMAND_RESULT_NOT_CURRENT_STATE");
    result.put("runtimeAuthorityIssued",false);
    result.put("notReleaseAcceptance",true);
    String encodedResult=encode(result);
    db.sql("update ouf_sem.proposal_command_receipt set result_json=cast(:r as jsonb) "
        +"where tenant_id=:t and principal_id=:p and idempotency_key=:k and result_json is null")
        .param("r",encodedResult).param("t",tenant).param("p",principal).param("k",key).update();
    return decode(encodedResult);
  }
  private static void validKey(String key) {
    if(key==null||!key.matches("[A-Za-z0-9_:.-]{1,128}"))throw new IllegalArgumentException("PROPOSAL_KEY_INVALID");
  }
  private String encode(Object value) {
    try{return json.writeValueAsString(value);}catch(Exception e){throw new IllegalArgumentException("PROPOSAL_JSON_INVALID",e);}
  }
  @SuppressWarnings("unchecked") private Map<String,Object> decode(Object value) {
    try{return json.readValue(String.valueOf(value),Map.class);}catch(Exception e){throw new IllegalStateException("PROPOSAL_RECEIPT_INVALID",e);}
  }
}

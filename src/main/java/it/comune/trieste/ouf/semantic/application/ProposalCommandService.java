package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.api.ArtifactApi.CreateArtifact;
import java.time.Duration;
import java.util.*;
import java.util.function.Supplier;
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
  public ProposalCommandService(JdbcClient db,ObjectMapper json,ArtifactService artifacts,
      ValidationService validation,GovernanceService governance,InterchangeService interchange) {
    this.db=db;this.json=json;this.artifacts=artifacts;this.validation=validation;this.governance=governance;this.interchange=interchange;
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
    return execute(tenant,principal,key,"CREATE",command,
        ()->artifacts.create(command,principal,type,correlation));
  }
  @Transactional(timeout=10) public Map<String,Object> validate(String tenant,String principal,String key,
      UUID revision,long expectedVersion) {
    return execute(tenant,principal,key,"VALIDATE",Map.of("revisionId",revision,"expectedRowVersion",expectedVersion),()->{
      lockDraft(revision,expectedVersion);
      return validation.validate(revision,principal);
    });
  }
  @Transactional(timeout=10) public Map<String,Object> review(String tenant,String principal,String type,String key,
      UUID revision,long expectedVersion,UUID validationRun,String correlation) {
    return execute(tenant,principal,key,"REVIEW",Map.of("revisionId",revision,
        "expectedRowVersion",expectedVersion,"validationRunId",validationRun),()->{
      Map<String,Object> current=lockDraft(revision,expectedVersion);
      var rows=db.sql("select validated_content_hash from ouf_sem.validation_run where validation_run_id=:v "
          +"and revision_id=:r and validated_row_version=:version and status='PASS' and error_count=0 "
          +"and validated_content_hash=:hash")
          .param("v",validationRun).param("r",revision).param("version",expectedVersion)
          .param("hash",current.get("current_hash")).query().listOfRows();
      if(rows.size()!=1)throw new GovernanceService.Conflict("CURRENT_GREEN_VALIDATION_REQUIRED");
      Map<String,Object> out=new LinkedHashMap<>(governance.challenge(revision,
          String.valueOf(current.get("current_hash")),Duration.ofMinutes(15),principal,type,correlation));
      out.put("validationRunId",validationRun);
      out.put("expectedRowVersion",expectedVersion);
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
  private Map<String,Object> lockDraft(UUID revision,long expected) {
    var rows=db.sql("select row_version,lifecycle_status,encode(public.digest("+
        "(label_json::text||description_json::text||definition_json::text)::bytea,'sha256'),'hex') current_hash "
        +"from ouf_sem.artifact_revision where revision_id=:r for update")
        .param("r",revision).query().listOfRows();
    if(rows.size()!=1)throw new NoSuchElementException("REVISION_NOT_FOUND");
    var row=rows.get(0);
    if(!"DRAFT".equals(row.get("lifecycle_status"))||((Number)row.get("row_version")).longValue()!=expected)
      throw new GovernanceService.Conflict("DRAFT_VERSION_CONFLICT");
    return row;
  }
  private Map<String,Object> execute(String tenant,String principal,String key,String operation,Object payload,
      Supplier<Map<String,Object>> effects) {
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
      return decode(row.get("result"));
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

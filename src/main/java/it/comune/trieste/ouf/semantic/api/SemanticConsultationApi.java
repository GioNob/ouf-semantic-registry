package it.comune.trieste.ouf.semantic.api;

import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.authorization.*;
import it.comune.trieste.ouf.semantic.application.SemanticReadService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.*;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/** Channel-neutral owner adapter for Gateway-authenticated delegated read requests. */
@RestController
@RequestMapping("/api/internal/v1/semantic/consultation")
public class SemanticConsultationApi {
  private final SemanticReadDelegation receipts;
  private final SemanticReadService reads;
  private final ObjectMapper json;
  public SemanticConsultationApi(SemanticReadDelegation receipts,SemanticReadService reads,ObjectMapper json) {
    this.receipts=receipts;this.reads=reads;
    this.json=json.copy().enable(com.fasterxml.jackson.core.JsonParser.Feature.STRICT_DUPLICATE_DETECTION);
  }
  private JsonNode arguments(byte[] raw,HttpServletRequest request,String capability,String operation,String resourceType,Set<String> keys) {
    var principal=receipts.verify(request.getHeader("X-OUF-Semantic-Read-Receipt"),request.getRequestURI(),capability,raw);
    request.setAttribute(ServletAuthorization.TRUSTED_PRINCIPAL,new TrustedPrincipal(principal));
    OwnerAuthorization.bind(request).require(capability,new ResourceContext(resourceType,null,principal.tenantId(),null,Map.of("module","SEMANTIC")));
    try {
      JsonNode e=json.readTree(raw),a=e.required("Arguments");
      if(!capability.equals(e.required("CapabilityID").asText())||!("capability://"+capability).equals(e.required("GatewayBindingRef").asText())
          ||!"semantic".equals(e.required("Owner").asText())||!operation.equals(e.required("OperationClass").asText())||!a.isObject())throw new IllegalArgumentException();
      for(var fields=a.fieldNames();fields.hasNext();)if(!keys.contains(fields.next()))throw new IllegalArgumentException();
      return a;
    }catch(Exception e){throw new IllegalArgumentException("SEM_CONSULTATION_ARGUMENTS_INVALID");}
  }
  @PostMapping("/search") public Object search(@RequestBody byte[] raw,HttpServletRequest request) {
    var a=arguments(raw,request,"ouf.semantic.search","READ","semantic.artifact",Set.of("q","limit","type","namespace","domain","range"));
    int limit=20;if(a.has("limit")){if(!a.get("limit").isIntegralNumber()||!a.get("limit").canConvertToInt())throw new IllegalArgumentException("SEM_SEARCH_LIMIT_INVALID");limit=a.get("limit").intValue();}
    return reads.search(text(a,"q",true),"ACTIVE",limit,text(a,"type",false),text(a,"namespace",false),text(a,"domain",false),text(a,"range",false));
  }
  @PostMapping("/get") public Object get(@RequestBody byte[] raw,HttpServletRequest request) {
    var a=arguments(raw,request,"ouf.semantic.consultation.read","READ","semantic.validation",Set.of("semanticId","revisionId","publicationSetId"));
    return reads.resolve(text(a,"semanticId",true),UUID.fromString(text(a,"revisionId",true)),UUID.fromString(text(a,"publicationSetId",true)));
  }
  private static String text(JsonNode node,String key,boolean required){
    if(!node.has(key)&&!required)return null;
    if(!node.hasNonNull(key)||!node.get(key).isTextual())throw new IllegalArgumentException("SEM_CONSULTATION_ARGUMENTS_INVALID");
    return node.get(key).textValue();
  }
  @ExceptionHandler(SecurityException.class) ResponseEntity<?> denied(){return ResponseEntity.status(403).body(Map.of("code","SEM_READ_RECEIPT_OR_POLICY_DENIED"));}
}

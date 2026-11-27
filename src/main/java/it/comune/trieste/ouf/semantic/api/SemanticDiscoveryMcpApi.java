package it.comune.trieste.ouf.semantic.api;

import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.authorization.*;
import it.comune.trieste.ouf.semantic.application.DiscoveryJobService;
import it.comune.trieste.ouf.semantic.application.DiscoveryService.CandidatePosition;
import jakarta.servlet.http.HttpServletRequest;
import java.time.Instant;
import java.util.*;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/** Delegated discovery jobs only. Adoption uses the proposal command channel. */
@RestController
@RequestMapping("/api/internal/v1/semantic/discovery")
public class SemanticDiscoveryMcpApi {
  private static final int CANDIDATE_PAGE_BYTES=4096; // The remainder of 8 KiB is for the MCP result and navigation.
  private static final String CURSOR_SPACE="A".repeat(DiscoveryCandidateCursor.ENCODED_SIZE);
  private static final int DEFAULT_PAGE_LIMIT=16;
  private static final int MAX_PAGE_LIMIT=64;
  private static final String CANDIDATES="ouf.semantic.discovery.candidates";
  private final SemanticDiscoveryDelegation receipts;
  private final DiscoveryJobService jobs;
  private final ObjectMapper json;
  private final DiscoveryCandidateCursor cursors;
  public SemanticDiscoveryMcpApi(SemanticDiscoveryDelegation receipts,DiscoveryJobService jobs,ObjectMapper json) {
    this.receipts=receipts;this.jobs=jobs;
    this.json=json.copy().enable(com.fasterxml.jackson.core.JsonParser.Feature.STRICT_DUPLICATE_DETECTION);
    this.cursors=new DiscoveryCandidateCursor(receipts);
  }
  private record Input(JsonNode arguments,String actor,PrincipalContext principal) {}
  private Input input(byte[] raw,HttpServletRequest request,String capability,String operation,Set<String> keys) {
    var principal=receipts.verify(request.getHeader("X-OUF-Semantic-Discovery-Receipt"),request.getRequestURI(),capability,raw);
    request.setAttribute(ServletAuthorization.TRUSTED_PRINCIPAL,new TrustedPrincipal(principal));
    if(!CANDIDATES.equals(capability))authorize(request,capability,principal,null);
    try {
      var e=json.readTree(raw);var a=e.required("Arguments");
      if(!capability.equals(e.required("CapabilityID").asText())||!("capability://"+capability).equals(e.required("GatewayBindingRef").asText())
          ||!"semantic".equals(e.required("Owner").asText())||!operation.equals(e.required("OperationClass").asText())||!a.isObject())throw new IllegalArgumentException();
      for(var fields=a.fieldNames();fields.hasNext();)if(!keys.contains(fields.next()))throw new IllegalArgumentException();
      // Namespace delegated jobs by trusted issuer, tenant and subject, never caller-supplied identity.
      // Native subject-only job history is preserved and cannot alias this bridge's namespace.
      return new Input(a,SemanticDiscoveryDelegation.jobSubject(principal,json),principal);
    }catch(Exception e){
      if(CANDIDATES.equals(capability))authorize(request,capability,principal,null);
      throw invalid();
    }
  }
  @PostMapping("/request") public Object create(@RequestBody byte[] raw,HttpServletRequest request) {
    var in=input(raw,request,"ouf.semantic.discovery","COMMAND",Set.of("requestedArtifactType","intent","preferredLanguages","idempotencyKey"));
    var a=in.arguments();var langs=a.required("preferredLanguages");
    if(!langs.isArray()||langs.size()>5)throw invalid();
    var languages=new ArrayList<String>();
    for(var language:langs){if(!language.isTextual())throw invalid();languages.add(language.textValue());}
    return jobs.request(text(a,"requestedArtifactType"),text(a,"intent"),languages,in.actor(),text(a,"idempotencyKey"));
  }
  @PostMapping("/status") public Object status(@RequestBody byte[] raw,HttpServletRequest request) {
    var in=input(raw,request,"ouf.semantic.discovery.status","READ",Set.of("requestId"));
    return jobs.status(id(in.arguments()),in.actor());
  }
  @PostMapping("/candidates") public Object candidates(@RequestBody byte[] raw,HttpServletRequest request) {
    var in=input(raw,request,CANDIDATES,"READ",Set.of("requestId","includeState","projection","limit","cursor"));
    var a=in.arguments();
    var includeState=a.get("includeState");
    boolean paged=a.has("limit") || a.has("cursor") || a.has("projection");
    if(!paged)authorize(request,CANDIDATES,in.principal(),null);
    if(includeState!=null && !includeState.isBoolean())throw invalid();
    var id=id(a);
    if(paged)return candidatePage(in,id,request,includeState);
    return includeState!=null && includeState.booleanValue()
        ?jobs.candidatesWithState(id,in.actor()):jobs.candidates(id,in.actor());
  }

  private static AuthorizationPolicy.AuthorizationDecision authorize(HttpServletRequest request,String capability,
      PrincipalContext principal,UUID id) {
    return OwnerAuthorization.bind(request).require(capability,
        new ResourceContext("semantic.DiscoveryApi",id==null?null:id.toString(),principal.tenantId(),null,Map.of("module","SEMANTIC")));
  }

  private Object candidatePage(Input in,UUID id,HttpServletRequest request,JsonNode includeState) {
    var a=in.arguments();
    var principal=in.principal();
    var decision=authorize(request,CANDIDATES,principal,id);
    byte[] binding=serialized(List.of(id,in.actor(),principal.actorType(),principal.servicePrincipalId(),
        principal.audience(),principal.authenticationContextRef(),new TreeSet<>(principal.scopes()),
        new TreeSet<>(principal.claims().externalRoleRefs()),decision.decisionRef(),decision.permittedDetailLevel(),
        new TreeMap<>(decision.resourceScope())));
    var limitNode=a.get("limit");
    if(limitNode!=null && (!limitNode.isIntegralNumber() || !limitNode.canConvertToInt()
        || limitNode.intValue()<1 || limitNode.intValue()>MAX_PAGE_LIMIT))throw invalid();
    int limit=limitNode==null?DEFAULT_PAGE_LIMIT:limitNode.intValue();
    var projection=a.get("projection");
    if(projection!=null && (!projection.isTextual() || !"COMPACT".equals(projection.textValue())))throw invalid();
    Instant now=Instant.now();
    var continuation=a.has("cursor")?cursors.decode(text(a,"cursor"),binding,now):null;
    var options=continuation==null?new DiscoveryCandidateCursor.Options(projection!=null,includeState!=null && includeState.booleanValue())
        :continuation.options();
    if((projection!=null && !options.compact()) ||
        (includeState!=null && includeState.booleanValue()!=options.includeState()))
      throw new IllegalArgumentException("SEM_DISCOVERY_CURSOR_INVALID");
    var page=jobs.candidatePage(id,in.actor(),limit,options.compact(),continuation==null?null:continuation.position());
    var response=new LinkedHashMap<String,Object>();
    var items=new ArrayList<Map<String,Object>>();
    var adoptable=new ArrayList<UUID>();
    response.put("requestId",id);
    response.put("state",page.state());
    response.put("candidateCount",page.candidateCount());
    response.put("candidates",items);
    if(options.includeState()) {
      response.put("recoveryState",page.recoveryState());
      response.put("adoptableCandidateIds",adoptable);
      boolean poll=switch(page.state()){
        case PENDING,RUNNING -> switch(page.recoveryState()){
          case ACTIVE,RETRY_WAIT -> true;
          default -> false;
        };
        default -> false;
      };
      response.put("allowedActions",List.of(poll?"POLL_DISCOVERY":"NONE"));
      if(poll)response.put("pollAfterSeconds",page.pollAfterSeconds());
    }
    UUID last=null;
    boolean more=false;
    var rows=page.candidates();
    for(int i=0;i<Math.min(limit,rows.size());i++) {
      var item=new LinkedHashMap<>(rows.get(i));
      var candidate=(UUID)item.get(options.compact()?"candidateId":"candidate_id");
      boolean available=options.compact()?"AVAILABLE".equals(item.get("state")):item.remove("adopted_artifact_id")==null;
      items.add(item);
      if(options.includeState() && available)adoptable.add(candidate);
      more=i+1<rows.size();
      completePage(response,options,adoptable,more?CURSOR_SPACE:null);
      if(serialized(response).length>CANDIDATE_PAGE_BYTES) {
        items.removeLast();
        if(options.includeState() && available)adoptable.removeLast();
        if(items.isEmpty())throw new IllegalArgumentException("SEM_DISCOVERY_CANDIDATE_PAGE_ITEM_TOO_LARGE");
        more=true;
        break;
      }
      last=candidate;
    }
    if(more) {
      Instant deadline=continuation==null?DiscoveryCandidateCursor.deadline(now,page.evidenceExpiresAt()):continuation.expiresAt();
      String next=cursors.encode(new DiscoveryCandidateCursor.Continuation(new CandidatePosition(page.evidenceVersion(),last),
          options,deadline),binding);
      completePage(response,options,adoptable,next);
    }
    return response;
  }

  private static void completePage(Map<String,Object> response,DiscoveryCandidateCursor.Options options,
      List<UUID> adoptable,String cursor) {
    if(cursor==null)response.remove("nextCursor");
    else response.put("nextCursor",cursor);
    if(options.includeState())response.put("allowedActions",List.of(adoptable.isEmpty()?"NONE":"ADOPT_CANDIDATE"));
  }

  private byte[] serialized(Object value) {
    try {return json.writeValueAsBytes(value);}
    catch(com.fasterxml.jackson.core.JsonProcessingException e){throw new IllegalStateException("SEM_DISCOVERY_PAGE_SERIALIZATION_FAILED",e);}
  }
  private static UUID id(JsonNode a){String value=text(a,"requestId");if(!value.matches("[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"))throw invalid();return UUID.fromString(value);}
  private static String text(JsonNode a,String key){if(!a.hasNonNull(key)||!a.get(key).isTextual())throw invalid();return a.get(key).textValue();}
  private static IllegalArgumentException invalid(){return new IllegalArgumentException("SEM_DISCOVERY_ARGUMENTS_INVALID");}
  @ExceptionHandler(SecurityException.class) ResponseEntity<?> denied(){return ResponseEntity.status(403).body(Map.of("code","SEM_DISCOVERY_RECEIPT_OR_POLICY_DENIED"));}
}

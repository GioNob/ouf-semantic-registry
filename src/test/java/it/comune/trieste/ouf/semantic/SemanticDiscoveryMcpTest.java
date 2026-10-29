package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;
import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.semantic.api.*;
import it.comune.trieste.ouf.semantic.application.DiscoveryJobService;
import it.comune.trieste.ouf.authorization.TestAuthorization;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.mock.web.MockHttpServletRequest;

class SemanticDiscoveryMcpTest {
  final ObjectMapper json=new ObjectMapper();
  final String key="ab".repeat(32),prefix="/api/internal/v1/semantic/discovery/";
  @TempDir Path tmp;
  SemanticDiscoveryDelegation verifier() throws Exception {
    Path file=tmp.resolve("discovery-key");Files.writeString(file,key);
    return new SemanticDiscoveryDelegation(json,file.toString(),"fixture-issuer","fixture-audience","workload");
  }
  byte[] body(String cap,String operation,Map<String,Object> args) throws Exception {
    return json.writeValueAsBytes(Map.of("CapabilityID",cap,"GatewayBindingRef","capability://"+cap,"Owner","semantic","OperationClass",operation,"Arguments",args));
  }
  Map<String,Object> receipt(byte[] body,String cap,String path) throws Exception {
    long now=Instant.now().getEpochSecond();var r=new LinkedHashMap<String,Object>();
    r.put("v",1);r.put("purpose","semantic-discovery-owner");r.put("method","POST");r.put("path",path);
    r.put("bodyHash",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)));r.put("capability",cap);
    r.put("iat",now);r.put("exp",now+30);r.put("issuer","fixture-issuer");r.put("audience","fixture-audience");
    r.put("workload","workload");r.put("subject","reader");r.put("tenant","tenant-a");r.put("acr","fixture-authentication");r.put("roles","");r.put("scope","ouf.semantic.discovery");
    return r;
  }
  String sign(Map<String,Object> r,String domain) throws Exception {
    var b64=Base64.getUrlEncoder().withoutPadding();String payload=b64.encodeToString(json.writeValueAsBytes(r));
    var mac=Mac.getInstance("HmacSHA256");mac.init(new SecretKeySpec(key.getBytes(StandardCharsets.US_ASCII),"HmacSHA256"));
    return payload+"."+b64.encodeToString(mac.doFinal((domain+payload).getBytes(StandardCharsets.US_ASCII)));
  }
  MockHttpServletRequest request(byte[] raw,String cap,String op,Set<String> grants) throws Exception {
    var req=new MockHttpServletRequest("POST",prefix+op);
    req.addHeader("X-OUF-Semantic-Discovery-Receipt",sign(receipt(raw,cap,prefix+op),"ouf-semantic-discovery-owner-v1."));
    TestAuthorization.bind(req,"reader","HUMAN",grants);
    if(!grants.isEmpty()) {
      var now=Instant.now();
      var descriptor=new it.comune.trieste.ouf.authorization.AuthorizationPolicy.CapabilityDescriptor(
        cap,op.equals("request")?"COMMAND":"READ","ouf.semantic.discovery",Set.of(it.comune.trieste.ouf.authorization.PrincipalContext.ActorType.HUMAN));
      var grant=new it.comune.trieste.ouf.authorization.AuthorizationPolicy.Grant(
        "discovery-fixture",cap,"tenant-a","reader",null,null,now.minusSeconds(60),now.plusSeconds(3600));
      var runtime=new it.comune.trieste.ouf.authorization.LocalAuthorization(java.time.Clock.systemUTC(),java.time.Duration.ofHours(1));
      TestAuthorization.install(runtime,new it.comune.trieste.ouf.authorization.AuthorizationPolicy.PolicyBundle(
        "discovery-fixture",1,now,List.of(descriptor),List.of(grant)));
      req.getServletContext().setAttribute(it.comune.trieste.ouf.authorization.ServletAuthorization.RUNTIME,runtime);
    }
    return req;
  }
  @Test void actualGatewayLuaDiscoveryReceiptsAreAcceptedAtJavaOwner() throws Exception {
    String gateway=System.getenv("OUF_DISCOVERY_GATEWAY_PAIRWISE_ROOT");
    org.junit.jupiter.api.Assumptions.assumeTrue(gateway!=null&&!gateway.isBlank());
    Path fixture=tmp.resolve("gateway-discovery.json");
    var builder=new ProcessBuilder("python3",Path.of(gateway,"scripts/export_semantic_discovery_pairwise.py").toString(),"--output",fixture.toString());
    builder.environment().put("PYTHONPATH",gateway);
    var process=builder.redirectErrorStream(true).start();
    assertThat(process.waitFor(10,java.util.concurrent.TimeUnit.SECONDS)).isTrue();
    assertThat(process.exitValue()).isZero();
    Path file=tmp.resolve("gateway-key");Files.writeString(file,key);
    var v=new SemanticDiscoveryDelegation(json,file.toString(),"https://auth.test/realms/ouf","gateway","workload");
    var jobs=mock(DiscoveryJobService.class);var api=new SemanticDiscoveryMcpApi(v,jobs,json);
    for(var f:json.readTree(Files.readString(fixture))) {
      String op=f.required("operation").asText();
      String cap="ouf.semantic.discovery"+(op.equals("request")?"":"."+op);
      byte[] raw=f.required("body").asText().getBytes(StandardCharsets.UTF_8);
      var req=request(raw,cap,op,Set.of(cap));
      req.removeHeader("X-OUF-Semantic-Discovery-Receipt");
      req.addHeader("X-OUF-Semantic-Discovery-Receipt",f.required("receipt").asText());
      switch(op) {
        case "request" -> api.create(raw,req);
        case "status" -> api.status(raw,req);
        case "candidates" -> api.candidates(raw,req);
        default -> throw new IllegalArgumentException("unexpected operation");
      }
    }
    var actor=org.mockito.ArgumentCaptor.forClass(String.class);
    verify(jobs).request(eq("CLASS"),eq("teatro"),eq(List.of("it","en")),actor.capture(),eq("discovery-test-0001"));
    UUID id=UUID.fromString("11111111-1111-4111-8111-111111111111");
    verify(jobs).status(id,actor.getValue());
    verify(jobs).candidates(id,actor.getValue());
  }
  @Test void requestStatusAndCandidatesReuseOneTrustedCallerNamespace() throws Exception {
    var jobs=mock(DiscoveryJobService.class);var api=new SemanticDiscoveryMcpApi(verifier(),jobs,json);
    String cap="ouf.semantic.discovery";UUID id=UUID.randomUUID();
    byte[] raw=body(cap,"COMMAND",Map.of("requestedArtifactType","CLASS","intent","teatro","preferredLanguages",List.of("it","en"),"idempotencyKey","discovery-test-0001"));
    api.create(raw,request(raw,cap,"request",Set.of(cap)));
    var actor=org.mockito.ArgumentCaptor.forClass(String.class);
    verify(jobs).request(eq("CLASS"),eq("teatro"),eq(List.of("it","en")),actor.capture(),eq("discovery-test-0001"));
    assertThat(actor.getValue()).matches("mcp-discovery-v1:[0-9a-f]{64}");
    String statusCap=cap+".status";byte[] status=body(statusCap,"READ",Map.of("requestId",id.toString()));
    api.status(status,request(status,statusCap,"status",Set.of(statusCap)));
    verify(jobs).status(id,actor.getValue());
    String candidatesCap=cap+".candidates";byte[] candidates=body(candidatesCap,"READ",Map.of("requestId",id.toString()));
    api.candidates(candidates,request(candidates,candidatesCap,"candidates",Set.of(candidatesCap)));
    verify(jobs).candidates(id,actor.getValue());
  }
  @Test void ownerPolicyDenialAndUnknownArgumentsNeverCallJobs() throws Exception {
    var jobs=mock(DiscoveryJobService.class);var api=new SemanticDiscoveryMcpApi(verifier(),jobs,json);
    String cap="ouf.semantic.discovery.status";byte[] raw=body(cap,"READ",Map.of("requestId",UUID.randomUUID().toString()));
    var denied=request(raw,cap,"status",Set.of());
    assertThatThrownBy(()->api.status(raw,denied)).isInstanceOf(SecurityException.class);
    byte[] unknown=body(cap,"READ",Map.of("requestId",UUID.randomUUID().toString(),"url","https://example.test"));
    var invalid=request(unknown,cap,"status",Set.of(cap));
    assertThatThrownBy(()->api.status(unknown,invalid)).isInstanceOf(IllegalArgumentException.class);
    byte[] shortId=body(cap,"READ",Map.of("requestId","1-1-1-1-1"));
    var badId=request(shortId,cap,"status",Set.of(cap));
    assertThatThrownBy(()->api.status(shortId,badId)).isInstanceOf(IllegalArgumentException.class);
    verifyNoInteractions(jobs);
  }
  @Test void readReceiptCannotAuthorizeDiscoveryAndReceiptCannotAuthorizePublication() throws Exception {
    var v=verifier();String cap="ouf.semantic.discovery";byte[] raw=body(cap,"COMMAND",Map.of());
    var r=receipt(raw,cap,prefix+"request");
    String good=sign(r,"ouf-semantic-discovery-owner-v1.");
    assertThat(v.verify(good,prefix+"request",cap,raw).tenantId()).isEqualTo("tenant-a");
    r.put("purpose","semantic-read-owner");String read=sign(r,"ouf-semantic-read-owner-v1.");
    assertThatThrownBy(()->v.verify(read,prefix+"request",cap,raw)).isInstanceOf(SecurityException.class);
    assertThatThrownBy(()->v.verify(good,prefix+"request","ouf.semantic.publish",raw)).isInstanceOf(SecurityException.class);
    assertThatThrownBy(()->v.verify(good,prefix+"status",cap,raw)).isInstanceOf(SecurityException.class);
    assertThatThrownBy(()->v.verify(good,prefix+"request",cap,new byte[]{1})).isInstanceOf(SecurityException.class);
    assertThatThrownBy(()->new SemanticDiscoveryDelegation(json,"","","","").verify(good,prefix+"request",cap,raw)).isInstanceOf(SecurityException.class);
  }
}

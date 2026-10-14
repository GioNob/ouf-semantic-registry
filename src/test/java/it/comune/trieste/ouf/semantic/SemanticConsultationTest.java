package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.semantic.api.*;
import it.comune.trieste.ouf.semantic.application.SemanticReadService;
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
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.beans.factory.annotation.Autowired;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
class SemanticConsultationTest {
  @Autowired SemanticReadService reads;
  final ObjectMapper json=new ObjectMapper();
  @TempDir Path tmp;
  final String key="ab".repeat(32),cap="ouf.semantic.search",path="/api/internal/v1/semantic/consultation/search";
  SemanticReadDelegation verifier() throws Exception {
    Path file=tmp.resolve("receipt-key");Files.writeString(file,key);
    return new SemanticReadDelegation(json,file.toString(),"fixture-issuer","fixture-audience","workload");
  }
  byte[] body(Map<String,Object> args) throws Exception {
    return json.writeValueAsBytes(Map.of("CapabilityID",cap,"GatewayBindingRef","capability://"+cap,"Owner","semantic","OperationClass","READ","Arguments",args));
  }
  Map<String,Object> receipt(byte[] body) throws Exception {
    long now=Instant.now().getEpochSecond();
    var r=new LinkedHashMap<String,Object>();
    r.put("v",1);r.put("purpose","semantic-read-owner");r.put("method","POST");r.put("path",path);
    r.put("bodyHash",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)));r.put("capability",cap);
    r.put("iat",now);r.put("exp",now+30);r.put("issuer","fixture-issuer");r.put("audience","fixture-audience");
    r.put("workload","workload");r.put("subject","reader");r.put("tenant","tenant-a");r.put("acr","fixture-authentication");r.put("roles","");r.put("scope",cap);
    return r;
  }
  String sign(Map<String,Object> receipt) throws Exception {
    var b64=Base64.getUrlEncoder().withoutPadding();String payload=b64.encodeToString(json.writeValueAsBytes(receipt));
    var mac=Mac.getInstance("HmacSHA256");mac.init(new SecretKeySpec(key.getBytes(StandardCharsets.US_ASCII),"HmacSHA256"));
    return payload+"."+b64.encodeToString(mac.doFinal(("ouf-semantic-read-owner-v1."+payload).getBytes(StandardCharsets.US_ASCII)));
  }
  MockHttpServletRequest request(String proof,Set<String> grants) {
    var req=new MockHttpServletRequest("POST",path);if(proof!=null)req.addHeader("X-OUF-Semantic-Read-Receipt",proof);
    TestAuthorization.bind(req,"reader","HUMAN",grants);return req;
  }
  @Test void actualGatewayLuaReceiptIsAcceptedByJavaOwner() throws Exception {
    String gateway=System.getenv("OUF_SEMANTIC_GATEWAY_PAIRWISE_ROOT");
    org.junit.jupiter.api.Assumptions.assumeTrue(gateway!=null&&!gateway.isBlank());
    Path fixture=tmp.resolve("gateway-receipt.json");
    var builder=new ProcessBuilder("python3",Path.of(gateway,"scripts/export_semantic_read_pairwise.py").toString(),"--output",fixture.toString());
    builder.environment().put("PYTHONPATH",gateway);
    var process=builder.redirectErrorStream(true).start();
    assertThat(process.waitFor(10,java.util.concurrent.TimeUnit.SECONDS)).isTrue();
    assertThat(process.exitValue()).isZero();
    var f=json.readTree(Files.readString(fixture));
    Path file=tmp.resolve("pairwise-key");Files.writeString(file,key);
    var v=new SemanticReadDelegation(json,file.toString(),"https://auth.test/realms/ouf","gateway","workload");
    byte[] raw=f.required("body").asText().getBytes(StandardCharsets.UTF_8);
    var req=new MockHttpServletRequest("POST",path);
    req.addHeader("X-OUF-Semantic-Read-Receipt",f.required("receipt").asText());
    TestAuthorization.bind(req,"human-a","HUMAN",Set.of(cap));
    assertThat(new SemanticConsultationApi(v,reads,json).search(raw,req)).isInstanceOf(List.class);
  }
  @Test void signedGatewayReadStillRequiresOwnerPolicyAndClosedArguments() throws Exception {
    var v=verifier();var api=new SemanticConsultationApi(v,reads,json);
    byte[] raw=body(Map.of("q","no-match-"+UUID.randomUUID()));String proof=sign(receipt(raw));
    assertThat(api.search(raw,request(proof,Set.of(cap)))).isInstanceOf(List.class);
    assertThatThrownBy(()->api.search(raw,request(proof,Set.of()))).isInstanceOf(SecurityException.class);
    byte[] unknown=body(Map.of("q","x","url","https://example.test"));String unknownProof=sign(receipt(unknown));
    assertThatThrownBy(()->api.search(unknown,request(unknownProof,Set.of(cap)))).isInstanceOf(IllegalArgumentException.class);
    assertThatThrownBy(()->api.search(raw,request(null,Set.of(cap)))).isInstanceOf(SecurityException.class);
    byte[] fractional=body(Map.of("q","x","limit",1.5));String fracProof=sign(receipt(fractional));
    assertThatThrownBy(()->api.search(fractional,request(fracProof,Set.of(cap)))).isInstanceOf(IllegalArgumentException.class);
  }
  @Test void humanGetUsesSeparateCapabilityAndExistingReadScope() throws Exception {
    String humanCap="ouf.semantic.consultation.read",nativeCap="ouf.semantic.read";
    String getPath="/api/internal/v1/semantic/consultation/get";
    byte[] raw=json.writeValueAsBytes(Map.of("CapabilityID",humanCap,"GatewayBindingRef","capability://"+humanCap,
      "Owner","semantic","OperationClass","READ","Arguments",Map.of("semanticId","no-match:"+UUID.randomUUID(),
        "revisionId",UUID.randomUUID().toString(),"publicationSetId",UUID.randomUUID().toString())));
    var r=receipt(raw);r.put("path",getPath);r.put("capability",humanCap);r.put("scope",nativeCap);
    var v=verifier();String proof=sign(r);
    assertThat(v.verify(proof,getPath,humanCap,raw).actorType()).isEqualTo(it.comune.trieste.ouf.authorization.PrincipalContext.ActorType.HUMAN);
    assertThatThrownBy(()->v.verify(proof,getPath,nativeCap,raw)).isInstanceOf(SecurityException.class);
    var api=new SemanticConsultationApi(v,reads,json);
    var req=new MockHttpServletRequest("POST",getPath);req.addHeader("X-OUF-Semantic-Read-Receipt",proof);
    TestAuthorization.bind(req,"reader","HUMAN",Set.of(nativeCap));
    assertThatThrownBy(()->api.get(raw,req)).isInstanceOf(SecurityException.class);
    var allowed=new MockHttpServletRequest("POST",getPath);allowed.addHeader("X-OUF-Semantic-Read-Receipt",proof);
    var now=Instant.now();
    var descriptor=new it.comune.trieste.ouf.authorization.AuthorizationPolicy.CapabilityDescriptor(
      humanCap,"READ",nativeCap,Set.of(it.comune.trieste.ouf.authorization.PrincipalContext.ActorType.HUMAN));
    var grant=new it.comune.trieste.ouf.authorization.AuthorizationPolicy.Grant(
      "human-read",humanCap,"tenant-a","reader",null,null,now.minusSeconds(60),now.plusSeconds(3600));
    var runtime=new it.comune.trieste.ouf.authorization.LocalAuthorization(java.time.Clock.systemUTC(),java.time.Duration.ofHours(1));
    TestAuthorization.install(runtime,
      new it.comune.trieste.ouf.authorization.AuthorizationPolicy.PolicyBundle("human-read-fixture",1,now,List.of(descriptor),List.of(grant)));
    allowed.getServletContext().setAttribute(it.comune.trieste.ouf.authorization.ServletAuthorization.RUNTIME,runtime);
    assertThatThrownBy(()->api.get(raw,allowed)).isInstanceOf(NoSuchElementException.class);
    r.put("scope",humanCap);String wrongScope=sign(r);
    assertThatThrownBy(()->v.verify(wrongScope,getPath,humanCap,raw)).isInstanceOf(SecurityException.class);
  }
  @Test void receiptsFailClosedOnWrongBindingSignatureScopeTenantOrExpiry() throws Exception {
    var v=verifier();byte[] raw=body(Map.of("q","x"));
    String good=sign(receipt(raw));assertThat(v.verify(good,path,cap,raw).tenantId()).isEqualTo("tenant-a");
    assertThatThrownBy(()->v.verify(good,path,cap,body(Map.of("q","changed")))).isInstanceOf(SecurityException.class);
    assertThatThrownBy(()->v.verify(good,path+"/other",cap,raw)).isInstanceOf(SecurityException.class);
    assertThatThrownBy(()->v.verify(good,path,"ouf.semantic.publish",raw)).isInstanceOf(SecurityException.class);
    for(String field:List.of("purpose","issuer","audience","workload","scope")) {
      var r=receipt(raw);r.put(field,"wrong");String p=sign(r);
      assertThatThrownBy(()->v.verify(p,path,cap,raw)).isInstanceOf(SecurityException.class);
    }
    for(String field:List.of("iat","exp")) {
      var r=receipt(raw);r.put(field,field.equals("iat")?Instant.now().getEpochSecond()+100:1);String p=sign(r);
      assertThatThrownBy(()->v.verify(p,path,cap,raw)).isInstanceOf(SecurityException.class);
    }
    var r=receipt(raw);r.put("tenant","another-tenant");String p=sign(r);
    var api=new SemanticConsultationApi(v,reads,json);
    assertThatThrownBy(()->api.search(raw,request(p,Set.of(cap)))).isInstanceOf(SecurityException.class);
    assertThatThrownBy(()->v.verify(good+"a",path,cap,raw)).isInstanceOf(SecurityException.class);
    assertThatThrownBy(()->new SemanticReadDelegation(json,"","","","").verify(good,path,cap,raw)).isInstanceOf(SecurityException.class);
  }
}

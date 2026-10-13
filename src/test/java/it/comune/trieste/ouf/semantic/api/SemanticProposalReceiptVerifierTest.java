package it.comune.trieste.ouf.semantic.api;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.*;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.time.*;
import java.util.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.junit.jupiter.api.Test;

class SemanticProposalReceiptVerifierTest {
  private final ObjectMapper json=new ObjectMapper();
  private final byte[] key="ab".repeat(32).getBytes(StandardCharsets.US_ASCII);
  private final String path="/api/semantic/v1/proposal-commands/create";
  private final byte[] body=("{\"CapabilityID\":\"ouf.semantic.propose\",\"GatewayBindingRef\":\"capability://ouf.semantic.propose\","+
      "\"Owner\":\"semantic\",\"OperationClass\":\"COMMAND\",\"Identity\":{\"PrincipalID\":\"agent\",\"TenantID\":\"tenant-a\",\"ActorType\":\"AI_AGENT\"},"+
      "\"IdempotencyKey\":\"intent-1\",\"Arguments\":{\"commandKey\":\"intent-1\",\"semanticId\":\"ouf:test:Place\"}}").getBytes(StandardCharsets.UTF_8);
  private SemanticProposalReceiptVerifier verifier(){return new SemanticProposalReceiptVerifier(json,key,"https://auth.test/realms/ouf","gateway","workload",Clock.fixed(Instant.ofEpochSecond(1000),ZoneOffset.UTC));}
  private Map<String,Object> receipt()throws Exception{
    Map<String,Object> r=new LinkedHashMap<>();
    r.put("v",1);r.put("purpose","semantic-proposal-owner");r.put("method","POST");r.put("path",path);
    r.put("bodyHash",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)));
    r.put("capability","ouf.semantic.propose");r.put("iat",1000);r.put("exp",1030);
    r.put("issuer","https://auth.test/realms/ouf");r.put("audience","gateway");r.put("workload","workload");
    r.put("subject","agent");r.put("tenant","tenant-a");r.put("actor","AI_AGENT");r.put("acr","1");r.put("roles","ente:staff");
    r.put("scope","mcp.connect ouf.semantic.propose");r.put("idempotencyKey","intent-1");return r;
  }
  private String sign(Map<String,Object> r)throws Exception{
    var enc=Base64.getUrlEncoder().withoutPadding();String payload=enc.encodeToString(json.writeValueAsBytes(r));
    var mac=Mac.getInstance("HmacSHA256");mac.init(new SecretKeySpec(key,"HmacSHA256"));
    return payload+"."+enc.encodeToString(mac.doFinal(("ouf-semantic-proposal-owner-v1."+payload).getBytes(StandardCharsets.US_ASCII)));
  }
  @Test void validReceiptPreservesVerifiedActorAndRemovesOnlyStableKey()throws Exception{
    var result=verifier().verify(sign(receipt()),path,body);
    assertThat(result.principal().context().actorType().name()).isEqualTo("AI_AGENT");
    assertThat(result.principal().context().tenantId()).isEqualTo("tenant-a");
    assertThat(json.readTree(result.arguments()).has("commandKey")).isFalse();
    assertThat(result.idempotencyKey()).isEqualTo("intent-1");
  }
  @Test void signatureBodyPathAndPurposeAreBound()throws Exception{
    String proof=sign(receipt());
    assertThatThrownBy(()->verifier().verify(proof+"x",path,body)).hasMessage("SEM_PROPOSAL_RECEIPT_INVALID");
    assertThatThrownBy(()->verifier().verify(proof,path,new byte[0])).hasMessage("SEM_PROPOSAL_RECEIPT_INVALID");
    assertThatThrownBy(()->verifier().verify(proof,"/api/trusted-human/v1/semantic-approval-challenges/x/publish",body)).hasMessage("SEM_PROPOSAL_RECEIPT_INVALID");
    var r=receipt();r.put("purpose","authorization-proposal-owner");String bad=sign(r);
    assertThatThrownBy(()->verifier().verify(bad,path,body)).hasMessage("SEM_PROPOSAL_RECEIPT_INVALID");
  }
  @Test void expiredFutureAndUnboundedLifetimeAreRejected()throws Exception{
    for(var change:List.of(Map.of("exp",1000),Map.of("iat",1001),Map.of("exp",1031))){
      var r=receipt();r.putAll(change);String proof=sign(r);
      assertThatThrownBy(()->verifier().verify(proof,path,body)).hasMessage("SEM_PROPOSAL_RECEIPT_INVALID");
    }
  }
  @Test void identityIssuerAudienceScopeAndIntentCannotDrift()throws Exception{
    for(var change:List.of(Map.of("subject","admin"),Map.of("tenant","tenant-b"),Map.of("actor","HUMAN"),
        Map.of("issuer","other"),Map.of("audience","other"),Map.of("workload","other"),Map.of("scope","mcp.connect"),Map.of("idempotencyKey","intent-2"))){
      var r=receipt();r.putAll(change);String proof=sign(r);
      assertThatThrownBy(()->verifier().verify(proof,path,body)).hasMessage("SEM_PROPOSAL_RECEIPT_INVALID");
    }
  }
  @Test void unknownFieldsAndDuplicateJsonAreRejected()throws Exception{
    var r=receipt();r.put("approvedBy","admin");String proof=sign(r);
    assertThatThrownBy(()->verifier().verify(proof,path,body)).hasMessage("SEM_PROPOSAL_RECEIPT_INVALID");
    var valid=receipt();String duplicate=new String(json.writeValueAsBytes(valid),StandardCharsets.UTF_8).replace("\"v\":1","\"v\":1,\"v\":1");
    String p=Base64.getUrlEncoder().withoutPadding().encodeToString(duplicate.getBytes(StandardCharsets.UTF_8));
    var mac=Mac.getInstance("HmacSHA256");mac.init(new SecretKeySpec(key,"HmacSHA256"));
    String signed=p+"."+Base64.getUrlEncoder().withoutPadding().encodeToString(mac.doFinal(("ouf-semantic-proposal-owner-v1."+p).getBytes(StandardCharsets.US_ASCII)));
    assertThatThrownBy(()->verifier().verify(signed,path,body)).hasMessage("SEM_PROPOSAL_RECEIPT_INVALID");
  }
  @Test void missingKeyNeverAcceptsReceipt()throws Exception{
    String proof=sign(receipt());var missing=new SemanticProposalReceiptVerifier(json,new byte[0],"issuer","audience","workload",Clock.systemUTC());
    assertThatThrownBy(()->missing.verify(proof,path,body)).hasMessage("SEM_PROPOSAL_RECEIPT_INVALID");
  }
}

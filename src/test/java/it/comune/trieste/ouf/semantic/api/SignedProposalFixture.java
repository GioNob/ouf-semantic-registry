package it.comune.trieste.ouf.semantic.api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.authorization.*;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.time.*;
import java.util.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.*;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

abstract class SignedProposalFixture {
  static final byte[] KEY="ab".repeat(32).getBytes(StandardCharsets.US_ASCII);
  static final String ADOPT="ouf.semantic.discovery.adopt";
  static final String DISCOVERY_SCOPE="ouf.semantic.discovery";
  static final Set<String> CAPS=Set.of("ouf.semantic.proposal.read","ouf.semantic.propose","ouf.semantic.review.prepare","ouf.semantic.approval.request");
  @Autowired MockMvc http;
  @Autowired ObjectMapper json;
  @Autowired org.springframework.jdbc.core.simple.JdbcClient db;
  @TestConfiguration static class Fixture {
    @Bean @Primary SemanticProposalReceiptVerifier fixtureVerifier(ObjectMapper json){return new SemanticProposalReceiptVerifier(json,KEY,"https://auth.test/realms/ouf","gateway","workload",Clock.fixed(Instant.ofEpochSecond(1000),ZoneOffset.UTC));}
  }
  String proof(String path,String cap,String key,byte[] body)throws Exception{
    var r=new SemanticProposalReceiptVerifier.Receipt(1,"semantic-proposal-owner","POST",path,
        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)),cap,1000,1030,
        "https://auth.test/realms/ouf","gateway","workload","agent","tenant-a",path.endsWith("/read")||cap.equals(ADOPT)?"HUMAN":"AI_AGENT","1","",
        String.join(" ",CAPS)+" "+DISCOVERY_SCOPE,key);
    return sign("ouf-semantic-proposal-owner-v1",r);
  }
  String sign(String domain,Object receipt)throws Exception{
    var enc=Base64.getUrlEncoder().withoutPadding();String p=enc.encodeToString(json.writeValueAsBytes(receipt));
    var mac=Mac.getInstance("HmacSHA256");mac.init(new SecretKeySpec(KEY,"HmacSHA256"));
    return p+"."+enc.encodeToString(mac.doFinal((domain+"."+p).getBytes(StandardCharsets.US_ASCII)));
  }
  byte[] envelope(String cap,String op,String key,Map<String,Object> args)throws Exception{
    return json.writeValueAsBytes(Map.of("CapabilityID",cap,"GatewayBindingRef","capability://"+cap,"Owner","semantic","OperationClass",op,
        "IdempotencyKey",key,"Identity",Map.of("PrincipalID","agent","TenantID","tenant-a","ActorType",(op.equals("READ")||cap.equals(ADOPT))?"HUMAN":"AI_AGENT"),"Arguments",args));
  }
  JsonNode send(String mode,String cap,String ownerCap,String key,Map<String,Object> args,Set<String> grants,int expected)throws Exception{
    String path="/api/semantic/v1/proposal-commands/"+mode;byte[] raw=envelope(cap,mode.equals("read")?"READ":"COMMAND",key,args);
    String signature=proof(path,ownerCap,key,raw);
    var response=http.perform(post(path).with(r->{it.comune.trieste.ouf.authorization.TestAuthorization.bind(r,"agent",mode.equals("read")?"HUMAN":"AI_AGENT",grants);return r;})
        .header("X-OUF-Semantic-Proposal-Receipt",signature).header("Idempotency-Key",key).contentType(MediaType.APPLICATION_JSON).content(raw))
        .andExpect(status().is(expected)).andReturn().getResponse();
    return json.readTree(response.getContentAsByteArray());
  }
}

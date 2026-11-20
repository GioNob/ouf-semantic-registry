package it.comune.trieste.ouf.semantic.api;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.authorization.*;
import it.comune.trieste.ouf.authorization.AuthorizationPolicy.*;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.time.*;
import java.util.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.*;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
@AutoConfigureMockMvc
@Import(SemanticProposalReceiptHttpTest.Fixture.class)
class SemanticProposalReceiptHttpTest {
  private static final byte[] KEY="ab".repeat(32).getBytes(StandardCharsets.US_ASCII);
  private static final String ADOPT="ouf.semantic.discovery.adopt";
  private static final String DISCOVERY_SCOPE="ouf.semantic.discovery";
  private static final Set<String> CAPS=Set.of("ouf.semantic.proposal.read","ouf.semantic.propose","ouf.semantic.review.prepare","ouf.semantic.approval.request");
  @Autowired MockMvc http;
  @Autowired ObjectMapper json;
  @Autowired org.springframework.jdbc.core.simple.JdbcClient db;
  @TestConfiguration static class Fixture {
    @Bean @Primary SemanticProposalReceiptVerifier fixtureVerifier(ObjectMapper json){return new SemanticProposalReceiptVerifier(json,KEY,"https://auth.test/realms/ouf","gateway","workload",Clock.fixed(Instant.ofEpochSecond(1000),ZoneOffset.UTC));}
  }
  private String proof(String path,String cap,String key,byte[] body)throws Exception{
    var r=new SemanticProposalReceiptVerifier.Receipt(1,"semantic-proposal-owner","POST",path,
        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)),cap,1000,1030,
        "https://auth.test/realms/ouf","gateway","workload","agent","tenant-a",path.endsWith("/read")||cap.equals(ADOPT)?"HUMAN":"AI_AGENT","1","",
        String.join(" ",CAPS)+" "+DISCOVERY_SCOPE,key);
    var enc=Base64.getUrlEncoder().withoutPadding();String p=enc.encodeToString(json.writeValueAsBytes(r));
    var mac=Mac.getInstance("HmacSHA256");mac.init(new SecretKeySpec(KEY,"HmacSHA256"));
    return p+"."+enc.encodeToString(mac.doFinal(("ouf-semantic-proposal-owner-v1."+p).getBytes(StandardCharsets.US_ASCII)));
  }
  private byte[] envelope(String cap,String op,String key,Map<String,Object> args)throws Exception{
    return json.writeValueAsBytes(Map.of("CapabilityID",cap,"GatewayBindingRef","capability://"+cap,"Owner","semantic","OperationClass",op,
        "IdempotencyKey",key,"Identity",Map.of("PrincipalID","agent","TenantID","tenant-a","ActorType",(op.equals("READ")||cap.equals(ADOPT))?"HUMAN":"AI_AGENT"),"Arguments",args));
  }
  private JsonNode send(String mode,String cap,String ownerCap,String key,Map<String,Object> args,Set<String> grants,int expected)throws Exception{
    String path="/api/semantic/v1/proposal-commands/"+mode;byte[] raw=envelope(cap,mode.equals("read")?"READ":"COMMAND",key,args);
    String signature=proof(path,ownerCap,key,raw);
    var response=http.perform(post(path).with(r->{it.comune.trieste.ouf.authorization.TestAuthorization.bind(r,"agent",mode.equals("read")?"HUMAN":"AI_AGENT",grants);return r;})
        .header("X-OUF-Semantic-Proposal-Receipt",signature).header("Idempotency-Key",key).contentType(MediaType.APPLICATION_JSON).content(raw))
        .andExpect(status().is(expected)).andReturn().getResponse();
    return json.readTree(response.getContentAsByteArray());
  }
  @Test void signedEnvelopeTraversesFilterCurrentOwnerPolicyPostgresqlAndReceiptRead()throws Exception{
    String k=UUID.randomUUID().toString();String semantic="ouf:signed:"+UUID.randomUUID();
    var c=new LinkedHashMap<String,Object>();c.put("semanticId",semantic);c.put("artifactType","CLASS");c.put("namespace","ouf");c.put("localName","SignedPlace"+UUID.randomUUID().toString().replace("-",""));
    c.put("ownerRef","owner");c.put("authorityRef","authority");c.put("semanticVersion","1.0.0");c.put("labels",Map.of("it","Luogo"));c.put("definition",Map.of());c.put("commandKey",k);
    var created=send("create","ouf.semantic.propose","ouf.semantic.propose",k,c,CAPS,200);
    var read=send("read","ouf.semantic.proposal.read","ouf.semantic.proposal.read",UUID.randomUUID().toString(),Map.of("commandKey",k),CAPS,200);
    assertThat(read.get("result").get("revisionId").asText()).isEqualTo(created.get("revisionId").asText());
    send("read","ouf.semantic.proposal.read","ouf.semantic.proposal.read",UUID.randomUUID().toString(),Map.of("commandKey",k),Set.of("ouf.semantic.read","ouf.semantic.propose"),403);
    send("read","ouf.semantic.proposal.read","ouf.semantic.proposal.read",UUID.randomUUID().toString(),Map.of("commandKey",k),Set.of("ouf.semantic.proposal.read"),403);
    send("read","ouf.semantic.proposal.read","ouf.semantic.read",UUID.randomUUID().toString(),Map.of("commandKey",k),CAPS,403);
    send("create","ouf.semantic.propose","ouf.semantic.propose",k,c,Set.of(),403);
    String revision=created.get("revisionId").asText();String vk=UUID.randomUUID().toString();
    var validation=send("validate","ouf.semantic.review.prepare","ouf.semantic.review.prepare",vk,Map.of("commandKey",vk,"revisionId",revision,"expectedRowVersion",0),CAPS,200);
    String rk=UUID.randomUUID().toString();var review=send("review","ouf.semantic.approval.request","ouf.semantic.approval.request",rk,
        Map.of("commandKey",rk,"revisionId",revision,"expectedRowVersion",0,"validationRunId",validation.get("validation_run_id").asText()),CAPS,200);
    assertThat(review.get("trustedApprovalRef").asText()).startsWith("ths://semantic-approval-challenges/");
    assertThat(review.get("humanAuthorityRequired").asBoolean()).isTrue();
  }
  @Test void adoptionRequiresProposalProofDiscoveryScopeHumanDescriptorAndClosedArguments()throws Exception {
    String path="/api/semantic/v1/proposal-commands/adopt";
    String key=UUID.randomUUID().toString();
    UUID job=UUID.randomUUID(),candidate=UUID.randomUUID();
    var args=Map.<String,Object>of("commandKey",key,"requestId",job,"candidateId",candidate);
    byte[] raw=envelope(ADOPT,"COMMAND",key,args);
    var now=Instant.now();
    var human=Set.of(PrincipalContext.ActorType.HUMAN);
    var descriptor=new CapabilityDescriptor(ADOPT,"COMMAND",DISCOVERY_SCOPE,human);
    String readCap="ouf.semantic.proposal.read";
    var read=new CapabilityDescriptor(readCap,"READ",readCap,human);
    var grant=new Grant("grant",ADOPT,"tenant-a","agent",null,null,
        now.minusSeconds(60),now.plusSeconds(600));
    var readGrant=new Grant("read",readCap,"tenant-a","agent",null,null,grant.validFrom(),grant.validUntil());
    var runtime=new LocalAuthorization(Clock.systemUTC(),Duration.ofHours(1));
    TestAuthorization.install(runtime,new PolicyBundle("fixture",1,now,List.of(descriptor,read),List.of(grant,readGrant)));
    http.getDispatcherServlet().getServletContext().setAttribute(ServletAuthorization.RUNTIME,runtime);
    http.perform(post(path).header("X-OUF-Semantic-Proposal-Receipt",proof(path,ADOPT,key,raw))
        .contentType(MediaType.APPLICATION_JSON).content(raw)).andExpect(status().isNotFound())
        .andExpect(jsonPath("$.code").value("SEMANTIC_CANDIDATE_NOT_FOUND"));
    String uri="https://example.org/"+candidate;
    String actor="mcp-discovery-v1:"+HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(
        json.writeValueAsBytes(List.of("https://auth.test/realms/ouf","tenant-a","agent"))));
    db.sql("insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,state,created_by_subject) values(:j,'CLASS','place','SUCCEEDED',:actor)")
        .param("j",job).param("actor",actor).update();
    byte[] bytes=("<"+uri+"> a <http://www.w3.org/2002/07/owl#Class> ; <http://purl.org/dc/terms/publisher> <urn:publisher> .").getBytes(StandardCharsets.UTF_8);
    db.sql("""
        insert into ouf_sem.discovery_candidate(candidate_id,request_id,provider_id,canonical_uri,source_location,artifact_type,
          provider_trust,score,normalized_payload,content_hash,media_type,content_bytes,expires_at)
        values(:c,:r,'TEST',:uri,:uri,'CLASS','HIGH',1,'{}',:hash,'text/turtle',:bytes,now()+interval '1 hour')
        """).param("c",candidate).param("r",job).param("uri",uri).param("bytes",bytes)
        .param("hash",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))).update();
    var signed=post(path).header("X-OUF-Semantic-Proposal-Receipt",proof(path,ADOPT,key,raw))
        .contentType(MediaType.APPLICATION_JSON).content(raw);
    var receipt=json.readTree(http.perform(signed).andExpect(status().isOk()).andReturn().getResponse().getContentAsByteArray());
    assertThat(json.readTree(http.perform(signed).andExpect(status().isOk()).andReturn().getResponse().getContentAsByteArray())).isEqualTo(receipt);
    String readPath="/api/semantic/v1/proposal-commands/read",readKey=UUID.randomUUID().toString();
    byte[] query=envelope(readCap,"READ",readKey,Map.of("commandKey",key));
    var lookup=post(readPath).header("X-OUF-Semantic-Proposal-Receipt",proof(readPath,readCap,readKey,query))
        .contentType(MediaType.APPLICATION_JSON).content(query);
    assertThat(json.readTree(http.perform(lookup).andExpect(status().isOk()).andReturn().getResponse().getContentAsByteArray()).required("result"))
        .isEqualTo(receipt);
    http.perform(post(path).contentType(MediaType.APPLICATION_JSON).content(raw)).andExpect(status().isForbidden());
    var extra=new LinkedHashMap<>(args);extra.put("publisher","caller");
    byte[] changed=envelope(ADOPT,"COMMAND",key,extra);
    http.perform(post(path).header("X-OUF-Semantic-Proposal-Receipt",proof(path,ADOPT,key,changed))
        .contentType(MediaType.APPLICATION_JSON).content(changed)).andExpect(status().isForbidden());
    TestAuthorization.install(runtime,new PolicyBundle("fixture",2,now,List.of(descriptor,read),List.of(readGrant)));
    http.perform(signed).andExpect(status().isForbidden());
    http.perform(lookup).andExpect(status().isForbidden());
  }
  @Test void unsignedBodyAndTamperedReceiptCannotEstablishIdentity()throws Exception{
    String path="/api/semantic/v1/proposal-commands/create";byte[] raw=envelope("ouf.semantic.propose","COMMAND","intent-1",Map.of("commandKey","intent-1"));
    http.perform(post(path).header("X-OUF-Principal-ID","agent").header("Idempotency-Key","intent-1").contentType(MediaType.APPLICATION_JSON).content(raw)).andExpect(status().isForbidden());
    http.perform(post(path).header("X-OUF-Semantic-Proposal-Receipt",proof(path,"ouf.semantic.propose","intent-1",raw)).contentType(MediaType.APPLICATION_JSON).content("{}"))
        .andExpect(status().isForbidden()).andExpect(jsonPath("$.code").value("SEM_PROPOSAL_RECEIPT_INVALID"));
  }
}

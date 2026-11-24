package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import it.comune.trieste.ouf.semantic.api.*;
import it.comune.trieste.ouf.semantic.application.SemanticReadService;
import it.comune.trieste.ouf.semantic.application.PublishedBatchSearch;
import it.comune.trieste.ouf.semantic.application.PublishedBatchSearch.*;
import it.comune.trieste.ouf.authorization.*;
import it.comune.trieste.ouf.authorization.AuthorizationPolicy.*;
import static org.mockito.Mockito.*;
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
import org.springframework.boot.test.context.ConfigDataApplicationContextInitializer;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.runner.WebApplicationContextRunner;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.servlet.config.annotation.DelegatingWebMvcConfiguration;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
class SemanticConsultationTest {
  @Autowired SemanticReadService reads;
  @Autowired PublishedBatchSearch published;
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
  @org.junit.jupiter.api.Nested
  class Batch {
    final String batchCap=cap+".batch", batchPath=path+"-batch";
    final PublishedBatchSearch service=mock(PublishedBatchSearch.class);
    final UUID hidden=UUID.randomUUID();
    LocalAuthorization owner;
    org.springframework.test.web.servlet.MockMvc http;

    @org.junit.jupiter.api.BeforeEach void setup() throws Exception {
      owner=new LocalAuthorization(java.time.Clock.systemUTC(),java.time.Duration.ofHours(1));
      var caps=List.of(descriptor(cap),descriptor(batchCap));
      var now=Instant.now();
      var denyOne=new GrantConstraints("DENY",null,"semantic.artifact",hidden.toString(),Map.of(),Set.of(),Set.of(),null,Set.of(),null);
      TestAuthorization.install(owner,new PolicyBundle("fixture",1,now,caps,List.of(
          grant(cap,null),grant(batchCap,null),grant(cap,denyOne))));
      when(service.search(anyList(),anyInt(),any())).thenAnswer(call -> {
        java.util.function.Predicate<UUID> visible=call.getArgument(2);
        assertThat(visible.test(hidden)).isFalse();
        assertThat(visible.test(new UUID(0,0))).isTrue();
        List<Intent> intents=call.getArgument(0);
        return new Response(PublishedBatchSearch.CONTRACT,intents.stream()
            .map(intent -> new Result(intent.id(),State.NONE,false,List.of())).toList());
      });
      configure(64,8,65536,262144);
    }
    Grant grant(String capability,GrantConstraints constraints) {
      var now=Instant.now();
      return new Grant(UUID.randomUUID().toString(),capability,"tenant-a","reader",null,null,
          now.minusSeconds(60),now.plusSeconds(3600),constraints);
    }
    CapabilityDescriptor descriptor(String capability) {
      return new CapabilityDescriptor(capability,"READ",cap,Set.of(PrincipalContext.ActorType.HUMAN));
    }
    void configure(int intents,int hits,int input,int output) throws Exception {
      configure(service,intents,hits,input,output);
    }
    void configure(PublishedBatchSearch backend,int intents,int hits,int input,int output) throws Exception {
      http=MockMvcBuilders
          .standaloneSetup(new PublishedBatchApi(verifier(),backend,json,intents,hits,input,output))
          .setControllerAdvice(new ProblemHandler()).build();
    }
    WebApplicationContextRunner productionBatchContext() throws Exception {
      var delegation = verifier();
      return new WebApplicationContextRunner()
          .withPropertyValues("spring.config.location=classpath:/application.yml", "spring.profiles.active=")
          .withInitializer(new ConfigDataApplicationContextInitializer())
          .withUserConfiguration(DelegatingWebMvcConfiguration.class, PublishedBatchApi.class, ProblemHandler.class)
          .withBean(SemanticReadDelegation.class, () -> delegation)
          .withBean(PublishedBatchSearch.class, () -> service)
          .withBean(ObjectMapper.class, () -> json);
    }
    byte[] batchWithIntents(int count, int limitPerIntent) throws Exception {
      var root = envelope();
      var args = (ObjectNode) root.get("Arguments");
      args.put("limitPerIntent", limitPerIntent);
      var items = args.withArray("intents");
      var template = (ObjectNode) items.get(0);
      for (int i = 1; i < count; i++) {
        items.add(template.deepCopy().put("intentId", "i" + i));
      }
      return json.writeValueAsBytes(root);
    }
    @Test void productionDefaultsRegisterTheRouteWithoutDev() throws Exception {
      productionBatchContext().run(context -> {
        assertThat(context.getEnvironment().getActiveProfiles()).doesNotContain("dev");
        assertThat(context).hasSingleBean(PublishedBatchApi.class);
        assertThat(context.getBean(PublishedBatchApi.class))
            .hasFieldOrPropertyWithValue("maxIntents", 64)
            .hasFieldOrPropertyWithValue("maxHits", 3)
            .hasFieldOrPropertyWithValue("maxRequestBytes", 65536)
            .hasFieldOrPropertyWithValue("maxResponseBytes", 262144);
        http = MockMvcBuilders.webAppContextSetup(context).build();
        assertThat(json.readTree(expect(batchWithIntents(64, 3), 200, null)).path("results").size()).isEqualTo(64);
      });
    }
    @Test void productionFlagOverrideRemovesTheRoute() throws Exception {
      productionBatchContext().withPropertyValues("OUF_SEM_PUBLISHED_BATCH_ENABLED=false").run(context -> {
        assertThat(context).doesNotHaveBean(PublishedBatchApi.class);
        http = MockMvcBuilders.webAppContextSetup(context).build();
        expect(batchWithIntents(1, 1), 404, null);
      });
    }
    @Test void productionIntentLimitOverrideAppliesToTheRoute() throws Exception {
      productionBatchContext().withPropertyValues("OUF_SEM_PUBLISHED_BATCH_MAX_INTENTS=8").run(context -> {
        assertThat(context).hasSingleBean(PublishedBatchApi.class);
        http = MockMvcBuilders.webAppContextSetup(context).build();
        expect(batchWithIntents(8, 1), 200, null);
        expect(batchWithIntents(9, 1), 400, null);
        verify(service, times(1)).search(anyList(), anyInt(), any());
      });
    }
    com.fasterxml.jackson.databind.node.ObjectNode envelope() {
      var root=json.createObjectNode();
      root.put("Owner","semantic").put("CapabilityID",batchCap).put("GatewayBindingRef","capability://"+batchCap)
          .put("OperationClass","READ");
      var args=root.putObject("Arguments");
      args.put("contract",PublishedBatchSearch.CONTRACT).put("limitPerIntent",1);
      var item=args.putArray("intents").addObject().put("intentId","i0").put("intent"," Straße ").put("requestedArtifactType","CLASS");
      item.putArray("preferredLanguages").add("IT");
      item.putObject("context");
      return root;
    }
    String proof(byte[] body) throws Exception {
      var claims=receipt(body);claims.put("capability",batchCap);claims.put("path",batchPath);
      return sign(claims);
    }
    org.springframework.test.web.servlet.ResultActions post(byte[] bytes,String proof) throws Exception {
      return post(bytes,proof,"identity");
    }
    org.springframework.test.web.servlet.ResultActions post(byte[] bytes,String proof,String encoding) throws Exception {
      return http.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post(batchPath)
          .header("Content-Encoding",encoding)
          .contentType("application/json").content(bytes).header("X-OUF-Semantic-Read-Receipt",proof)
          .with(req->{req.getServletContext().setAttribute(ServletAuthorization.RUNTIME,owner);return req;}));
    }
    byte[] expect(byte[] raw,int status,String code) throws Exception {
      var result=post(raw,proof(raw)).andReturn().getResponse();
      assertThat(result.getStatus()).isEqualTo(status);
      if(code!=null)assertThat(json.readTree(result.getContentAsByteArray()).path("code").textValue()).isEqualTo(code);
      return result.getContentAsByteArray();
    }
    @Test void verifiesWireBytesBindingSearchRightAndTenantPolicy() throws Exception {
      byte[] raw=json.writeValueAsBytes(envelope());
      assertThat(json.readTree(expect(raw,200,null)).path("results").size()).isOne();
      byte[] changed=Arrays.copyOf(raw,raw.length+1);changed[raw.length]=' ';
      var denied=post(changed,proof(raw)).andReturn().getResponse();
      assertThat(denied.getStatus()).isEqualTo(403);
      assertThat(json.readTree(denied.getContentAsByteArray())).isEqualTo(json.createObjectNode()
          .put("code","SEM_READ_RECEIPT_INVALID").put("denial","RECEIPT"));
      assertThat(post(raw,sign(receipt(raw))).andReturn().getResponse().getStatus()).isEqualTo(403);
      var claims=receipt(raw);claims.put("capability",batchCap);claims.put("path",batchPath);claims.put("scope",batchCap);
      assertThat(post(raw,sign(claims)).andReturn().getResponse().getStatus()).isEqualTo(403);
      claims.put("scope",cap);claims.put("tenant","other");
      assertThat(post(raw,sign(claims)).andReturn().getResponse().getStatus()).isEqualTo(403);
      TestAuthorization.install(owner,new PolicyBundle("fixture",2,Instant.now(),List.of(descriptor(cap),descriptor(batchCap)),
          List.of(grant(batchCap,null))));
      assertThat(json.readTree(expect(raw,403,"NO_APPLICABLE_GRANT"))).isEqualTo(json.createObjectNode()
          .put("code","NO_APPLICABLE_GRANT").put("denial","POLICY").put("capability",cap));
      verify(service,times(1)).search(anyList(),anyInt(),any());
    }
    @Test void signedThreeTypeBatchTraversesTheOwnerRouteAndCatalog() throws Exception {
      configure(published,64,3,65536,262144);
      var envelope=envelope();
      var items=(com.fasterxml.jackson.databind.node.ArrayNode)envelope.at("/Arguments/intents");
      var original=(com.fasterxml.jackson.databind.node.ObjectNode)items.get(0);
      original.put("intent","😀".repeat(256));
      original.putObject("context").put("namespace","fixture-"+UUID.randomUUID());
      items.removeAll();
      for (var type:ArtifactType.values())
        items.add(original.deepCopy().put("intentId",type.name()).put("requestedArtifactType",type.name()));
      var response=json.readTree(expect(json.writeValueAsBytes(envelope),200,null));
      assertThat(response.size()).isEqualTo(2);
      assertThat(response.required("contract").textValue()).isEqualTo(PublishedBatchSearch.CONTRACT);
      var results=response.required("results");
      assertThat(results.size()).isEqualTo(3);
      for (int i=0;i<3;i++) {
        var expected=json.createObjectNode().put("intentId",ArtifactType.values()[i].name()).put("state","NONE").put("hasMore",false);
        expected.putArray("hits");
        assertThat(results.get(i)).isEqualTo(expected);
      }
    }
    @Test void rejectsClosedShapeViolationsBeforeCatalogAccess() throws Exception {
      String raw=json.writeValueAsString(envelope());
      String item=json.writeValueAsString(envelope().at("/Arguments/intents/0"));
      for(String invalid:List.of(raw+"{}",raw.replace("\"Arguments\":{","\"Arguments\":{\"extra\":true,"),
          raw.replace("\"intentId\":","\"intentId\":\"other\",\"intentId\":"),
          raw.replace("\"i0\"","\"bad id\""),raw.replace("\"i0\"","null"),
          raw.replace(item,item+","+item),raw.replace(item,""),
          raw.replace("\"CLASS\"","\"ONTOLOGY\""),raw.replace("\"CLASS\"","null"),
          raw.replace("\"context\":{}","\"other\":{}"),raw.replace("\"context\":{}","\"context\":{\"range\":null}"),
          raw.replace("\"context\":{}","\"context\":{\"namespace\":\"\"}"),
          raw.replace("\"context\":{}","\"context\":{\"source\":\"x\"}"),
          raw.replace("\"IT\"","\"it\",\"IT\""),raw.replace("\"IT\"","\"it_IT\""),raw.replace("\"IT\"",""),
          raw.replace("\"IT\"","\"it\",\"en\",\"fr\",\"de\",\"es\",\"pt\""),
          raw.replace(" Straße ","\u00a0"),raw.replace(" Straße ","a".repeat(257)),raw.replace(" Straße ","ß".repeat(129)),
          raw.replace("\"limitPerIntent\":1","\"limitPerIntent\":1.0"),raw.replace("\"limitPerIntent\":1","\"limitPerIntent\":\"1\""),
          raw.replace("\"limitPerIntent\":1","\"limitPerIntent\":9"),raw.replace("published-batch.v1","published-batch.v2"),
          raw.replace("\"Owner\":\"semantic\"","\"Owner\":\"other\""),
          raw.replace("\"Arguments\":","\"MaxResultBytes\":0,\"Arguments\":"))) {
        expect(invalid.getBytes(StandardCharsets.UTF_8),400,"SEM_BATCH_ARGUMENTS_INVALID");
      }
      expect(raw.getBytes(StandardCharsets.UTF_16LE),400,"SEM_BATCH_ARGUMENTS_INVALID");
      verifyNoInteractions(service);
    }
    @Test void boundsBothWireBodiesAndHonorsNegotiationAtTheExactBoundary() throws Exception {
      var envelope=envelope();
      byte[] raw=json.writeValueAsBytes(envelope);
      byte[] response=expect(raw,200,null);
      configure(1,1,raw.length,response.length);
      assertThat(expect(raw,200,null)).isEqualTo(response);
      configure(1,1,raw.length-1,response.length);
      expect(raw,413,"SEM_BATCH_REQUEST_TOO_LARGE");
      configure(1,1,65536,response.length-1);
      expect(raw,422,"SEM_BATCH_RESULT_TOO_LARGE");
      configure(1,1,65536,262144);
      envelope.put("MaxResultBytes",response.length-1);
      expect(json.writeValueAsBytes(envelope),422,"SEM_BATCH_RESULT_TOO_LARGE");
      envelope.put("MaxResultBytes",response.length);
      assertThat(expect(json.writeValueAsBytes(envelope),200,null)).isEqualTo(response);
      var items=(com.fasterxml.jackson.databind.node.ArrayNode)envelope.at("/Arguments/intents");
      items.add((JsonNode)items.get(0).deepCopy());
      ((com.fasterxml.jackson.databind.node.ObjectNode)items.get(1)).put("intentId","i1");
      expect(json.writeValueAsBytes(envelope),400,"SEM_BATCH_ARGUMENTS_INVALID");
      for(int[] limits:List.of(new int[]{65,1,1,1},new int[]{1,0,1,1},new int[]{1,9,1,1},
          new int[]{1,1,65537,1},new int[]{1,1,1,262145}))
        assertThatThrownBy(()->configure(limits[0],limits[1],limits[2],limits[3])).hasMessage("SEM_BATCH_CONFIG_INVALID");
    }
    @Test void onlyExplicitDatabasePressureAndOutageReturnTransientCodes() throws Exception {
      byte[] raw=json.writeValueAsBytes(envelope());
      for(String state:List.of("53300","57P03")) {
        doThrow(new org.springframework.jdbc.CannotGetJdbcConnectionException("fixture",new java.sql.SQLException("fixture",state)))
            .when(service).search(anyList(),anyInt(),any());
        boolean limited=state.equals("53300");
        expect(raw,limited?429:503,limited?"SEM_BATCH_RATE_LIMITED":"SEM_BATCH_UNAVAILABLE");
      }
    }
    @Test void gzipUsesDecodedEnvelopeSizeAndAuthenticatesExactForwardedBytes() throws Exception {
      String padded=json.writeValueAsString(envelope())+" ".repeat(2048);
      byte[] decoded=padded.getBytes(StandardCharsets.UTF_8);
      var buffer=new java.io.ByteArrayOutputStream();
      try(var gzip=new java.util.zip.GZIPOutputStream(buffer)){gzip.write(decoded);}
      byte[] wire=buffer.toByteArray();
      assertThat(wire.length).isLessThan(decoded.length-1);
      configure(1,1,decoded.length,262144);
      var signature=proof(wire);
      var result=post(wire,signature,"gzip").andReturn().getResponse();
      assertThat(result.getStatus()).isEqualTo(200);
      assertThat(post(wire,proof(decoded),"gzip").andReturn().getResponse().getStatus()).isEqualTo(403);
      byte[] altered=wire.clone();altered[4]^=1; // modification time changes only the gzip representation
      assertThat(post(altered,signature,"gzip").andReturn().getResponse().getStatus()).isEqualTo(403);
      configure(1,1,decoded.length-1,262144);
      var overflow=post(wire,signature,"gzip").andReturn().getResponse();
      assertThat(overflow.getStatus()).isEqualTo(413);
      assertThat(json.readTree(overflow.getContentAsByteArray()).path("code").textValue()).isEqualTo("SEM_BATCH_REQUEST_TOO_LARGE");
    }
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

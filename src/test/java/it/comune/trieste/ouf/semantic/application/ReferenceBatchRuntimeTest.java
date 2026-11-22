package it.comune.trieste.ouf.semantic.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import it.comune.trieste.ouf.authorization.TestAuthorization;
import it.comune.trieste.ouf.authorization.PrincipalContext;
import it.comune.trieste.ouf.authorization.ServletAuthorization;
import it.comune.trieste.ouf.authorization.TrustedPrincipal;
import it.comune.trieste.ouf.semantic.application.ReferenceBatchService.Pin;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.RequestPostProcessor;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
@AutoConfigureMockMvc
@Transactional
class ReferenceBatchRuntimeTest {
  private static final String GET="/api/semantic/v1/references:resolve";
  private static final String BATCH=GET+"-batch";
  private static final List<String> TYPES=List.of("CLASS","PROPERTY","RELATIONSHIP","VOCABULARY","CONCEPT",
      "ONTOLOGY","DATATYPE","VALUE_MAP");
  @Autowired JdbcTemplate db;
  @Autowired ObjectMapper json;
  @Autowired MockMvc http;

  @Test void resolves1024PinsInOrderAndMeasuresBothChunkSizes() throws Exception {
    var pins=seed(Collections.nCopies(1023,"PROPERTY"),true);
    Collections.reverse(pins);
    var missing=new Pin("urn:batch:absent",UUID.randomUUID(),pins.getFirst().publicationSetId());
    pins.add(511,missing);
    for (int size : List.of(1000,1024)) {
      var chunk=pins.subList(0,size);
      byte[] request=body(chunk);
      var runtime=TestAuthorization.runtime("reader","SERVICE",Set.of("ouf.semantic.read"));
      var actor=TestAuthorization.principal("reader","SERVICE",Set.of("ouf.semantic.read"));
      var call=post(BATCH).contentType("application/json").content(request).with(r -> {
        r.getServletContext().setAttribute(ServletAuthorization.RUNTIME,runtime);
        r.setUserPrincipal(actor);
        return r;
      });
      long start=System.nanoTime();
      byte[] bytes=http.perform(call).andExpect(status().isOk()).andReturn().getResponse().getContentAsByteArray();
      long elapsed=System.nanoTime()-start;
      System.out.printf(Locale.ROOT,"SEM_REFERENCE_BATCH items=%d requestBytes=%d responseBytes=%d mockMvcMs=%.3f%n",
          size,request.length,bytes.length,elapsed/1_000_000.0);
      var response=json.readTree(bytes);
      assertThat(response.required("contract").asText()).isEqualTo("ouf.semantic.reference-batch.v1");
      assertThat(response.required("registryVersion").asText()).isNotBlank();
      var results=response.required("results");
      assertThat(results.size()).isEqualTo(size);
      for (int i=0;i<size;i++) {
        var pin=chunk.get(i);
        var result=results.get(i);
        assertEcho(result,i,pin);
        if (pin.equals(missing)) {
          assertThat(result.required("outcome").asText()).isEqualTo("NOT_RESOLVABLE");
          assertThat(result.has("resolved")).isFalse();
        } else {
          assertThat(result.required("outcome").asText()).isEqualTo("RESOLVED");
          assertThat(result.at("/resolved/revision_id").asText()).isEqualTo(pin.revisionId().toString());
        }
      }
      if (size==1000) {
        String plan=db.query("explain (analyze, buffers, memory, format json) "+ReferenceBatchService.SQL,
            ReferenceBatchService.parameters(chunk),rs -> { rs.next(); return rs.getString(1); });
        assertThat(json.readTree(plan).at("/0/Plan/Actual Rows").asInt()).isEqualTo(size);
        System.out.println("SEM_REFERENCE_BATCH plan1000="+plan);
      }
    }
  }

  @Test void compactFieldsMatchGetForEveryArtifactType() throws Exception {
    var pins=seed(TYPES,true);
    var results=json.readTree(postBatch(body(pins))).required("results");
    for (int i=0;i<TYPES.size();i++) {
      var pin=pins.get(i);
      var single=getPin(pin,200);
      assertThat(single.required("artifact_type").asText()).isEqualTo(TYPES.get(i));
      var expected=json.createObjectNode();
      for (String key : List.of("semantic_id","semantic_version","revision_id","publication_set_id",
          "publication_checksum","status","artifact_type","content_hash")) {
        expected.set(key,single.required(key));
      }
      if (Set.of("DATATYPE","VALUE_MAP").contains(TYPES.get(i))) {
        assertThat(single.required("definitionSha256").asText()).matches("[0-9a-f]{64}");
        expected.set("definitionSha256",single.required("definitionSha256"));
      }
      if ("CONCEPT".equals(TYPES.get(i))) {
        // Vocabulary membership proof used by Ingestion and UDP instead of a per-element GET.
        assertThat(single.required("definition").required("vocabularyRef").asText()).isNotBlank();
        expected.set("definition",single.required("definition"));
      }
      assertThat(results.get(i).required("resolved")).isEqualTo(expected);
    }
  }

  @Test void hiddenAndAbsentPinsHaveTheSameOutcome() throws Exception {
    var hidden=seed(List.of("CLASS"),false).getFirst();
    var visible=seed(List.of("CLASS"),true).getFirst();
    var pins=List.of(hidden,new Pin(visible.semanticId(),visible.revisionId(),hidden.publicationSetId()),
        new Pin(visible.semanticId(),hidden.revisionId(),visible.publicationSetId()));
    var results=json.readTree(postBatch(body(pins))).required("results");
    for (int i=0;i<pins.size();i++) {
      getPin(pins.get(i),404);
      var result=results.get(i);
      assertEcho(result,i,pins.get(i));
      assertThat(result.required("outcome").asText()).isEqualTo("NOT_RESOLVABLE");
      assertThat(result.size()).isEqualTo(5);
    }
  }

  @Test void versionTracksRevisionAndPublicationChangesAcrossChunks() throws Exception {
    var active=seed(List.of("PROPERTY"),true).getFirst();
    var building=seed(List.of("CLASS"),false).getFirst();
    String version=version(active);
    assertThat(version(building)).isEqualTo(version);
    assertThat(version(active)).isEqualTo(version);
    db.update("update ouf_sem.artifact_revision set lifecycle_status='DEPRECATED' where revision_id=?",active.revisionId());
    var changed=json.readTree(postBatch(body(List.of(active))));
    assertThat(changed.at("/results/0/resolved/status").asText()).isEqualTo("DEPRECATED");
    String deprecated=changed.required("registryVersion").asText();
    assertThat(deprecated).isNotEqualTo(version).isEqualTo(version(building));
    db.update("update ouf_sem.semantic_publication_set set checksum=encode(sha256(convert_to(checksum||'/changed','UTF8')),'hex') where publication_set_id=?",
        building.publicationSetId());
    String checksumChanged=version(building);
    assertThat(checksumChanged).isNotEqualTo(deprecated);
    publish(building.publicationSetId());
    assertThat(version(building)).isNotEqualTo(checksumChanged).isEqualTo(version(active));
  }

  @Test void rejectsFirstInvalidIndexAndMalformedJson() throws Exception {
    var pin=new Pin("urn:batch:one",UUID.randomUUID(),UUID.randomUUID());
    ObjectNode first=json.valueToTree(pin);
    var duplicate=first.deepCopy().put("revisionId",pin.revisionId().toString().toUpperCase(Locale.ROOT));
    invalid(body(List.of(first,duplicate)),1,"DUPLICATE_REFERENCE");
    var bad=first.deepCopy().put("semanticId","urn:batch:two");
    bad.remove("publicationSetId");
    invalid(body(List.of(first,bad,duplicate)),1,"MISSING_FIELD");
    invalid(body(List.of(first,first.deepCopy().put("revisionId","1-2-3-4-5"))),1,"INVALID_UUID");
    invalid(body(List.of(first,first.deepCopy().put("semanticId","urn:"+"x".repeat(2045)))),1,"INVALID_SEMANTIC_ID");
    invalid(body(List.of(first,first.deepCopy().put("semanticId","relative"))),1,"INVALID_SEMANTIC_ID");
    invalid(body(List.of(first,first.deepCopy().put("revisionId",1))),1,"INVALID_FIELD_TYPE");
    invalid(body(Arrays.asList(first,null)),1,"INVALID_ELEMENT");
    invalid(body(List.of()),0,"EMPTY_REFERENCES");
    http.perform(post(BATCH).with(reader())).andExpect(status().isBadRequest())
        .andExpect(jsonPath("$.code").value("SEM_REFERENCE_BATCH_INVALID")).andExpect(jsonPath("$.index").value(0));
    invalid(("{\"references\":["+first+",{\"semanticId\":").getBytes(java.nio.charset.StandardCharsets.UTF_8),
        1,"INVALID_JSON");
  }

  @Test void rejectsOversizedByteAndItemCounts() throws Exception {
    var pins=new ArrayList<Pin>();
    UUID set=UUID.randomUUID();
    for (int i=0;i<1025;i++) pins.add(new Pin("urn:batch:"+i,UUID.randomUUID(),set));
    byte[] tooMany=body(pins);
    assertThat(tooMany.length).isLessThan(262144);
    for (byte[] oversized : List.of(tooMany,new byte[262145])) {
      http.perform(post(BATCH).with(reader()).contentType("application/json").content(oversized))
          .andExpect(status().is(413)).andExpect(jsonPath("$.code").value("SEM_REFERENCE_BATCH_TOO_LARGE"));
    }
  }

  @Test void authorizationMatchesGetBeforeReadingBody() throws Exception {
    var pin=new Pin("urn:batch:one",UUID.randomUUID(),UUID.randomUUID());
    for (var request : List.of(get(GET).param("semanticId",pin.semanticId()).param("revisionId",pin.revisionId().toString())
        .param("publicationSetId",pin.publicationSetId().toString()),post(BATCH).contentType("application/json").content("{}"))) {
      http.perform(request).andExpect(status().isForbidden());
      http.perform(request.with(r -> { TestAuthorization.bind(r,"worker","SERVICE",Set.of("ouf.semantic.search")); return r; }))
          .andExpect(status().isForbidden());
      http.perform(request.with(r -> {
        var scopes=Set.of("ouf.semantic.read");
        TestAuthorization.bind(r,"reader","SERVICE",scopes);
        r.setUserPrincipal(new TrustedPrincipal(new PrincipalContext("reader","tenant-b",PrincipalContext.ActorType.SERVICE,
            "reader","fixture-authentication","fixture-issuer","fixture-audience",scopes)));
        return r;
      })).andExpect(status().isForbidden());
    }
  }

  private static void assertEcho(JsonNode result,int i,Pin pin) {
    assertThat(result.required("index").asInt()).isEqualTo(i);
    assertThat(result.required("semanticId").asText()).isEqualTo(pin.semanticId());
    assertThat(result.required("revisionId").asText()).isEqualTo(pin.revisionId().toString());
    assertThat(result.required("publicationSetId").asText()).isEqualTo(pin.publicationSetId().toString());
  }
  private String version(Pin pin) throws Exception {
    return json.readTree(postBatch(body(List.of(pin)))).required("registryVersion").asText();
  }
  private void invalid(byte[] body,int index,String reason) throws Exception {
    http.perform(post(BATCH).with(reader()).contentType("application/json").content(body))
        .andExpect(status().isBadRequest()).andExpect(jsonPath("$.code").value("SEM_REFERENCE_BATCH_INVALID"))
        .andExpect(jsonPath("$.index").value(index)).andExpect(jsonPath("$.reason").value(reason));
  }
  private byte[] body(List<?> pins) throws Exception {
    return json.writeValueAsBytes(Map.of("references",pins));
  }
  private byte[] postBatch(byte[] body) throws Exception {
    return http.perform(post(BATCH).with(reader()).contentType("application/json").content(body))
        .andExpect(status().isOk()).andReturn().getResponse().getContentAsByteArray();
  }
  private JsonNode getPin(Pin pin,int statusCode) throws Exception {
    return json.readTree(http.perform(get(GET).with(reader()).param("semanticId",pin.semanticId())
        .param("revisionId",pin.revisionId().toString()).param("publicationSetId",pin.publicationSetId().toString()))
        .andExpect(status().is(statusCode)).andReturn().getResponse().getContentAsByteArray());
  }
  private static RequestPostProcessor reader() {
    return r -> { TestAuthorization.bind(r,"reader","SERVICE",Set.of("ouf.semantic.read")); return r; };
  }
  private void publish(UUID set) {
    db.update("update ouf_sem.semantic_publication_set set status='PUBLISHED' where publication_set_id=?",set);
  }
  private List<Pin> seed(List<String> types,boolean published) throws Exception {
    UUID set=UUID.randomUUID();
    String prefix="urn:batch:"+set+":";
    db.update("""
        insert into ouf_sem.semantic_publication_set values (?,nextval('ouf_sem.publication_no_seq'),
          encode(sha256(convert_to(?,'UTF8')),'hex'),now(),'tester','BUILDING')
        """,set,prefix);
    var pins=new ArrayList<Pin>();
    var artifacts=new ArrayList<Object[]>();
    var revisions=new ArrayList<Object[]>();
    var members=new ArrayList<Object[]>();
    for (String type : types) {
      UUID artifact=UUID.randomUUID();
      String name=Integer.toString(pins.size());
      var pin=new Pin(prefix+name,UUID.randomUUID(),set);
      Object definition=switch (type) {
        case "DATATYPE" -> Map.of("components",List.of(Map.of("name","title","type","string","required",true,"cardinality","ONE")));
        case "CONCEPT" -> Map.of("vocabularyRef",prefix+types.indexOf("VOCABULARY"));
        case "VALUE_MAP" -> Map.of("targetVocabulary",prefix+types.indexOf("VOCABULARY")+"@"+set,"entries",
            List.of(Map.of("code","Città","concept",prefix+types.indexOf("CONCEPT"))));
        default -> Map.of();
      };
      artifacts.add(new Object[]{artifact,pin.semanticId(),type,prefix,name});
      revisions.add(new Object[]{pin.revisionId(),artifact,json.writeValueAsString(definition)});
      members.add(new Object[]{set,pin.semanticId(),pin.revisionId()});
      pins.add(pin);
    }
    db.batchUpdate("""
        insert into ouf_sem.semantic_artifact(artifact_id,semantic_id,artifact_type,namespace,local_name,
          owner_ref,authority_ref,origin_kind) values(?,?,?,?,?,'owner','authority','OUF')
        """,artifacts);
    db.batchUpdate("""
        insert into ouf_sem.artifact_revision(revision_id,artifact_id,revision_no,lifecycle_status,semantic_version,
          definition_json,content_hash,created_by_subject,published_at) values(?,?,1,'ACTIVE','1.0.0',?::jsonb,repeat('a',64),'tester',now())
        """,revisions);
    db.batchUpdate("insert into ouf_sem.semantic_publication_member values(?,?,?)",members);
    if (published) publish(set);
    return pins;
  }
}

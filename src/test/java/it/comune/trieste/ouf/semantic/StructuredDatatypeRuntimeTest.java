package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.semantic.api.ArtifactApi.CreateArtifact;
import it.comune.trieste.ouf.semantic.api.ArtifactApi.PatchRevision;
import it.comune.trieste.ouf.semantic.application.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.stream.IntStream;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
@AutoConfigureMockMvc
class StructuredDatatypeRuntimeTest {
  @Autowired MockMvc http;
  @Autowired ProposalCommandService commands;
  @Autowired ArtifactService artifacts;
  @Autowired GovernanceService governance;
  @Autowired InterchangeService interchange;
  @Autowired SemanticReadService reads;
  @Autowired ObjectMapper json;

  private record Draft(String iri,UUID revision) {}
  private record Publication(Draft draft,UUID set,JsonNode card) {
    String ref() {return draft.iri()+"@"+set;}
  }
  private static String key() {return UUID.randomUUID().toString();}
  private static String iri() {return "https://example.org/datatypes/"+key();}
  private static Map<String,Object> field(String name,String type) {
    return new LinkedHashMap<>(Map.of("name",name,"type",type,"required",true,"cardinality","ONE"));
  }
  private static Map<String,Object> fields(int count,String type) {
    return Map.of("components",IntStream.range(0,count).mapToObj(i->field("campo"+i,type)).toList());
  }
  private Draft create(String id,String version,Map<String,Object> definition) {
    var proposalDefinition=new LinkedHashMap<>(definition);
    proposalDefinition.put("description",Map.of("it","Indirizzo del servizio"));
    var c=new CreateArtifact(id,"DATATYPE","https://example.org/datatypes/",id.substring(id.lastIndexOf('/')+1),
        "owner","authority",version,Map.of("it","Indirizzo"),proposalDefinition);
    var created=commands.create("tenant","agent","AI_AGENT",key(),c,"test");
    return new Draft(id,UUID.fromString(created.get("revisionId").toString()));
  }
  private Map<String,Object> validate(Draft d) {return commands.validate("tenant","agent",key(),d.revision(),0);}
  private Publication publish(Draft d) {
    var result=validate(d);
    assertThat(result).containsEntry("status","PASS");
    var review=commands.review("tenant","agent","AI_AGENT",key(),d.revision(),0,
        UUID.fromString(result.get("validation_run_id").toString()),"test");
    UUID challenge=UUID.fromString(review.get("challengeId").toString());
    JsonNode card=json.valueToTree(governance.card(challenge).get("datatypeReview"));
    assertThatThrownBy(()->governance.decide(challenge,"APPROVED","agent","AI_AGENT","test-decision","test"))
        .hasMessage("HUMAN_IDENTITY_REQUIRED");
    var decision=governance.decide(challenge,"APPROVED","reviewer","HUMAN","test-decision","test");
    var published=governance.publish(d.revision(),(UUID)decision.get("decisionId"),key(),
        review.get("targetContentHash").toString(),"reviewer","HUMAN","test");
    return new Publication(d,(UUID)published.get("publicationSetId"),card);
  }
  private void invalid(Draft d,String code) {
    var result=validate(d);
    assertThat(result).containsEntry("status","FAIL");
    JsonNode issues=json.valueToTree(result.get("issues"));
    assertThat(issues.get(0).path("rule_id").asText()).isEqualTo(code);
    assertThat(issues.get(0).path("message").asText()).isEqualTo(code);
    assertThatThrownBy(()->commands.review("tenant","agent","AI_AGENT",key(),d.revision(),0,
        UUID.fromString(result.get("validation_run_id").toString()),"test")).hasMessage("CURRENT_GREEN_VALIDATION_REQUIRED");
  }

  @Test void publishedDefinitionHashRdfReviewAndHistoricalPin() throws Exception {
    var street=field("via","string");
    street.put("constraints",Map.of("maxLength",80));
    var child=publish(create(iri(),"1.0.0",Map.of("components",List.of(street))));
    var first=reads.resolve(child.draft().iri(),null,child.set());
    String canonical="{\"components\":[{\"cardinality\":\"ONE\",\"constraints\":{\"maxLength\":80},\"name\":\"via\",\"required\":true,\"type\":\"string\"}]}";
    assertThat(json.writeValueAsString(first.get("definition"))).isEqualTo(canonical);
    assertThat(first.get("definitionSha256")).isEqualTo(HexFormat.of().formatHex(
        MessageDigest.getInstance("SHA-256").digest(canonical.getBytes(StandardCharsets.UTF_8))));
    JsonNode rdf=json.valueToTree(first.get("rdf_snapshot"));
    assertThat(rdf.required("statements").toString()).contains("http://www.w3.org/2000/01/rdf-schema#Datatype");
    var statements=rdf.required("statements");
    var value=java.util.stream.StreamSupport.stream(statements.spliterator(),false)
        .filter(s->s.path("predicate").asText().equals("http://www.w3.org/1999/02/22-rdf-syntax-ns#value"))
        .findFirst().orElseThrow().required("object");
    assertThat(value.path("datatype").asText()).isEqualTo("http://www.w3.org/1999/02/22-rdf-syntax-ns#JSON");
    assertThat(json.readTree(value.path("value").asText())).isEqualTo(json.readTree(canonical));
    var exported=interchange.export(child.set(),(UUID)first.get("artifact_id"),"text/turtle");
    assertThat(new String(exported.body(),StandardCharsets.UTF_8)).contains("Datatype");
    assertThat(child.card().path("etichetta").asText()).isEqualTo("Indirizzo");
    assertThat(child.card().path("descrizione").asText()).isEqualTo("Indirizzo del servizio");
    var row=child.card().required("componenti").get(0);
    assertThat(row.path("tipo").asText()).isEqualTo("Testo");
    assertThat(row.path("vincoli").asText()).isEqualTo("Lunghezza massima 80");
    assertThat(child.card().required("avvisi").toString()).contains("via","senza etichetta");
    String id=child.draft().iri();
    assertThat(reads.search(id,"ACTIVE",1,"DATATYPE",null,null,null).getFirst()).containsEntry("semantic_id",id);
    assertThatThrownBy(()->create(id,"1.0.0",fields(1,"integer"))).hasMessage("DT-VERSION");
    assertThatThrownBy(()->artifacts.patch(child.draft().revision(),"\"0\"",new PatchRevision(Map.of(),Map.of(),"1.0.1"),
        "agent","AI_AGENT","test")).hasMessage("VERSION_CONFLICT");
    var parent=publish(create(iri(),"1.0.0",fields(1,child.ref())));
    street.put("constraints",Map.of("maxLength",40));
    var next=create(id,"2.0.0",Map.of("components",List.of(street,field("numero","integer"))));
    var v2=publish(next);
    assertThat(v2.card().path("versionePrecedente").asText()).isEqualTo("1.0.0");
    assertThat(v2.card().required("differenze").toString()).contains("via","prima","80","dopo","40","numero","Aggiunto");
    var parentPin=reads.resolve(parent.draft().iri(),null,v2.set());
    assertThat(parentPin).containsEntry("status","ACTIVE");
    JsonNode parentDefinition=json.valueToTree(parentPin.get("definition"));
    assertThat(parentDefinition.at("/components/0/type").asText()).isEqualTo(child.ref());
    assertThat(reads.resolve(id,null,child.set())).containsEntry("status","DEPRECATED")
        .containsEntry("revision_id",child.draft().revision()).containsEntry("definitionSha256",first.get("definitionSha256"));
    assertThat(reads.resolve(id,null,v2.set()).get("definitionSha256")).isNotEqualTo(first.get("definitionSha256"));
    assertThatThrownBy(()->reads.resolve(id,next.revision(),child.set())).hasMessage("SEMANTIC_REFERENCE_NOT_FOUND");
  }

  @Test void resolveReturnsCurrentPinStatusAndExactTypedBoundsThroughRetirement() throws Exception {
    var component=field("misura","decimal");
    component.put("constraints",Map.of("minInclusive","-0.125","maxInclusive","9007199254740993.123456789"));
    var definition=Map.of("components",List.of(component));
    var published=publish(create(iri(),"1.0.0",definition));
    String activeHash=null;
    for (String state:List.of("ACTIVE","DEPRECATED","RETIRED")) {
      if (!state.equals("ACTIVE"))
        governance.lifecycle(published.draft().revision(),state,"reviewer","HUMAN","fixture:decision",key());
      var response=http.perform(get("/api/semantic/v1/references:resolve")
          .param("semanticId",published.draft().iri()).param("publicationSetId",published.set().toString())
          .with(request -> {
            it.comune.trieste.ouf.authorization.TestAuthorization.bind(request,"reader","SERVICE",Set.of("ouf.semantic.read"));
            return request;
          })).andExpect(status().isOk()).andReturn().getResponse();
      var pin=json.readTree(response.getContentAsByteArray());
      assertThat(pin.required("status").asText()).isEqualTo(state);
      assertThat(pin.required("revision_id").asText()).isEqualTo(published.draft().revision().toString());
      assertThat(pin.required("definition")).isEqualTo(json.valueToTree(definition));
      String hash=pin.required("definitionSha256").asText();
      if (activeHash==null) activeHash=hash;
      assertThat(hash).matches("[0-9a-f]{64}").isEqualTo(activeHash);
    }
  }

  @Test void rejectsCyclesMissingMembersAndWrongArtifactType() {
    String id=iri();
    invalid(create(id,"1.0.0",fields(1,id+"@"+key())),"DT-CYCLE");
    var leaf=publish(create(iri(),"1.0.0",fields(1,"date")));
    var parent=publish(create(iri(),"1.0.0",fields(1,leaf.ref())));
    invalid(create(leaf.draft().iri(),"2.0.0",fields(1,parent.ref())),"DT-CYCLE");
    var draft=create(iri(),"1.0.0",fields(1,"boolean"));
    invalid(create(iri(),"1.0.0",fields(1,draft.iri()+"@"+parent.set())),"DT-UNPUBLISHED");
    invalid(create(iri(),"1.0.0",fields(1,leaf.draft().iri())),"DT-TYPE");
    var other=new CreateArtifact(iri(),"CLASS","ns",key(),"owner","authority","1.0.0",Map.of("it","Classe"),Map.of());
    var created=artifacts.create(other,"agent","AI_AGENT","test");
    var cls=publish(new Draft(other.semanticId(),(UUID)created.get("revisionId")));
    invalid(create(iri(),"1.0.0",fields(1,cls.ref())),"DT-UNPUBLISHED");
    assertThat(reads.resolve(cls.draft().iri(),cls.draft().revision(),cls.set())).doesNotContainKeys("definitionSha256","rdf_snapshot");
  }

  @Test void enforcesDepthWidthAndRepeatedLeafBudgetAtBoundaries() {
    invalid(create(iri(),"1.0.0",fields(0,"string")),"DT-COUNT");
    invalid(create(iri(),"1.0.0",fields(33,"string")),"DT-COUNT");
    var wide=publish(create(iri(),"1.0.0",fields(32,"string")));
    var two=publish(create(iri(),"1.0.0",fields(8,wide.ref())));
    invalid(create(iri(),"1.0.0",fields(9,wide.ref())),"DT-LEAVES");
    var three=publish(create(iri(),"1.0.0",fields(1,two.ref())));
    var four=publish(create(iri(),"1.0.0",fields(1,three.ref())));
    invalid(create(iri(),"1.0.0",fields(1,four.ref())),"DT-DEPTH");
  }

  @Test void validatesClosedComponentShapeAndTypedConstraints() {
    var good=new ArrayList<Map<String,Object>>();
    for(String type:List.of("integer","decimal","date","datetime","string","geometry","concept","boolean")) {
      var c=field(type,type);
      c.put("cardinality","MANY"); c.put("required",false);
      c.put("labels",Map.of("it","Componente"));
      c.put("constraints",switch(type){
        case "integer","decimal" -> Map.of("minInclusive","-123456789012345678901","maxInclusive","99");
        case "date" -> Map.of("minInclusive","2024-02-29");
        case "datetime" -> Map.of("minInclusive","2024-02-29T00:00:00Z","maxInclusive","2024-02-29T00:00:00.000000001Z");
        case "string" -> Map.of("maxLength",0);
        default -> Map.of();
      });
      good.add(c);
    }
    assertThat(validate(create(iri(),"1.0.0",Map.of("components",good)))).containsEntry("status","PASS");
    var c=field("nome","string");
    invalid(create(iri(),"1.0.0",Map.of("components",List.of(c,c))),"DT-NAME");
    for(var example:List.of(List.of("name","1nome","DT-NAME"),List.of("required","true","DT-REQUIRED"),
        List.of("cardinality","OPTIONAL","DT-CARDINALITY"),List.of("alias","alias","DT-COMPONENT"))) {
      var bad=field("nome","string"); bad.put(example.get(0),example.get(1));
      invalid(create(iri(),"1.0.0",Map.of("components",List.of(bad))),example.get(2));
    }
    var reversed=field("istante","datetime");
    reversed.put("constraints",Map.of("minInclusive","2026-01-01T00:00:00.000000002Z","maxInclusive","2026-01-01T00:00:00.000000001Z"));
    invalid(create(iri(),"1.0.0",Map.of("components",List.of(reversed))),"DT-CONSTRAINT");
    for(var example:List.of(List.of("integer","maxLength","1"),List.of("date","minInclusive","2026-02-30"),
        List.of("geometry","minInclusive","1"),List.of("string","maxLength","-1"),List.of("concept","vocabularyRef",""))) {
      var bad=field("nome",example.get(0)); bad.put("constraints",Map.of(example.get(1),example.get(2)));
      invalid(create(iri(),"1.0.0",Map.of("components",List.of(bad))),"DT-CONSTRAINT");
    }
  }

  @Test void rejectsWrongJsonTypesAndNoncanonicalBounds() {
    record Example(String type,String constraint,Object value) {}
    for (var example:List.of(new Example("integer","minInclusive",-90),new Example("decimal","maxInclusive",45.5),
        new Example("date","maxInclusive",20260101),new Example("datetime","minInclusive",true),
        new Example("integer","minInclusive","01"),new Example("decimal","maxInclusive","45.50"),
        new Example("datetime","minInclusive","2026-01-01T01:00:00+01:00"),
        new Example("string","maxLength","80"),new Example("string","maxLength",1.5),
        new Example("concept","vocabularyRef",42),new Example("concept","vocabularyRef","relative/path"))) {
      var c=field("valore",example.type());
      c.put("constraints",Map.of(example.constraint(),example.value()));
      invalid(create(iri(),"1.0.0",Map.of("components",List.of(c))),"DT-CONSTRAINT");
    }
  }

  @Test void conceptConstraintRequiresPublishedVocabularyIri() {
    var vocabulary=new CreateArtifact(iri(),"VOCABULARY","ns",key(),"owner","authority","1.0.0",Map.of("it","Stati"),Map.of());
    var created=artifacts.create(vocabulary,"agent","AI_AGENT","test");
    var concept=field("stato","concept");
    concept.put("constraints",Map.of("vocabularyRef",vocabulary.semanticId()));
    var draft=create(iri(),"1.0.0",Map.of("components",List.of(concept)));
    invalid(draft,"DT-CONSTRAINT");
    publish(new Draft(vocabulary.semanticId(),(UUID)created.get("revisionId")));
    var published=publish(draft);
    concept.put("constraints",Map.of("vocabularyRef",published.draft().iri()));
    invalid(create(iri(),"1.0.0",Map.of("components",List.of(concept))),"DT-CONSTRAINT");
  }
}

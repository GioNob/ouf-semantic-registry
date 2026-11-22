package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.authorization.TestAuthorization;
import it.comune.trieste.ouf.semantic.api.ArtifactApi.CreateArtifact;
import it.comune.trieste.ouf.semantic.api.ArtifactApi.PatchRevision;
import it.comune.trieste.ouf.semantic.application.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.*;
import java.util.stream.IntStream;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
@AutoConfigureMockMvc
class ValueMapRuntimeTest {
  @Autowired MockMvc http;
  @Autowired ProposalCommandService commands;
  @Autowired GovernanceService governance;
  @Autowired ArtifactService artifacts;
  @Autowired SemanticReadService reads;
  @Autowired ObjectMapper json;
  @Autowired JdbcClient db;

  private record Published(String id, UUID revision, UUID set, JsonNode card) {
    String pin() { return id+"@"+set; }
  }

  private static String key() { return UUID.randomUUID().toString(); }
  private static String iri() { return "https://example.org/value-map/"+key(); }

  private CreateArtifact command(String iri, String type, String version, String label, Map<String,Object> definition) {
    return new CreateArtifact(iri,type,"https://example.org/value-map/",iri.substring(iri.lastIndexOf('/')+1),
        "owner","authority",version,Map.of("it",label),definition);
  }

  private UUID create(CreateArtifact proposal) {
    return UUID.fromString(commands.create("tenant","agent","AI_AGENT",key(),proposal,"test").get("revisionId").toString());
  }

  private Published publish(CreateArtifact proposal) {
    UUID revision=create(proposal);
    var validation=commands.validate("tenant","agent",key(),revision,0);
    assertThat(validation).containsEntry("status","PASS");
    var review=commands.review("tenant","agent","AI_AGENT",key(),revision,0,
        UUID.fromString(validation.get("validation_run_id").toString()),"test");
    UUID challenge=UUID.fromString(review.get("challengeId").toString());
    JsonNode card=json.valueToTree(governance.card(challenge));
    assertThatThrownBy(()->governance.decide(challenge,"APPROVED","agent","AI_AGENT","fixture","test"))
        .hasMessage("HUMAN_IDENTITY_REQUIRED");
    var decision=governance.decide(challenge,"APPROVED","reviewer","HUMAN","fixture","test");
    var result=governance.publish(revision,(UUID)decision.get("decisionId"),key(),review.get("targetContentHash").toString(),
        "reviewer","HUMAN","test");
    return new Published(proposal.semanticId(),revision,(UUID)result.get("publicationSetId"),card);
  }

  private Published vocabulary(String label) {
    return publish(command(iri(),"VOCABULARY","1.0.0",label,Map.of()));
  }

  private Published concept(Published vocabulary, String label) {
    return publish(command(iri(),"CONCEPT","1.0.0",label,Map.of("vocabularyRef",vocabulary.id())));
  }

  private static Map<String,String> entry(String code, Published target) {
    return Map.of("code",code,"concept",target.id());
  }

  private static Map<String,Object> definition(String pin, List<?> entries) {
    return Map.of("targetVocabulary",pin,"entries",entries,"labels",Map.of("it","Codici servizio"));
  }

  private JsonNode createHttp(String id, Object definition, int status) throws Exception {
    var proposal=new LinkedHashMap<>(Map.<String,Object>of("semanticId",id,"artifactType","VALUE_MAP","namespace","https://example.org/value-map/",
        "localName",id.substring(id.lastIndexOf('/')+1),"ownerRef","owner","authorityRef","authority","semanticVersion","1.0.0"));
    proposal.put("definition",definition);
    var response=http.perform(post("/api/semantic/v1/proposal-commands/create")
        .with(request -> { TestAuthorization.bind(request,"agent","AI_AGENT",Set.of("ouf.semantic.propose")); return request; })
        .header("Idempotency-Key",key()).contentType(MediaType.APPLICATION_JSON).content(json.writeValueAsBytes(proposal)))
        .andExpect(status().is(status)).andReturn().getResponse();
    return json.readTree(response.getContentAsByteArray());
  }

  @Test void valueMapRejectsInvalidDefinitionsAndExactPinMismatchesWithoutSourceValues() throws Exception {
    var vocab=vocabulary("Servizi");
    var member=concept(vocab,"Biblioteca");
    var other=vocabulary("Altri servizi");
    var outsider=concept(other,"Archivio");
    String pin=vocab.id()+"@"+member.set();
    var valid=entry("A",member);
    String marker="private-code";
    var bad=Arrays.asList(null, List.of(valid), definition(vocab.pin(),List.of(valid)),
        definition(member.pin(),List.of(valid)), definition(vocab.id(),List.of(valid)),
        definition(vocab.id()+"@"+outsider.set(),List.of(entry(marker,outsider))),
        definition(pin,List.of()), definition(pin,List.of(valid,valid)),
        definition(pin,List.of(entry(" ",member))), definition(pin,List.of(entry(marker+" ",member))),
        definition(pin,List.of(entry("\u2003"+marker,member))), definition(pin,List.of(entry(marker+"\u007f",member))),
        definition(pin,List.of(entry("A\u001c"+marker,member))), definition(pin,List.of(entry("A\u0085"+marker,member))),
        definition(pin,List.of(entry("A\u009f"+marker,member))), definition(pin,List.of(entry(marker+"\u202f",member))),
        definition(pin,List.of(entry(marker+"\u2007",member))),
        definition(pin,List.of(entry(marker+(char)0,member))), definition(pin,List.of(entry("A".repeat(129),member))),
        definition(pin,List.of(Map.of("code",marker,"concept",member.id(),"extra",true))),
        definition(pin,List.of(Map.of("code",10,"concept",member.id()))),
        definition(pin,List.of(Map.of("code",marker,"concept",vocab.id()))),
        Map.of("targetVocabulary",pin,"entries",List.of(valid),"labels",Map.of("fr","Label")),
        Map.of("targetVocabulary",pin,"entries",List.of(valid),"description",marker));
    for (Object definition : bad) {
      var problem=createHttp(iri(),definition,400);
      assertThat(problem.required("code").asText()).isEqualTo("SEMANTIC_VALUE_MAP_INVALID");
      assertThat(problem.required("detail").asText()).isEqualTo("SEMANTIC_VALUE_MAP_INVALID");
      assertThat(problem.toString()).doesNotContain(marker);
    }
    var vacant=vocabulary("Vocabolario senza collegamenti");
    governance.lifecycle(vacant.revision(),"DEPRECATED","reviewer","HUMAN","fixture",key());
    assertThat(createHttp(iri(),definition(vacant.pin(),List.of(valid)),400).required("code").asText())
        .isEqualTo("SEMANTIC_VALUE_MAP_INVALID");
  }

  @Test void valueMapUsesTheContractWhitespaceVectorAndKeepsExactCodes() throws Exception {
    var vocab=vocabulary("Servizi");
    var member=concept(vocab,"Biblioteca");
    var vectors=json.readTree(Path.of("contracts/ouf-value-types-v1.json").toFile()).at("/whitespace/vectors");
    var vector=java.util.stream.StreamSupport.stream(vectors.spliterator(),false)
        .filter(v -> "VALUE_MAP_V1".equals(v.path("reader").asText())).findFirst().orElseThrow();
    assertThat(vector.required("result").asText()).isEqualTo("concept mapped from code 'A1'");
    String pin=vocab.id()+"@"+member.set();
    assertThat(createHttp(iri(),definition(pin,List.of(entry(vector.required("cell").asText(),member))),400)
        .required("code").asText()).isEqualTo("SEMANTIC_VALUE_MAP_INVALID");
    var entries=List.of(entry("A1",member),entry("A\u00a01",member),entry("\ufeffA1",member));
    var published=publish(command(iri(),"VALUE_MAP","1.0.0","Mappa",definition(pin,entries)));
    assertThat(published.card().at("/valueMapReview/entries/0/concept").asText()).isEqualTo(member.id());
    assertThat(published.card().at("/valueMapReview/entries/1/code").asText()).isEqualTo("A\u00a01");
    assertThat(published.card().at("/valueMapReview/entries/2/code").asText()).isEqualTo("\ufeffA1");
  }

  @Test void valueMapEnforcesConceptLengthAndCompactUtf8DefinitionSize() throws Exception {
    var vocab=vocabulary("Servizi");
    String memberPrefix=iri();
    String longMember=memberPrefix+"a".repeat(513-memberPrefix.length());
    var outOfBounds=publish(command(longMember,"CONCEPT","1.0.0","Archivio",Map.of("vocabularyRef",vocab.id())));
    var member=concept(vocab,"Biblioteca");
    String pin=vocab.id()+"@"+member.set();
    assertThat(createHttp(iri(),definition(pin,List.of(entry("A",outOfBounds))),400).required("code").asText())
        .isEqualTo("SEMANTIC_VALUE_MAP_INVALID");

    var definition=new LinkedHashMap<String,Object>();
    definition.put("targetVocabulary",pin);
    definition.put("entries",List.of(entry("A",member),entry("B",member)));
    var labels=new LinkedHashMap<>(Map.of("it","Spazi , : \" \\ \t","en","Label"));
    definition.put("labels",labels);
    int remaining=786432-json.writeValueAsString(definition).getBytes(StandardCharsets.UTF_8).length;
    labels.compute("it",(language,label) -> label+"é".repeat(remaining/2)+"a".repeat(remaining%2));
    assertThat(json.writeValueAsString(definition).getBytes(StandardCharsets.UTF_8)).hasSize(786432);
    UUID draft=UUID.fromString(createHttp(iri(),definition,200).required("revisionId").asText());
    labels.compute("it",(language,label) -> label+"a");
    assertThat(createHttp(iri(),definition,400).required("code").asText()).isEqualTo("SEMANTIC_VALUE_MAP_INVALID");
    assertThatThrownBy(()->artifacts.patch(draft,"\"0\"",new PatchRevision(null,definition,null),
        "agent","AI_AGENT","test")).hasMessage("SEMANTIC_VALUE_MAP_INVALID");
  }

  @Test void valueMapNativePublicationUsesCanonicalHashAndHistoricalPins() throws Exception {
    var vocab=vocabulary("Servizi");
    var first=concept(vocab,"Biblioteca");
    var second=concept(vocab,"Archivio");
    String pin=vocab.id()+"@"+second.set();
    String id=iri();
    var entries=List.of(entry("\uE000",first),entry("a",first),entry("\uD800\uDC00",first),entry("A",first),
        entry("\uDBFF\uDFFF",first));
    var v1=publish(command(id,"VALUE_MAP","1.0.0","Mappa",definition(pin,entries)));
    var response=http.perform(get("/api/semantic/v1/references:resolve")
        .param("semanticId",id).param("publicationSetId",v1.set().toString())
        .with(request -> { TestAuthorization.bind(request,"reader","SERVICE",Set.of("ouf.semantic.read")); return request; }))
        .andExpect(status().isOk()).andReturn().getResponse();
    var resolved=json.readTree(response.getContentAsByteArray());
    String canonical=json.writer(SerializationFeature.ORDER_MAP_ENTRIES_BY_KEYS).writeValueAsString(
        definition(pin,List.of(entries.get(3),entries.get(1),entries.get(2),entries.get(4),entries.get(0))));
    String expected=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(canonical.getBytes(StandardCharsets.UTF_8)));
    assertThat(resolved.required("artifact_type").asText()).isEqualTo("VALUE_MAP");
    assertThat(resolved.required("revision_id").asText()).isEqualTo(v1.revision().toString());
    assertThat(resolved.required("publication_set_id").asText()).isEqualTo(v1.set().toString());
    assertThat(resolved.required("status").asText()).isEqualTo("ACTIVE");
    assertThat(resolved.required("definition").toString()).isEqualTo(canonical);
    assertThat(resolved.required("definitionSha256").asText()).isEqualTo(expected);
    assertThat(v1.card().required("valueMapReview").has("changes")).isFalse();
    assertThat(reads.resolve(vocab.id(),vocab.revision(),second.set())).containsEntry("artifact_type","VOCABULARY")
        .doesNotContainKey("definitionSha256");
    assertThat(reads.resolve(second.id(),second.revision(),second.set())).containsEntry("artifact_type","CONCEPT")
        .doesNotContainKey("definitionSha256");

    var changed=definition(pin,List.of(entry("Z",first),entry("A",second)));
    assertThatThrownBy(()->create(command(id,"VALUE_MAP","1.0.0","Mappa",changed))).hasMessage("SEMANTIC_VERSION_CONFLICT");
    var v2=publish(command(id,"VALUE_MAP","2.0.0","Mappa",changed));
    var card=v2.card().required("valueMapReview");
    assertThat(card.required("name").asText()).isEqualTo("Codici servizio");
    assertThat(card.required("targetVocabulary")).isEqualTo(json.valueToTree(Map.of("label","Servizi",
        "semanticId",vocab.id(),"publicationSetId",second.set().toString())));
    assertThat(card.at("/entries/0/conceptLabel").asText()).isEqualTo("Archivio");
    assertThat(card.required("entryCount").asInt()).isEqualTo(2);
    assertThat(card.required("changes")).isEqualTo(json.valueToTree(Map.of("added",List.of("Z"),
        "removed",List.of("a","\uD800\uDC00","\uDBFF\uDFFF","\uE000"),
        "changed",List.of(Map.of("code","A","from",first.id(),"to",second.id())))));

    assertThatThrownBy(()->db.sql("update ouf_sem.artifact_revision set definition_json='{}' where revision_id=:r")
        .param("r",v1.revision()).update()).hasMessageContaining("published revision immutable");
    assertThat(reads.resolve(id,null,v1.set())).containsEntry("status","DEPRECATED").containsEntry("definitionSha256",expected);
    governance.lifecycle(v1.revision(),"RETIRED","reviewer","HUMAN","fixture",key());
    assertThat(reads.resolve(id,v1.revision(),v1.set())).containsEntry("status","RETIRED").containsEntry("definitionSha256",expected);
    assertThat(reads.resolve(id,null,v2.set())).containsEntry("status","ACTIVE").containsEntry("revision_id",v2.revision());
    assertThatThrownBy(()->reads.resolve(id,v2.revision(),v1.set())).hasMessage("SEMANTIC_REFERENCE_NOT_FOUND");
  }

  @Test void valueMapRoundTripsTwoThousandEntriesAndRejectsTheNext() throws Exception {
    var vocab=vocabulary("Servizi");
    var member=concept(vocab,"Biblioteca");
    String pin=vocab.id()+"@"+member.set();
    var entries=IntStream.range(0,2001).mapToObj(i->entry("a".repeat(124)+String.format(Locale.ROOT,"%04d",i),member)).toList();
    var published=publish(command(iri(),"VALUE_MAP","1.0.0","Mappa",definition(pin,entries.subList(0,2000))));
    JsonNode resolved=json.valueToTree(reads.resolve(published.id(),null,published.set()));
    assertThat(resolved.at("/definition/entries").size()).isEqualTo(2000);
    assertThat(resolved.at("/definition/entries/1999/code").asText()).endsWith("1999").hasSize(128);
    assertThat(createHttp(iri(),definition(pin,entries),400).required("code").asText()).isEqualTo("SEMANTIC_VALUE_MAP_INVALID");
  }

  @Test void valueMapDraftEditPreservesContentAndRejectsAnInvalidVersionOrDefinition() throws Exception {
    var vocab=vocabulary("Servizi");
    var member=concept(vocab,"Biblioteca");
    var definition=definition(vocab.id()+"@"+member.set(),List.of(entry("A",member)));
    String id=iri();
    publish(command(id,"VALUE_MAP","1.0.0","Mappa",definition));
    UUID draft=create(command(id,"VALUE_MAP","2.0.0","Mappa",definition));
    assertThatThrownBy(()->artifacts.patch(draft,"\"0\"",new PatchRevision(null,null,"1.0.0"),
        "agent","AI_AGENT","test")).hasMessage("SEMANTIC_VERSION_INVALID");
    assertThatThrownBy(()->artifacts.patch(draft,"\"0\"",new PatchRevision(null,Map.of(),"3.0.0"),
        "agent","AI_AGENT","test")).hasMessage("SEMANTIC_VALUE_MAP_INVALID");
    var updated=artifacts.patch(draft,"\"0\"",new PatchRevision(null,null,"2.1.0"),"agent","AI_AGENT","test");
    assertThat(updated).containsEntry("etag","\"1\"");
    var stored=db.sql("select semantic_version, definition_json::text definition from ouf_sem.artifact_revision where revision_id=:r")
        .param("r",draft).query().singleRow();
    assertThat(stored).containsEntry("semantic_version","2.1.0");
    assertThat(json.readTree(stored.get("definition").toString())).isEqualTo(json.valueToTree(definition));
  }
}

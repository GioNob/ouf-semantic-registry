package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.application.SemanticReadService;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.simple.JdbcClient;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
@org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc
class SemanticReadRuntimeTest {
  @Autowired JdbcClient db;
  @Autowired SemanticReadService reads;
  @Autowired ObjectMapper json;
  @Autowired org.springframework.test.web.servlet.MockMvc http;

  @Test void httpReadPreservesExactPinAndAuthorizationBoundary() throws Exception {
    var f=fixture();
    http.perform(get("/api/semantic/v1/references:resolve")
      .param("semanticId",f.semanticId).param("revisionId",f.revision.toString())
      .param("publicationSetId",f.publication.toString()))
      .andExpect(status().isForbidden());
    http.perform(get("/api/semantic/v1/references:resolve")
      .param("semanticId",f.semanticId).param("revisionId",f.revision.toString())
      .param("publicationSetId",f.publication.toString()).with(readActor()))
      .andExpect(status().isOk()).andExpect(jsonPath("$.label.it").value(f.label))
      .andExpect(jsonPath("$.definition.domainRefs[0]").value(f.domain));
    http.perform(get("/api/semantic/v1/references:resolve")
      .param("semanticId",f.semanticId).param("revisionId",f.revision.toString())
      .param("publicationSetId",UUID.randomUUID().toString()).with(readActor()))
      .andExpect(status().isNotFound());
    http.perform(get("/api/semantic/v1/search").param("q",f.label).param("status","DRAFT").with(readActor()))
      .andExpect(status().isForbidden());
  }
  private static org.springframework.test.web.servlet.request.RequestPostProcessor readActor() {
    return request->{it.comune.trieste.ouf.authorization.TestAuthorization.bind(request,"reader","SERVICE",Set.of("ouf.semantic.read","ouf.semantic.search"));return request;};
  }

  @Test void searchesLabelsAliasesAndDefinitionsAndReturnsPublishedPin() {
    var f=fixture();
    for(String q:List.of(f.label,f.alias,f.description,f.localName,f.semanticId)) {
      var rows=reads.search(q,"ACTIVE",100,"PROPERTY","read-test",f.domain,f.range);
      assertThat(rows).anySatisfy(row->{
        assertThat(row.get("semantic_id")).isEqualTo(f.semanticId);
        assertThat(row.get("revision_id")).isEqualTo(f.revision);
        assertThat(row.get("publication_set_id")).isEqualTo(f.publication);
        assertThat(row.get("label")).isInstanceOf(Map.class);
        assertThat(row.get("definition")).isInstanceOf(Map.class);
      });
    }
    assertThat(reads.search(f.label,"ACTIVE",20,"CLASS",null,null,null)).isEmpty();
    assertThat(reads.search(f.label,"ACTIVE",20,null,null,"wrong",null)).isEmpty();
    assertThat(reads.search(f.label,"ACTIVE",20,null,null,null,"wrong")).isEmpty();
  }

  @Test void currentSearchDoesNotReturnSupersededRevisionAndExactReadRetainsHistory() {
    var f=fixture();
    UUID next=UUID.randomUUID(),set=UUID.randomUUID();
    revision(f.artifact,next,2,f.label,"replacement",f.domain,f.range);
    publication(set,next,f.semanticId);
    db.sql("update ouf_sem.artifact_active_revision set revision_id=:r where artifact_id=:a")
      .param("r",next).param("a",f.artifact).update();
    var results=reads.search(f.label,"ACTIVE",20,null,null,null,null);
    assertThat(results).extracting(r->r.get("revision_id")).contains(next).doesNotContain(f.revision);
    var old=reads.resolve(f.semanticId,f.revision,f.publication);
    assertThat(((Map<?,?>)old.get("description")).get("it")).isEqualTo(f.description);
    assertThat(old.get("publication_set_id")).isEqualTo(f.publication);
    assertThatThrownBy(()->reads.resolve(f.semanticId,next,f.publication)).isInstanceOf(NoSuchElementException.class);
    assertThatThrownBy(()->reads.resolve("other",f.revision,f.publication)).isInstanceOf(NoSuchElementException.class);
    assertThatThrownBy(()->reads.resolve(f.semanticId,f.revision,UUID.randomUUID())).isInstanceOf(NoSuchElementException.class);
  }

  @Test void boundsAreEnforcedAndNoIncompleteMappingIsReturnedOnOverflow() {
    var f=fixture();
    assertThatThrownBy(()->reads.search(" ","ACTIVE",20,null,null,null,null)).isInstanceOf(IllegalArgumentException.class);
    assertThatThrownBy(()->reads.search("x".repeat(257),"ACTIVE",20,null,null,null,null)).isInstanceOf(IllegalArgumentException.class);
    assertThatThrownBy(()->reads.search(f.label,"ACTIVE",101,null,null,null,null)).isInstanceOf(IllegalArgumentException.class);
    assertThatThrownBy(()->reads.search(f.label,"bad",20,null,null,null,null)).isInstanceOf(IllegalArgumentException.class);
    UUID big=UUID.randomUUID();
    revision(f.artifact,big,2,"x".repeat(2048),"big",f.domain,f.range);
    UUID set=UUID.randomUUID(); publication(set,big,f.semanticId);
    var small=new SemanticReadService(db,json,1024);
    assertThatThrownBy(()->small.resolve(f.semanticId,big,set)).hasMessage("SEM_READ_RESULT_TOO_LARGE");
  }

  private record Fixture(UUID artifact,UUID revision,UUID publication,String semanticId,String localName,String label,String alias,String description,String domain,String range){}
  @Test void exactReadProjectsOnlyItsOwnImmutableImportedSnapshot() {
    var f=fixture();
    byte[] bytes=("<"+f.semanticId+"> <http://www.w3.org/2000/01/rdf-schema#label> \"RDF storico\"@it .")
      .getBytes(java.nio.charset.StandardCharsets.UTF_8);
    var parsed=new it.comune.trieste.ouf.semantic.domain.SafeRdfParser().parse(bytes,"text/turtle");
    db.sql("insert into ouf_sem.revision_interchange_snapshot values(:r,'text/turtle',:h,:b,:n,'tester',transaction_timestamp())")
      .param("r",f.revision).param("h",parsed.contentHash()).param("b",bytes).param("n",parsed.statementCount()).update();
    var read=reads.resolve(f.semanticId,f.revision,f.publication);
    assertThat((Map<String,Object>)read.get("rdf_snapshot"))
      .containsEntry("content_hash",parsed.contentHash()).containsEntry("partial",false);
    assertThat(((Map<?,?>)read.get("label")).get("it")).isEqualTo(f.label);
    assertThatThrownBy(()->reads.resolve("urn:other",f.revision,f.publication))
      .isInstanceOf(NoSuchElementException.class);
    UUID next=UUID.randomUUID(),set=UUID.randomUUID();
    revision(f.artifact,next,2,f.label,"replacement",f.domain,f.range);
    publication(set,next,f.semanticId);
    assertThat(reads.resolve(f.semanticId,next,set)).doesNotContainKey("rdf_snapshot");
    assertThat((Map<String,Object>)reads.resolve(f.semanticId,f.revision,f.publication).get("rdf_snapshot"))
      .containsEntry("content_hash",parsed.contentHash());
    var small=new SemanticReadService(db,json,1024);
    assertThatThrownBy(()->small.resolve(f.semanticId,f.revision,f.publication))
      .hasMessage("SEM_READ_RESULT_TOO_LARGE");
  }
  private Fixture fixture() {
    String suffix=UUID.randomUUID().toString().replace("-","");
    var f=new Fixture(UUID.randomUUID(),UUID.randomUUID(),UUID.randomUUID(),"test:read:"+suffix,
      "field"+suffix,"label"+suffix,"alias"+suffix,"description"+suffix,"test:domain:"+suffix,"test:range:"+suffix);
    db.sql("insert into ouf_sem.semantic_artifact values(:a,:s,'PROPERTY','read-test',:n,'owner','authority','OUF',transaction_timestamp(),null)")
      .param("a",f.artifact).param("s",f.semanticId).param("n",f.localName).update();
    revision(f.artifact,f.revision,1,f.label,f.description,f.domain,f.range);
    // Alternative labels are optional definition metadata; all JSON string values are searchable.
    // The published payload is immutable; revision() includes the alias derived from the label.
    db.sql("insert into ouf_sem.artifact_active_revision values(:a,:r,transaction_timestamp(),'tester')")
      .param("a",f.artifact).param("r",f.revision).update();
    publication(f.publication,f.revision,f.semanticId);
    return f;
  }
  private void revision(UUID artifact,UUID revision,int no,String label,String description,String domain,String range) {
    db.sql("""
      insert into ouf_sem.artifact_revision(revision_id,artifact_id,revision_no,lifecycle_status,semantic_version,
        label_json,description_json,definition_json,created_by_subject,published_at)
      values(:r,:a,:n,'ACTIVE','1.0.0',jsonb_build_object('it',cast(:label as text)),
        jsonb_build_object('it',cast(:description as text)),
        jsonb_build_object('alternativeLabels',jsonb_build_array(cast(:alias as text)),
          'domainRefs',jsonb_build_array(cast(:domain as text)),'rangeRefs',jsonb_build_array(cast(:range as text))),
        'tester',transaction_timestamp())
      """).param("r",revision).param("a",artifact).param("n",no).param("label",label).param("description",description)
      .param("alias",label.replace("label","alias")).param("domain",domain).param("range",range).update();
  }
  private void publication(UUID set,UUID revision,String semanticId) {
    db.sql("insert into ouf_sem.semantic_publication_set values(:p,nextval('ouf_sem.publication_no_seq'),encode(public.digest(cast(:p as text)::bytea,'sha256'),'hex'),transaction_timestamp(),'tester','BUILDING')")
      .param("p",set).update();
    db.sql("insert into ouf_sem.semantic_publication_member values(:p,:s,:r)").param("p",set).param("s",semanticId).param("r",revision).update();
    db.sql("update ouf_sem.semantic_publication_set set status='PUBLISHED' where publication_set_id=:p").param("p",set).update();
  }
}

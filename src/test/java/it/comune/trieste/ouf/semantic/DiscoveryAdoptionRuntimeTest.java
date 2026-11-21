package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.authorization.PrincipalContext;
import it.comune.trieste.ouf.authorization.PrincipalContext.ActorType;
import it.comune.trieste.ouf.semantic.api.SemanticDiscoveryDelegation;
import it.comune.trieste.ouf.semantic.application.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.simple.JdbcClient;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
class DiscoveryAdoptionRuntimeTest {
  @Autowired JdbcClient db;
  @Autowired ObjectMapper json;
  @Autowired ProposalCommandService commands;
  @Autowired GovernanceService governance;
  @Autowired SemanticReadService reads;
  @Autowired InterchangeService interchange;
  @Autowired DiscoveryService nativeDiscovery;

  private static final String SOURCE="https://example.org/catalogue/download.ttl";
  private static final String PUBLISHER="https://example.org/publisher";
  private static final String LICENSE="https://example.org/license";
  private static final PrincipalContext MAPPER=human("tenant-a","mapper","issuer");
  private static PrincipalContext human(String tenant,String subject,String issuer) {
    return new PrincipalContext(subject,tenant,ActorType.HUMAN,"gateway","1",issuer,"audience",Set.of("ouf.semantic.discovery"));
  }
  private record Candidate(UUID request,UUID id,String uri,byte[] bytes,String hash){}
  private Candidate seed(boolean expired,boolean licensed) throws Exception {
    return seed(expired,licensed,"https://example.org/onto/"+UUID.randomUUID(),MAPPER,"mapping");
  }
  private Candidate seed(boolean expired,boolean licensed,String uri,PrincipalContext principal,String intent) throws Exception {
    UUID candidate=UUID.randomUUID(),request=UUID.randomUUID();
    String rdf="# "+"comment retained ".repeat(256)+"\r\n<"+uri+"> a <http://www.w3.org/2002/07/owl#Class> ;\n"
        +" <http://purl.org/dc/terms/publisher> <"+PUBLISHER+"> .\n"
        +(licensed?"<"+uri+"> <http://purl.org/dc/terms/license> <"+LICENSE+"> .\n":"")
        +"<urn:unrelated> <http://purl.org/dc/terms/license> <urn:wrong> .\n";
    byte[] bytes=rdf.getBytes(StandardCharsets.UTF_8);
    String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    db.sql("""
        insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,state,created_by_subject)
        values(:id,'CLASS',:intent,'SUCCEEDED',:actor)
        """).param("id",request).param("intent",intent).param("actor",SemanticDiscoveryDelegation.jobSubject(principal,json)).update();
    db.sql("""
        insert into ouf_sem.discovery_candidate(candidate_id,request_id,provider_id,canonical_uri,source_location,
          artifact_type,provider_trust,score,normalized_payload,content_hash,media_type,content_bytes,expires_at)
        values(:id,:r,'TEST',:uri,:source,'CLASS','HIGH',1,'{}',:hash,'text/turtle',:bytes,
          clock_timestamp()+cast(:ttl as interval))
        """).param("id",candidate).param("r",request).param("uri",uri).param("source",SOURCE).param("hash",hash)
        .param("bytes",bytes).param("ttl",expired?"-1 hour":"1 hour").update();
    return new Candidate(request,candidate,uri,bytes,hash);
  }

  @ParameterizedTest @ValueSource(booleans={true,false})
  void adoptedBytesAndReviewedProvenanceSurvivePublication(boolean licensed) throws Exception {
    var c=seed(false,licensed);
    String key=c.id().toString();
    var receipt=commands.adopt(MAPPER,key,c.request(),c.id());
    assertThat(receipt).containsEntry("requestId",c.request().toString()).containsEntry("candidateId",key)
        .containsEntry("expectedRowVersion",0).containsEntry("status","DRAFT").containsEntry("semanticId",c.uri());
    JsonNode source=json.valueToTree(receipt.get("provenance"));
    assertThat(source.required("canonicalUri").asText()).isEqualTo(c.uri());
    assertThat(source.required("sourceLocation").asText()).isEqualTo(SOURCE);
    assertThat(source.required("providerId").asText()).isEqualTo("TEST");
    assertThat(source.required("publisher").asText()).isEqualTo(PUBLISHER);
    assertThat(source.required("rdfSha256").asText()).isEqualTo(c.hash());
    assertThat(source.required("license").textValue()).isEqualTo(licensed?LICENSE:null);
    assertThat(source.required("licenseWarning").textValue()).isEqualTo(licensed?null:"licenza mancante");
    UUID snapshot=UUID.fromString(source.required("snapshotId").asText());
    UUID revision=UUID.fromString(receipt.get("revisionId").toString());
    UUID artifact=UUID.fromString(receipt.get("artifactId").toString());
    assertThat(commands.adopt(MAPPER,key,c.request(),c.id())).isEqualTo(receipt);
    assertThat(db.sql("select count(*) from ouf_sem.artifact_revision r join ouf_sem.semantic_artifact a using(artifact_id) where a.semantic_id=:uri and a.origin_kind='EXTERNAL' and lifecycle_status='DRAFT'")
        .param("uri",c.uri()).query(Long.class).single()).isOne();
    assertThatThrownBy(()->commands.adopt(MAPPER,key,c.request(),UUID.randomUUID())).hasMessage("IDEMPOTENCY_KEY_REUSE");
    var next=seed(false,licensed,c.uri(),MAPPER,licensed?"mapping":"second CSV");
    assertThat(commands.adopt(MAPPER,key+"-next",next.request(),next.id()))
        .containsEntry("status","DRAFT").containsEntry("revisionId",revision.toString());
    var foreign=human("tenant-b","mapper","issuer");
    var privateLookup=seed(false,licensed,c.uri(),foreign,"mapping");
    assertThatThrownBy(()->commands.adopt(foreign,key,privateLookup.request(),privateLookup.id()))
        .hasMessage("SEMANTIC_CANDIDATE_NOT_FOUND");

    String tenant=MAPPER.tenantId(),subject=MAPPER.subjectId();
    var run=commands.validate(tenant,subject,key+"-prepare",revision,0);
    assertThat(run.get("status")).isEqualTo("PASS");
    UUID validation=UUID.fromString(run.get("validation_run_id").toString());
    var review=commands.review(tenant,subject,"HUMAN",key+"-review",revision,0,validation,key);
    UUID challenge=UUID.fromString(review.get("challengeId").toString());
    assertThat(commands.adopt(MAPPER,key+"-resume",next.request(),next.id())).containsEntry("status","UNDER_REVIEW")
        .containsEntry("revisionId",revision.toString()).containsEntry("challengeId",challenge.toString());
    var card=governance.card(challenge);
    assertThat(card.get("semantic_version")).isEqualTo("1.0.0");
    JsonNode reviewed=json.valueToTree(card.get("adoptionProvenance"));
    assertThat(reviewed).isEqualTo(source);
    assertThat(((Map<?,?>)card.get("definition_json")).get("adoptionProvenance")).isEqualTo(card.get("adoptionProvenance"));
    var decision=governance.decide(challenge,"APPROVED","reviewer","HUMAN","fixture:decision",key);
    var publication=governance.publish(revision,(UUID)decision.get("decisionId"),key+"-publish",
        (String)review.get("targetContentHash"),"reviewer","HUMAN",key);
    UUID set=(UUID)publication.get("publicationSetId");
    // This later manifest also contains c. The reference must still identify c's publication.
    var other=seed(false,true);
    String otherKey=other.id().toString();
    var otherAdoption=commands.adopt(MAPPER,otherKey,other.request(),other.id());
    UUID otherRevision=UUID.fromString(otherAdoption.get("revisionId").toString());
    var green=commands.validate(tenant,subject,otherKey+"-prepare",otherRevision,0);
    var otherReview=commands.review(tenant,subject,"HUMAN",otherKey+"-review",otherRevision,0,
        UUID.fromString(green.get("validation_run_id").toString()),otherKey);
    var approved=governance.decide(UUID.fromString(otherReview.get("challengeId").toString()),
        "APPROVED","reviewer","HUMAN","fixture:decision",otherKey);
    var later=governance.publish(otherRevision,(UUID)approved.get("decisionId"),otherKey,(String)otherReview.get("targetContentHash"),
        "reviewer","HUMAN",otherKey);
    assertThat(reads.resolve(c.uri(),revision,(UUID)later.get("publicationSetId"))).containsEntry("revision_id",revision);
    var terms=reads.publishedTerms(List.of(otherRevision,revision)).terms();
    assertThat(terms).extracting(SemanticReadService.PublishedTerm::revisionId).containsExactly(otherRevision,revision);
    var original=terms.get(1);
    assertThat(original.publicationSetId()).isEqualTo(set);
    assertThat(original.license()).isEqualTo(licensed ? LICENSE : null);
    assertThat(original.licenseWarning()).isEqualTo(licensed ? null : "licenza mancante");
    var second=seed(false,licensed,c.uri(),MAPPER,licensed?"mapping":"second CSV");
    for(var reused:List.of(commands.adopt(MAPPER,key,c.request(),c.id()),
        commands.adopt(MAPPER,key+"-same",c.request(),c.id()),commands.adopt(MAPPER,key+"-second",second.request(),second.id()))) {
      assertThat(reused).containsEntry("status","ACTIVE").containsEntry("semanticId",c.uri())
          .containsEntry("revisionId",revision.toString()).containsEntry("publicationSetId",set.toString());
      assertThat(reads.resolve(c.uri(),revision,set)).containsEntry("publication_set_id",set);
    }
    assertThat(commands.adopt(foreign,key,privateLookup.request(),privateLookup.id()))
        .containsEntry("status","ACTIVE").containsEntry("publicationSetId",set.toString());
    var drift=seed(false,!licensed,c.uri(),MAPPER,"changed RDF");
    assertThatThrownBy(()->commands.adopt(MAPPER,key+"-drift",drift.request(),drift.id())).hasMessage("SEMANTIC_IDENTITY_MISMATCH");
    assertThat(db.sql("select count(*) from ouf_sem.artifact_revision where artifact_id=:a")
        .param("a",artifact).query(Long.class).single()).isOne();
    assertThat(db.sql("select count(*) from ouf_sem.publish_claim where revision_id=:r")
        .param("r",revision).query(Long.class).single()).isOne();
    governance.lifecycle(revision,"DEPRECATED","reviewer","HUMAN","fixture:decision",key);
    assertThat(reads.publishedTerms(List.of(revision))).isEqualTo(new SemanticReadService.PublishedTerms(List.of(),List.of(revision)));
    var rdf=(Map<?,?>)reads.resolve(c.uri(),revision,set).get("rdf_snapshot");
    assertThat(rdf.get("snapshot_id")).isEqualTo(snapshot);
    assertThat(rdf.get("content_hash")).isEqualTo(c.hash());
    assertThat(Base64.getDecoder().decode((String)rdf.get("content_base64"))).isEqualTo(c.bytes());
    var bounded=(Map<?,?>)new SemanticReadService(db,json,4096).resolve(c.uri(),revision,set).get("rdf_snapshot");
    assertThat(bounded.containsKey("content_base64")).isFalse();
    assertThat(bounded.get("content_path")).isEqualTo("/api/semantic/v1/publication-sets/"+set+"/artifacts/"+artifact);
    assertThat(interchange.export(set,artifact,"text/turtle").body()).isEqualTo(c.bytes());
    assertThat(commands.receipt(tenant,subject,key).get("result")).isEqualTo(receipt);
    assertThatThrownBy(()->commands.adopt(MAPPER,key,c.request(),c.id())).hasMessage("SEMANTIC_REVISION_UNAVAILABLE");
  }

  @Test void onlyTheJobIdentityCanAdoptAndExpiryRollsBackReceipt() throws Exception {
    var c=seed(false,true);
    String key=c.id().toString();
    for(var other:List.of(human("tenant-a","other","issuer"),human("tenant-b","mapper","issuer"),human("tenant-a","mapper","other"))) {
      assertThatThrownBy(()->commands.adopt(other,key,c.request(),c.id())).hasMessage("SEMANTIC_CANDIDATE_NOT_FOUND");
    }
    assertThatThrownBy(()->nativeDiscovery.adopt(c.request(),c.id(),c.uri(),"ns","name","owner","authority","other"))
        .hasMessage("SEMANTIC_CANDIDATE_NOT_FOUND");
    var expired=seed(true,false);
    for(var type:List.of(ActorType.SERVICE,ActorType.AI_AGENT)) {
      var otherType=new PrincipalContext("mapper","tenant-a",type,"gateway","1","issuer","audience",Set.of("ouf.semantic.discovery"));
      assertThatThrownBy(()->commands.adopt(otherType,key,c.request(),c.id())).hasMessage("SEM_HUMAN_REQUIRED");
    }
    assertThatThrownBy(()->commands.adopt(MAPPER,key,expired.request(),expired.id())).hasMessage("CANDIDATE_EXPIRED");
    assertThatThrownBy(()->commands.receipt("tenant-a","mapper",key)).hasMessage("PROPOSAL_RECEIPT_NOT_FOUND");
    assertThat(db.sql("select count(*) from ouf_sem.semantic_artifact where semantic_id in (:a,:b)")
        .param("a",c.uri()).param("b",expired.uri()).query(Long.class).single()).isZero();
  }

  @Test void concurrentDiscoveriesOfOneClassResumeOneDraft() throws Exception {
    var one=seed(false,true);
    var two=seed(false,true,one.uri(),MAPPER,"second CSV");
    var start=new java.util.concurrent.CountDownLatch(1);
    try(var pool=java.util.concurrent.Executors.newFixedThreadPool(2)) {
      var first=pool.submit(()->{start.await();return commands.adopt(MAPPER,one.id().toString(),one.request(),one.id());});
      var second=pool.submit(()->{start.await();return commands.adopt(MAPPER,two.id().toString(),two.request(),two.id());});
      start.countDown();
      var draft=first.get(10,java.util.concurrent.TimeUnit.SECONDS);
      assertThat(second.get(10,java.util.concurrent.TimeUnit.SECONDS))
          .containsEntry("revisionId",draft.get("revisionId")).containsEntry("status","DRAFT");
    }
    assertThat(db.sql("select count(*) from ouf_sem.immutable_semantic_snapshot s join ouf_sem.external_semantic_origin o using(origin_id) where canonical_uri=:uri")
        .param("uri",one.uri()).query(Long.class).single()).isOne();
  }

  @Test void editingTheDraftCannotReplaceItsAttestedProvenance() throws Exception {
    var c=seed(false,false);
    String key=c.id().toString();
    var receipt=commands.adopt(MAPPER,key,c.request(),c.id());
    UUID revision=UUID.fromString(receipt.get("revisionId").toString());
    db.sql("""
        select ouf_sem.edit_draft(:r,0,'{}','{"adoptionProvenance":{"publisher":"caller","license":"caller"}}')
        """).param("r",revision).query(Long.class).single();
    String stored=db.sql("select (definition_json->'adoptionProvenance')::text from ouf_sem.artifact_revision where revision_id=:r")
        .param("r",revision).query(String.class).single();
    JsonNode expected=json.valueToTree(receipt.get("provenance"));
    assertThat(json.readTree(stored)).isEqualTo(expected);
    assertThatThrownBy(()->commands.validate("tenant-a","mapper",key+"-stale",revision,0)).hasMessage("DRAFT_VERSION_CONFLICT");
  }
}

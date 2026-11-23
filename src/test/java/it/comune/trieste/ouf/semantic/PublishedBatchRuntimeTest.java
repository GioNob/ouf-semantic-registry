package it.comune.trieste.ouf.semantic;

import static it.comune.trieste.ouf.semantic.application.PublishedBatchSearch.*;
import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.application.PublishedBatchSearch;
import java.sql.Connection;
import java.util.*;
import java.util.stream.IntStream;
import javax.sql.DataSource;
import org.junit.jupiter.api.Test;
import org.mockito.AdditionalAnswers;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.jdbc.datasource.DataSourceUtils;
import org.springframework.jdbc.datasource.SingleConnectionDataSource;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
@Transactional
class PublishedBatchRuntimeTest {
  @Autowired JdbcClient db;
  @Autowired DataSource dataSource;
  @Autowired PublishedBatchSearch reads;
  @Autowired ObjectMapper json;
  @Autowired org.springframework.transaction.PlatformTransactionManager transactions;
  final String ns = "fixture-" + UUID.randomUUID();
  record Pin(UUID artifact, UUID revision, String id) {}

  Pin term(String suffix, String local, String labels, ArtifactType type, String status) {
    var pin = new Pin(UUID.randomUUID(),UUID.randomUUID(),"urn:"+ns+":"+suffix);
    db.sql("""
        insert into ouf_sem.semantic_artifact(artifact_id,semantic_id,artifact_type,namespace,local_name,owner_ref,authority_ref,origin_kind)
        values(:a,:id,:type,:ns,:local,'fixture','fixture','OUF')
        """).param("a",pin.artifact()).param("id",pin.id()).param("type",type.name()).param("ns",ns).param("local",local).update();
    revision(pin,labels,status,1);
    db.sql("insert into ouf_sem.artifact_active_revision values(:a,:r,now(),'fixture')")
        .param("a",pin.artifact()).param("r",pin.revision()).update();
    return pin;
  }
  void revision(Pin pin,String labels,String status,int number) {
    db.sql("""
        insert into ouf_sem.artifact_revision(revision_id,artifact_id,revision_no,lifecycle_status,semantic_version,
          label_json,definition_json,created_by_subject,published_at)
        values(:r,:a,:n,:status,'1.0.0',cast(:labels as jsonb),'{"domainRefs":["urn:D"]}','fixture',
               case when :status='ACTIVE' then now() end)
        """).param("r",pin.revision()).param("a",pin.artifact()).param("n",number)
        .param("labels",labels).param("status",status).update();
  }
  UUID membership(Pin pin,String id,String state) {
    UUID set = UUID.randomUUID();
    db.sql("""
        insert into ouf_sem.semantic_publication_set values(:p,nextval('ouf_sem.publication_no_seq'),
          encode(sha256(convert_to(cast(:p as text),'UTF8')),'hex'),now(),'fixture',:state)
        """).param("p",set).param("state",state).update();
    db.sql("insert into ouf_sem.semantic_publication_member values(:p,:s,:r)")
        .param("p",set).param("s",id).param("r",pin.revision()).update();
    return set;
  }
  Intent intent(String id,String term,List<String> langs,ArtifactType type) {
    return new Intent(id,normalize(term),langs,new Filter(type,ns,null,null));
  }

  @Test void ranksBestEvidencePerRevisionBeforeLimitingAndPreservesInputOrder() {
    var it = term("z","nome","{\"it\":\"Caffè\",\"en\":\"caffè lungo\"}",ArtifactType.CLASS,"ACTIVE");
    var en = term("a","altro","{\"EN\":\"Caffè\"}",ArtifactType.CLASS,"ACTIVE");
    var local = term("b","CAFFÈ","{\"it\":\"bevanda\"}",ArtifactType.CLASS,"ACTIVE");
    for (var pin : List.of(it,en,local)) membership(pin,pin.id(),"PUBLISHED");
    var latest = membership(it,it.id(),"PUBLISHED");
    var first = intent("second","CAFFE\u0300",List.of("it","en"),ArtifactType.CLASS);
    var reversed = intent("first","caffè",List.of("en","it"),ArtifactType.CLASS);
    var weak = intent("weak","caf",List.of("en"),ArtifactType.CLASS);
    var none = intent("none","caffe",List.of("it"),ArtifactType.CLASS);
    var input = List.of(first,reversed,weak,none);
    var results = reads.search(input,1, id -> true).results();
    assertThat(results).extracting(Result::intentId).containsExactly("second","first","weak","none");
    assertThat(results.get(0)).isEqualTo(new Result("second",State.AMBIGUOUS,true,List.of(new Hit(it.id(),"1.0.0",
        it.revision(),latest,100,List.of("EXACT_LABEL","PREFERRED_LANGUAGE","CONTEXT_MATCH")))));
    assertThat(results.get(1).hits().getFirst().semanticId()).isEqualTo(en.id());
    var strongAndWeak = reads.search(List.of(intent("en","caffè",List.of("en"),ArtifactType.CLASS)),1,id -> true)
        .results().getFirst();
    assertThat(strongAndWeak.state()).isEqualTo(State.MATCH);
    assertThat(strongAndWeak.hasMore()).isTrue();
    assertThat(strongAndWeak.hits().getFirst().semanticId()).isEqualTo(en.id());
    assertThat(results.get(2).state()).isEqualTo(State.AMBIGUOUS);
    assertThat(results.get(2).hits().getFirst().score()).isEqualTo(60);
    assertThat(results.get(2).hits().getFirst().reasons()).containsExactly("LABEL_PREFIX","PREFERRED_LANGUAGE","CONTEXT_MATCH");
    assertThat(results.get(3)).isEqualTo(new Result("none",State.NONE,false,List.of()));
    assertThat(reads.search(input,1,id -> true).results()).isEqualTo(results);
    var all = reads.search(List.of(first),8,id -> true).results().getFirst();
    assertThat(all.hits()).extracting(Hit::score).containsExactly(100,100,95);
    assertThat(all.hits().getLast().reasons()).containsExactly("EXACT_LOCAL_NAME","PREFERRED_LANGUAGE","CONTEXT_MATCH");
    var one = reads.search(List.of(first),1,id -> id.equals(local.artifact())).results().getFirst();
    assertThat(one.state()).isEqualTo(State.MATCH);
    assertThat(one.hasMore()).isFalse();
  }

  @Test void excludesEveryNonCurrentOrInvisiblePinAndAppliesBothContextSources() {
    var labels = "{\"it\":\"segnale\"}";
    var good = term("good","g",labels,ArtifactType.PROPERTY,"ACTIVE");
    var hidden = term("hidden","h",labels,ArtifactType.PROPERTY,"ACTIVE");
    var retired = term("retired","r",labels,ArtifactType.PROPERTY,"ACTIVE");
    var draft = term("draft","d",labels,ArtifactType.PROPERTY,"DRAFT");
    var old = term("old","o",labels,ArtifactType.PROPERTY,"ACTIVE");
    var building = term("building","b",labels,ArtifactType.PROPERTY,"ACTIVE");
    var mismatch = term("mismatch","m",labels,ArtifactType.PROPERTY,"ACTIVE");
    var datatype = term("datatype","t",labels,ArtifactType.DATATYPE,"ACTIVE");
    for (var pin : List.of(good,hidden,retired,draft,old,datatype)) membership(pin,pin.id(),"PUBLISHED");
    membership(building,building.id(),"BUILDING");
    membership(mismatch,good.id(),"PUBLISHED");
    db.sql("update ouf_sem.semantic_artifact set retired_at=now() where artifact_id=:a").param("a",retired.artifact()).update();
    var replacement = new Pin(old.artifact(),UUID.randomUUID(),old.id());
    revision(replacement,labels,"ACTIVE",2);
    db.sql("update ouf_sem.artifact_active_revision set revision_id=:r where artifact_id=:a")
        .param("r",replacement.revision()).param("a",old.artifact()).update();
    db.sql("""
        insert into ouf_sem.semantic_dependency(source_revision_id,dependency_type,dependency_role,target_semantic_id)
        values(:r,'USES_CLASS','RANGE','urn:R')
        """).param("r",good.revision()).update();

    var base = intent("all","segnale",List.of("it"),ArtifactType.PROPERTY);
    var input = new ArrayList<>(List.of(base,intent("data","segnale",List.of("it"),ArtifactType.DATATYPE)));
    for (var filter : List.of(new Filter(ArtifactType.PROPERTY,ns,"urn:D","urn:R"),
        new Filter(ArtifactType.PROPERTY,ns,"urn:d","urn:R"),new Filter(ArtifactType.PROPERTY,ns,"urn:D","urn:r"),
        new Filter(ArtifactType.PROPERTY,ns+"x",null,null))) {
      input.add(new Intent("ctx"+input.size(),base.term(),base.languages(),filter));
    }
    var results = reads.search(input,8,id -> !id.equals(hidden.artifact())).results();
    assertThat(results).extracting(Result::state).containsExactly(State.MATCH,State.MATCH,State.MATCH,State.NONE,State.NONE,State.NONE);
    assertThat(results.getFirst().hits()).extracting(Hit::semanticId).containsExactly(good.id());
    assertThat(results.get(1).hits()).extracting(Hit::semanticId).containsExactly(datatype.id());
  }

  @Test void onePreparedSelectForOneAnd64IntentsIncludingHitsAndUtf8Ties(org.junit.jupiter.api.TestReporter reporter) throws Exception {
    String label = "c".repeat(65);
    for (String suffix : List.of("\uD800\uDC00","\uE000")) {
      var pin = term(suffix,suffix,json.writeValueAsString(Map.of("it",label)),ArtifactType.CLASS,"ACTIVE");
      membership(pin,pin.id(),"PUBLISHED");
    }
    var real = DataSourceUtils.getConnection(dataSource);
    var counted = mock(Connection.class,AdditionalAnswers.delegatesTo(real));
    var template = new JdbcTemplate(new SingleConnectionDataSource(counted,true));
    var measured = new PublishedBatchSearch(template,json);
    for (int n : List.of(1,64)) {
      clearInvocations(counted);
      var intents = IntStream.rangeClosed(1,n)
          .mapToObj(i -> intent("i"+i,label.substring(0,i),List.of("it"),ArtifactType.CLASS)).toList();
      var response = measured.search(intents,2,id -> true);
      assertThat(response.results()).hasSize(n).allSatisfy(result -> {
        assertThat(result.state()).isEqualTo(State.AMBIGUOUS);
        assertThat(result.hasMore()).isFalse();
        assertThat(result.hits()).extracting(Hit::semanticId).containsExactly("urn:"+ns+":\uE000","urn:"+ns+":\uD800\uDC00");
      });
      long statements = mockingDetails(counted).getInvocations().stream()
          .filter(call -> Set.of("prepareStatement","prepareCall","createStatement").contains(call.getMethod().getName())).count();
      reporter.publishEntry("jdbcStatementsFor"+n+"DistinctIntents",Long.toString(statements));
      assertThat(statements).as("istruzioni JDBC per %d intenti distinti con due riscontri ciascuno",n).isOne();
    }
  }

  @Test void concurrentPublicationBecomesVisibleOnlyToTheNextBatch() {
    var before = term("before","first","{\"it\":\"strada\"}",ArtifactType.PROPERTY,"ACTIVE");
    membership(before,before.id(),"PUBLISHED");
    var independent = new org.springframework.transaction.support.TransactionTemplate(transactions);
    independent.setPropagationBehavior(org.springframework.transaction.TransactionDefinition.PROPAGATION_REQUIRES_NEW);
    var published = new java.util.concurrent.atomic.AtomicBoolean();
    var intents = IntStream.range(0,64)
        .mapToObj(i -> intent("i"+i,"strada",List.of("it"),ArtifactType.PROPERTY)).toList();
    var snapshot = reads.search(intents,1,id -> {
      if (published.compareAndSet(false,true)) independent.executeWithoutResult(tx -> {
        var after = term("after","second","{\"it\":\"strada\"}",ArtifactType.PROPERTY,"ACTIVE");
        membership(after,after.id(),"PUBLISHED");
      });
      return true;
    });
    assertThat(published).isTrue();
    assertThat(snapshot.results()).hasSize(64).allSatisfy(result -> {
      assertThat(result.state()).isEqualTo(State.MATCH);
      assertThat(result.hits().getFirst().revisionId()).isEqualTo(before.revision());
    });
    assertThat(reads.search(intents,1,id -> true).results()).allSatisfy(result -> {
      assertThat(result.state()).isEqualTo(State.AMBIGUOUS);
      assertThat(result.hasMore()).isTrue();
    });
  }

  @Test void normV1UsesFullDefaultFoldingNfcAndUnicodeWhitespace() {
    assertThat(com.ibm.icu.lang.UCharacter.getUnicodeVersion().toString()).isEqualTo("15.1.0.0");
    assertThat(normalize("\u00a0Straße\u0085\u202fCAFÉ-01.\t")).isEqualTo("strasse café-01.");
    assertThat(normalize("CAFE\u0301")).isEqualTo(normalize("Café")).isNotEqualTo(normalize("cafe"));
    assertThat(normalize("Σςİı")).isEqualTo("σσi\u0307ı");
    assertThat(normalize("a\u200bb")).isEqualTo("a\u200bb");
  }
}

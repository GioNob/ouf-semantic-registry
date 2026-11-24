package it.comune.trieste.ouf.semantic.application;

import static org.assertj.core.api.Assertions.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.api.ProposalCommandApi.SourceColumn;
import java.util.*;
import org.junit.jupiter.api.Test;

class ValueMapReviewCardTest {
  private final ObjectMapper json = new ObjectMapper();

  @Test void valueMapReviewDiffUsesConceptIdentityAndPinnedLabels() {
    String original = "urn:concept:a";
    String other = "urn:concept:b";
    String vocabulary = "urn:vocabulary:1";
    UUID set = UUID.randomUUID();
    String pin = vocabulary + "@" + set;
    var labels = Map.of(vocabulary, "Vocabolario", original, "Etichetta corrente", other, "Secondo concetto");
    var previous = json.valueToTree(Map.of("targetVocabulary", pin, "entries",
        List.of(entry("same", original),entry("changed", original),entry("removed", original))));
    var current = json.valueToTree(Map.of("targetVocabulary", pin, "entries",
        List.of(entry("same", original),entry("changed", other),entry("added", other))));
    var source = new SourceColumn("codice_servizio", null);
    var review = ValueMapReviewCard.build("Mappa", current, labels, source, previous);
    assertThat(review.name()).isEqualTo("Mappa");
    assertThat(review.targetVocabulary()).isEqualTo(new ValueMapReviewCard.Vocabulary("Vocabolario", vocabulary, set));
    assertThat(review.entryCount()).isEqualTo(3);
    assertThat(review.entries()).extracting(ValueMapReviewCard.Entry::code).containsExactly("added", "changed", "same");
    assertThat(review.entries().getLast()).isEqualTo(new ValueMapReviewCard.Entry("same", original, "Etichetta corrente"));
    assertThat(review.changes()).isEqualTo(new ValueMapReviewCard.Changes(List.of("added"), List.of("removed"),
        List.of(new ValueMapReviewCard.Change("changed", original, other))));
    assertThat(json.valueToTree(review).at("/sourceColumn")).isEqualTo(json.valueToTree(Map.of("fieldName","codice_servizio")));
    assertThat(json.valueToTree(ValueMapReviewCard.build("Mappa", current, labels, null, null)).has("sourceColumn")).isFalse();
  }

  private static Map<String,String> entry(String code, String concept) {
    return Map.of("code",code,"concept",concept);
  }
}

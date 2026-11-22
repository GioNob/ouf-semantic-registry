package it.comune.trieste.ouf.semantic.application;

import static org.assertj.core.api.Assertions.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;
import org.junit.jupiter.api.Test;

class ValueMapReviewCardTest {
  private final ObjectMapper json = new ObjectMapper();

  @Test void valueMapReviewDiffUsesConceptIdentityAndPinnedLabels() {
    var original = new ValueMapReviewCard.Term("urn:concept:a", "Prima etichetta");
    var sameConcept = new ValueMapReviewCard.Term(original.identificativo(), "Etichetta corrente");
    var other = new ValueMapReviewCard.Term("urn:concept:b", "Secondo concetto");
    var vocabulary = new ValueMapReviewCard.Term("urn:vocabulary:1", "Vocabolario");
    var before = Map.of(vocabulary.identificativo(), vocabulary, original.identificativo(), original);
    var after = Map.of(vocabulary.identificativo(), vocabulary, sameConcept.identificativo(), sameConcept,
        other.identificativo(), other);
    String pin = vocabulary.identificativo() + "@00000000-0000-0000-0000-000000000000";
    var previous = json.valueToTree(Map.of("semantic_version", "1.0.0", "definition_json",
        Map.of("targetVocabulary", pin, "entries", List.of(entry("same", original),entry("changed", original),entry("removed", original)))));
    var current = json.valueToTree(Map.of("targetVocabulary", pin, "entries",
        List.of(entry("same", sameConcept),entry("changed", other),entry("added", other))));
    var review = ValueMapReviewCard.build("Mappa", current, after, previous, before);
    assertThat(review.numeroVoci()).isEqualTo(3);
    assertThat(review.voci()).extracting(ValueMapReviewCard.Entry::codice).containsExactly("added", "changed", "same");
    assertThat(review.voci().getLast().concetto()).isEqualTo(sameConcept);
    assertThat(review.versionePrecedente()).isEqualTo("1.0.0");
    assertThat(review.differenze()).containsExactly(
        new ValueMapReviewCard.Change("added", "Aggiunto", null, other),
        new ValueMapReviewCard.Change("changed", "Modificato", original, other),
        new ValueMapReviewCard.Change("removed", "Rimosso", original, null));
  }

  private static Map<String,String> entry(String code, ValueMapReviewCard.Term term) {
    return Map.of("code",code,"concept",term.identificativo());
  }
}

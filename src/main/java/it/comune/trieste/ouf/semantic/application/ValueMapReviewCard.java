package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.*;

final class ValueMapReviewCard {
  record Term(String identificativo, String etichetta) {}
  record Entry(String codice, Term concetto) {}
  record Change(String codice, String modifica, Term prima, Term dopo) {}
  record Review(String nome, Term vocabolario, int numeroVoci, List<Entry> voci,
      String versionePrecedente, List<Change> differenze) {}

  private ValueMapReviewCard() {}

  static Review build(String name, JsonNode definition, Map<String,Term> terms,
      JsonNode previous, Map<String,Term> previousTerms) {
    var entries = entries(definition, terms);
    var differences = new ArrayList<Change>();
    if (previous != null) {
      var before = entries(previous.path("definition_json"), previousTerms);
      var codes = new TreeSet<>(before.keySet());
      codes.addAll(entries.keySet());
      for (String code : codes) {
        Term oldTerm = before.get(code);
        Term newTerm = entries.get(code);
        if (oldTerm == null) differences.add(new Change(code, "Aggiunto", null, newTerm));
        else if (newTerm == null) differences.add(new Change(code, "Rimosso", oldTerm, null));
        else if (!oldTerm.identificativo().equals(newTerm.identificativo()))
          differences.add(new Change(code, "Modificato", oldTerm, newTerm));
      }
    }
    String vocabulary = vocabularyId(definition);
    return new Review(name, term(terms, vocabulary), entries.size(),
        entries.entrySet().stream().map(entry -> new Entry(entry.getKey(), entry.getValue())).toList(),
        previous == null ? "Prima pubblicazione" : previous.path("semantic_version").asText(), differences);
  }

  static String vocabularyId(JsonNode definition) {
    String pin = definition.path("targetVocabulary").asText();
    return pin.substring(0, pin.lastIndexOf('@'));
  }

  static Set<String> memberIds(JsonNode definition) {
    var ids = new LinkedHashSet<String>();
    ids.add(vocabularyId(definition));
    definition.path("entries").forEach(entry -> ids.add(entry.path("concept").asText()));
    return ids;
  }

  private static SortedMap<String,Term> entries(JsonNode definition, Map<String,Term> terms) {
    var entries = new TreeMap<String,Term>();
    definition.path("entries").forEach(entry ->
        entries.put(entry.path("code").asText(), term(terms, entry.path("concept").asText())));
    return entries;
  }

  private static Term term(Map<String,Term> terms, String id) {
    Term result = terms.get(id);
    if (result == null) throw new IllegalStateException("SEMANTIC_CARD_PIN_MISSING");
    return result;
  }

  static String name(JsonNode definition, JsonNode labels, String fallback) {
    return List.of(definition.path("labels"), labels).stream()
        .flatMap(label -> java.util.stream.Stream.of(label.path("it").asText(), label.path("en").asText()))
        .filter(label -> !label.isBlank()).findFirst().orElse(fallback);
  }
}

package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.JsonNode;
import it.comune.trieste.ouf.semantic.api.ProposalCommandApi.SourceColumn;
import java.util.*;

final class ValueMapReviewCard {
  record Vocabulary(String label, String semanticId, UUID publicationSetId) {}
  record Entry(String code, String concept, String conceptLabel) {}
  record Change(String code, String from, String to) {}
  record Changes(List<String> added, List<String> removed, List<Change> changed) {}
  @JsonInclude(JsonInclude.Include.NON_NULL)
  record Review(String name, Vocabulary targetVocabulary, int entryCount, List<Entry> entries,
      SourceColumn sourceColumn, Changes changes) {}

  private ValueMapReviewCard() {}

  static Review build(String name, JsonNode definition, Map<String,String> labels,
      SourceColumn sourceColumn, JsonNode previous) {
    var current = conceptsByCode(definition);
    String id = vocabularyId(definition);
    var vocabulary = new Vocabulary(label(labels,id),id,publicationSetId(definition));
    var entries = current.entrySet().stream()
        .map(entry -> new Entry(entry.getKey(),entry.getValue(),label(labels,entry.getValue()))).toList();
    var changes = previous==null?null:changes(conceptsByCode(previous),current);
    return new Review(name,vocabulary,entries.size(),entries,sourceColumn,changes);
  }

  private static Changes changes(SortedMap<String,String> before, SortedMap<String,String> current) {
    var added = current.keySet().stream().filter(code -> !before.containsKey(code)).toList();
    var removed = before.keySet().stream().filter(code -> !current.containsKey(code)).toList();
    var changed = current.entrySet().stream().filter(entry -> before.containsKey(entry.getKey())
        && !before.get(entry.getKey()).equals(entry.getValue()))
        .map(entry -> new Change(entry.getKey(),before.get(entry.getKey()),entry.getValue())).toList();
    return new Changes(added,removed,changed);
  }

  private static String vocabularyId(JsonNode definition) {
    String pin = definition.path("targetVocabulary").asText();
    return pin.substring(0, pin.lastIndexOf('@'));
  }

  static UUID publicationSetId(JsonNode definition) {
    String pin = definition.path("targetVocabulary").asText();
    return UUID.fromString(pin.substring(pin.lastIndexOf('@')+1));
  }

  static Set<String> memberIds(JsonNode definition) {
    var ids = new LinkedHashSet<String>();
    ids.add(vocabularyId(definition));
    definition.path("entries").forEach(entry -> ids.add(entry.path("concept").asText()));
    return ids;
  }

  private static SortedMap<String,String> conceptsByCode(JsonNode definition) {
    var entries = new TreeMap<String,String>();
    definition.path("entries").forEach(entry ->
        entries.put(entry.path("code").asText(),entry.path("concept").asText()));
    return entries;
  }

  private static String label(Map<String,String> labels, String id) {
    String result = labels.get(id);
    if (result == null) throw new IllegalStateException("SEMANTIC_CARD_PIN_MISSING");
    return result;
  }

  static String name(JsonNode definition, JsonNode labels, String fallback) {
    return List.of(definition.path("labels"), labels).stream()
        .flatMap(label -> java.util.stream.Stream.of(label.path("it").asText(), label.path("en").asText()))
        .filter(label -> !label.isBlank()).findFirst().orElse(fallback);
  }
}

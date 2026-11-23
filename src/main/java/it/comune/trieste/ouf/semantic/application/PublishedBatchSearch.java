package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ibm.icu.lang.UCharacter;
import com.ibm.icu.text.Normalizer2;
import java.nio.charset.StandardCharsets;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.*;
import java.util.function.Predicate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowCallbackHandler;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PublishedBatchSearch {
  public static final String CONTRACT = "ouf.semantic.published-batch.v1";
  public enum ArtifactType { PROPERTY, CLASS, DATATYPE }
  public record Filter(ArtifactType type, String namespace, String domain, String range) {
    boolean hasContext() { return namespace != null || domain != null || range != null; }
    // PostgreSQL identifiers cannot contain NUL. Such opaque filters have no possible match.
    boolean representable() {
      return java.util.stream.Stream.of(namespace, domain, range).filter(Objects::nonNull)
          .noneMatch(value -> value.indexOf(0) >= 0);
    }
  }
  public record Intent(String id, String term, List<String> languages, Filter filter) {}
  public record Hit(String semanticId, String semanticVersion, UUID revisionId, UUID publicationSetId,
                    int score, List<String> reasons) {}
  public enum State { MATCH, AMBIGUOUS, NONE }
  public record Result(String intentId, State state, boolean hasMore, List<Hit> hits) {}
  public record Response(String contract, List<Result> results) {}

  private static final java.util.regex.Pattern LANGUAGE =
      java.util.regex.Pattern.compile("[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8}){0,3}");
  public static boolean isLanguage(String value) {
    return value != null && LANGUAGE.matcher(value).matches();
  }

  private static final Normalizer2 NFC = Normalizer2.getNFCInstance();
  public static String normalize(String value) {
    String folded = NFC.normalize(UCharacter.foldCase(NFC.normalize(value), true));
    var out = new StringBuilder();
    boolean space = false;
    for (int pos = 0; pos < folded.length();) {
      int cp = folded.codePointAt(pos);
      pos += Character.charCount(cp);
      if (UCharacter.isUWhiteSpace(cp)) {
        space = !out.isEmpty();
      } else {
        if (space) out.append(' ');
        out.appendCodePoint(cp);
        space = false;
      }
    }
    return out.toString();
  }

  private static final String SQL = """
      select f.idx,a.artifact_id,a.semantic_id,a.local_name,r.semantic_version,r.revision_id,
             p.publication_set_id,r.label_json::text as label_json
      %s
      join jsonb_array_elements(cast(? as jsonb)) with ordinality f(data,idx)
        on a.artifact_type=f.data->>'type'
       and (f.data->>'namespace' is null or a.namespace=f.data->>'namespace')
       and (f.data->>'domain' is null or %s)
       and (f.data->>'range' is null or %s)
      where r.lifecycle_status='ACTIVE' and %s
      """.formatted(SemanticReadService.SEARCH_JOINS, SemanticReadService.referenceFilter("DOMAIN","f.data->>'domain'"),
          SemanticReadService.referenceFilter("RANGE","f.data->>'range'"), SemanticReadService.CURRENT_PUBLISHED);

  private final JdbcTemplate db;
  private final ObjectMapper json;
  public PublishedBatchSearch(JdbcTemplate db, ObjectMapper json) {
    this.db = db;
    this.json = json;
  }

  @Transactional(readOnly=true)
  public Response search(List<Intent> intents, int limit, Predicate<UUID> visible) {
    var ordered = intents.stream().map(intent -> new Ranking(intent, limit)).toList();
    var groups = new LinkedHashMap<Filter,List<Ranking>>();
    for (var ranking : ordered) {
      var filter = ranking.intent.filter();
      if (filter.representable()) groups.computeIfAbsent(filter, ignored -> new ArrayList<>()).add(ranking);
    }
    var byIndex = List.copyOf(groups.values());
    try {
      String filters = json.writeValueAsString(groups.keySet());
      db.query(connection -> {
        var query = connection.prepareStatement(SQL);
        query.setString(1, filters);
        query.setFetchSize(128);
        return query;
      }, (RowCallbackHandler) row -> {
        if (!visible.test(row.getObject("artifact_id", UUID.class))) return;
        var labels = new HashMap<String,List<String>>();
        try {
          json.readTree(row.getString("label_json")).fields().forEachRemaining(entry -> {
            if (entry.getValue().isTextual() && isLanguage(entry.getKey())) {
              var text = normalize(entry.getValue().textValue());
              if (!text.isEmpty()) labels.computeIfAbsent(entry.getKey().toLowerCase(Locale.ROOT),
                  ignored -> new ArrayList<>()).add(text);
            }
          });
        } catch (JsonProcessingException invalid) {
          throw new IllegalStateException("SEM_BATCH_CATALOG_INVALID", invalid);
        }
        String name = normalize(row.getString("local_name"));
        for (var ranking : byIndex.get(row.getInt("idx") - 1)) ranking.consider(row, name, labels);
      });
    } catch (JsonProcessingException impossible) {
      throw new IllegalStateException(impossible);
    }
    return new Response(CONTRACT, ordered.stream().map(Ranking::result).toList());
  }

  private record Ranked(Hit hit, int language, byte[] sortKey) {}
  private static final Comparator<Ranked> ORDER = Comparator
      .comparingInt((Ranked r) -> r.hit.score()).reversed()
      .thenComparingInt(Ranked::language)
      .thenComparing(Ranked::sortKey, Arrays::compareUnsigned)
      .thenComparing(r -> r.hit.revisionId().toString());

  private static final class Ranking {
    final Intent intent;
    final int limit;
    final List<Ranked> best = new ArrayList<>();
    int strong;
    boolean more;
    Ranking(Intent intent, int limit) { this.intent = intent; this.limit = limit; }

    void consider(ResultSet row, String name, Map<String,List<String>> labels) throws SQLException {
      int score = 0, language = -1;
      for (int i = 0; i < intent.languages().size(); i++) {
        var texts = labels.get(intent.languages().get(i));
        if (texts == null) continue;
        int candidate = 0;
        if (texts.contains(intent.term())) candidate = 100;
        else if (name.equals(intent.term())) candidate = 95;
        else if (texts.stream().anyMatch(text -> text.startsWith(intent.term()))) candidate = 60;
        if (candidate > score) { score = candidate; language = i; }
        if (score == 100) break;
      }
      if (score == 0) return;
      if (score >= 95 && strong < 2) strong++;
      String id = row.getString("semantic_id"), version = row.getString("semantic_version");
      if (!boundedText(id,2048) || !boundedText(version,128))
        throw new IllegalStateException("SEM_BATCH_CATALOG_INVALID");
      String evidence = switch (score) {
        case 100 -> "EXACT_LABEL";
        case 95 -> "EXACT_LOCAL_NAME";
        default -> "LABEL_PREFIX";
      };
      var reasons = intent.filter().hasContext() ? List.of(evidence,"PREFERRED_LANGUAGE","CONTEXT_MATCH")
          : List.of(evidence,"PREFERRED_LANGUAGE");
      var hit = new Hit(id, version, row.getObject("revision_id",UUID.class),
          row.getObject("publication_set_id",UUID.class), score, reasons);
      var ranked = new Ranked(hit,language,id.getBytes(StandardCharsets.UTF_8));
      int position = Collections.binarySearch(best, ranked, ORDER);
      best.add(-position - 1, ranked);
      if (best.size() > limit) { best.removeLast(); more = true; }
    }

    Result result() {
      var state = best.isEmpty() ? State.NONE : strong == 1 ? State.MATCH : State.AMBIGUOUS;
      return new Result(intent.id(),state,more,best.stream().map(Ranked::hit).toList());
    }
  }

  public static boolean boundedText(String text,int max) {
    return text != null && !text.isEmpty() && text.codePointCount(0,text.length()) <= max
        && StandardCharsets.UTF_8.newEncoder().canEncode(text);
  }
}

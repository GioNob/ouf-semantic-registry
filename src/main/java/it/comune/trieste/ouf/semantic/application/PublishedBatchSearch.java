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

  static final String SQL = """
      select f.idx, pin.*, evidence.score, evidence.preference
      from jsonb_array_elements(cast(? as jsonb)) with ordinality f(data,idx)
      cross join lateral (select convert_to(f.data->>'term','UTF8') as term, f.data->'filter' as filter) q
      cross join lateral (
        select distinct on (t.revision_id) t.revision_id,
               case when k.kind='LOCAL' then 95 when t.term=q.term then 100 else 60 end as score,
               l.preference
        from jsonb_array_elements_text(f.data->'languages') with ordinality l(language,preference)
        -- 0xff sorts after every valid UTF-8 suffix. LOCAL uses a closed singleton range.
        cross join lateral (values ('LABEL',q.term || decode('ff','hex')), ('LOCAL',q.term)) k(kind,upper_bound)
        cross join lateral (
          select revision_id, term from ouf_sem.revision_batch_term
          where artifact_type=q.filter->>'type' and language=l.language and kind=k.kind
            and term between q.term and k.upper_bound
          offset 0
        ) t
        order by t.revision_id,score desc,l.preference
      ) evidence
      cross join lateral (
        select a.artifact_id,a.semantic_id,r.semantic_version,r.revision_id,p.publication_set_id
        %s
        where r.revision_id=evidence.revision_id and r.lifecycle_status='ACTIVE' and %s
          and a.artifact_type=q.filter->>'type'
          and (q.filter->>'namespace' is null or a.namespace=q.filter->>'namespace')
          and (q.filter->>'domain' is null or %s)
          and (q.filter->>'range' is null or %s)
        offset 0
      ) pin
      """.formatted(SemanticReadService.SEARCH_JOINS, SemanticReadService.CURRENT_PUBLISHED,
          SemanticReadService.referenceFilter("DOMAIN","q.filter->>'domain'"),
          SemanticReadService.referenceFilter("RANGE","q.filter->>'range'"));

  private final JdbcTemplate db;
  private final ObjectMapper json;
  public PublishedBatchSearch(JdbcTemplate db, ObjectMapper json) {
    this.db = db;
    this.json = json;
  }

  @Transactional(readOnly=true)
  public Response search(List<Intent> intents, int limit, Predicate<UUID> visible) {
    var ordered = intents.stream().map(intent -> new Ranking(intent, limit)).toList();
    // PostgreSQL text cannot contain NUL, so these intents can only return NONE.
    var byIndex = ordered.stream().filter(r -> r.intent.filter().representable()
        && r.intent.term().indexOf(0) < 0).toList();
    try {
      String arguments = json.writeValueAsString(byIndex.stream().map(r -> r.intent).toList());
      db.query(connection -> {
        var query = connection.prepareStatement(SQL);
        query.setString(1, arguments);
        query.setFetchSize(128);
        return query;
      }, (RowCallbackHandler) row -> {
        if (visible.test(row.getObject("artifact_id", UUID.class)))
          byIndex.get(row.getInt("idx") - 1).consider(row);
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

    void consider(ResultSet row) throws SQLException {
      int score = row.getInt("score"), language = row.getInt("preference");
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

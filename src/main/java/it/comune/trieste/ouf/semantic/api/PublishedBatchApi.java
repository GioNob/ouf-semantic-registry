package it.comune.trieste.ouf.semantic.api;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.authorization.ResourceContext;
import it.comune.trieste.ouf.semantic.application.PublishedBatchSearch;
import it.comune.trieste.ouf.semantic.application.PublishedBatchSearch.*;
import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.sql.SQLException;
import java.security.DigestInputStream;
import java.util.*;
import java.util.regex.Pattern;
import java.util.zip.GZIPInputStream;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.dao.DataAccessException;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.CannotCreateTransactionException;
import org.springframework.web.bind.annotation.*;

@RestController
@ConditionalOnProperty(prefix="ouf.semantic.published-batch", name="enabled", havingValue="true")
public class PublishedBatchApi {
  private static final Logger log = LoggerFactory.getLogger(PublishedBatchApi.class);
  private static final String CAP = SemanticReadDelegation.BATCH;
  private static final Pattern ID = Pattern.compile("[A-Za-z0-9_-]{1,64}");
  private final SemanticReadDelegation receipts;
  private final PublishedBatchSearch reads;
  private final ObjectMapper json;
  private final int maxIntents, maxHits, maxRequestBytes, maxResponseBytes;

  public PublishedBatchApi(SemanticReadDelegation receipts, PublishedBatchSearch reads, ObjectMapper json,
      @Value("${ouf.semantic.published-batch.max-intents}") int maxIntents,
      @Value("${ouf.semantic.published-batch.max-hits}") int maxHits,
      @Value("${ouf.semantic.published-batch.max-request-bytes}") int maxRequestBytes,
      @Value("${ouf.semantic.published-batch.max-response-bytes}") int maxResponseBytes) {
    if (maxIntents < 1 || maxIntents > 64 || maxHits < 1 || maxHits > 8 ||
        maxRequestBytes < 1 || maxRequestBytes > 65536 || maxResponseBytes < 1 || maxResponseBytes > 262144)
      throw new IllegalArgumentException("SEM_BATCH_CONFIG_INVALID");
    this.receipts = receipts;
    this.reads = reads;
    this.json = json.copy().enable(JsonParser.Feature.STRICT_DUPLICATE_DETECTION)
        .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    this.maxIntents = maxIntents;
    this.maxHits = maxHits;
    this.maxRequestBytes = maxRequestBytes;
    this.maxResponseBytes = maxResponseBytes;
  }

  @PostMapping(path="/api/internal/v1/semantic/consultation/search-batch", produces=MediaType.APPLICATION_JSON_VALUE)
  public ResponseEntity<?> search(HttpServletRequest request) throws IOException {
    String encoding = request.getHeader("Content-Encoding");
    boolean gzip = "gzip".equalsIgnoreCase(encoding);
    if (!gzip && encoding != null && !"identity".equalsIgnoreCase(encoding)) throw invalid();
    if (!gzip && request.getContentLengthLong() > maxRequestBytes) return error(413,"SEM_BATCH_REQUEST_TOO_LARGE");
    String digest = "unverified";
    String scope = "unverified";
    try {
      var signed = receipts.signed(request,CAP);
      scope = SemanticReadDelegation.digest(signed.principal().tenantId().getBytes(StandardCharsets.UTF_8));
      byte[] raw;
      var hash = SemanticReadDelegation.sha256();
      try (var wire = new DigestInputStream(request.getInputStream(),hash);
           var decoded = gzip ? new GZIPInputStream(wire) : wire) {
        raw = decoded.readNBytes(maxRequestBytes + 1);
        if (raw.length > maxRequestBytes) return error(413,"SEM_BATCH_REQUEST_TOO_LARGE");
        // Include every forwarded octet in the receipt, including any gzip reader look-ahead.
        if (gzip) wire.transferTo(OutputStream.nullOutputStream());
      } catch (java.util.zip.ZipException | java.io.EOFException malformed) { throw invalid(); }
      digest = HexFormat.of().formatHex(hash.digest());
      var owner = receipts.authorize(request,signed,digest,"semantic.artifact");
      var tenant = owner.principal().tenantId();
      JsonNode envelope;
      try {
        envelope = json.readTree(StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(raw)).toString());
      } catch (IOException malformed) { throw invalid(); }
      fields(envelope,Set.of("CapabilityID","GatewayBindingRef","Owner","OperationClass","Arguments",
          "MaxResultBytes","Identity","AuthorizationDecisionRef","CorrelationID","IdempotencyKey","AttemptID","RequestHash"));
      if (!SemanticReadDelegation.matchesDispatch(envelope,CAP,"READ")) throw invalid();
      int resultBytes = maxResponseBytes;
      if (envelope.has("MaxResultBytes")) {
        var negotiated = envelope.get("MaxResultBytes");
        if (!negotiated.isIntegralNumber() || negotiated.bigIntegerValue().signum() <= 0) throw invalid();
        resultBytes = negotiated.bigIntegerValue().min(java.math.BigInteger.valueOf(maxResponseBytes)).intValueExact();
      }
      var args = envelope.path("Arguments");
      fields(args,Set.of("contract","limitPerIntent","intents"));
      if (!PublishedBatchSearch.CONTRACT.equals(args.path("contract").textValue())) throw invalid();
      var limit = args.path("limitPerIntent");
      if (!limit.isIntegralNumber() || !limit.canConvertToInt() || limit.intValue() < 1 || limit.intValue() > maxHits)
        throw invalid();
      var intents = intents(args.path("intents"));
      var response = reads.search(intents,limit.intValue(),id -> {
        var resource = new ResourceContext("semantic.artifact",id.toString(),tenant,null,Map.of("module","SEMANTIC"));
        return owner.decide(CAP,resource).allowed() && owner.decide(SemanticReadDelegation.SEARCH,resource).allowed();
      });
      byte[] bytes = json.writeValueAsBytes(response);
      var counts = new EnumMap<State,Integer>(State.class);
      response.results().forEach(result -> counts.merge(result.state(),1,Integer::sum));
      boolean oversized = bytes.length > resultBytes;
      log.info("decision=ALLOW status={} capability={} scope={} ranking={} batch={} intents={} match={} ambiguous={} none={}",
          oversized ? 422 : 200,CAP,scope,PublishedBatchSearch.CONTRACT,digest,intents.size(),counts.getOrDefault(State.MATCH,0),
          counts.getOrDefault(State.AMBIGUOUS,0),counts.getOrDefault(State.NONE,0));
      if (oversized) return error(422,"SEM_BATCH_RESULT_TOO_LARGE");
      return ResponseEntity.ok().contentType(MediaType.APPLICATION_JSON).body(bytes);
    } catch (SecurityException denied) {
      log.info("decision=DENY capability={} scope={} ranking={} batch={}",CAP,scope,PublishedBatchSearch.CONTRACT,digest);
      return error(403,"SEM_READ_RECEIPT_OR_POLICY_DENIED");
    }
  }

  private List<Intent> intents(JsonNode array) {
    if (!array.isArray() || array.isEmpty() || array.size() > maxIntents) throw invalid();
    var ids = new HashSet<String>();
    var intents = new ArrayList<Intent>();
    for (var item : array) {
      fields(item,Set.of("intentId","intent","preferredLanguages","requestedArtifactType","context"));
      String id = string(item,"intentId",64);
      if (!ID.matcher(id).matches() || !ids.add(id)) throw invalid();
      String term = PublishedBatchSearch.normalize(string(item,"intent",256));
      if (!PublishedBatchSearch.boundedText(term,256)) throw invalid();
      var languages = new LinkedHashSet<String>();
      var list = item.path("preferredLanguages");
      if (!list.isArray() || list.isEmpty() || list.size() > 5) throw invalid();
      for (var language : list) {
        if (!PublishedBatchSearch.isLanguage(language.textValue()) ||
            !languages.add(language.textValue().toLowerCase(Locale.ROOT))) throw invalid();
      }
      ArtifactType type;
      try { type = ArtifactType.valueOf(string(item,"requestedArtifactType",8)); }
      catch (IllegalArgumentException wrongType) { throw invalid(); }
      var context = item.path("context");
      fields(context,Set.of("namespace","domain","range"));
      var filter = new Filter(type, optional(context,"namespace",512),optional(context,"domain",2048),
          optional(context,"range",2048));
      intents.add(new Intent(id,term,List.copyOf(languages),filter));
    }
    return intents;
  }

  private static void fields(JsonNode node,Set<String> allowed) {
    if (node == null || !node.isObject()) throw invalid();
    for (var keys = node.fieldNames(); keys.hasNext();) if (!allowed.contains(keys.next())) throw invalid();
  }
  private static String optional(JsonNode node,String field,int max) {
    return node.has(field) ? string(node,field,max) : null;
  }
  private static String string(JsonNode node,String field,int max) {
    String value = node.path(field).textValue();
    if (!PublishedBatchSearch.boundedText(value,max)) throw invalid();
    return value;
  }
  private static IllegalArgumentException invalid() { return new IllegalArgumentException("SEM_BATCH_ARGUMENTS_INVALID"); }
  private static ResponseEntity<?> error(int status,String code) {
    return ResponseEntity.status(status).body(Map.of("code",code));
  }

  @ExceptionHandler({DataAccessException.class,CannotCreateTransactionException.class})
  ResponseEntity<?> databaseFailure(RuntimeException failure) {
    for (Throwable cause = failure; cause != null; cause = cause.getCause()) {
      if (cause instanceof javax.net.ssl.SSLException) throw failure;
    }
    for (Throwable cause = failure; cause != null; cause = cause.getCause()) {
      if (cause instanceof SQLException sql && sql.getSQLState() != null) {
        switch (sql.getSQLState()) {
          case "53300": return error(429,"SEM_BATCH_RATE_LIMITED");
          case "08006","57P01","57P02","57P03","40001","40P01": return error(503,"SEM_BATCH_UNAVAILABLE");
          case "08001":
            if (sql.getCause() instanceof java.net.ConnectException || sql.getCause() instanceof java.net.SocketTimeoutException)
              return error(503,"SEM_BATCH_UNAVAILABLE");
        }
      }
    }
    throw failure;
  }
}

package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.SemanticReadService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.UUID;
import java.util.regex.Pattern;
import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class SemanticPublishedTermsApi {
  private static final int MAX_IDS = 64;
  private static final Pattern UUID_TEXT = Pattern.compile(
      "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}");
  private final SemanticReadService reads;
  private final TrustedActorResolver actors;

  public SemanticPublishedTermsApi(SemanticReadService reads, TrustedActorResolver actors) {
    this.reads = reads;
    this.actors = actors;
  }

  @GetMapping("/api/trusted-human/v1/semantic-published-terms")
  ResponseEntity<SemanticReadService.PublishedTerms> publishedTerms(HttpServletRequest request) {
    actors.requireReviewer(request);
    var ids = revisionIds(request.getParameterValues("revisionIds"));
    return ResponseEntity.ok().cacheControl(CacheControl.noStore()).body(reads.publishedTerms(ids));
  }

  private static List<UUID> revisionIds(String[] values) {
    if (values == null || values.length != 1 || values[0].length() > MAX_IDS * 37 - 1)
      throw new IllegalArgumentException("SEM_REVISION_IDS_INVALID");
    String[] tokens = values[0].split(",", -1);
    if (tokens.length > MAX_IDS) throw new IllegalArgumentException("SEM_REVISION_IDS_INVALID");
    var ids = new LinkedHashSet<UUID>();
    for (String token : tokens) {
      if (!UUID_TEXT.matcher(token).matches()) throw new IllegalArgumentException("SEM_REVISION_IDS_INVALID");
      ids.add(UUID.fromString(token));
    }
    return List.copyOf(ids);
  }
}

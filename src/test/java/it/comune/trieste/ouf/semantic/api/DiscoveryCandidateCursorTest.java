package it.comune.trieste.ouf.semantic.api;

import static org.assertj.core.api.Assertions.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.application.ArtifactService;
import it.comune.trieste.ouf.semantic.application.DiscoveryService.CandidatePosition;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class DiscoveryCandidateCursorTest {
  @TempDir Path directory;

  @Test void cursorExpiresAtTheEarlierOfEvidenceAndTraversalDeadlines() throws Exception {
    Path key=directory.resolve("owner-key");
    Files.writeString(key,"ab".repeat(32));
    var delegation=new SemanticDiscoveryDelegation(new ObjectMapper(),key.toString(),"issuer","audience","workload");
    var cursors=new DiscoveryCandidateCursor(delegation);
    Instant now=Instant.parse("2026-11-27T10:00:00Z");
    Instant evidence=now.plusSeconds(60);
    assertThat(DiscoveryCandidateCursor.deadline(now,now.plusSeconds(900))).isEqualTo(now.plusSeconds(300));
    assertThat(DiscoveryCandidateCursor.deadline(now,evidence)).isEqualTo(evidence);
    var continuation=new DiscoveryCandidateCursor.Continuation(new CandidatePosition(7,UUID.randomUUID()),
        new DiscoveryCandidateCursor.Options(true,false),evidence);
    byte[] binding={1,2,3};
    String cursor=cursors.encode(continuation,binding);
    assertThat(cursors.decode(cursor,binding,evidence.minusMillis(1))).isEqualTo(continuation);
    assertThatThrownBy(()->cursors.decode(cursor,binding,evidence))
        .isInstanceOf(ArtifactService.Conflict.class).hasMessage("SEM_DISCOVERY_CURSOR_EXPIRED");
  }
}

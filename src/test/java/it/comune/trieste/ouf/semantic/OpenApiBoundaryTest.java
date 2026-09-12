package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.assertThat;
import java.nio.file.*;
import org.junit.jupiter.api.Test;

class OpenApiBoundaryTest {
  @Test void approvalAndPublicationAreSeparatedFromMcpSurface() throws Exception {
    String mcp=Files.readString(Path.of("openapi/semantic-v1.yaml"));
    String ths=Files.readString(Path.of("openapi/semantic-ths-v1.yaml"));
    assertThat(mcp).contains("createSemanticApprovalChallenge","trustedApprovalRef")
        .doesNotContain("decideSemanticApproval","publishApprovedSemanticRevision");
    assertThat(ths).contains("x-ouf-mcp-exposed: false","decideSemanticApproval","publishApprovedSemanticRevision")
        .doesNotContain("x-ouf-mcp-capability");
  }
}

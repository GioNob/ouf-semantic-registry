package it.comune.trieste.ouf.semantic.api;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.*;
import java.nio.charset.StandardCharsets;
import java.time.*;
import org.junit.jupiter.api.Test;

/** Committed fixtures were emitted by actual materialized Gateway Lua in CI. */
class SemanticProposalLuaVectorTest {
  @Test void actualGatewayLuaReceiptsVerifyAtJavaOwner()throws Exception{
    var json=new ObjectMapper();
    var verifier=new SemanticProposalReceiptVerifier(json,"ab".repeat(32).getBytes(StandardCharsets.US_ASCII),
        "https://auth.test/realms/ouf","gateway","workload",Clock.fixed(Instant.ofEpochSecond(1000),ZoneOffset.UTC));
    try(var input=getClass().getResourceAsStream("/semantic-proposal-lua-vectors.json")){
      assertThat(input).isNotNull();var vectors=json.readTree(input);assertThat(vectors.size()).isEqualTo(4);
      for(var v:vectors){
        byte[] body=v.required("body").asText().getBytes(StandardCharsets.UTF_8);
        var verified=verifier.verify(v.required("proof").asText(),v.required("path").asText(),body);
        assertThat(verified.principal().context().actorType().name()).isEqualTo("AI_AGENT");
        assertThat(verified.principal().context().subjectId()).isEqualTo("human-a");
        assertThat(json.readTree(verified.arguments()).has("commandKey")).isEqualTo(v.required("path").asText().endsWith("/read"));
        assertThatThrownBy(()->verifier.verify(v.required("proof").asText(),v.required("path").asText(),"{}".getBytes(StandardCharsets.UTF_8)))
            .hasMessage("SEM_PROPOSAL_RECEIPT_INVALID");
      }
    }
  }
}

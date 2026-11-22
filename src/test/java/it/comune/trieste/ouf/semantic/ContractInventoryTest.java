package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.assertThat;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.*;
import org.junit.jupiter.api.Test;

class ContractInventoryTest {
  private final ObjectMapper json=new ObjectMapper();
  @Test void d084ContractMatchesFrozenBytes() throws Exception {
    byte[] bytes=Files.readAllBytes(Path.of("contracts/ouf-value-types-v1.json"));
    assertThat(java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)))
        .isEqualTo("3b85052e253b985f1082527eb595d2f02e5336047203deb3503a9766c1324295");
    assertThat(json.readTree(bytes).required("schema").asText()).isEqualTo("ouf.value-types.v1");
  }
  @Test void allBundledSchemasAreDraft202012AndParseable() throws Exception {
    try(var files=Files.list(Path.of("contracts"))){
      var frozen=java.util.Set.of("ouf-value-types-v1.json","ouf-value-maps-v1.json");
      var schemas=files.filter(p->p.toString().endsWith(".json") && !frozen.contains(p.getFileName().toString())).toList();
      assertThat(schemas).hasSize(13).contains(Path.of("contracts/semantic-reference-batch-v1.json"));
      for(var file:schemas){var root=json.readTree(file.toFile());assertThat(root.path("$schema").asText()).isEqualTo("https://json-schema.org/draft/2020-12/schema");assertThat(root.path("$id").asText()).startsWith("https://ouf.trieste.it/contracts/semantic/");}
    }
  }
  @Test void d084ValueMapsContractMatchesFrozenBytes() throws Exception {
    byte[] bytes=Files.readAllBytes(Path.of("contracts/ouf-value-maps-v1.json"));
    assertThat(java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)))
        .isEqualTo("40b247ad3422e09245a8314fdcc59ffe0b039e25733a2ca8f31aa6ba03ff2d2e");
    assertThat(json.readTree(bytes).required("schema").asText()).isEqualTo("ouf.value-maps.v1");
  }
}

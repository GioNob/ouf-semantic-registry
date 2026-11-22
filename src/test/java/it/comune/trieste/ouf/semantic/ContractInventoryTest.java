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
        .isEqualTo("4b90e85ecd1573404612ef0a0ee627feffaa9c189fe4363e82079bd07824c333");
    assertThat(json.readTree(bytes).required("schema").asText()).isEqualTo("ouf.value-types.v1");
  }
  @Test void allBundledSchemasAreDraft202012AndParseable() throws Exception {
    try(var files=Files.list(Path.of("contracts"))){
      var frozen=java.util.Set.of("ouf-value-types-v1.json","ouf-value-maps-v1.json");
      var schemas=files.filter(p->p.toString().endsWith(".json") && !frozen.contains(p.getFileName().toString())).toList();
      assertThat(schemas).hasSize(12);
      for(var file:schemas){var root=json.readTree(file.toFile());assertThat(root.path("$schema").asText()).isEqualTo("https://json-schema.org/draft/2020-12/schema");assertThat(root.path("$id").asText()).startsWith("https://ouf.trieste.it/contracts/semantic/");}
    }
  }
  @Test void d084ValueMapsContractMatchesFrozenBytes() throws Exception {
    byte[] bytes=Files.readAllBytes(Path.of("contracts/ouf-value-maps-v1.json"));
    assertThat(java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)))
        .isEqualTo("2f4528eb4c9c6bd9d2c6345464c8292f0cb3f36834cb2f54f81ae20e3dbe4a71");
    assertThat(json.readTree(bytes).required("schema").asText()).isEqualTo("ouf.value-maps.v1");
  }
}

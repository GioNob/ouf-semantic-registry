package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.assertThat;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.*;
import org.junit.jupiter.api.Test;

class ContractInventoryTest {
  private final ObjectMapper json=new ObjectMapper();
  @Test void allBundledSchemasAreDraft202012AndParseable() throws Exception {
    try(var files=Files.list(Path.of("contracts"))){
      var schemas=files.filter(p->p.toString().endsWith(".json")).toList();
      assertThat(schemas).hasSize(12);
      for(var file:schemas){var root=json.readTree(file.toFile());assertThat(root.path("$schema").asText()).isEqualTo("https://json-schema.org/draft/2020-12/schema");assertThat(root.path("$id").asText()).startsWith("https://ouf.trieste.it/contracts/semantic/");}
    }
  }
}

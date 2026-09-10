package it.comune.trieste.ouf.semantic.adapters.discovery;

import static org.assertj.core.api.Assertions.*;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider.Query;
import java.util.List;
import org.junit.jupiter.api.Test;

class SchemaGovProviderTest {
  @Test void queryIsBoundedAndSelectsOfficialSemanticKinds(){for(var type:List.of("CLASS","PROPERTY","RELATIONSHIP","CONCEPT","VOCABULARY","ONTOLOGY")){String q=SchemaGovProvider.query(new Query(type,"luogo",List.of("it")));assertThat(q).contains("LIMIT 50").contains("SELECT DISTINCT ?resource ?label");}}
  @Test void propertyIncludesObjectAndDatatypeProperties(){assertThat(SchemaGovProvider.query(new Query("PROPERTY","nome",List.of("it")))).contains("owl:ObjectProperty owl:DatatypeProperty");}
  @Test void literalCannotBreakOutOfQuery(){String q=SchemaGovProvider.query(new Query("CLASS","x\") } UNION { ?evil ?p ?o } #",List.of()));assertThat(q).contains("LCASE(\"x\\\") } UNION { ?evil ?p ?o } #\")");assertThat(q).endsWith("LIMIT 50");}
}

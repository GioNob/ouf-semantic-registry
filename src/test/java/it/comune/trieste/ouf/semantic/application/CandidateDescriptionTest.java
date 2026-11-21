package it.comune.trieste.ouf.semantic.application;

import static org.assertj.core.api.Assertions.assertThat;
import java.util.Map;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.vocabulary.*;
import org.junit.jupiter.api.Test;

class CandidateDescriptionTest {
  @Test void propertyUsesItsOwnCommentsAndDefinitionsWithinEachLanguage(){
    var model=ModelFactory.createDefaultModel();
    try {
      var property=model.createResource("urn:property");
      property.addProperty(RDF.type,OWL.DatatypeProperty);
      property.addProperty(SKOS.definition,"Definition","en");
      property.addProperty(SKOS.definition,"Fallback","it");
      property.addProperty(RDFS.comment,"Secondo","it").addProperty(RDFS.comment,"Primo","it");
      property.addProperty(RDFS.comment,"   ","en").addProperty(RDFS.comment,"Senza lingua");
      property.addProperty(SKOS.definition,model.createResource("urn:nonliteral"));
      model.createResource("urn:other").addProperty(RDFS.comment,"Autre","fr");
      assertThat(CandidateAdoptionService.descriptions(property))
          .isEqualTo(Map.of("en","Definition","it","Primo","und","Senza lingua"));
    } finally {model.close();}
  }

  @Test void boundsLanguagesDeterministicallyAndKeepsSupplementaryCodePointsWhole(){
    var model=ModelFactory.createDefaultModel();
    try {
      var property=model.createResource("urn:property");
      String prefix="a".repeat(4095)+"\uD83D\uDE00";
      property.addProperty(SKOS.definition,prefix+"z","en");
      for(char suffix='z';suffix>='a';suffix--)
        property.addProperty(RDFS.comment,"test","it-x-"+suffix);
      var descriptions=CandidateAdoptionService.descriptions(property);
      assertThat(descriptions).hasSize(16).containsEntry("en",prefix)
          .containsKey("it-x-o").doesNotContainKey("it-x-p");
    } finally {model.close();}
  }
}

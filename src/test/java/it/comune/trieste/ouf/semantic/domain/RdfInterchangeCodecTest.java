package it.comune.trieste.ouf.semantic.domain;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;

class RdfInterchangeCodecTest {
  final ObjectMapper json=new ObjectMapper();final RdfInterchangeCodec codec=new RdfInterchangeCodec(new SafeRdfParser());
  @Test void roundTripsAllFrozenRdfRepresentations() throws Exception {var model=codec.nativeView("https://example.test/Place","CLASS",json.readTree("{\"it\":\"Luogo\"}"),json.readTree("{\"it\":\"Definizione\"}"),json.readTree("{}"));for(String type:List.of("text/turtle","application/ld+json","application/rdf+xml","application/n-triples")){byte[] bytes=codec.serialize(model,type);assertThat(codec.parse(bytes,type).size()).isPositive();}}
  @Test void ontologyImportsAreSerializedButNeverDereferenced() throws Exception {var model=codec.nativeView("https://example.test/onto","ONTOLOGY",json.readTree("{}"),json.readTree("{}"),json.readTree("{\"imports\":[\"https://unreachable.invalid/ontology\"]}"));String turtle=new String(codec.serialize(model,"text/turtle"),StandardCharsets.UTF_8);assertThat(turtle).contains("unreachable.invalid/ontology");}
  @Test void csvIsRestrictedToTheVocabularyPathByServiceContract() throws Exception {byte[] csv=codec.vocabularyCsv("ouf:Status",json.readTree("{\"it\":\"Stato\",\"en\":\"Status\"}"),json.readTree("{}"));assertThat(new String(csv,StandardCharsets.UTF_8)).contains("semanticId,label,language").contains("\"it\"").contains("\"en\"");}
  @Test void importedIdentityAndTypeMustMatchPayload(){var model=codec.parse("<https://example.test/Real> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .".getBytes(),"application/n-triples");assertThatThrownBy(()->codec.validateImportedIdentity(model,"https://example.test/Forged","CLASS")).isInstanceOf(SafeRdfParser.UnsafeRdf.class).hasMessage("RDF_IDENTITY_OR_TYPE_MISMATCH");}
}

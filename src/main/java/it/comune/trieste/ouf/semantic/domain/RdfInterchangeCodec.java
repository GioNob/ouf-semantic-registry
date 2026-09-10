package it.comune.trieste.ouf.semantic.domain;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Iterator;
import org.apache.jena.rdf.model.*;
import org.apache.jena.riot.*;
import org.apache.jena.vocabulary.*;
import org.springframework.stereotype.Component;

@Component
public class RdfInterchangeCodec {
  private final SafeRdfParser parser;public RdfInterchangeCodec(SafeRdfParser parser){this.parser=parser;}
  public Model parse(byte[] bytes,String mediaType){return parser.model(bytes,mediaType);}
  public void validateImportedIdentity(Model model,String semanticId,String artifactType){Resource r=model.createResource(semanticId);boolean valid=switch(artifactType){case "CLASS"->model.contains(r,RDF.type,OWL.Class);case "RELATIONSHIP"->model.contains(r,RDF.type,OWL.ObjectProperty);case "PROPERTY"->model.contains(r,RDF.type,RDF.Property)||model.contains(r,RDF.type,OWL.ObjectProperty)||model.contains(r,RDF.type,OWL.DatatypeProperty);case "VOCABULARY"->model.contains(r,RDF.type,SKOS.ConceptScheme);case "CONCEPT"->model.contains(r,RDF.type,SKOS.Concept);case "ONTOLOGY"->model.contains(r,RDF.type,OWL.Ontology);default->false;};if(!valid)throw new SafeRdfParser.UnsafeRdf("RDF_IDENTITY_OR_TYPE_MISMATCH");}
  public byte[] serialize(Model model,String mediaType){Lang lang=switch(mediaType){case "text/turtle"->Lang.TURTLE;case "application/ld+json"->Lang.JSONLD;case "application/rdf+xml"->Lang.RDFXML;case "application/n-triples"->Lang.NTRIPLES;default->throw new IllegalArgumentException("RDF_MEDIA_TYPE_UNSUPPORTED");};var out=new ByteArrayOutputStream();RDFDataMgr.write(out,model,lang);return out.toByteArray();}
  public Model nativeView(String semanticId,String artifactType,JsonNode labels,JsonNode descriptions,JsonNode definition){Model m=ModelFactory.createDefaultModel();Resource r=m.createResource(semanticId);r.addProperty(RDF.type,type(m,artifactType,definition));addLocalized(r,RDFS.label,labels);addLocalized(r,RDFS.comment,descriptions);array(definition,"domainRefs").forEachRemaining(x->r.addProperty(RDFS.domain,m.createResource(x.asText())));array(definition,"rangeRefs").forEachRemaining(x->r.addProperty(RDFS.range,m.createResource(x.asText())));if(definition.hasNonNull("datatype"))r.addProperty(RDFS.range,m.createResource(definition.get("datatype").asText()));if(definition.hasNonNull("vocabularyRef"))r.addProperty(SKOS.inScheme,m.createResource(definition.get("vocabularyRef").asText()));array(definition,"imports").forEachRemaining(x->r.addProperty(OWL.imports,m.createResource(x.asText())));return m;}
  public byte[] vocabularyCsv(String semanticId,JsonNode labels,JsonNode definition){StringBuilder b=new StringBuilder("semanticId,label,language\n");labels.fields().forEachRemaining(e->b.append(csv(semanticId)).append(',').append(csv(e.getValue().asText())).append(',').append(csv(e.getKey())).append('\n'));return b.toString().getBytes(StandardCharsets.UTF_8);}
  private static Resource type(Model m,String type,JsonNode definition){return switch(type){case "CLASS"->OWL.Class;case "RELATIONSHIP"->OWL.ObjectProperty;case "PROPERTY"->definition.hasNonNull("datatype")?OWL.DatatypeProperty:RDF.Property;case "VOCABULARY"->SKOS.ConceptScheme;case "CONCEPT"->SKOS.Concept;case "ONTOLOGY"->OWL.Ontology;default->throw new IllegalArgumentException("RDF_ARTIFACT_TYPE_UNSUPPORTED");};}
  private static void addLocalized(Resource r,Property p,JsonNode values){if(values!=null&&values.isObject())values.fields().forEachRemaining(e->r.addProperty(p,r.getModel().createLiteral(e.getValue().asText(),e.getKey())));}
  private static Iterator<JsonNode> array(JsonNode n,String name){JsonNode a=n==null?null:n.get(name);return a!=null&&a.isArray()?a.elements():java.util.Collections.emptyIterator();}
  private static String csv(String value){return "\""+value.replace("\"","\"\"")+"\"";}
}

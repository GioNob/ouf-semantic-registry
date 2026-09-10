package it.comune.trieste.ouf.semantic.domain;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Set;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.riot.Lang;
import org.apache.jena.riot.RDFParser;
import org.springframework.stereotype.Component;

@Component
public class SafeRdfParser {
  public static final int MAX_BYTES=8*1024*1024;
  private static final Set<String> XML_MARKERS=Set.of("<!DOCTYPE","<!ENTITY","SYSTEM ","PUBLIC ");
  public Parsed parse(byte[] bytes,String mediaType){
    if(bytes==null||bytes.length==0||bytes.length>MAX_BYTES)throw new UnsafeRdf("RDF_SIZE_LIMIT");
    // Scan the complete bounded document: leading padding must not bypass the XML guard.
    String boundedText=new String(bytes,StandardCharsets.UTF_8).toUpperCase();
    if(XML_MARKERS.stream().anyMatch(boundedText::contains))throw new UnsafeRdf("RDF_EXTERNAL_ENTITY_FORBIDDEN");
    Lang lang=language(mediaType);
    try{Model model=read(bytes,lang);return new Parsed(model.size(),sha256(bytes));}
    catch(RuntimeException e){throw new UnsafeRdf("RDF_PARSE_FAILED",e);}
  }
  public Model model(byte[] bytes,String mediaType){parse(bytes,mediaType);return read(bytes,language(mediaType));}
  private static Model read(byte[] bytes,Lang lang){Model model=ModelFactory.createDefaultModel();RDFParser.create().source(new ByteArrayInputStream(bytes)).lang(lang).checking(true).parse(model);return model;}
  private static Lang language(String mediaType){return switch(mediaType){case "text/turtle"->Lang.TURTLE;case "application/ld+json"->Lang.JSONLD;case "application/rdf+xml"->Lang.RDFXML;case "application/n-triples"->Lang.NTRIPLES;default->throw new UnsafeRdf("RDF_MEDIA_TYPE_UNSUPPORTED");};}
  private static String sha256(byte[] b){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b));}catch(Exception e){throw new IllegalStateException(e);}}
  public record Parsed(long statementCount,String contentHash){}
  public static class UnsafeRdf extends RuntimeException{public UnsafeRdf(String m){super(m);}public UnsafeRdf(String m,Throwable t){super(m,t);}}
}

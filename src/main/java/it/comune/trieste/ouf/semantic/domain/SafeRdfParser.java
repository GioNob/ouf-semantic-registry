package it.comune.trieste.ouf.semantic.domain;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Locale;
import java.util.Set;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.riot.Lang;
import org.apache.jena.riot.RDFParser;
import org.apache.jena.riot.RiotException;
import org.apache.jena.riot.system.ErrorHandler;
import org.springframework.stereotype.Component;

@Component
public class SafeRdfParser {
  private static final ObjectMapper JSON=new ObjectMapper().enable(com.fasterxml.jackson.core.JsonParser.Feature.STRICT_DUPLICATE_DETECTION);
  public static final int MAX_BYTES=8*1024*1024;
  private static final Set<String> XML_MARKERS=Set.of("<!DOCTYPE","<!ENTITY");
  // RIOT's default handler can log fragments of invalid, provider-controlled input.
  private static final ErrorHandler QUIET_ERRORS=new ErrorHandler(){
    public void warning(String message,long line,long col){}
    public void error(String message,long line,long col){throw new RiotException("RDF_PARSE_FAILED");}
    public void fatal(String message,long line,long col){throw new RiotException("RDF_PARSE_FAILED");}
  };
  public Parsed parse(byte[] bytes,String mediaType){
    Model model=model(bytes,mediaType);
    try{return new Parsed(model.size(),sha256(bytes));}finally{model.close();}
  }
  public Model model(byte[] bytes,String mediaType){
    if(bytes==null||bytes.length==0||bytes.length>MAX_BYTES)throw new UnsafeRdf("RDF_SIZE_LIMIT");
    Lang lang=language(mediaType);
    if(lang==Lang.JSONLD)checkLocalContexts(bytes);
    if(lang==Lang.RDFXML){
      String boundedText=new String(bytes,StandardCharsets.UTF_8).toUpperCase(Locale.ROOT);
      if(XML_MARKERS.stream().anyMatch(boundedText::contains))throw new UnsafeRdf("RDF_EXTERNAL_ENTITY_FORBIDDEN");
    }
    Model model=ModelFactory.createDefaultModel();
    try{
      RDFParser.create().source(new ByteArrayInputStream(bytes)).lang(lang).checking(true).errorHandler(QUIET_ERRORS).parse(model);
      return model;
    }catch(RiotException invalid){model.close();throw new UnsafeRdf("RDF_PARSE_FAILED",invalid);}
    catch(RuntimeException unexpected){model.close();throw unexpected;}
  }
  public static void checkLocalContexts(byte[] bytes){
    try{rejectRemoteContexts(JSON.readTree(bytes));}
    catch(java.io.IOException e){throw new UnsafeRdf("SEM_READ_RDF_JSON_INVALID",e);}
  }
  private static void rejectRemoteContexts(JsonNode node){
    if(node==null)return;
    var context=node.get("@context");
    if(node.has("@import") || (context!=null && (context.isTextual() || (context.isArray()
        && java.util.stream.StreamSupport.stream(context.spliterator(),false).anyMatch(JsonNode::isTextual)))))
      throw new UnsafeRdf("SEM_READ_RDF_REMOTE_CONTEXT_FORBIDDEN");
    if(node.isContainerNode())node.forEach(SafeRdfParser::rejectRemoteContexts);
  }
  private static Lang language(String mediaType){return switch(mediaType){case "text/turtle"->Lang.TURTLE;case "application/ld+json"->Lang.JSONLD;case "application/rdf+xml"->Lang.RDFXML;case "application/n-triples"->Lang.NTRIPLES;case null,default->throw new UnsafeRdf("RDF_MEDIA_TYPE_UNSUPPORTED");};}
  private static String sha256(byte[] b){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b));}catch(Exception e){throw new IllegalStateException(e);}}
  public record Parsed(long statementCount,String contentHash){}
  public static class UnsafeRdf extends RuntimeException{public UnsafeRdf(String m){super(m);}public UnsafeRdf(String m,Throwable t){super(m,t);}}
}

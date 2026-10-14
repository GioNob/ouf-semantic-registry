package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import java.util.*;
import org.apache.jena.rdf.model.*;

/** Asserted RDF evidence from an exact immutable snapshot, without inference or I/O. */
public final class PublishedRdfSnapshot {
  public static final int MAX_STATEMENTS=1000;
  private final SafeRdfParser parser=new SafeRdfParser();
  private final ObjectMapper json=new ObjectMapper();

  public Map<String,Object> project(byte[] bytes,String mediaType,String hash,long count) {
    if(bytes==null || bytes.length==0 || bytes.length>SafeRdfParser.MAX_BYTES)
      throw new IllegalArgumentException("SEM_READ_RDF_SIZE_LIMIT");
    // Remote JSON-LD contexts/imports must not create an ungoverned fetch path.
    if("application/ld+json".equals(mediaType)) {
      try {rejectRemoteContexts(json.readTree(bytes));}
      catch(java.io.IOException e){throw new IllegalArgumentException("SEM_READ_RDF_JSON_INVALID",e);}
    }
    var parsed=parser.parse(bytes,mediaType);
    if(!parsed.contentHash().equals(hash) || parsed.statementCount()!=count)
      throw new IllegalStateException("SEM_READ_RDF_SNAPSHOT_MISMATCH");
    Model model=parser.model(bytes,mediaType);
    try {
      Comparator<Statement> order=Comparator
        .comparing((Statement s)->org.apache.jena.riot.out.NodeFmtLib.strNT(s.getSubject().asNode()))
        .thenComparing(s->s.getPredicate().getURI())
        .thenComparing(s->org.apache.jena.riot.out.NodeFmtLib.strNT(s.getObject().asNode()));
      var selected=new TreeSet<Statement>(order);
      var iterator=model.listStatements();
      try {
        while(iterator.hasNext()) {
          selected.add(iterator.nextStatement());
          if(selected.size()>MAX_STATEMENTS)selected.pollLast();
        }
      } finally {iterator.close();}
      List<Map<String,Object>> statements=new ArrayList<>();
      for(var s:selected)statements.add(Map.of("subject",node(s.getSubject()),
        "predicate",s.getPredicate().getURI(),"object",node(s.getObject())));
      return Map.of("content_hash",hash,"media_type",mediaType,"statement_count",count,
        "statements",statements,"partial",count>statements.size(),
        "interpretation","ASSERTED_RDF_NO_INFERENCE",
        "blank_node_scope","THIS_SNAPSHOT_RESPONSE",
        "term_reference_scope","CONTAINING_REVISION_AND_PUBLICATION_SET");
    } finally {model.close();}
  }
  private static Map<String,Object> node(RDFNode node) {
    if(node.isURIResource())return Map.of("kind","IRI","value",node.asResource().getURI());
    if(node.isAnon())return Map.of("kind","BLANK_NODE","value",node.asResource().getId().getLabelString());
    if(node.isLiteral()) {
      var literal=node.asLiteral();
      var out=new LinkedHashMap<String,Object>();
      out.put("kind","LITERAL");out.put("value",literal.getLexicalForm());
      out.put("language",literal.getLanguage());
      if(literal.getDatatypeURI()!=null)out.put("datatype",literal.getDatatypeURI());
      return out;
    }
    throw new IllegalArgumentException("SEM_READ_RDF_NODE_UNSUPPORTED");
  }
  private static void rejectRemoteContexts(JsonNode node) {
    if(node==null)return;
    if(node.isObject()) {
      if(node.has("@import"))throw new IllegalArgumentException("SEM_READ_RDF_REMOTE_CONTEXT_FORBIDDEN");
      JsonNode context=node.get("@context");
      if(context!=null && (context.isTextual() || (context.isArray() &&
          java.util.stream.StreamSupport.stream(context.spliterator(),false).anyMatch(JsonNode::isTextual))))
        throw new IllegalArgumentException("SEM_READ_RDF_REMOTE_CONTEXT_FORBIDDEN");
    }
    if(node.isContainerNode())node.forEach(PublishedRdfSnapshot::rejectRemoteContexts);
  }
}

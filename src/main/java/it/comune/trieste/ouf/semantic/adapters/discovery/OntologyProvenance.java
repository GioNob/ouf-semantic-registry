package it.comune.trieste.ouf.semantic.adapters.discovery;

import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.function.Function;
import java.util.function.Predicate;
import org.apache.jena.rdf.model.*;
import org.apache.jena.riot.out.NodeFmtLib;
import org.apache.jena.vocabulary.*;

/** One discovery attempt. Cache only bounded projections, including unavailable results. */
final class OntologyProvenance {
  record Evidence(byte[] triples, Map<String,String> labels, List<String> gaps) {}
  record Description(Map<String,String> labels,SortedSet<String> definitions) {}
  private static final Set<Property> TERMS=Set.of(DCTerms.publisher,DCTerms.license,DCTerms.rightsHolder,
      OWL.versionInfo,RDFS.label);
  private final SafeRdfParser parser=new SafeRdfParser();
  private final Map<String,Optional<byte[]>> projections=new HashMap<>();
  private final int limit;
  private final Predicate<String> admitted;
  private int namespaceExcluded;
  private boolean gatewayUnavailable;
  OntologyProvenance(int limit, Predicate<String> admitted){this.limit=limit;this.admitted=admitted;}
  int namespaceExcluded(){return namespaceExcluded;}

  Description inspect(String uri,BoundedGatewayClient.Response description){
    Model model=parser.model(description.body(),description.mediaType());
    try {
      var subject=model.getResource(uri);
      var labels=new TreeMap<String,String>();
      subject.listProperties(RDFS.label).forEachRemaining(s->{
        if(s.getObject().isLiteral()){
          Literal label=s.getLiteral();
          String lang=label.getLanguage().toLowerCase(Locale.ROOT);
          String value=label.getLexicalForm();
          if(!value.isBlank() && value.length()<=1024)
            labels.merge(lang.isEmpty()?"und":lang,value,(a,b)->a.compareTo(b)<=0?a:b);
        }
      });
      var definitions=new TreeSet<String>();
      subject.listProperties(RDFS.isDefinedBy).forEachRemaining(s->{
        if(s.getObject().isURIResource() && !uri.equals(s.getResource().getURI()))definitions.add(s.getResource().getURI());
      });
      return new Description(labels,definitions);
    } finally {model.close();}
  }

  Evidence read(Description description,Function<String,BoundedGatewayClient.Response> fetch){
    var labels=description.labels();
    var definitions=description.definitions();
    var joined=new java.io.ByteArrayOutputStream();
    boolean incomplete=definitions.size()>2;
    for(String link:definitions.stream().limit(2).toList()){
      var bytes=projections.computeIfAbsent(link,id->projection(id,fetch));
      if(bytes.isEmpty()){
        incomplete=true;
        continue;
      }
      if(bytes.get().length>limit-joined.size())
        return new Evidence(null,labels,List.of("ONTOLOGY_PROVENANCE_UNAVAILABLE"));
      joined.writeBytes(bytes.get());
    }
    return new Evidence(joined.size()==0?null:joined.toByteArray(),labels,
        incomplete?List.of("ONTOLOGY_PROVENANCE_UNAVAILABLE"):List.of());
  }

  private Optional<byte[]> projection(String uri,Function<String,BoundedGatewayClient.Response> fetch){
    if(gatewayUnavailable)return Optional.empty();
    if(!admitted.test(uri)){
      namespaceExcluded++;
      return Optional.empty();
    }
    try {
      var response=fetch.apply(uri);
      Model model=parser.model(response.body(),response.mediaType());
      try {
        var lines=new TreeSet<String>();
        int count=0;
        var statements=model.getResource(uri).listProperties();
        while(statements.hasNext()){
          Statement statement=statements.nextStatement();
          if(!TERMS.contains(statement.getPredicate()))continue;
          RDFNode object=statement.getObject();
          if(!object.isURIResource() && !object.isLiteral())return Optional.empty();
          String line=NodeFmtLib.strNT(statement.getSubject().asNode())+" "
              +NodeFmtLib.strNT(statement.getPredicate().asNode())+" "+NodeFmtLib.strNT(object.asNode())+" .\n";
          count+=line.getBytes(StandardCharsets.UTF_8).length;
          if(count>limit)return Optional.empty();
          lines.add(line);
        }
        return Optional.of(String.join("",lines).getBytes(StandardCharsets.UTF_8));
      } finally {model.close();}
    } catch(SafeRdfParser.UnsafeRdf rejected){return Optional.empty();}
    catch(BoundedGatewayClient.ProviderFailure failure){
      if(failure.decision().kind()==ProviderFailurePolicy.Kind.CANCELLED || Thread.currentThread().isInterrupted())throw failure;
      String code=failure.decision().code();
      gatewayUnavailable=failure.decision().kind()==ProviderFailurePolicy.Kind.TRANSIENT || code.startsWith("GATEWAY_")
          || code.equals("PROVIDER_TLS_UNPROVEN") || code.equals("PROVIDER_HTTP_401") || code.equals("PROVIDER_HTTP_403");
      return Optional.empty();
    }
  }
}

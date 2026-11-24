package it.comune.trieste.ouf.semantic.adapters.discovery;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.mockito.Mockito.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.io.*;
import java.net.URI;
import java.net.URLEncoder;
import java.time.*;
import java.util.*;
import org.apache.jena.rdf.model.*;
import org.apache.jena.riot.*;

/** Fake only the gateway transport, including its subject-only CONSTRUCT response. */
public final class OntopiaGatewayFixture {
  public static final String ONTOLOGY="https://w3id.org/italia/onto/POI";
  public static final String POI=ONTOLOGY+"/PointOfInterest";
  public final byte[] poiBytes;
  public final SemanticDiscoveryProvider provider;
  private final BoundedGatewayClient gateway=mock(BoundedGatewayClient.class);
  private final URI base=URI.create("https://gateway.invalid");
  private final int maxBytes=65536;

  private boolean available;
  private boolean changedOntology;
  public OntopiaGatewayFixture(ObjectMapper json) throws IOException {
    Duration timeout=Duration.ofSeconds(5);
    var cfg=new SchemaGovProperties(true,base,"/search","/fetch",timeout,timeout,maxBytes,5,1,
        Duration.ofSeconds(1),1,Duration.ofSeconds(30),List.of("https://w3id.org/italia/onto/"));
    provider=new SchemaGovProvider(cfg,gateway,json,Clock.systemUTC());
    Model ontology=ModelFactory.createDefaultModel();
    try(var original=resource("POI-AP_IT.ttl");var fetched=resource("fetched/PointOfInterest.ttl")){
      RDFDataMgr.read(ontology,original,Lang.TURTLE);
      poiBytes=fetched.readAllBytes();
      var bindings=json.createArrayNode();
      for(String name:List.of("MultiplePointOfInterest","POINameInTime","POIState","PointOfInterest","PointOfInterestCategory")){
        String uri=ONTOLOGY+"/"+name;
        bindings.addObject().putObject("resource").put("type","uri").put("value",uri);
        serve(uri,uri.equals(POI)?poiBytes:description(ontology,uri));
      }
      var result=json.createObjectNode();
      result.putObject("results").set("bindings",bindings);
      when(gateway.postForm(eq(base),eq(base.resolve("/search")),contains("SELECT"),any(Duration.class),eq(maxBytes),anySet(),any()))
          .thenReturn(new BoundedGatewayClient.Response(json.writeValueAsBytes(result),"application/sparql-results+json"));
      var header=new BoundedGatewayClient.Response(description(ontology,ONTOLOGY),"text/turtle");
      when(gateway.get(eq(base),eq(fetch(ONTOLOGY)),any(Duration.class),eq(maxBytes),anySet(),any(),anyString())).thenAnswer(call->{
        if(!available)throw new BoundedGatewayClient.ProviderFailure("PROVIDER_HTTP_503");
        if(changedOntology)return new BoundedGatewayClient.Response(("<"+ONTOLOGY+"> <http://purl.org/dc/terms/publisher> "
            +"<http://spcdata.digitpa.gov.it/Amministrazione/agid> .").getBytes(UTF_8),"text/turtle");
        return header;
      });
    } finally {ontology.close();}
  }
  public void ontologyAvailable(boolean available){
    clearInvocations(gateway);
    this.available=available;
    changedOntology=false;
  }
  public void verifyOntologyFetches(int count){
    verify(gateway,times(count)).get(eq(base),eq(fetch(ONTOLOGY)),any(Duration.class),eq(maxBytes),anySet(),any(),anyString());
  }
  public void serveChangedOntology(){changedOntology=true;}
  private InputStream resource(String file){
    return Objects.requireNonNull(getClass().getResourceAsStream("/discovery/ontopia/"+file),file);
  }
  private URI fetch(String uri){return base.resolve("/fetch?uri="+URLEncoder.encode(uri,UTF_8));}
  private void serve(String uri,byte[] bytes){
    when(gateway.get(eq(base),eq(fetch(uri)),any(Duration.class),eq(maxBytes),anySet(),any(),anyString()))
        .thenReturn(new BoundedGatewayClient.Response(bytes,"text/turtle"));
  }
  private static byte[] description(Model ontology,String uri){
    Model graph=ModelFactory.createDefaultModel();
    try {
      graph.add(ontology.listStatements(ontology.getResource(uri),null,(RDFNode)null));
      var out=new ByteArrayOutputStream();
      RDFDataMgr.write(out,graph,Lang.TURTLE);
      return out.toByteArray();
    } finally {graph.close();}
  }
}

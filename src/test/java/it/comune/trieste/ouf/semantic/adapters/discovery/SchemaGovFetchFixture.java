package it.comune.trieste.ouf.semantic.adapters.discovery;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.mockito.Mockito.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.net.URI;
import java.util.List;
import java.net.URLEncoder;
import java.time.*;

/** Synthetic Gateway responses for the required description and optional ontology GETs. */
final class SchemaGovFetchFixture {
  static final String DENIED="https://w3id.org/italia/env/onto/place/lat";
  static final String TEST_NAMESPACE="https://terms.example.test/";
  static final String REMOTE_DENIAL=TEST_NAMESPACE+"absent";
  static final String VALID="https://w3id.org/italia/onto/CLV/lat";
  private final URI base=URI.create("https://gateway.invalid");
  private final BoundedGatewayClient client=mock(BoundedGatewayClient.class);
  final SchemaGovProvider provider;

  SchemaGovFetchFixture(int maxCandidates,String... uris){
    this(maxCandidates,bindings(uris));
  }
  private static ArrayNode bindings(String[] uris){
    var rows=new ObjectMapper().createArrayNode();
    for(String uri:uris)rows.addObject().putObject("resource").put("type","uri").put("value",uri);
    return rows;
  }
  SchemaGovFetchFixture(int maxCandidates,ArrayNode rows){
    var json=new ObjectMapper();
    var cfg=new SchemaGovProperties(true,base,"/search","/fetch",Duration.ofSeconds(1),Duration.ofSeconds(2),
        8192,maxCandidates,1,Duration.ofSeconds(1),3,Duration.ofSeconds(30),List.of("https://w3id.org/italia/onto/",TEST_NAMESPACE));
    provider=new SchemaGovProvider(cfg,client,json,Clock.systemUTC());
    var result=json.createObjectNode();
    result.putObject("results").set("bindings",rows);
    when(client.postForm(eq(base),eq(base.resolve("/search")),anyString(),any(Duration.class),eq(8192),anySet(),any()))
        .thenReturn(new BoundedGatewayClient.Response(result.toString().getBytes(UTF_8),"application/sparql-results+json"));
  }
  void rejectSearch(String code){
    when(client.postForm(eq(base),eq(base.resolve("/search")),anyString(),any(Duration.class),eq(8192),anySet(),any()))
        .thenThrow(new BoundedGatewayClient.ProviderFailure(code));
  }
  void reject(String uri,String code){
    when(client.get(eq(base),eq(endpoint(uri)),any(Duration.class),eq(8192),anySet(),any(),anyString()))
        .thenThrow(new BoundedGatewayClient.ProviderFailure(code));
  }
  void describe(String uri,String rdf){
    when(client.get(eq(base),eq(endpoint(uri)),any(Duration.class),eq(8192),anySet(),any(),anyString()))
        .thenReturn(new BoundedGatewayClient.Response(rdf.getBytes(UTF_8),"text/turtle"));
  }
  void verifyFetches(String uri,int count){
    verify(client,times(count)).get(eq(base),eq(endpoint(uri)),any(Duration.class),eq(8192),anySet(),any(),anyString());
  }
  private URI endpoint(String uri){return base.resolve("/fetch?uri="+URLEncoder.encode(uri,UTF_8));}
}

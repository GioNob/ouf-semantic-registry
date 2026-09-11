package it.comune.trieste.ouf.fixture;

import jakarta.servlet.http.HttpServletRequest;
import java.util.UUID;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
public class SchemaGovFixtureApi {
  private static final String CORRELATION="X-Correlation-Id";
  private final SchemaGovProxy proxy;
  SchemaGovFixtureApi(SchemaGovProxy proxy){this.proxy=proxy;}

  @PostMapping(path="/semantic-providers/schema-gov/sparql",consumes=MediaType.APPLICATION_FORM_URLENCODED_VALUE)
  ResponseEntity<byte[]> sparql(@RequestBody byte[] body,HttpServletRequest request){return response(proxy.sparql(body,correlation(request)));}

  @GetMapping("/semantic-providers/schema-gov/fetch")
  ResponseEntity<byte[]> fetch(@RequestParam("uri") String uri,HttpServletRequest request){return response(proxy.fetch(uri,correlation(request)));}

  private ResponseEntity<byte[]> response(SchemaGovProxy.ProxyResponse result){return ResponseEntity.ok().contentType(MediaType.parseMediaType(result.mediaType())).body(result.body());}
  private String correlation(HttpServletRequest request){String value=request.getHeader(CORRELATION);return value!=null&&value.matches("[A-Za-z0-9._:-]{1,128}")?value:UUID.randomUUID().toString();}

  @ExceptionHandler(SchemaGovProxy.GatewayFailure.class)
  ResponseEntity<ProblemDetail> failure(SchemaGovProxy.GatewayFailure e){var p=ProblemDetail.forStatusAndDetail(HttpStatusCode.valueOf(e.status),e.getMessage());p.setTitle("Semantic provider gateway rejection");return ResponseEntity.status(e.status).body(p);}
}

package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.ArtifactService.Conflict;
import it.comune.trieste.ouf.semantic.application.GovernanceService.Forbidden;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser.UnsafeRdf;
import it.comune.trieste.ouf.semantic.adapters.discovery.BoundedGatewayClient.ProviderFailure;
import java.net.URI;
import java.util.NoSuchElementException;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestControllerAdvice
public class ProblemHandler {
  @ExceptionHandler(Conflict.class) ResponseEntity<ProblemDetail> conflict(Conflict e){var p=ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT,e.getMessage());p.setType(URI.create("urn:ouf:error:"+e.getMessage()));return ResponseEntity.status(409).body(p);}
  @ExceptionHandler(it.comune.trieste.ouf.semantic.application.GovernanceService.Conflict.class) ResponseEntity<ProblemDetail> governanceConflict(RuntimeException e){var p=ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT,e.getMessage());return ResponseEntity.status(409).body(p);}
  @ExceptionHandler(Forbidden.class) ResponseEntity<ProblemDetail> forbidden(Forbidden e){var p=ProblemDetail.forStatusAndDetail(HttpStatus.FORBIDDEN,e.getMessage());p.setType(URI.create("urn:ouf:error:"+e.getMessage()));return ResponseEntity.status(403).body(p);}
  @ExceptionHandler(UnsafeRdf.class) ResponseEntity<ProblemDetail> unsafeRdf(UnsafeRdf e){var p=ProblemDetail.forStatusAndDetail(HttpStatus.UNPROCESSABLE_ENTITY,e.getMessage());p.setType(URI.create("urn:ouf:error:"+e.getMessage()));return ResponseEntity.unprocessableEntity().body(p);}
  @ExceptionHandler(ProviderFailure.class) ResponseEntity<ProblemDetail> provider(ProviderFailure e){var p=ProblemDetail.forStatusAndDetail(HttpStatus.BAD_GATEWAY,e.getMessage());p.setType(URI.create("urn:ouf:error:"+e.getMessage()));return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(p);}
  @ExceptionHandler(IllegalArgumentException.class) ResponseEntity<ProblemDetail> bad(IllegalArgumentException e){return ResponseEntity.badRequest().body(ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST,e.getMessage()));}
  @ExceptionHandler(NoSuchElementException.class) ResponseEntity<ProblemDetail> missing(NoSuchElementException e){return ResponseEntity.status(HttpStatus.NOT_FOUND).body(ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND,e.getMessage()));}
}

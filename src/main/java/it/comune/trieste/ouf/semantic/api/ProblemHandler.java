package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.ArtifactService.Conflict;
import it.comune.trieste.ouf.semantic.application.GovernanceService.Forbidden;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser.UnsafeRdf;
import it.comune.trieste.ouf.semantic.adapters.discovery.BoundedGatewayClient.ProviderFailure;
import java.net.URI;
import java.util.NoSuchElementException;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestControllerAdvice
public class ProblemHandler {
  @ExceptionHandler(Conflict.class) ResponseEntity<ProblemDetail> conflict(Conflict e,HttpServletRequest r){return problem(HttpStatus.CONFLICT,e.getMessage(),r);}
  @ExceptionHandler(it.comune.trieste.ouf.semantic.application.GovernanceService.Conflict.class) ResponseEntity<ProblemDetail> governanceConflict(RuntimeException e,HttpServletRequest r){return problem(HttpStatus.CONFLICT,e.getMessage(),r);}
  @ExceptionHandler(Forbidden.class) ResponseEntity<ProblemDetail> forbidden(Forbidden e,HttpServletRequest r){return problem(HttpStatus.FORBIDDEN,e.getMessage(),r);}
  @ExceptionHandler(UnsafeRdf.class) ResponseEntity<ProblemDetail> unsafeRdf(UnsafeRdf e,HttpServletRequest r){return problem(HttpStatus.UNPROCESSABLE_ENTITY,e.getMessage(),r);}
  @ExceptionHandler(ProviderFailure.class) ResponseEntity<ProblemDetail> provider(ProviderFailure e,HttpServletRequest r){return problem(HttpStatus.BAD_GATEWAY,e.getMessage(),r);}
  @ExceptionHandler(IllegalArgumentException.class) ResponseEntity<ProblemDetail> bad(IllegalArgumentException e,HttpServletRequest r){return problem(HttpStatus.BAD_REQUEST,e.getMessage(),r);}
  @ExceptionHandler(NoSuchElementException.class) ResponseEntity<ProblemDetail> missing(NoSuchElementException e,HttpServletRequest r){return problem(HttpStatus.NOT_FOUND,e.getMessage(),r);}
  @ExceptionHandler(MethodArgumentNotValidException.class) ResponseEntity<ProblemDetail> invalid(MethodArgumentNotValidException e,HttpServletRequest r){var response=problem(HttpStatus.BAD_REQUEST,"SEM_REQUEST_INVALID",r);response.getBody().setProperty("violations",e.getBindingResult().getFieldErrors().stream().map(x->java.util.Map.of("field",x.getField(),"message",String.valueOf(x.getDefaultMessage()))).toList());return response;}
  private ResponseEntity<ProblemDetail> problem(HttpStatus status,String code,HttpServletRequest request){String safe=(code==null||code.isBlank())?"SEM_INTERNAL_ERROR":code;var p=ProblemDetail.forStatusAndDetail(status,safe);p.setType(URI.create("urn:ouf:error:"+safe.replaceAll("[^A-Za-z0-9._:-]","_")));p.setProperty("code",safe);Object correlation=request.getAttribute(RequestObservabilityFilter.CORRELATION_ATTRIBUTE);if(correlation!=null)p.setProperty("correlationId",correlation);return ResponseEntity.status(status).body(p);}
}

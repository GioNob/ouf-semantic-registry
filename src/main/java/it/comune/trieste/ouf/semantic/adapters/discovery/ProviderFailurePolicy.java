package it.comune.trieste.ouf.semantic.adapters.discovery;

import java.net.ConnectException;
import java.net.UnknownHostException;
import java.net.http.HttpTimeoutException;
import java.time.Clock;
import java.time.Duration;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Set;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeoutException;
import javax.net.ssl.SSLException;

/** Classification only: never sleeps, retries, grants authority or resets an incident budget. */
public final class ProviderFailurePolicy {
  private ProviderFailurePolicy() {}
  public enum Kind { TRANSIENT, BLOCKED, CANCELLED }
  public record Decision(Kind kind, String code, Duration retryAfter) {}
  private static final Set<String> BLOCKED_CODES=Set.of(
      "PROVIDER_REDIRECT_FORBIDDEN", "PROVIDER_MEDIA_TYPE_REJECTED",
      "PROVIDER_RESPONSE_TOO_LARGE", "GATEWAY_ORIGIN_VIOLATION",
      "GATEWAY_HTTPS_REQUIRED", "GATEWAY_AUTH_REQUIRED", "GATEWAY_TOKEN_REJECTED",
      "GATEWAY_TOKEN_INVALID", "GATEWAY_TOKEN_UNAVAILABLE", "GATEWAY_AUTH_CONFIGURATION_INVALID",
      "GATEWAY_CREDENTIAL_FILE_INVALID", "SCHEMA_GOV_CIRCUIT_OPEN",
      "SCHEMA_GOV_SPARQL_RESULT_INVALID", "PROVIDER_TLS_UNPROVEN",
      "PROVIDER_RETRY_AFTER_INVALID", "PROVIDER_UNKNOWN");

  public static Decision http(int status, String retryAfter, Clock clock) {
    if(status<100 || status>599)return blocked("PROVIDER_UNKNOWN");
    boolean transientStatus=status==408 || status==429 || status==500 || status==502 || status==503 || status==504;
    Duration delay=Duration.ZERO;
    if(transientStatus && retryAfter!=null) {
      try {
        String value=retryAfter.trim();
        if(value.isEmpty() || value.length()>128)throw new IllegalArgumentException();
        if(value.matches("[0-9]+"))delay=Duration.ofSeconds(Long.parseLong(value));
        else delay=Duration.between(clock.instant(),
            ZonedDateTime.parse(value,DateTimeFormatter.RFC_1123_DATE_TIME).toInstant());
        if(delay.isNegative())delay=Duration.ZERO;
      }catch(RuntimeException invalid){return blocked("PROVIDER_RETRY_AFTER_INVALID");}
    }
    // Do not shorten a valid delay to fit a budget. The persistent scheduler decides exhaustion.
    return new Decision(transientStatus?Kind.TRANSIENT:Kind.BLOCKED,"PROVIDER_HTTP_"+status,delay);
  }

  public static Decision exception(Throwable error) {
    // Security/cancellation cannot become retryable merely because a transport wrapper hides it.
    Throwable nested=error;
    for(int depth=0;depth<8 && nested!=null;depth++,nested=nested.getCause()) {
      if(nested instanceof SSLException)return blocked("PROVIDER_TLS_UNPROVEN");
      if(nested instanceof InterruptedException)return new Decision(Kind.CANCELLED,"PROVIDER_INTERRUPTED",Duration.ZERO);
    }
    Throwable cause=error;
    for(int depth=0;depth<8 && cause instanceof ExecutionException && cause.getCause()!=null;depth++)
      cause=cause.getCause();
    if(cause instanceof BoundedGatewayClient.ProviderFailure failure)return failure.decision();
    if(cause instanceof InterruptedException)return new Decision(Kind.CANCELLED,"PROVIDER_INTERRUPTED",Duration.ZERO);
    if(cause instanceof SSLException)return blocked("PROVIDER_TLS_UNPROVEN");
    if(cause instanceof HttpTimeoutException || cause instanceof TimeoutException)
      return new Decision(Kind.TRANSIENT,"PROVIDER_TIMEOUT",Duration.ZERO);
    if(cause instanceof ConnectException || cause instanceof UnknownHostException)
      return new Decision(Kind.TRANSIENT,"PROVIDER_UNAVAILABLE",Duration.ZERO);
    return blocked("PROVIDER_UNKNOWN");
  }

  public static Decision code(String code) {
    if("PROVIDER_UNAVAILABLE".equals(code) || "PROVIDER_TIMEOUT".equals(code))
      return new Decision(Kind.TRANSIENT,code,Duration.ZERO);
    if("PROVIDER_INTERRUPTED".equals(code))return new Decision(Kind.CANCELLED,code,Duration.ZERO);
    if(code!=null && code.matches("PROVIDER_HTTP_[1-5][0-9]{2}"))
      return http(Integer.parseInt(code.substring(14)),null,Clock.systemUTC());
    return blocked(BLOCKED_CODES.contains(code==null?"":code)?code:"PROVIDER_UNKNOWN");
  }
  private static Decision blocked(String code){return new Decision(Kind.BLOCKED,code,Duration.ZERO);}
}


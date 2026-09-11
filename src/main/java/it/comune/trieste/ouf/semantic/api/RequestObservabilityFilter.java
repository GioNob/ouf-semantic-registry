package it.comune.trieste.ouf.semantic.api;

import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public final class RequestObservabilityFilter extends OncePerRequestFilter {
  public static final String CORRELATION_HEADER = "X-Correlation-Id";
  private static final String SAFE_ID = "[A-Za-z0-9._:-]{1,128}";
  private final MeterRegistry meters;

  public RequestObservabilityFilter(MeterRegistry meters) {
    this.meters = meters;
  }

  @Override
  protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
      FilterChain chain) throws ServletException, IOException {
    String supplied = request.getHeader(CORRELATION_HEADER);
    String correlationId = supplied != null && supplied.matches(SAFE_ID)
        ? supplied : UUID.randomUUID().toString();
    response.setHeader(CORRELATION_HEADER, correlationId);
    Timer.Sample sample = Timer.start(meters);
    MDC.put("correlationId", correlationId);
    try {
      chain.doFilter(request, response);
    } finally {
      sample.stop(Timer.builder("ouf.semantic.http.requests")
          .description("Bounded-cardinality Semantic Registry HTTP request latency")
          .tag("method", request.getMethod())
          .tag("status_class", statusClass(response.getStatus()))
          .register(meters));
      MDC.remove("correlationId");
    }
  }

  private static String statusClass(int status) {
    return status >= 100 && status <= 599 ? (status / 100) + "xx" : "unknown";
  }
}

package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import io.micrometer.core.instrument.MeterRegistry;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest(properties={
    "ouf.semantic.discovery-worker.enabled=false",
    "ouf.semantic.providers.schema-gov.enabled=false"
})
@AutoConfigureMockMvc
class ObservabilityRuntimeTest {
  @Autowired MockMvc http;
  @Autowired MeterRegistry meters;

  @Test
  void correlationAndBoundedMetricsAreAppliedToSuccessAndFailure() throws Exception {
    String supplied = "trace-test-" + UUID.randomUUID();
    http.perform(get("/actuator/health").header("X-Correlation-Id", supplied))
        .andExpect(status().isOk())
        .andExpect(header().string("X-Correlation-Id", supplied));

    http.perform(get("/api/semantic/v1/artifacts/{id}", UUID.randomUUID())
            .header("X-Correlation-Id", "invalid id with spaces"))
        .andExpect(status().isNotFound())
        .andExpect(header().exists("X-Correlation-Id"))
        .andExpect(header().string("X-Correlation-Id",
            org.hamcrest.Matchers.not("invalid id with spaces")));

    assertThat(meters.find("ouf.semantic.http.requests").tag("status_class", "2xx").timer())
        .isNotNull();
    assertThat(meters.find("ouf.semantic.http.requests").tag("status_class", "4xx").timer())
        .isNotNull();
  }

  @Test
  void healthMetricsAndPrometheusEndpointsAreExposed() throws Exception {
    http.perform(get("/actuator/health/readiness")).andExpect(status().isOk());
    http.perform(get("/actuator/metrics/ouf.semantic.http.requests"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.name").value("ouf.semantic.http.requests"));
    http.perform(get("/actuator/prometheus"))
        .andExpect(status().isOk())
        .andExpect(content().string(org.hamcrest.Matchers.containsString("ouf_semantic_http_requests")));
  }
}

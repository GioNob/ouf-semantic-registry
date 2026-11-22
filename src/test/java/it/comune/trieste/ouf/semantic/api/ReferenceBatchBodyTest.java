package it.comune.trieste.ouf.semantic.api;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;

class ReferenceBatchBodyTest {
  @Test void configuredLimitCountsUtf8BytesWithoutContentLength() throws Exception {
    var json=new ObjectMapper();
    var pin=Map.of("semanticId","urn:esempio:città","revisionId",UUID.randomUUID(),"publicationSetId",UUID.randomUUID());
    byte[] bytes=json.writeValueAsString(Map.of("references",List.of(pin))).getBytes(StandardCharsets.UTF_8);
    var reader=new ReferenceBatchBody(json,bytes.length,1);
    assertThat(reader.read(chunked(bytes))).hasSize(1);
    assertThatThrownBy(() -> reader.read(chunked(java.util.Arrays.copyOf(bytes,bytes.length+1))))
        .isInstanceOf(ReferenceBatchBody.Rejected.class).hasMessage("SEM_REFERENCE_BATCH_TOO_LARGE");
    byte[] two=json.writeValueAsBytes(Map.of("references",List.of(pin,pin)));
    var singleItem=new ReferenceBatchBody(json,two.length,1);
    assertThatThrownBy(() -> singleItem.read(chunked(two))).hasMessage("SEM_REFERENCE_BATCH_TOO_LARGE");
  }
  private static MockHttpServletRequest chunked(byte[] bytes) {
    var request=new MockHttpServletRequest(){
      @Override public long getContentLengthLong() { return -1; }
    };
    request.setContent(bytes);
    return request;
  }
}

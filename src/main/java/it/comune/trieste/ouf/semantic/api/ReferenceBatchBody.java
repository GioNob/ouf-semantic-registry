package it.comune.trieste.ouf.semantic.api;

import static com.fasterxml.jackson.core.JsonToken.*;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.application.ReferenceBatchService.Pin;
import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
class ReferenceBatchBody {
  private final ObjectMapper json;
  private final int maxBytes;
  private final int maxItems;

  ReferenceBatchBody(ObjectMapper json,
      @Value("${ouf.semantic.reference-batch.max-request-bytes}") int maxBytes,
      @Value("${ouf.semantic.reference-batch.max-items}") int maxItems) {
    if (maxBytes<1 || maxBytes==Integer.MAX_VALUE || maxItems<1)
      throw new IllegalArgumentException("SEM_REFERENCE_BATCH_LIMIT_INVALID");
    this.json=json;
    this.maxBytes=maxBytes;
    this.maxItems=maxItems;
  }

  static class Rejected extends RuntimeException {
    final int status;
    final Map<String,Object> body;
    Rejected(int status,Map<String,Object> body) {
      super((String)body.get("code"));
      this.status=status;
      this.body=body;
    }
  }
  private static Rejected invalid(int index,String reason) {
    return new Rejected(400,Map.of("code","SEM_REFERENCE_BATCH_INVALID","index",index,"reason",reason));
  }
  private static Rejected tooLarge() {
    return new Rejected(413,Map.of("code","SEM_REFERENCE_BATCH_TOO_LARGE"));
  }

  List<Pin> read(HttpServletRequest request) {
    if (request.getContentLengthLong()>maxBytes) throw tooLarge();
    int index=0;
    Rejected firstInvalid=null;
    try {
      byte[] body=request.getInputStream().readNBytes(maxBytes+1);
      if (body.length>maxBytes) throw tooLarge();
      try (var parser=json.getFactory().createParser(body)) {
        parser.enable(JsonParser.Feature.STRICT_DUPLICATE_DETECTION);
        if (parser.nextToken()!=START_OBJECT || parser.nextToken()!=FIELD_NAME ||
            !"references".equals(parser.currentName()) || parser.nextToken()!=START_ARRAY)
          throw invalid(0,"INVALID_ENVELOPE");
        var pins=new ArrayList<Pin>();
        var seen=new HashSet<Pin>();
        while (parser.nextToken()!=END_ARRAY) {
          if (parser.currentToken()==null) throw invalid(index,"INVALID_JSON");
          if (index==maxItems) throw tooLarge();
          // Continue counting after an invalid pin so the item limit applies to the whole array.
          if (firstInvalid==null) {
            JsonNode item=json.readTree(parser);
            try {
              Pin pin=pin(item,index);
              if (!seen.add(pin)) throw invalid(index,"DUPLICATE_REFERENCE");
              pins.add(pin);
            } catch (Rejected invalidPin) {
              firstInvalid=invalidPin;
            }
          } else {
            parser.skipChildren();
          }
          index++;
        }
        if (firstInvalid!=null) throw firstInvalid;
        index=0;
        if (pins.isEmpty()) throw invalid(0,"EMPTY_REFERENCES");
        if (parser.nextToken()!=END_OBJECT || parser.nextToken()!=null) throw invalid(0,"INVALID_ENVELOPE");
        return pins;
      }
    } catch (IOException malformed) {
      throw firstInvalid!=null ? firstInvalid : invalid(index,"INVALID_JSON");
    }
  }

  private static Pin pin(JsonNode item,int index) {
    if (!item.isObject()) throw invalid(index,"INVALID_ELEMENT");
    String id=field(item,"semanticId",index);
    try {
      if (id.length()>2048 || !URI.create(id).isAbsolute() || !StandardCharsets.UTF_8.newEncoder().canEncode(id))
        throw invalid(index,"INVALID_SEMANTIC_ID");
    } catch (IllegalArgumentException malformed) {
      throw invalid(index,"INVALID_SEMANTIC_ID");
    }
    var pin=new Pin(id,uuid(item,"revisionId",index),uuid(item,"publicationSetId",index));
    if (item.size()!=3) throw invalid(index,"UNKNOWN_FIELD");
    return pin;
  }

  private static String field(JsonNode item,String name,int index) {
    JsonNode value=item.get(name);
    if (value==null || value.isNull()) throw invalid(index,"MISSING_FIELD");
    if (!value.isTextual()) throw invalid(index,"INVALID_FIELD_TYPE");
    return value.textValue();
  }

  private static UUID uuid(JsonNode item,String name,int index) {
    String raw=field(item,name,index);
    try {
      UUID id=UUID.fromString(raw);
      if (id.toString().equalsIgnoreCase(raw)) return id;
    } catch (IllegalArgumentException malformed) {
      // Reject abbreviated UUIDs as well as invalid digits.
    }
    throw invalid(index,"INVALID_UUID");
  }
}

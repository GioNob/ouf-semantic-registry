package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.PreparedStatementSetter;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ReferenceBatchService {
  public record Pin(String semanticId, UUID revisionId, UUID publicationSetId) {}
  public record Batch(String contract, String registryVersion, List<Map<String,Object>> results) {}

  // Each scalar aggregate runs once per statement, independently of the requested chunk.
  // XOR of fixed-width row fingerprints is order independent and needs constant aggregate memory.
  static final String SQL = """
      select pins.ordinality, visible.*, (select md5(concat_ws('/',
        (select bit_xor(('x' || md5(revision_id::text || '/' || lifecycle_status))::bit(128))
           from ouf_sem.artifact_revision),
        (select bit_xor(('x' || md5(publication_set_id::text || '/' || status || '/' || checksum))::bit(128))
           from ouf_sem.semantic_publication_set)))) registry_version
      from unnest(?::text[], ?::uuid[], ?::uuid[]) with ordinality
        pins(semantic_id, revision_id, publication_set_id, ordinality)
      left join (
        select %s, %s,
          case when a.artifact_type in ('DATATYPE','VALUE_MAP','CONCEPT') then r.definition_json::text end definition
        %s where %s
      ) visible using (semantic_id, revision_id, publication_set_id)
      """.formatted(SemanticReadService.REFERENCE_DETAIL, SemanticReadService.PUBLICATION_FIELDS,
          SemanticReadService.PUBLICATION_JOINS, SemanticReadService.VISIBLE_REFERENCE);

  private final JdbcTemplate db;
  private final ObjectMapper json;

  public ReferenceBatchService(JdbcTemplate db, ObjectMapper json) {
    this.db=db;
    this.json=json;
  }

  static PreparedStatementSetter parameters(List<Pin> pins) {
    return statement -> {
      statement.setObject(1,pins.stream().map(Pin::semanticId).toArray(String[]::new));
      statement.setObject(2,pins.stream().map(pin -> pin.revisionId().toString()).toArray(String[]::new));
      statement.setObject(3,pins.stream().map(pin -> pin.publicationSetId().toString()).toArray(String[]::new));
      // Value maps can be large. Consume the JDBC cursor before closing the read transaction.
      statement.setFetchSize(8);
    };
  }

  @Transactional(readOnly=true)
  public Batch resolve(List<Pin> pins) {
    return db.query(SQL,parameters(pins),rs -> {
      var results=new ArrayList<Map<String,Object>>(Collections.nCopies(pins.size(),null));
      String version=null;
      while (rs.next()) {
        int index=rs.getInt("ordinality")-1;
        var pin=pins.get(index);
        var item=new LinkedHashMap<String,Object>();
        item.put("index",index);
        item.put("semanticId",pin.semanticId());
        item.put("revisionId",pin.revisionId());
        item.put("publicationSetId",pin.publicationSetId());
        if (rs.getString("artifact_type")==null) {
          item.put("outcome","NOT_RESOLVABLE");
        } else {
          item.put("outcome","RESOLVED");
          item.put("resolved",compact(rs));
        }
        results.set(index,item);
        version=rs.getString("registry_version");
      }
      return new Batch("ouf.semantic.reference-batch.v1",version,results);
    });
  }

  private Map<String,Object> compact(ResultSet rs) throws SQLException {
    var fields=new LinkedHashMap<String,Object>();
    for (String key : List.of("semantic_id","semantic_version","revision_id","publication_set_id",
        "publication_checksum","status","artifact_type","content_hash")) {
      fields.put(key,rs.getObject(key));
    }
    String definition=rs.getString("definition");
    if (definition!=null) {
      try {
        Object decoded=json.readValue(definition,Object.class);
        if ("CONCEPT".equals(rs.getString("artifact_type"))) {
          // Same value as the GET: the concept definition carries the vocabulary membership
          // (vocabularyRef) that Ingestion and UDP check for structured types.
          fields.put("definition",decoded);
        } else {
          String canonical=SemanticReadService.canonicalDefinition(json,decoded);
          fields.put("definitionSha256",SemanticReadService.definitionSha256(canonical));
        }
      } catch (JsonProcessingException invalidStoredDefinition) {
        throw new IllegalStateException("SEM_READ_JSON_INVALID",invalidStoredDefinition);
      }
    }
    return fields;
  }
}

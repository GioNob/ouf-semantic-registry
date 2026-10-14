package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;

/** Internal search and exact historical reads; no discovery or lifecycle mutation. */
@Service
public class SemanticReadService {
  private final JdbcClient db;
  private final ObjectMapper json;
  private final int maxResultBytes;
  public SemanticReadService(JdbcClient db, ObjectMapper json,
      @Value("${ouf.semantic.read.max-result-bytes:262144}") int maxResultBytes) {
    if (maxResultBytes < 1024 || maxResultBytes > 1048576)
      throw new IllegalArgumentException("SEM_READ_LIMIT_INVALID");
    this.db=db; this.json=json; this.maxResultBytes=maxResultBytes;
  }

  private static final String DETAIL = """
      a.semantic_id,a.artifact_id,a.artifact_type,a.namespace,a.local_name,
      a.owner_ref,a.authority_ref,a.origin_kind,r.revision_id,r.semantic_version,
      r.lifecycle_status status,r.content_hash,r.label_json::text label,
      r.description_json::text description,r.definition_json::text definition
      """;

  public List<Map<String,Object>> search(String q,String status,int limit,
      String type,String namespace,String domain,String range) {
    bounded(q,"q",256,true); bounded(namespace,"namespace",512,false);
    bounded(domain,"domain",2048,false); bounded(range,"range",2048,false);
    if (limit<1 || limit>100) throw new IllegalArgumentException("SEM_SEARCH_LIMIT_INVALID");
    if (!Set.of("ACTIVE","DEPRECATED","RETIRED","DRAFT","UNDER_REVIEW").contains(status))
      throw new IllegalArgumentException("SEM_SEARCH_STATUS_INVALID");
    if (type!=null && !Set.of("CLASS","PROPERTY","RELATIONSHIP","VOCABULARY","CONCEPT","ONTOLOGY").contains(type))
      throw new IllegalArgumentException("SEM_SEARCH_TYPE_INVALID");
    String sql="""
        select %s,p.publication_set_id,p.checksum publication_checksum,
          case when lower(a.semantic_id)=lower(:q) or lower(a.local_name)=lower(:q) then 10
               when exists(select 1 from jsonb_each_text(r.label_json) l where lower(l.value)=lower(:q)) then 8
               else 0 end + greatest(similarity(a.semantic_id,:q),similarity(a.local_name,:q)) +
          ts_rank(jsonb_to_tsvector('simple',jsonb_build_array(r.label_json,r.description_json,r.definition_json),'["string"]'),
                  plainto_tsquery('simple',:q)) score
        from ouf_sem.semantic_artifact a
        join ouf_sem.artifact_revision r on r.artifact_id=a.artifact_id
        left join ouf_sem.artifact_active_revision ar on ar.artifact_id=a.artifact_id
        left join lateral (
          select m.publication_set_id,s.checksum
          from ouf_sem.semantic_publication_member m
          join ouf_sem.semantic_publication_set s using(publication_set_id)
          where m.revision_id=r.revision_id and m.semantic_id=a.semantic_id and s.status='PUBLISHED'
          order by s.publication_no desc limit 1
        ) p on true
        where r.lifecycle_status=:status
          and (:status<>'ACTIVE' or (ar.revision_id=r.revision_id and p.publication_set_id is not null))
          and (a.semantic_id %% :q or a.local_name %% :q or
               strpos(lower(a.semantic_id),lower(:q))>0 or
               exists(select 1 from jsonb_each_text(r.label_json) l where starts_with(lower(l.value),lower(:q))) or
               jsonb_to_tsvector('simple',jsonb_build_array(r.label_json,r.description_json,r.definition_json),'["string"]')
                   @@ plainto_tsquery('simple',:q))
        """.formatted(DETAIL);
    var params=new LinkedHashMap<String,Object>();
    params.put("q",q.strip()); params.put("status",status); params.put("n",limit);
    if(type!=null){sql+=" and a.artifact_type=:type";params.put("type",type);}
    if(namespace!=null){sql+=" and a.namespace=:namespace";params.put("namespace",namespace);}
    for(var filter:Map.of("DOMAIN",domain==null?"":domain,"RANGE",range==null?"":range).entrySet()) {
      if(!filter.getValue().isEmpty()) {
        String key=filter.getKey().toLowerCase(Locale.ROOT);
        sql+=" and (jsonb_exists(r.definition_json->'"+key+"Refs',:"+key+") or exists(select 1 from ouf_sem.semantic_dependency d where d.source_revision_id=r.revision_id and d.dependency_role='"+filter.getKey()+"' and d.target_semantic_id=:"+key+"))";
        params.put(key,filter.getValue());
      }
    }
    sql+=" order by score desc,a.semantic_id,r.revision_no desc limit :n";
    var rows=db.sql(sql).params(params).query().listOfRows();
    rows.forEach(this::decode);
    return boundedResult(rows);
  }

  public Map<String,Object> resolve(String semanticId,UUID revision,UUID publicationSet) {
    bounded(semanticId,"semanticId",2048,true);
    if(revision==null || publicationSet==null)throw new IllegalArgumentException("SEM_REFERENCE_INVALID");
    var rows=db.sql("select "+DETAIL+"""
        ,coalesce(o.canonical_uri,a.semantic_id) canonical_uri,m.publication_set_id,
        s.checksum publication_checksum
        from ouf_sem.semantic_publication_member m
        join ouf_sem.semantic_publication_set s using(publication_set_id)
        join ouf_sem.artifact_revision r on r.revision_id=m.revision_id
        join ouf_sem.semantic_artifact a on a.artifact_id=r.artifact_id
        left join lateral (select canonical_uri from ouf_sem.external_semantic_origin x
          where x.artifact_id=a.artifact_id order by canonical_uri limit 1) o on true
        where m.publication_set_id=:p and m.revision_id=:r and m.semantic_id=:s
          and a.semantic_id=m.semantic_id and s.status='PUBLISHED'
        """).param("p",publicationSet).param("r",revision).param("s",semanticId).query().listOfRows();
    if(rows.size()!=1)throw new NoSuchElementException("SEMANTIC_REFERENCE_NOT_FOUND");
    var row=rows.get(0); decode(row);
    var dependencies=db.sql("""
        select dependency_type,dependency_role,target_semantic_id,target_revision_id
        from ouf_sem.semantic_dependency where source_revision_id=:r
        order by dependency_role,dependency_type,target_semantic_id limit 101
        """).param("r",revision).query().listOfRows();
    row.put("dependencies",dependencies.subList(0,Math.min(100,dependencies.size())));
    row.put("dependencies_partial",dependencies.size()>100);
    var snapshots=db.sql("""
        select media_type,content_hash,statement_count,
          octet_length(content_bytes) byte_count,
          case when octet_length(content_bytes)<=8388608 then content_bytes end content_bytes
        from ouf_sem.revision_interchange_snapshot where revision_id=:r
        """).param("r",revision).query().listOfRows();
    if(!snapshots.isEmpty()) {
      var snapshot=snapshots.get(0);
      if(((Number)snapshot.get("byte_count")).longValue()>8388608)
        throw new IllegalArgumentException("SEM_READ_RDF_SIZE_LIMIT");
      row.put("rdf_snapshot",new PublishedRdfSnapshot().project((byte[])snapshot.get("content_bytes"),
        (String)snapshot.get("media_type"),snapshot.get("content_hash").toString().strip(),
        ((Number)snapshot.get("statement_count")).longValue()));
    }
    return boundedResult(row);
  }

  private static void bounded(String value,String name,int max,boolean required) {
    if((required && (value==null || value.isBlank())) ||
        (value!=null && (value.isBlank() || value.length()>max)))
      throw new IllegalArgumentException("SEM_READ_INPUT_INVALID:"+name);
  }
  private void decode(Map<String,Object> row) {
    for(String key:List.of("label","description","definition")) {
      try {row.put(key,json.readValue((String)row.get(key),Object.class));}
      catch(JsonProcessingException e){throw new IllegalStateException("SEM_READ_JSON_INVALID",e);}
    }
  }
  private <T> T boundedResult(T result) {
    try {if(json.writeValueAsBytes(result).length>maxResultBytes)
      throw new IllegalArgumentException("SEM_READ_RESULT_TOO_LARGE");}
    catch(JsonProcessingException e){throw new IllegalStateException("SEM_READ_JSON_INVALID",e);}
    return result;
  }
}

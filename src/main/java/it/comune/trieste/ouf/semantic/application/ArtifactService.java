package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.api.ArtifactApi.CreateArtifact;
import it.comune.trieste.ouf.semantic.api.ArtifactApi.PatchRevision;
import java.util.*;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ArtifactService {
  private final JdbcClient db; private final ObjectMapper json;
  public ArtifactService(JdbcClient db,ObjectMapper json){this.db=db;this.json=json;}
  private String j(Object o){try{return json.writeValueAsString(o==null?Map.of():o);}catch(JsonProcessingException e){throw new IllegalArgumentException(e);}}
  @Transactional
  public Map<String,Object> create(CreateArtifact c){
    UUID a=UUID.randomUUID(),r=UUID.randomUUID();
    try {
      db.sql("insert into ouf_sem.semantic_artifact(artifact_id,semantic_id,artifact_type,namespace,local_name,owner_ref,authority_ref,origin_kind) values(:a,:s,:t,:n,:l,:o,:u,'OUF')")
        .param("a",a).param("s",c.semanticId()).param("t",c.artifactType()).param("n",c.namespace()).param("l",c.localName()).param("o",c.ownerRef()).param("u",c.authorityRef()).update();
      db.sql("insert into ouf_sem.artifact_revision(revision_id,artifact_id,revision_no,lifecycle_status,label_json,definition_json,created_by_subject) values(:r,:a,1,'DRAFT',cast(:l as jsonb),cast(:d as jsonb),'api')")
        .param("r",r).param("a",a).param("l",j(c.labels())).param("d",j(c.definition())).update();
    } catch(DuplicateKeyException e){throw new Conflict("SEMANTIC_ID_CONFLICT");}
    return Map.of("artifactId",a,"revisionId",r,"semanticId",c.semanticId(),"status","DRAFT","etag","\"0\"");
  }
  public Map<String,Object> get(UUID id){return db.sql("select a.artifact_id,a.semantic_id,a.artifact_type,r.revision_id,r.lifecycle_status status,r.row_version from ouf_sem.semantic_artifact a join lateral (select * from ouf_sem.artifact_revision r where r.artifact_id=a.artifact_id order by r.revision_no desc limit 1) r on true where a.artifact_id=:id").param("id",id).query().singleRow();}
  public List<Map<String,Object>> search(String q,String status,int limit){if(limit<1||limit>100)throw new IllegalArgumentException("limit");return db.sql("select a.semantic_id,a.artifact_id,r.revision_id,r.lifecycle_status status,similarity(a.semantic_id,:q) score from ouf_sem.semantic_artifact a join ouf_sem.artifact_revision r on r.artifact_id=a.artifact_id where r.lifecycle_status=:s and a.semantic_id % :q order by score desc,a.semantic_id limit :n").param("q",q).param("s",status).param("n",limit).query().listOfRows();}
  @Transactional public Map<String,Object> patch(UUID id,String etag,PatchRevision p){long expected=Long.parseLong(etag.replace("\"",""));Long v=db.sql("select ouf_sem.edit_draft(:id,:v,cast(:l as jsonb),cast(:d as jsonb))").param("id",id).param("v",expected).param("l",j(p.labels())).param("d",j(p.definition())).query(Long.class).single();return Map.of("revisionId",id,"etag","\""+v+"\"");}
  public static class Conflict extends RuntimeException{public Conflict(String m){super(m);}}
}

package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.api.ArtifactApi.CreateArtifact;
import it.comune.trieste.ouf.semantic.api.ArtifactApi.PatchRevision;
import java.util.*;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ArtifactService {
  private final JdbcClient db; private final ObjectMapper json;
  public ArtifactService(JdbcClient db,ObjectMapper json){this.db=db;this.json=json;}
  private String j(Object o){try{return json.writeValueAsString(o==null?Map.of():o);}catch(JsonProcessingException e){throw new IllegalArgumentException(e);}}
  @Transactional
  public Map<String,Object> create(CreateArtifact c,String actor,String actorType,String correlation){
    UUID a=UUID.randomUUID(),r=UUID.randomUUID();
    try {
      db.sql("insert into ouf_sem.semantic_artifact(artifact_id,semantic_id,artifact_type,namespace,local_name,owner_ref,authority_ref,origin_kind) values(:a,:s,:t,:n,:l,:o,:u,'OUF')")
        .param("a",a).param("s",c.semanticId()).param("t",c.artifactType()).param("n",c.namespace()).param("l",c.localName()).param("o",c.ownerRef()).param("u",c.authorityRef()).update();
      db.sql("insert into ouf_sem.artifact_revision(revision_id,artifact_id,revision_no,lifecycle_status,semantic_version,label_json,definition_json,created_by_subject) values(:r,:a,1,'DRAFT',:v,cast(:l as jsonb),cast(:d as jsonb),:x)")
        .param("r",r).param("a",a).param("v",c.semanticVersion()).param("l",j(c.labels())).param("d",j(c.definition())).param("x",actor).update();
      audit("SEMANTIC_ARTIFACT_CREATED",actor,actorType,"ARTIFACT",a.toString(),correlation,Map.of("revisionId",r,"semanticId",c.semanticId()));
    } catch(DuplicateKeyException e){throw new Conflict("SEMANTIC_ID_CONFLICT");}
    return Map.of("artifactId",a,"revisionId",r,"semanticId",c.semanticId(),"status","DRAFT","etag","\"0\"");
  }
  public Map<String,Object> get(UUID id){return db.sql("select a.artifact_id,a.semantic_id,a.artifact_type,r.revision_id,r.lifecycle_status status,r.row_version from ouf_sem.semantic_artifact a join lateral (select * from ouf_sem.artifact_revision r where r.artifact_id=a.artifact_id order by r.revision_no desc limit 1) r on true where a.artifact_id=:id").param("id",id).query().singleRow();}
  public List<Map<String,Object>> search(String q,String status,int limit){if(limit<1||limit>100)throw new IllegalArgumentException("limit");return db.sql("select a.semantic_id,a.artifact_id,r.revision_id,r.lifecycle_status status,similarity(a.semantic_id,:q) score from ouf_sem.semantic_artifact a join ouf_sem.artifact_revision r on r.artifact_id=a.artifact_id where r.lifecycle_status=:s and a.semantic_id % :q order by score desc,a.semantic_id limit :n").param("q",q).param("s",status).param("n",limit).query().listOfRows();}
  @Transactional public Map<String,Object> patch(UUID id,String etag,PatchRevision p,String actor,String actorType,String correlation){
    final long expected;
    try{expected=Long.parseLong(etag.replace("\"",""));}
    catch(RuntimeException e){throw new IllegalArgumentException("ETAG_INVALID",e);}
    try{
      Long v=db.sql("select ouf_sem.edit_draft(:id,:v,cast(:l as jsonb),cast(:d as jsonb))").param("id",id).param("v",expected).param("l",j(p.labels())).param("d",j(p.definition())).query(Long.class).single();
      audit("SEMANTIC_DRAFT_EDITED",actor,actorType,"REVISION",id.toString(),correlation,Map.of("rowVersion",v));return Map.of("revisionId",id,"etag","\""+v+"\"");
    }catch(DataAccessException e){
      if(e.getMessage()!=null&&e.getMessage().contains("VERSION_CONFLICT"))throw new Conflict("VERSION_CONFLICT");
      throw e;
    }
  }
  private void audit(String event,String actor,String actorType,String resourceType,String resourceId,String correlation,Object detail){db.sql("insert into ouf_sem.audit_event(event_id,event_type,subject_ref,resource_type,resource_id,correlation_id,detail_json) values(:i,:e,:a,:t,:r,:c,cast(:d as jsonb))").param("i",UUID.randomUUID()).param("e",event).param("a",actor).param("t",resourceType).param("r",resourceId).param("c",correlation).param("d",j(Map.of("actorType",actorType,"detail",detail))).update();}
  public static class Conflict extends RuntimeException{public Conflict(String m){super(m);}}
}

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
  private final JdbcClient db; private final ObjectMapper json; private final SemanticReadService reads;
  public ArtifactService(JdbcClient db,ObjectMapper json,SemanticReadService reads){this.db=db;this.json=json;this.reads=reads;}
  private String j(Object o){try{return json.writeValueAsString(o==null?Map.of():o);}catch(JsonProcessingException e){throw new IllegalArgumentException(e);}}
  @Transactional
  public Map<String,Object> create(CreateArtifact c,String actor,String actorType,String correlation){
    UUID a=UUID.randomUUID(),r=UUID.randomUUID();
    try {
      int revisionNo=1;
      if ("DATATYPE".equals(c.artifactType())) {
        try {
          if (!new java.net.URI(c.semanticId()).isAbsolute()) throw new IllegalArgumentException("DT-IRI");
        } catch (java.net.URISyntaxException invalid) { throw new IllegalArgumentException("DT-IRI"); }
        if (c.semanticVersion()==null || !c.semanticVersion().matches("[0-9]+\\.[0-9]+\\.[0-9]+(?:-[A-Za-z0-9.-]+)?(?:\\+[A-Za-z0-9.-]+)?"))
          throw new IllegalArgumentException("SEMANTIC_VERSION_INVALID");
        var existing=db.sql("""
            select artifact_id, artifact_type, namespace, local_name, owner_ref, authority_ref, retired_at
            from ouf_sem.semantic_artifact where semantic_id=:s for update
            """).param("s",c.semanticId()).query().listOfRows();
        if (!existing.isEmpty()) {
          var identity=existing.getFirst();
          if (!"DATATYPE".equals(identity.get("artifact_type")) || identity.get("retired_at")!=null ||
              !c.namespace().equals(identity.get("namespace")) || !c.localName().equals(identity.get("local_name")) ||
              !c.ownerRef().equals(identity.get("owner_ref")) || !c.authorityRef().equals(identity.get("authority_ref")))
            throw new Conflict("SEMANTIC_ID_CONFLICT");
          a=(UUID)identity.get("artifact_id");
          var revisions=db.sql("""
              select max(revision_no)+1 next_no, bool_or(published_at is null or semantic_version=:v) blocked
              from ouf_sem.artifact_revision where artifact_id=:a
              """).param("v",c.semanticVersion()).param("a",a).query().singleRow();
          if (!Boolean.FALSE.equals(revisions.get("blocked"))) throw new Conflict("DT-VERSION");
          revisionNo=((Number)revisions.get("next_no")).intValue();
        }
      }
      if (revisionNo==1) db.sql("insert into ouf_sem.semantic_artifact(artifact_id,semantic_id,artifact_type,namespace,local_name,owner_ref,authority_ref,origin_kind) values(:a,:s,:t,:n,:l,:o,:u,'OUF')")
        .param("a",a).param("s",c.semanticId()).param("t",c.artifactType()).param("n",c.namespace()).param("l",c.localName()).param("o",c.ownerRef()).param("u",c.authorityRef()).update();
      db.sql("insert into ouf_sem.artifact_revision(revision_id,artifact_id,revision_no,lifecycle_status,semantic_version,label_json,definition_json,created_by_subject) values(:r,:a,:no,'DRAFT',:v,cast(:l as jsonb),cast(:d as jsonb),:x)")
        .param("no",revisionNo)
        .param("r",r).param("a",a).param("v",c.semanticVersion()).param("l",j(c.labels())).param("d",j(c.definition())).param("x",actor).update();
      audit(revisionNo==1?"SEMANTIC_ARTIFACT_CREATED":"SEMANTIC_REVISION_CREATED",actor,actorType,"ARTIFACT",a.toString(),correlation,Map.of("revisionId",r,"semanticId",c.semanticId()));
    } catch(DuplicateKeyException e){throw new Conflict("SEMANTIC_ID_CONFLICT");}
    return Map.of("artifactId",a,"revisionId",r,"semanticId",c.semanticId(),"status","DRAFT","etag","\"0\"");
  }
  public Map<String,Object> get(UUID id){return db.sql("select a.artifact_id,a.semantic_id,a.artifact_type,r.revision_id,r.lifecycle_status status,r.row_version from ouf_sem.semantic_artifact a join lateral (select * from ouf_sem.artifact_revision r where r.artifact_id=a.artifact_id order by r.revision_no desc limit 1) r on true where a.artifact_id=:id").param("id",id).query().singleRow();}
  public List<Map<String,Object>> search(String q,String status,int limit){return search(q,status,limit,null,null,null,null);}
  public List<Map<String,Object>> search(String q,String status,int limit,String type,String namespace,String domain,String range){return reads.search(q,status,limit,type,namespace,domain,range);}
  @Transactional public Map<String,Object> patch(UUID id,String etag,PatchRevision p,String actor,String actorType,String correlation){
    final long expected;
    try{expected=Long.parseLong(etag.replace("\"",""));}
    catch(RuntimeException e){throw new IllegalArgumentException("ETAG_INVALID",e);}
    try{
      if(p.semanticVersion()!=null){
        if(!p.semanticVersion().matches("[0-9]+\\.[0-9]+\\.[0-9]+(?:-[A-Za-z0-9.-]+)?(?:\\+[A-Za-z0-9.-]+)?"))throw new IllegalArgumentException("SEMANTIC_VERSION_INVALID");
        int changed=db.sql("update ouf_sem.artifact_revision set semantic_version=:version where revision_id=:id and lifecycle_status='DRAFT' and row_version=:expected")
          .param("version",p.semanticVersion()).param("id",id).param("expected",expected).update();
        if(changed!=1)throw new Conflict("VERSION_CONFLICT");
      }
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

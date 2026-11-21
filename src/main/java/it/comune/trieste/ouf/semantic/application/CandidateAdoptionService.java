package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;
import org.apache.jena.rdf.model.*;
import org.apache.jena.vocabulary.RDFS;
import org.apache.jena.vocabulary.SKOS;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;

/** Effects inside the proposal receipt transaction. All evidence is read locally. */
@Service
class CandidateAdoptionService {
  private final JdbcClient db;
  private final ObjectMapper json;

  CandidateAdoptionService(JdbcClient db,ObjectMapper json) {
    this.db=db;
    this.json=json;
  }

  Map<String,Object> adopt(UUID request,UUID candidate,String jobSubject,String principal) {
    var row=db.sql("""
        select c.canonical_uri,c.artifact_type,c.media_type,c.content_hash,c.content_bytes,c.adopted_artifact_id,
               c.expires_at<=clock_timestamp() expired
          from ouf_sem.discovery_request j join ouf_sem.discovery_candidate c using(request_id)
         where j.request_id=:r and c.candidate_id=:c and j.created_by_subject=:actor and j.state='SUCCEEDED'
         for update of c,j
        """).param("r",request).param("c",candidate).param("actor",jobSubject).query().listOfRows().stream().findFirst()
        .orElseThrow(()->new NoSuchElementException("SEMANTIC_CANDIDATE_NOT_FOUND"));
    if(row.get("adopted_artifact_id") instanceof UUID adopted)return reference(request,candidate,jobSubject,adopted,false);
    if(Boolean.TRUE.equals(row.get("expired")))throw new GovernanceService.Conflict("CANDIDATE_EXPIRED");

    String uri=(String)row.get("canonical_uri");
    Model model=new PublishedRdfSnapshot().verifiedModel((byte[])row.get("content_bytes"),
        (String)row.get("media_type"),(String)row.get("content_hash"));
    UUID artifact;
    try {
      Resource resource=model.getResource(uri);
      var metadata=metadata(resource);
      String publisher=metadata.publisher();
      if(publisher==null)throw new GovernanceService.Conflict("CANDIDATE_PUBLISHER_MISSING");
      String definition=referenceDefinition(resource,(String)row.get("artifact_type")).toString();
      artifact=db.sql("select ouf_sem.adopt_or_find_candidate(:c,:uri,:ns,:name,:actor,:publisher,:license,cast(:definition as jsonb))")
          .param("c",candidate).param("uri",uri).param("ns",resource.getNameSpace()).param("name",resource.getLocalName())
          .param("actor",principal)
          .param("publisher",publisher).param("license",metadata.license()).param("definition",definition).query(UUID.class).single();
    } catch(DataAccessException e) {
      if(e.getMostSpecificCause() instanceof java.sql.SQLException sql) {
        if("P1503".equals(sql.getSQLState()))
          throw new GovernanceService.Conflict("SEMANTIC_IDENTITY_MISMATCH","NAME_OR_ORIGIN_ALREADY_BOUND");
        if("23514".equals(sql.getSQLState()) && sql.getMessage().contains("CANDIDATE_EXPIRED"))
          throw new GovernanceService.Conflict("CANDIDATE_EXPIRED");
      }
      throw e;
    } finally {
      model.close();
    }
    return reference(request,candidate,jobSubject,artifact,false);
  }

  Map<String,Object> reference(UUID request,UUID candidate,String jobSubject,UUID artifact,boolean replay) {
    var rows=db.sql("""
        select a.semantic_id,r.revision_id,r.row_version,r.lifecycle_status,c.adopted_at,
               ouf_sem.adoption_provenance(o,s)::text provenance, s.media_type,
               case when o.publisher is null then s.content_bytes end legacy_bytes,
               exists(select 1 from ouf_sem.discovery_candidate original
                      join ouf_sem.discovery_request job using(request_id)
                      join ouf_sem.audit_event e on e.resource_type='CANDIDATE' and e.event_type='SEMANTIC_CANDIDATE_ADOPTED'
                        and e.resource_id=original.candidate_id::text and e.detail_json->>'snapshotId'=s.snapshot_id::text
                      where original.adopted_artifact_id=a.artifact_id and job.created_by_subject=:actor) same_subject
        from ouf_sem.discovery_candidate c join ouf_sem.discovery_request j using(request_id)
        join ouf_sem.semantic_artifact a on a.artifact_id=:artifact and a.semantic_id=c.canonical_uri
          and a.artifact_type=c.artifact_type
        join ouf_sem.artifact_revision r on r.artifact_id=a.artifact_id
        join ouf_sem.revision_adoption b on b.revision_id=r.revision_id
        join ouf_sem.immutable_semantic_snapshot s on s.snapshot_id=b.snapshot_id
          and s.content_hash=c.content_hash and s.media_type=c.media_type
        join ouf_sem.external_semantic_origin o on o.origin_id=s.origin_id and o.artifact_id=a.artifact_id
          and o.provider_id=c.provider_id and o.canonical_uri=c.canonical_uri and o.source_url=c.source_location
        where (c.adopted_artifact_id is null or c.adopted_artifact_id=a.artifact_id)
          and (not jsonb_exists(r.definition_json,'adoptionProvenance')
               or r.definition_json->'adoptionProvenance'=ouf_sem.adoption_provenance(o,s))
          and c.candidate_id=:candidate and j.request_id=:request and j.created_by_subject=:actor and j.state='SUCCEEDED'
        for update of r
        """).param("artifact",artifact).param("candidate",candidate).param("request",request)
        .param("actor",jobSubject).query().listOfRows();
    if(rows.isEmpty())throw new GovernanceService.Conflict("SEMANTIC_IDENTITY_MISMATCH","TYPE_OR_PROVENANCE_UNMATCHED");
    if(rows.size()>1)throw new GovernanceService.Conflict("ADOPTION_RECONCILIATION_REQUIRED");
    var revision=rows.get(0);
    var id=(UUID)revision.get("revision_id");
    var status=(String)revision.get("lifecycle_status");
    Map<String,Object> result=new LinkedHashMap<>();
    if("ACTIVE".equals(status)) {
      var publications=db.sql("""
          select m.publication_set_id from ouf_sem.semantic_publication_member m
          join ouf_sem.semantic_publication_set p using(publication_set_id)
          join ouf_sem.artifact_active_revision ar using(revision_id)
          join ouf_sem.audit_event e on e.event_type='SEMANTIC_PUBLISHED' and e.resource_type='REVISION'
            and e.resource_id=m.revision_id::text and e.detail_json->>'publicationSetId'=m.publication_set_id::text
          where m.revision_id=:r and ar.artifact_id=:a and m.semantic_id=:uri and p.status='PUBLISHED'
          """).param("r",id).param("a",artifact).param("uri",revision.get("semantic_id")).query(UUID.class).list();
      if(publications.size()!=1)throw new GovernanceService.Conflict("PUBLICATION_RECONCILIATION_REQUIRED");
      result.put("publicationSetId",publications.get(0));
    } else if("DRAFT".equals(status)||"UNDER_REVIEW".equals(status)) {
      if(!Boolean.TRUE.equals(revision.get("same_subject")))throw new NoSuchElementException("SEMANTIC_CANDIDATE_NOT_FOUND");
      if("UNDER_REVIEW".equals(status)) {
        var challenges=db.sql("""
            select challenge_id,case when status='OPEN' and expires_at<=clock_timestamp() then 'EXPIRED' else status end status
            from ouf_sem.approval_challenge where revision_id=:r and status in ('OPEN','APPROVED')
            """).param("r",id).query().listOfRows();
        if(challenges.size()!=1)throw new GovernanceService.Conflict("REVIEW_RECONCILIATION_REQUIRED");
        var challenge=challenges.get(0);
        result.put("challengeId",challenge.get("challenge_id"));
        result.put("challengeStatus",challenge.get("status"));
        result.put("trustedApprovalRef","ths://semantic-approval-challenges/"+challenge.get("challenge_id"));
      }
    } else throw new GovernanceService.Conflict("SEMANTIC_REVISION_UNAVAILABLE");
    result.put("provenance",provenance(revision));
    result.put("requestId",request);
    result.put("candidateId",candidate);
    result.put("artifactId",artifact);
    result.put("revisionId",id);
    result.put("semanticId",revision.get("semantic_id"));
    result.put("expectedRowVersion",revision.get("row_version"));
    result.put("status",status);
    if(!replay && revision.get("adopted_at")==null) {
      int bound=db.sql("""
          update ouf_sem.discovery_candidate set adopted_artifact_id=:a,adopted_at=clock_timestamp()
          where candidate_id=:c and adopted_at is null and expires_at>clock_timestamp()
          """).param("a",artifact).param("c",candidate).update();
      if(bound!=1)throw new GovernanceService.Conflict("CANDIDATE_EXPIRED");
    }
    return result;
  }

  private JsonNode provenance(Map<String,Object> revision) {
    com.fasterxml.jackson.databind.node.ObjectNode source;
    try {source=(com.fasterxml.jackson.databind.node.ObjectNode)json.readTree((String)revision.get("provenance"));}
    catch(com.fasterxml.jackson.core.JsonProcessingException e){throw new IllegalStateException("ADOPTION_PROVENANCE_INVALID",e);}
    // V4 did not extract publisher/license. Read the exact snapshot bound by V13's adoption evidence.
    if(revision.get("legacy_bytes") instanceof byte[] bytes) {
      Model model=new PublishedRdfSnapshot().verifiedModel(bytes,(String)revision.get("media_type"),source.get("rdfSha256").asText());
      try {
        var terms=metadata(model.getResource(source.get("canonicalUri").asText()));
        if(terms.publisher()==null)throw new GovernanceService.Conflict("CANDIDATE_PUBLISHER_MISSING");
        source.put("publisher",terms.publisher());
        source.put("license",terms.license());
        source.put("licenseWarning",terms.license()==null?"licenza mancante":null);
      } finally {model.close();}
    }
    return source;
  }

  private JsonNode referenceDefinition(Resource subject,String type) {
    var definition=json.createObjectNode();
    if("RELATIONSHIP".equals(type)) {
      definition.set("domainRefs",json.valueToTree(references(subject,RDFS.domain)));
      definition.set("rangeRefs",json.valueToTree(references(subject,RDFS.range)));
    } else if("CONCEPT".equals(type)) {
      var schemes=references(subject,SKOS.inScheme);
      if(schemes.size()!=1)throw new GovernanceService.Conflict("CANDIDATE_VOCABULARY_UNRESOLVED");
      definition.put("vocabularyRef",schemes.first());
    }
    return definition;
  }

  private SortedSet<String> references(Resource subject,Property predicate) {
    var result=new TreeSet<String>();
    var statements=subject.listProperties(predicate);
    try {
      while(statements.hasNext()) {
        RDFNode target=statements.next().getObject();
        if(!target.isURIResource())throw new GovernanceService.Conflict("CANDIDATE_REFERENCE_UNRESOLVED");
        result.add(target.asResource().getURI());
      }
    } finally {statements.close();}
    if(result.isEmpty())throw new GovernanceService.Conflict("CANDIDATE_REFERENCE_UNRESOLVED");
    long known=db.sql("select count(*) from ouf_sem.semantic_artifact where semantic_id=any(:refs)")
        .param("refs",result.toArray(String[]::new)).query(Long.class).single();
    if(known!=result.size())throw new GovernanceService.Conflict("CANDIDATE_REFERENCE_UNRESOLVED");
    return result;
  }

  record Metadata(String publisher,String license){}

  static Metadata metadata(Resource resource) {
    var sources=new ArrayList<Resource>();
    var links=resource.listProperties(RDFS.isDefinedBy);
    try {
      while(links.hasNext()) {
        RDFNode node=links.next().getObject();
        if(node.isURIResource())sources.add(node.asResource());
      }
    } finally {links.close();}
    return new Metadata(metadata(resource,sources,"publisher"),metadata(resource,sources,"license"));
  }

  private static String metadata(Resource resource,List<Resource> definingResources,String field) {
    var values=new TreeSet<String>();
    collect(resource,field,values);
    if(values.isEmpty())for(var defining:definingResources)collect(defining,field,values);
    if(values.size()>1)throw new GovernanceService.Conflict("CANDIDATE_METADATA_AMBIGUOUS");
    return values.isEmpty()?null:values.first();
  }

  private static void collect(Resource subject,String field,Set<String> values) {
    for(String ns:List.of("http://purl.org/dc/terms/","http://purl.org/dc/elements/1.1/")) {
      var statements=subject.listProperties(subject.getModel().createProperty(ns+field));
      try {
        while(statements.hasNext()) {
          RDFNode node=statements.next().getObject();
          String value=node.isURIResource()?node.asResource().getURI():node.isLiteral()?node.asLiteral().getString():null;
          if(value==null || value.isBlank())throw new GovernanceService.Conflict("CANDIDATE_METADATA_UNRESOLVED");
          values.add(value);
        }
      } finally {statements.close();}
    }
  }
}

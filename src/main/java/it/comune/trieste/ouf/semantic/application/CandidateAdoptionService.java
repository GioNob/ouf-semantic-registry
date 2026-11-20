package it.comune.trieste.ouf.semantic.application;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;
import org.apache.jena.rdf.model.*;
import org.apache.jena.vocabulary.RDFS;
import org.apache.jena.vocabulary.SKOS;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.dao.DuplicateKeyException;
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
        select c.canonical_uri,c.artifact_type,c.media_type,c.content_hash,c.content_bytes,c.adopted_at,
               c.expires_at<=clock_timestamp() expired
          from ouf_sem.discovery_request j join ouf_sem.discovery_candidate c using(request_id)
         where j.request_id=:r and c.candidate_id=:c and j.created_by_subject=:actor and j.state='SUCCEEDED'
         for update of c,j
        """).param("r",request).param("c",candidate).param("actor",jobSubject).query().listOfRows().stream().findFirst()
        .orElseThrow(()->new NoSuchElementException("SEMANTIC_CANDIDATE_NOT_FOUND"));
    if(Boolean.TRUE.equals(row.get("expired")))throw new GovernanceService.Conflict("CANDIDATE_EXPIRED");
    if(row.get("adopted_at")!=null)throw new GovernanceService.Conflict("CANDIDATE_ALREADY_ADOPTED");

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
      artifact=db.sql("select ouf_sem.adopt_candidate(:c,:uri,:ns,:name,:owner,:authority,:actor,:publisher,:license,cast(:definition as jsonb))")
          .param("c",candidate).param("uri",uri).param("ns",resource.getNameSpace()).param("name",resource.getLocalName())
          .param("owner",principal).param("authority",publisher).param("actor",principal)
          .param("publisher",publisher).param("license",metadata.license()).param("definition",definition).query(UUID.class).single();
    } catch(DuplicateKeyException e) {
      throw new GovernanceService.Conflict("SEMANTIC_ID_CONFLICT");
    } catch(DataIntegrityViolationException e) {
      // The database rechecks wall-clock expiry after RDF processing and lock acquisition.
      if(e.getMostSpecificCause().getMessage().contains("CANDIDATE_EXPIRED"))
        throw new GovernanceService.Conflict("CANDIDATE_EXPIRED");
      throw e;
    } finally {
      model.close();
    }
    var revision=db.sql("""
        select revision_id,row_version,definition_json->'adoptionProvenance' provenance
        from ouf_sem.artifact_revision where artifact_id=:a and revision_no=1
        """).param("a",artifact).query().singleRow();
    JsonNode provenance;
    try {provenance=json.readTree(revision.get("provenance").toString());}
    catch(com.fasterxml.jackson.core.JsonProcessingException e){throw new IllegalStateException("ADOPTION_PROVENANCE_INVALID",e);}
    return Map.of("requestId",request,"candidateId",candidate,"artifactId",artifact,"revisionId",revision.get("revision_id"),
        "expectedRowVersion",revision.get("row_version"),"semanticId",uri,"status","DRAFT","provenance",provenance);
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

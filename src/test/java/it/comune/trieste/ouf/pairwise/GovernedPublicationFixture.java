package it.comune.trieste.ouf.pairwise;

import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.SemanticRegistryApplication;
import it.comune.trieste.ouf.semantic.application.*;
import it.comune.trieste.ouf.semantic.api.ArtifactApi.PatchRevision;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.*;
import org.springframework.boot.*;
import org.springframework.context.annotation.*;

/** Test-only upstream and human identity seams; all domain writes use production services. */
public class GovernedPublicationFixture {
 public static void main(String[] args){SpringApplication.run(new Class<?>[]{SemanticRegistryApplication.class,AuthenticatedSemanticFixture.FixtureConfiguration.class,Fixture.class},args);}
 @Configuration(proxyBeanMethods=false) public static class Fixture {
  @Bean SemanticDiscoveryProvider deterministicProvider(){return provider();}
  @Bean ApplicationRunner publish(DiscoveryService discovery,ArtifactService artifacts,ValidationService validation,GovernanceService governance,ObjectMapper json){return args->{
   var result=run(discovery,artifacts,validation,governance);
   Path output=Path.of(System.getenv("OUF_R2C_SEMANTIC_RESULT"));
   Files.writeString(output,json.writeValueAsString(result));
  };}
 }
 public static SemanticDiscoveryProvider provider(){return new SemanticDiscoveryProvider(){
  public String providerId(){return "R2C_DECLARED_UPSTREAM_FIXTURE";}
  public List<Candidate> search(Query query){return List.of(new Candidate("https://example.org/core","fixture://r2c/core.ttl","ONTOLOGY","HIGH",1.0,List.of("deterministic integration fixture"),List.of(),"<https://example.org/core> a <http://www.w3.org/2002/07/owl#Ontology> .".getBytes(StandardCharsets.UTF_8),"text/turtle"));}
 };}
 public static Map<String,Object> run(DiscoveryService discovery,ArtifactService artifacts,ValidationService validation,GovernanceService governance){
  UUID request=discovery.request("ONTOLOGY","core",List.of("it"),"fixture-service");
  if(discovery.executeOne()!=1)throw new IllegalStateException("R2C_DISCOVERY_NOT_EXECUTED");
  UUID candidate=(UUID)discovery.candidates(request).getFirst().get("candidate_id");
  UUID artifact=discovery.adopt(request,candidate,"core","https://example.org/","core","fixture-owner","fixture-authority","fixture-service");
  if(!artifact.equals(discovery.adopt(request,candidate,"core","https://example.org/","core","fixture-owner","fixture-authority","fixture-service")))throw new IllegalStateException("R2C_ADOPTION_NOT_IDEMPOTENT");
  UUID revision=(UUID)artifacts.get(artifact).get("revision_id");
  if(!"DRAFT".equals(artifacts.get(artifact).get("status")))throw new IllegalStateException("R2C_AUTO_PUBLICATION");
  artifacts.patch(revision,"\"0\"",new PatchRevision(Map.of("it","Vocabolario di prova"),Map.of(),"1.0.0"),"fixture-service","SERVICE","r2c");
  var validated=validation.validate(revision,"fixture-reviewer");
  if(!"PASS".equals(validated.get("status")))throw new IllegalStateException("R2C_VALIDATION_FAILED");
  String hash=validated.get("validated_content_hash").toString();
  UUID challenge=(UUID)governance.challenge(revision,hash,Duration.ofMinutes(10),"fixture-service","SERVICE","r2c").get("challengeId");
  try{governance.decide(challenge,"APPROVED","fixture-service","SERVICE","fixture:service","r2c");throw new IllegalStateException("R2C_SERVICE_APPROVAL_ALLOWED");}catch(GovernanceService.Forbidden expected){}
  UUID decision=(UUID)governance.decide(challenge,"APPROVED","fixture-human","HUMAN","fixture:mfa","r2c").get("decisionId");
  var published=governance.publish(revision,decision,"r2c-"+revision,hash,"fixture-human","HUMAN","r2c");
  if(!published.equals(governance.publish(revision,decision,"r2c-"+revision,hash,"fixture-human","HUMAN","r2c")))throw new IllegalStateException("R2C_PUBLICATION_NOT_IDEMPOTENT");
  UUID set=(UUID)published.get("publicationSetId");
  validation.resolve("core",revision,set);
  return Map.of("binding",Map.of("semanticId","core","semanticVersion","1.0.0","revisionId",revision,"publicationSetId",set),"requestId",request,"candidateId",candidate,"artifactId",artifact,"checks",List.of("discovery_candidate_persisted","adoption_idempotent_and_draft","explicit_version_validated","service_cannot_approve","human_approved_publication","publication_idempotent","exact_reference_resolved"));
 }
}

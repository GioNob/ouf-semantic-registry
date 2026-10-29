package it.comune.trieste.ouf.semantic.ports;

import java.util.List;

public interface SemanticDiscoveryProvider {
  String providerId();
  /** Configured adapters can be disabled without pretending an external search ran. */
  default boolean enabled(){return true;}
  List<Candidate> search(Query query);
  record Query(String artifactType,String intent,List<String> preferredLanguages){}
  record Candidate(String canonicalUri,String sourceLocation,String artifactType,String trust,double score,
                   List<String> reasons,List<String> gaps,byte[] content,String mediaType){}
}

package it.comune.trieste.ouf.semantic.ports;

import java.time.Instant;
import java.util.List;
import java.util.Map;

public interface SemanticDiscoveryProvider {
  String providerId();
  /** Configured adapters can be disabled without pretending an external search ran. */
  default boolean enabled(){return true;}
  List<Candidate> search(Query query);
  default SearchResult searchWithExclusions(Query query){
    return new SearchResult(search(query),0);
  }
  record SearchResult(List<Candidate> candidates,int fetchDenied){
    public SearchResult {
      candidates=List.copyOf(candidates);
      if(fetchDenied<0)throw new IllegalArgumentException("negative exclusion count");
    }
  }
  record Query(String artifactType,String intent,List<String> preferredLanguages,Instant deadline){
    public Query(String type,String intent,List<String> languages){
      this(type,intent,languages,Instant.now().plusSeconds(120));
    }
  }
  record Candidate(String canonicalUri,String sourceLocation,String artifactType,String trust,double score,
                   List<String> reasons,List<String> gaps,byte[] content,String mediaType,
                   byte[] ontologyProvenance,Map<String,String> labels){
    public Candidate(String uri,String source,String type,String trust,double score,List<String> reasons,
                     List<String> gaps,byte[] content,String mediaType){
      this(uri,source,type,trust,score,reasons,gaps,content,mediaType,null,Map.of());
    }
  }
}

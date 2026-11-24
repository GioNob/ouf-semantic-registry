package it.comune.trieste.ouf.semantic.application;

import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic;
import java.util.List;

/** A provider that can report how many fetches its namespace policy suppressed. */
public interface NamespaceFilteredDiscoveryProvider extends SemanticDiscoveryProvider {
  record FilteredResult(SearchResult fetched, int namespaceExcluded) {
    public FilteredResult {
      if(namespaceExcluded<0)throw new IllegalArgumentException("negative exclusion count");
    }
  }

  FilteredResult searchWithNamespaceFilter(Query query);

  default FilteredResult searchWithNamespaceFilter(Query query, DiscoveryTraffic traffic) {
    return searchWithNamespaceFilter(query);
  }

  @Override
  default SearchResult searchWithExclusions(Query query) {
    return searchWithNamespaceFilter(query).fetched();
  }

  @Override
  default List<Candidate> search(Query query) {
    return searchWithExclusions(query).candidates();
  }
}

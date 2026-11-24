package it.comune.trieste.ouf.semantic.ports;

/** Observations for one job, including work completed before an attempt failed. */
public interface DiscoveryTraffic {
  enum Route { search, fetch }
  enum Origin { APISIX, UPSTREAM, UNKNOWN }

  DiscoveryTraffic NONE = new DiscoveryTraffic() {};
  default void sent(Route route, String resource) {}
  default void excluded() {}
  default void useful(String resource) {}
  default void http429(Route route, Origin origin) {}
}

package it.comune.trieste.ouf.semantic.ports;

/** Observations for one job, including work completed before an attempt failed. */
public interface DiscoveryTraffic {
  enum Route { search, fetch }
  enum Origin { APISIX, UPSTREAM, UNKNOWN }

  DiscoveryTraffic NONE = new DiscoveryTraffic() {};
  enum Outcome { SUCCESS, KNOWN_ERROR, UNCERTAIN }

  interface Reservation {
    default <T> T dispatch(java.time.Duration timeout, java.util.function.Function<java.time.Duration,T> send) {
      return send.apply(timeout);
    }
    default void finish(Outcome outcome, java.time.Duration retryAfter) {}
  }

  default Reservation acquire() { return new Reservation() {}; }
  default void optionalBackoff(String code, java.time.Duration retryAfter) {}
  default void sent(Route route, String resource) {}
  default void excluded() {}
  default void useful(String resource) {}
  default void http429(Route route, Origin origin) {}
}

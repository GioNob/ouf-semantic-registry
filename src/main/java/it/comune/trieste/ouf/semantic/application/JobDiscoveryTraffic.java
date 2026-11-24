package it.comune.trieste.ouf.semantic.application;

import it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic;
import java.util.UUID;
import org.springframework.jdbc.core.simple.JdbcClient;

record JobDiscoveryTraffic(JdbcClient db, UUID job) implements DiscoveryTraffic {
  @Override public void sent(Route route, String resource) {
    if (route == Route.search) {
      increment("searchSent", "", "");
      return;
    }
    db.sql("""
        insert into ouf_sem.discovery_fetch_traffic as t (request_id,resource_hash,sends)
        values (:job,decode(:hash,'hex'),1)
        on conflict (request_id,resource_hash) do update set sends=t.sends+1
        """).param("job",job).param("hash",DiscoveryJobService.hash(resource)).update();
  }

  @Override public void useful(String resource) {
    db.sql("""
        update ouf_sem.discovery_fetch_traffic set useful=true
        where request_id=:job and resource_hash=decode(:hash,'hex') and not useful
        """).param("job",job).param("hash",DiscoveryJobService.hash(resource)).update();
  }

  @Override public void excluded() {
    increment("getExcluded", "", "");
  }

  @Override public void http429(Route route, Origin origin) {
    increment("http429", route.name(), origin.name());
  }

  private void increment(String metric, String route, String origin) {
    db.sql("""
        insert into ouf_sem.discovery_traffic_count as t (request_id,metric,route,origin,amount)
        values (:job,:metric,:route,:origin,1)
        on conflict (request_id,metric,route,origin) do update set amount=t.amount+1
        """).param("job",job).param("metric",metric).param("route",route).param("origin",origin).update();
  }
}

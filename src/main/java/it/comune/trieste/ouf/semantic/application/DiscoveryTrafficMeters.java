package it.comune.trieste.ouf.semantic.application;

import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.binder.MeterBinder;
import it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic.Origin;
import it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic.Route;
import java.util.List;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Component;

/** Each replica reads the same durable totals for retained jobs. Scraping is read-only. */
@Component
record DiscoveryTrafficMeters(ObjectProvider<DiscoveryJobService> jobs) implements MeterBinder {
  @Override public void bindTo(MeterRegistry meters) {
    for (String name : List.of("getUseful","getExcluded","getRepeated","getSent","searchSent")) {
      Gauge.builder("ouf.semantic.discovery."+name, jobs, j -> j.getObject().trafficTotal(name,"",""))
          .register(meters);
    }
    for (String name : List.of("slotOccupancy","slotWaits","slotUncertain","slotAcquisitionSeconds")) {
      Gauge.builder("ouf.semantic.discovery."+name, jobs, j -> j.getObject().slotMetric(name)).register(meters);
    }
    for (Route route : Route.values()) {
      for (Origin origin : Origin.values()) {
        Gauge.builder("ouf.semantic.discovery.http429", jobs,
                j -> j.getObject().trafficTotal("http429",route.name(),origin.name()))
            .tags("route",route.name(),"origin",origin.name()).register(meters);
      }
    }
  }
}

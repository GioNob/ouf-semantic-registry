package it.comune.trieste.ouf.semantic.application;

import it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic;
import it.comune.trieste.ouf.semantic.adapters.discovery.BoundedGatewayClient.ProviderFailure;
import it.comune.trieste.ouf.semantic.adapters.discovery.ProviderFailurePolicy;
import java.time.Duration;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;
import java.util.function.Function;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.jdbc.core.simple.JdbcClient;

final class JobDiscoveryTraffic implements DiscoveryTraffic {
  static final class Stale extends RuntimeException {}
  static final class SlotWaitExpired extends RuntimeException {}
  static final class ProfileDrift extends RuntimeException {}
  private final JdbcClient db;
  private final TransactionTemplate transactions;
  private final ProviderCapacityProfile profile;
  private final UUID job;
  private final long generation, token;
  private final String provider;
  private ProviderFailurePolicy.Decision optionalFailure;

  JobDiscoveryTraffic(JdbcClient db, TransactionTemplate transactions, ProviderCapacityProfile profile,
      UUID job, long generation, String provider, long token) {
    this.db=db;this.transactions=transactions;this.profile=profile;this.job=job;
    this.generation=generation;this.provider=provider;this.token=token;
  }

  @Override public void optionalBackoff(String code, Duration delay) {
    optionalFailure=new ProviderFailurePolicy.Decision(ProviderFailurePolicy.Kind.TRANSIENT,code,delay);
  }
  ProviderFailurePolicy.Decision optionalFailure(){return optionalFailure;}

  @Override public Reservation acquire() {
    UUID id=UUID.randomUUID();
    boolean first=true;
    while (true) {
      long beforePoll=System.nanoTime();
      var poll=db.sql("""
          select status,remaining_ms from ouf_sem.acquire_discovery_slot(:job,:worker,:provider,:token,
            :installation,:logical,:version,:capacity,:seconds,:reconcile,:wait,:id,:first)
          """).param("job",job).param("worker",generation).param("provider",provider).param("token",token)
          .param("installation",profile.installationId()).param("logical",profile.logicalProviderId())
          .param("version",profile.profileVersion()).param("capacity",profile.installationProviderInFlight())
          .param("seconds",profile.slotMaxSeconds()).param("reconcile",profile.reconciliationTimeoutSeconds())
          .param("wait",profile.slotWaitMaxSeconds()).param("id",id).param("first",first).query().singleRow();
      switch ((String)poll.get("status")) {
        case "ACQUIRED" -> { return new Slot(id); }
        case "TIMEOUT" -> throw new SlotWaitExpired();
        case "STALE" -> throw new Stale();
        case "DRIFT" -> throw new ProfileDrift();
        case "WAIT" -> first=false;
        default -> throw new IllegalStateException("DISCOVERY_ADMISSION_INVALID");
      }
      // The autocommit poll is over. Sleep with no database resource checked out.
      long remaining=((Number)poll.get("remaining_ms")).longValue()
          -TimeUnit.NANOSECONDS.toMillis(System.nanoTime()-beforePoll);
      long jitter=ThreadLocalRandom.current().nextLong(50,61);
      try {
        Thread.sleep(Math.max(0,Math.min(jitter,remaining)));
      } catch (InterruptedException interrupted) {
        db.sql("delete from ouf_sem.discovery_slot_waiter where id=?").param(id).update();
        Thread.currentThread().interrupt();
        throw new ProviderFailure("PROVIDER_INTERRUPTED");
      }
    }
  }

  private final class Slot implements Reservation {
    private final UUID id;
    Slot(UUID id){this.id=id;}

    @Override public <T> T dispatch(Duration timeout, Function<Duration,T> start) {
      // Fence enqueue and record its accepted-send count before releasing the lock.
      // A failed commit leaves the earlier durable reservation open.
      return transactions.execute(tx->{
        if(!ownerValid())throw new Stale();
        long checkedAt=System.nanoTime();
        var remaining=db.sql("""
            update ouf_sem.discovery_provider_slot set outcome='IN_FLIGHT'
            where reservation=? and outcome='RESERVED' and expires_at>clock_timestamp()
            returning floor(extract(epoch from expires_at-clock_timestamp())*1000)::bigint
            """).param(id).query(Long.class).optional();
        if(remaining.isEmpty() || remaining.get()<1)throw new Stale();
        var maximum=Duration.ofMillis(remaining.get()).minusNanos(System.nanoTime()-checkedAt);
        if(maximum.toMillis()<1)throw new Stale();
        return start.apply(timeout.compareTo(maximum)<0?timeout:maximum);
      });
    }
    @Override public void finish(Outcome outcome, Duration retryAfter) {
      boolean accepted=Boolean.TRUE.equals(transactions.execute(tx->{
        if(!ownerValid() || !transition("IN_FLIGHT",outcome.name())){
          // A late, known response is evidence only for this exact reservation.
          // Preserve it for the reconciler without granting publication authority.
          if(outcome!=Outcome.UNCERTAIN)
            db.sql("""
                update ouf_sem.discovery_provider_slot set ended_at=clock_timestamp(),outcome='UNCERTAIN'
                where reservation=? and outcome in ('IN_FLIGHT','UNCERTAIN')
                """).param(id).update();
          return false;
        }
        if(retryAfter!=null){
          // A crash between observing a transient response and scheduling the job
          // must not erase its Retry-After. Both clocks share the slot-close commit.
          db.sql("""
              with cooldown as (
                update ouf_sem.discovery_dependency set next_attempt_at=case
                  when :seconds>2147483647 then 'infinity'::timestamptz
                  else clock_timestamp()+make_interval(secs=>greatest(cast(:seconds as double precision),
                    (case attempts when 1 then 5 when 2 then 15 when 3 then 60 when 4 then 300 else 900 end)
                    *(1+random()*0.2))) end
                where active_request=:job and request_generation=:worker and provider_id=:provider
                returning next_attempt_at)
              update ouf_sem.discovery_request set next_attempt_at=cooldown.next_attempt_at
              from cooldown where request_id=:job
              """).param("seconds",retryAfter.getSeconds()+(retryAfter.getNano()==0?0d:1d))
              .param("job",job).param("worker",generation).param("provider",provider).update();
        }
        return true;
      }));
      if(!accepted)throw new Stale();
    }
    private boolean ownerValid() {
      return db.sql("select ouf_sem.discovery_owner_deadline(?,?,?,?) is not null")
          .param(job).param(generation).param(provider).param(token).query(Boolean.class).single();
    }
    private boolean transition(String expected,String next) {
      return db.sql("""
          update ouf_sem.discovery_provider_slot set outcome=:next
          where reservation=:id and outcome=:expected and expires_at>clock_timestamp()
          """).param("next",next).param("id",id).param("expected",expected).update()==1;
    }
  }

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

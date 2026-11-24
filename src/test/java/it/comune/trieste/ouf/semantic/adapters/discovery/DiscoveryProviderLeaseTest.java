package it.comune.trieste.ouf.semantic.adapters.discovery;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.assertj.core.api.Assertions.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import it.comune.trieste.ouf.semantic.application.DiscoveryJobService;
import it.comune.trieste.ouf.semantic.application.DiscoveryService;
import it.comune.trieste.ouf.semantic.application.ProviderCapacityProfile;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.jdbc.support.JdbcTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;
import org.testcontainers.containers.PostgreSQLContainer;

/** SEM-55F-01..06, PET-semantic-294/307. Only the disposable test sessions
 * resolve clock_timestamp() through a controllable PostgreSQL clock. */
class DiscoveryProviderLeaseTest {
  static final PostgreSQLContainer<?> postgres=new PostgreSQLContainer<>("postgres:17-alpine");
  static final String TERM="https://terms.example.test/a";
  static final String JSON="{\"results\":{\"bindings\":[{\"resource\":{\"value\":\""+TERM+"\"}}]}}";
  String searchResponse=JSON;
  final ObjectMapper json=new ObjectMapper();
  final ExecutorService pool=Executors.newCachedThreadPool();
  final AtomicInteger active=new AtomicInteger(),peak=new AtomicInteger(),searches=new AtomicInteger(),fetches=new AtomicInteger();
  final CountDownLatch entered=new CountDownLatch(1), release=new CountDownLatch(1);
  JdbcClient db;
  TransactionTemplate tx;
  HttpServer server;
  SchemaGovProperties config;

  @BeforeAll static void startDatabase(){postgres.start();}
  @AfterAll static void stopDatabase(){postgres.stop();}

  @BeforeEach void setup() throws IOException {
    var source=new DriverManagerDataSource(postgres.getJdbcUrl(),postgres.getUsername(),postgres.getPassword());
    var flyway=Flyway.configure().dataSource(source).schemas("ouf_sem").cleanDisabled(false).load();
    flyway.clean();
    flyway.migrate();
    db=JdbcClient.create(source);
    db.sql("create schema if not exists pet_clock").update();
    db.sql("create table if not exists pet_clock.offset_seconds(id boolean primary key, seconds integer not null)").update();
    db.sql("insert into pet_clock.offset_seconds values(true,0) on conflict(id) do update set seconds=0").update();
    db.sql("""
        create or replace function pet_clock.clock_timestamp() returns timestamptz language sql volatile as $$
          select pg_catalog.clock_timestamp()+make_interval(secs=>seconds) from pet_clock.offset_seconds
        $$
        """).update();
    var properties=new java.util.Properties();
    properties.setProperty("options","-c search_path=pet_clock,pg_catalog,public,ouf_sem");
    source.setConnectionProperties(properties);
    tx=new TransactionTemplate(new JdbcTransactionManager(source));
    server=HttpServer.create(new InetSocketAddress("localhost",0),0);
    server.setExecutor(pool);
    server.start();
    config=new SchemaGovProperties(true,URI.create("http://localhost:"+server.getAddress().getPort()),
        "/search","/fetch",Duration.ofSeconds(2),Duration.ofSeconds(20),8192,5,1,
        Duration.ofMillis(100),3,Duration.ofSeconds(30),List.of("https://terms.example.test/"));
  }
  @AfterEach void stop(){release.countDown();server.stop(0);pool.shutdownNow();}

  DiscoveryService worker(){return worker(new BoundedGatewayClient(config.connectTimeout()));}
  DiscoveryService worker(BoundedGatewayClient client){
    var adapter=new SchemaGovProvider(config,client,json,Clock.systemUTC());
    return new DiscoveryService(db,List.of(adapter),new SafeRdfParser(),json,tx);
  }
  DiscoveryService worker(ProviderCapacityProfile profile){
    var adapter=new SchemaGovProvider(config,new BoundedGatewayClient(config.connectTimeout()),json,Clock.systemUTC());
    return new DiscoveryService(db,List.of(adapter),new SafeRdfParser(),json,tx,null,profile);
  }
  void awaitWaiters(int expected) throws InterruptedException {
    long until=System.nanoTime()+TimeUnit.SECONDS.toNanos(8);
    while(count("select count(*) from ouf_sem.discovery_slot_waiter")!=expected && System.nanoTime()<until)
      Thread.sleep(10);
    assertThat(count("select count(*) from ouf_sem.discovery_slot_waiter")).isEqualTo(expected);
  }
  UUID queue(DiscoveryService worker,String scope){return worker.request("CLASS","term",List.of(),scope);}
  int metric(String metric){
    return db.sql("select amount from ouf_sem.discovery_slot_metrics where metric=?").param(metric).query(Integer.class).single();
  }
  String state(UUID id){
    return db.sql("select state from ouf_sem.discovery_request where request_id=?").param(id).query(String.class).single();
  }
  long count(String sql){return db.sql(sql).query(Long.class).single();}
  void advance(int seconds){
    db.sql("update pet_clock.offset_seconds set seconds=seconds+?").param(seconds).update();
    assertThat(db.sql("select clock_timestamp() >= pg_catalog.clock_timestamp()+make_interval(secs=>seconds-1) from pet_clock.offset_seconds")
        .query(Boolean.class).single()).isTrue();
  }
  void respond(HttpExchange exchange,boolean search,boolean hold,int status) throws IOException {
    respond(exchange,search,hold,status,entered);
  }
  void respond(HttpExchange exchange,boolean search,boolean hold,int status,CountDownLatch arrivals) throws IOException {
    peak.accumulateAndGet(active.incrementAndGet(),Math::max);
    try(exchange){
      (search?searches:fetches).incrementAndGet();
      if(hold){arrivals.countDown();await(release);}
      if(status==429)exchange.getResponseHeaders().set("Retry-After","3600");
      exchange.getResponseHeaders().set("Content-Type",search?"application/json":"text/turtle");
      String body=search?searchResponse:"<"+java.net.URLDecoder.decode(exchange.getRequestURI().getRawQuery().substring(4),UTF_8)
          +"> a <urn:fixture:Class> .";
      byte[] bytes=body.getBytes(UTF_8);
      exchange.sendResponseHeaders(status,bytes.length);
      exchange.getResponseBody().write(bytes);
    }finally{active.decrementAndGet();}
  }
  static void await(CountDownLatch latch){
    try{assertThat(latch.await(10,TimeUnit.SECONDS)).isTrue();}
    catch(InterruptedException e){Thread.currentThread().interrupt();throw new AssertionError(e);}
  }

  @Test @DisplayName("SEM-55F-01 two replicas share one physical slot across scopes and routes")
  void concurrency() throws Exception {
    server.createContext("/search",x->respond(x,true,false,200));
    server.createContext("/fetch",x->respond(x,false,fetches.get()==0,200));
    var first=worker();
    var second=worker();
    UUID a=queue(first,"tenant-a/subject-a");
    var running=pool.submit(first::executeOne);
    await(entered);
    try{
      UUID b=queue(second,"tenant-b/subject-b");
      var waiting=pool.submit(second::executeOne);
      awaitWaiters(1);
      assertThat(metric("slotOccupancy")).isOne();
      assertThat(metric("slotWaits")).isOne();
      assertThat(state(b)).isEqualTo("RUNNING");
      assertThat(count("select sum(amount) from ouf_sem.discovery_job_traffic where metric='searchSent'")).isOne();
      assertThat(count("select count(*) from ouf_sem.discovery_job_traffic where request_id='"+b+"'")).isZero();
      release.countDown();
      assertThat(running.get(10,TimeUnit.SECONDS)).isOne();
      assertThat(waiting.get(10,TimeUnit.SECONDS)).isOne();
      assertThat(state(a)).isEqualTo("SUCCEEDED");
      assertThat(state(b)).isEqualTo("SUCCEEDED");
      assertThat(peak).hasValue(1);
      assertThat(searches).hasValue(2);
      assertThat(fetches).hasValue(2);
      assertThat(count("select acquisitions from ouf_sem.discovery_provider_capacity")).isEqualTo(4);
      assertThat(metric("slotOccupancy")).isZero();
    }finally{release.countDown();}
  }

  @Test @DisplayName("SEM-55F-02 lost process, uncertain reservation and explicit reconciliation on the original job")
  void crash() throws Exception {
    // Lose the worker after an actual HTTP response, before its release commit.
    server.createContext("/search",x->respond(x,true,false,200));
    server.createContext("/fetch",x->respond(x,false,false,200));
    var crash=new AssertionError("stopped after dispatch");
    var abandoned=new java.util.concurrent.atomic.AtomicReference<DiscoveryTraffic.Reservation>();
    var first=worker(new BoundedGatewayClient(config.connectTimeout()){
      @Override Response postForm(URI base,URI uri,String form,Duration timeout,int limit,
          Set<String> media,DiscoveryTraffic traffic){
        return super.postForm(base,uri,form,timeout,limit,media,new DiscoveryTraffic(){
          @Override public Reservation acquire(){
            var slot=traffic.acquire();
            abandoned.set(slot);
            return new Reservation(){
              @Override public <T> T dispatch(Duration budget,java.util.function.Function<Duration,T> start){
                return slot.dispatch(budget,start);
              }
              @Override public void finish(Outcome outcome,Duration retryAfter){throw crash;}
            };
          }
          @Override public void sent(Route route,String resource){traffic.sent(route,resource);}
        });
      }
    });
    UUID id=queue(first,"tenant-a/subject-a");
    assertThatThrownBy(first::executeOne).isSameAs(crash);
    advance(121);
    var successor=worker(new ProviderCapacityProfile("default","SCHEMA_GOV_IT","2",1,2,60,300,30));
    var waiting=pool.submit(successor::executeOne);
    awaitWaiters(1);
    assertThat(count("select count(*) from ouf_sem.discovery_provider_capacity where profile_version='1'")).isOne();
    advance(31);
    assertThat(waiting.get(10,TimeUnit.SECONDS)).isOne();
    assertThat(metric("slotOccupancy")).isOne();
    assertThat(metric("slotUncertain")).isOne();
    assertThat(metric("slotWaits")).isOne();
    assertThat(searches).hasValue(1);
    assertThat(count("select count(*) from ouf_sem.discovery_provider_owner")).isOne();
    assertThat(count("select count(*) from ouf_sem.discovery_request")).isOne();
    advance(180);
    db.sql("select ouf_sem.reconcile_discovery_slots()").query().singleRow();
    assertThat(metric("slotOccupancy")).isZero();
    assertThat(db.sql("select outcome from ouf_sem.discovery_provider_slot").query(String.class).single()).isEqualTo("RECONCILED");
    assertThat(successor.executeOne()).isOne();
    assertThat(state(id)).isEqualTo("SUCCEEDED");
    assertThat(count("select count(*) from ouf_sem.discovery_provider_capacity where profile_version='2'")).isOne();
    assertThat(count("select count(*) from ouf_sem.discovery_request")).isOne();
    assertThat(count("select count(*) from ouf_sem.discovery_candidate")).isOne();
    assertThatThrownBy(()->abandoned.get().dispatch(Duration.ofSeconds(1),t->searches.incrementAndGet()))
        .isInstanceOf(RuntimeException.class);
    assertThat(searches).hasValue(2);
  }

  @ParameterizedTest(name="SEM-55F-03 stale {0} after claim cannot send or publish")
  @ValueSource(strings={"job","dependency"})
  void staleBeforeTransport(String fence) throws Exception {
    var first=worker(new BoundedGatewayClient(config.connectTimeout(),()->{
      entered.countDown();await(release);return "fixture";
    }));
    server.createContext("/search",x->respond(x,true,false,200));
    UUID id=queue(first,"tenant-a/subject-a");
    var running=pool.submit(first::executeOne);
    await(entered);
    if(fence.equals("job"))advance(121);
    else db.sql("update ouf_sem.discovery_dependency set generation=generation+1").update();
    release.countDown();
    assertThat(running.get(10,TimeUnit.SECONDS)).isOne();
    assertThat(state(id)).isEqualTo("RUNNING");
    assertThat(searches).hasValue(0);
    assertThat(count("select count(*) from ouf_sem.discovery_job_traffic")).isZero();
    assertThat(count("select count(*) from ouf_sem.audit_event where event_type='DISCOVERY_COMPLETED'")).isZero();
  }

  @Test @DisplayName("SEM-55F-03 late physical response cannot publish candidates")
  void lateResponse() throws Exception {
    server.createContext("/search",x->respond(x,true,false,200));
    server.createContext("/fetch",x->respond(x,false,true,200));
    var first=worker();
    UUID id=queue(first,"tenant-a/subject-a");
    var running=pool.submit(first::executeOne);
    await(entered);
    advance(121);
    release.countDown();
    assertThat(running.get(10,TimeUnit.SECONDS)).isOne();
    assertThat(state(id)).isEqualTo("RUNNING");
    assertThat(count("select count(*) from ouf_sem.discovery_candidate")).isZero();
    assertThat(count("select count(*) from ouf_sem.audit_event where event_type='DISCOVERY_COMPLETED'")).isZero();
    assertThat(metric("slotUncertain")).isOne();
    db.sql("select ouf_sem.reconcile_discovery_slots()").query().singleRow();
    assertThat(metric("slotOccupancy")).isZero(); // positive end evidence, before the maximum horizon
  }

  @Test @DisplayName("SEM-55F-03 subject lease spans final parsing and publication")
  void staleAfterSlotRelease() throws Exception {
    server.createContext("/search",x->respond(x,true,false,200));
    server.createContext("/fetch",x->respond(x,false,false,200));
    var parser=org.mockito.Mockito.mock(SafeRdfParser.class);
    org.mockito.Mockito.when(parser.parse(org.mockito.ArgumentMatchers.any(byte[].class),
        org.mockito.ArgumentMatchers.eq("text/turtle"))).thenAnswer(call->{
          entered.countDown();await(release);
          return new SafeRdfParser().parse(call.getArgument(0),call.getArgument(1));
        });
    var provider=new SchemaGovProvider(config,new BoundedGatewayClient(config.connectTimeout()),json,Clock.systemUTC());
    var first=new DiscoveryService(db,List.of(provider),parser,json,tx);
    UUID id=queue(first,"tenant-a/subject-a");
    var running=pool.submit(first::executeOne);
    await(entered);
    try{
      assertThat(metric("slotOccupancy")).isZero();
      assertThat(db.sql("select active_request from ouf_sem.discovery_dependency").query(UUID.class).single()).isEqualTo(id);
      var second=worker();
      UUID waiting=queue(second,"tenant-a/subject-a");
      assertThat(second.executeOne()).isZero();
      assertThat(db.sql("select attempt_count from ouf_sem.discovery_request where request_id=?")
          .param(waiting).query(Integer.class).single()).isZero();
      db.sql("update ouf_sem.discovery_dependency set generation=generation+1").update();
    }finally{release.countDown();}
    assertThat(running.get(10,TimeUnit.SECONDS)).isOne();
    assertThat(state(id)).isEqualTo("RUNNING");
    assertThat(count("select count(*) from ouf_sem.discovery_candidate")).isZero();
    assertThat(count("select count(*) from ouf_sem.audit_event where event_type='DISCOVERY_COMPLETED'")).isZero();
  }

  @Test @DisplayName("SEM-55F-04 known 429 releases capacity and resumes the same logical owner")
  void backoff(){
    server.createContext("/search",x->respond(x,true,false,searches.get()==0?429:200));
    server.createContext("/fetch",x->respond(x,false,false,200));
    var worker=worker();
    UUID id=queue(worker,"tenant-a/subject-a");
    assertThat(worker.executeOne()).isOne();
    assertThat(db.sql("""
        select r.next_attempt_at >= a.started_at+interval '1 hour' and r.next_attempt_at=d.next_attempt_at
          and r.lease_until is null and d.busy_until is null and r.recovery_state='RETRY_WAIT'
        from ouf_sem.discovery_request r join ouf_sem.discovery_attempt a using(request_id)
        join ouf_sem.discovery_dependency d using(scope_subject,provider_id) where r.request_id=?
        """).param(id).query(Boolean.class).single()).isTrue();
    assertThat(metric("slotOccupancy")).isZero();
    assertThat(metric("slotUncertain")).isZero();
    var successor=worker();
    assertThat(successor.executeOne()).isZero();
    assertThat(db.sql("select count(*) from ouf_sem.discovery_provider_owner where request_id=?")
        .param(id).query(Long.class).single()).isOne();
    advance(3601);
    assertThat(successor.executeOne()).isOne();
    assertThat(state(id)).isEqualTo("SUCCEEDED");
    assertThat(count("select count(*) from ouf_sem.discovery_request")).isOne();
    assertThat(count("select count(*) from ouf_sem.discovery_provider_owner")).isZero();
    assertThat(count("select amount from ouf_sem.discovery_job_traffic where metric='http429' and origin='UNKNOWN'")).isOne();
  }

  @Test @DisplayName("SEM-55F-01 denied GET consumes no fetch quota")
  void deniedFetch() throws Exception {
    var fetchReady=new CountDownLatch(1);
    var allowFetch=new CountDownLatch(1);
    var credentials=new AtomicInteger();
    var a=worker(new BoundedGatewayClient(config.connectTimeout(),()->{
      if(credentials.incrementAndGet()==2){fetchReady.countDown();await(allowFetch);}
      return "fixture";
    }));
    server.createContext("/search",x->respond(x,true,searches.get()>0,200));
    server.createContext("/fetch",x->respond(x,false,false,200));
    UUID original=queue(a,"tenant-a/subject-a");
    db.sql("update ouf_sem.discovery_request set attempt_count=127 where request_id=?").param(original).update();
    var first=pool.submit(a::executeOne);
    await(fetchReady); // A is between search and required GET, with no physical slot.
    assertThat(metric("slotOccupancy")).isZero();
    var b=worker();
    queue(b,"tenant-b/subject-b");
    var second=pool.submit(b::executeOne);
    await(entered);
    try{
      db.sql("update ouf_sem.discovery_request set lease_until=least(lease_until,clock_timestamp()+interval '65 seconds') where request_id=?")
          .param(original).update();
      allowFetch.countDown();
      awaitWaiters(1);
      assertThat(db.sql("""
          select w.wait_until=r.lease_until-interval '60 seconds' and w.wait_until<w.started_at+interval '30 seconds'
          from ouf_sem.discovery_slot_waiter w join ouf_sem.discovery_request r using(request_id) where r.request_id=?
          """).param(original).query(Boolean.class).single()).isTrue();
      advance(6);
      assertThat(first.get(10,TimeUnit.SECONDS)).isOne();
      assertThat(fetches).hasValue(0);
      assertThat(state(original)).isEqualTo("PENDING");
      assertThat(new DiscoveryJobService(db,a,List.of(),json).status(original,"tenant-a/subject-a"))
          .containsEntry("errorCode","SEM_DISCOVERY_PROVIDER_SLOT_BUSY");
      assertThat(metric("slotWaits")).isOne();
      assertThat(count("select count(*) from ouf_sem.discovery_fetch_traffic")).isZero();
      assertThat(db.sql("""
          select r.attempt_count=128 and r.recovery_state='RETRY_WAIT' and r.last_error_code='SEM_DISCOVERY_PROVIDER_SLOT_BUSY'
            and r.next_attempt_at<=clock_timestamp()+interval '1.2 seconds' and a.outcome is null
            and d.busy_until is null and r.lease_until is null and d.attempts=1
          from ouf_sem.discovery_request r join ouf_sem.discovery_attempt a using(request_id)
          join ouf_sem.discovery_dependency d using(scope_subject,provider_id) where r.request_id=?
          """).param(original).query(Boolean.class).single()).isTrue();
    }finally{allowFetch.countDown();release.countDown();}
    assertThat(second.get(10,TimeUnit.SECONDS)).isOne();
    advance(2);
    assertThat(a.executeOne()).isOne();
    assertThat(state(original)).isEqualTo("SUCCEEDED");
    assertThat(db.sql("select attempt_count from ouf_sem.discovery_request where request_id=?")
        .param(original).query(Integer.class).single()).isEqualTo(128);
    assertThat(db.sql("select cumulative_attempts from ouf_sem.discovery_dependency where active_request is null and scope_subject=?")
        .param("tenant-a/subject-a").query(Long.class).single()).isOne();
  }

  @Test @DisplayName("D-080 Semantic 35 claim, attempt, V24 counters and publication with a V25 reservation")
  void predecessorCanFinishWhileSlotOccupied() throws Exception {
    server.createContext("/search",x->respond(x,true,true,200));
    server.createContext("/fetch",x->respond(x,false,false,200));
    var candidate=worker();
    queue(candidate,"tenant-a/subject-a");
    var first=pool.submit(candidate::executeOne);
    await(entered);
    try{
      UUID prior=queue(candidate,"tenant-b/subject-b");
      assertThat(db.sql("select request_id from ouf_sem.claim_discovery_job('predecessor',120)")
          .query(UUID.class).single()).isEqualTo(prior);
      long token=db.sql("select (ouf_sem.reserve_discovery_dependency(?,1,'SCHEMA_GOV_IT','1.0.3')->>'generation')::bigint")
          .param(prior).query(Long.class).single();
      db.sql("insert into ouf_sem.discovery_traffic_count values(?,'searchSent','','',1)").param(prior).update();
      assertThat(db.sql("select ouf_sem.finish_discovery_dependency(?,1,'SCHEMA_GOV_IT',?,'SUCCESS',null,0)")
          .param(prior).param(token).query(Boolean.class).single()).isTrue();
      assertThat(db.sql("select ouf_sem.publish_discovery_candidates(?,1,'[]',0,0,0)")
          .param(prior).query(Boolean.class).single()).isTrue();
      assertThat(db.sql("select amount from ouf_sem.discovery_job_traffic where request_id=? and metric='searchSent'")
          .param(prior).query(Long.class).single()).isOne();
      assertThat(metric("slotOccupancy")).isOne();
    }finally{release.countDown();}
    assertThat(first.get(10,TimeUnit.SECONDS)).isOne();
  }

  @Test @DisplayName("SEM-55F-05 four jobs each finish one search and five GETs in FIFO order on two replicas")
  void fairPhysicalSends() throws Exception {
    // Check every grant against the oldest durable intent, including a newcomer
    // racing to reacquire immediately after its previous GET.
    db.sql("""
        create function ouf_sem.pet_fifo() returns trigger language plpgsql as $$
        declare head uuid;
        begin
          select id into head from ouf_sem.discovery_slot_waiter order by ticket limit 1;
          if head is not null and head<>new.reservation then raise exception 'PET_FIFO_OVERTAKE'; end if;
          return new;
        end $$
        """).update();
    db.sql("""
        create trigger pet_fifo after insert or update of reservation on ouf_sem.discovery_provider_slot
        for each row execute function ouf_sem.pet_fifo()
        """).update();
    searchResponse=json.writeValueAsString(java.util.Map.of("results",java.util.Map.of("bindings",
        java.util.stream.IntStream.range(0,5).mapToObj(i->java.util.Map.of("resource",java.util.Map.of("value",TERM+i))).toList())));
    server.createContext("/search",x->respond(x,true,searches.get()==0,200));
    server.createContext("/fetch",x->respond(x,false,false,200));
    var replicas=List.of(worker(),worker());
    var runs=new java.util.ArrayList<Future<Integer>>();
    var jobs=new java.util.ArrayList<UUID>();
    try {
      for(int i=0;i<4;i++){
        var replica=replicas.get(i%2);
        jobs.add(queue(replica,"scope-"+i));
        runs.add(pool.submit(replica::executeOne));
        if(i==0)await(entered);
        else awaitWaiters(i);
      }
      assertThat(db.sql("select request_id from ouf_sem.discovery_slot_waiter order by ticket").query(UUID.class).list())
          .containsExactlyElementsOf(jobs.subList(1,4));
    } finally {release.countDown();}
    for(var run:runs)assertThat(run.get(30,TimeUnit.SECONDS)).isOne();
    assertThat(peak).hasValue(1);
    assertThat(searches).hasValue(4);
    assertThat(fetches).hasValue(20);
    assertThat(metric("slotWaits")).isGreaterThanOrEqualTo(3);
    assertThat(count("select count(*) from ouf_sem.discovery_slot_waiter")).isZero();
    assertThat(count("select count(*) from ouf_sem.discovery_request where state='SUCCEEDED' and worker_generation=1 and attempt_count=1")).isEqualTo(4);
    assertThat(count("select count(*) from ouf_sem.discovery_candidate")).isEqualTo(20);
    assertThat(count("select count(*) from ouf_sem.discovery_job_traffic where metric='searchSent' and amount=1")).isEqualTo(4);
    assertThat(count("select count(*) from ouf_sem.discovery_job_traffic where metric='getSent' and amount=5")).isEqualTo(4);
    assertThat(count("select sum(amount) from ouf_sem.discovery_job_traffic where metric='getRepeated'")).isZero();
  }

  @Test @DisplayName("SEM-55F-06 drain A before B, including later GETs from the A worker")
  void profileRollout() throws Exception {
    var twoOnB=new CountDownLatch(2);
    var finishB=new CountDownLatch(1);
    server.createContext("/search",x->{
      if(searches.get()>0){twoOnB.countDown();await(finishB);}
      respond(x,true,searches.get()==0,200);
    });
    server.createContext("/fetch",x->{twoOnB.countDown();await(finishB);respond(x,false,false,200);});
    var a=worker(new ProviderCapacityProfile("default","logical","A",1,1,60,300,30));
    var b=worker(new ProviderCapacityProfile("default","logical","B",1,2,60,300,30));
    UUID original=queue(a,"scope-a");
    var first=pool.submit(a::executeOne);
    await(entered);
    var deadline=db.sql("select budget_deadline from ouf_sem.discovery_request where request_id=?")
        .param(original).query(java.time.OffsetDateTime.class).single();
    UUID next=queue(b,"scope-b");
    var second=pool.submit(b::executeOne);
    try {
      awaitWaiters(1);
      assertThat(count("select count(*) from ouf_sem.discovery_capacity_version")).isEqualTo(2);
      assertThat(count("select count(*) from ouf_sem.discovery_provider_capacity where profile_version='A'")).isOne();
      assertThat(metric("slotOccupancy")).isOne();
      assertThat(state(next)).isEqualTo("RUNNING");
      release.countDown();
      await(twoOnB);
      assertThat(count("select count(*) from ouf_sem.discovery_provider_capacity where profile_version='B'")).isOne();
      assertThat(metric("slotOccupancy")).isEqualTo(2);
    } finally {release.countDown();finishB.countDown();}
    assertThat(first.get(10,TimeUnit.SECONDS)).isOne();
    assertThat(second.get(10,TimeUnit.SECONDS)).isOne();
    assertThat(state(original)).isEqualTo("SUCCEEDED");
    assertThat(state(next)).isEqualTo("SUCCEEDED");
    assertThat(db.sql("select budget_deadline from ouf_sem.discovery_request where request_id=?")
        .param(original).query(java.time.OffsetDateTime.class).single()).isEqualTo(deadline);
    assertThat(count("select count(*) from ouf_sem.discovery_request where attempt_count=1")).isEqualTo(2);
    assertThat(count("select count(*) from ouf_sem.discovery_incident")).isZero();
  }

  @Test @DisplayName("SEM-55F-05 a cancelled head cannot dispatch or hold the FIFO")
  void cancelledWaiter() throws Exception {
    server.createContext("/search",x->respond(x,true,searches.get()==0,200));
    server.createContext("/fetch",x->respond(x,false,false,200));
    var worker=worker();
    queue(worker,"scope-holder");
    var holder=pool.submit(worker::executeOne);
    await(entered);
    UUID revoked=queue(worker,"scope-revoked");
    var head=pool.submit(worker::executeOne);
    awaitWaiters(1);
    UUID next=queue(worker,"scope-next");
    var follower=pool.submit(worker::executeOne);
    try {
      awaitWaiters(2);
      db.sql("""
          update ouf_sem.discovery_request set state='CANCELLED',recovery_state='CANCELLED',
            worker_generation=worker_generation+1,lease_until=null where request_id=?
          """).param(revoked).update();
      assertThat(head.get(8,TimeUnit.SECONDS)).isOne();
      awaitWaiters(1);
    } finally {release.countDown();}
    assertThat(holder.get(10,TimeUnit.SECONDS)).isOne();
    assertThat(follower.get(10,TimeUnit.SECONDS)).isOne();
    assertThat(state(next)).isEqualTo("SUCCEEDED");
    assertThat(state(revoked)).isEqualTo("CANCELLED");
    assertThat(db.sql("select count(*) from ouf_sem.discovery_job_traffic where request_id=?")
        .param(revoked).query(Long.class).single()).isZero();
  }

  @ParameterizedTest(name="SEM-55F-06 inconsistent {0} blocks only its scope")
  @ValueSource(strings={"installation","logical","values"})
  void inconsistentConfiguration(String mismatch){
    server.createContext("/search",x->respond(x,true,false,200));
    server.createContext("/fetch",x->respond(x,false,false,200));
    var first=worker(new ProviderCapacityProfile("default","logical","A",1,1,60,300,30));
    queue(first,"scope-a");
    assertThat(first.executeOne()).isOne();
    var changed=worker(new ProviderCapacityProfile(mismatch.equals("installation")?"other":"default",
        mismatch.equals("logical")?"other":"logical","A",1,mismatch.equals("values")?2:1,60,300,30));
    UUID id=queue(changed,"scope-b");
    assertThat(changed.executeOne()).isOne();
    assertThat(new DiscoveryJobService(db,changed,List.of(),json).status(id,"scope-b"))
        .containsEntry("errorCode","DISCOVERY_CAPACITY_CONFIG_DRIFT");
    assertThat(db.sql("""
        select recovery_state='BLOCKED' and last_error_code='DISCOVERY_CAPACITY_CONFIG_DRIFT'
        from ouf_sem.discovery_request where request_id=?
        """).param(id).query(Boolean.class).single()).isTrue();
    assertThat(count("select count(*) from ouf_sem.discovery_provider_capacity")).isOne();
    assertThat(searches).hasValue(1);
  }

  @Test @DisplayName("SEM-55F-01 configured capacity admits two concurrent replicas and defers the third")
  void configuredCapacity() throws Exception {
    var both=new CountDownLatch(2);
    server.createContext("/search",x->respond(x,true,true,200,both));
    server.createContext("/fetch",x->respond(x,false,false,200));
    var profile=new ProviderCapacityProfile("default","logical","1",1,2,120,300,30);
    var a=worker(profile);var b=worker(profile);var c=worker(profile);
    queue(a,"tenant-a/subject-a");queue(b,"tenant-a/subject-b");
    var first=pool.submit(a::executeOne);var second=pool.submit(b::executeOne);
    try{
      await(both);
      UUID third=queue(c,"tenant-b/subject-c");
      assertThat(c.executeOne()).isOne();
      assertThat(state(third)).isEqualTo("PENDING");
      assertThat(metric("slotOccupancy")).isEqualTo(2);
      assertThat(metric("slotWaits")).isOne();
    }finally{release.countDown();}
    assertThat(first.get(10,TimeUnit.SECONDS)).isOne();
    assertThat(second.get(10,TimeUnit.SECONDS)).isOne();
    assertThat(peak).hasValue(2);
    assertThat(searches).hasValue(2);
    assertThat(metric("slotOccupancy")).isZero();
  }

  @Test void installationBoundsAreValidated(){
    assertThatThrownBy(()->new ProviderCapacityProfile("","logical","1",1,1,120,300,30)).isInstanceOf(IllegalArgumentException.class);
    for(int bad:List.of(0,33))
      assertThatThrownBy(()->new ProviderCapacityProfile("default","logical","1",1,bad,120,300,30)).isInstanceOf(IllegalArgumentException.class);
    for(int bad:List.of(0,121))
      assertThatThrownBy(()->new ProviderCapacityProfile("default","logical","1",1,1,bad,300,30)).isInstanceOf(IllegalArgumentException.class);
    for(int bad:List.of(119,86401))
      assertThatThrownBy(()->new ProviderCapacityProfile("default","logical","1",1,1,120,bad,30)).isInstanceOf(IllegalArgumentException.class);
    for(int bad:List.of(0,121))
      assertThatThrownBy(()->new ProviderCapacityProfile("default","logical","1",1,1,60,300,bad)).isInstanceOf(IllegalArgumentException.class);
  }
}

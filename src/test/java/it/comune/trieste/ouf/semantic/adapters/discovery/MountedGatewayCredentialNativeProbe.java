package it.comune.trieste.ouf.semantic.adapters.discovery;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import it.comune.trieste.ouf.semantic.api.NativeIssuedWorkloadAdmission;

/** Disposable CI probe, outside the production JAR and default JUnit discovery. */
public final class MountedGatewayCredentialNativeProbe {
  public static void main(String[] args) throws Exception {
    if(args.length!=2)throw new AssertionError("EXACT_NATIVE_PROBE_ARGUMENTS_REQUIRED");
    String uid=Files.readAllLines(Path.of("/proc/self/status")).stream()
        .filter(v->v.startsWith("Uid:")).findFirst().orElseThrow();
    if(!uid.substring(4).trim().matches("10001\\s+10001\\s+10001\\s+10001"))
      throw new AssertionError("ACTUAL_NONROOT_SEMANTIC_UID_REQUIRED");
    if(args[1].startsWith("real-iam")){
      realIam(Path.of(args[0]).resolve("root-service-readonly"),args[1]);
      System.out.println("NATIVE_GATEWAY_CREDENTIAL_CONTRACT=PASS");return;
    }
    Path credential=Path.of(args[0]).resolve(args[1]);
    boolean accepted=Set.of("root-service-readonly","owner-private-readonly","owner-private-writable").contains(args[1]);
    AtomicInteger calls=new AtomicInteger();
    HttpServer server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);
    server.createContext("/token",exchange->{
      calls.incrementAndGet();byte[] raw=exchange.getRequestBody().readNBytes(8193);
      String form=new String(raw,StandardCharsets.UTF_8);
      if(!exchange.getRequestMethod().equals("POST") || raw.length>8192
          || !form.equals("grant_type=client_credentials&client_id=native-workload&client_secret=native-contract-fixture-only-secret&scope=gateway.invoke")){
        exchange.sendResponseHeaders(400,-1);exchange.close();return;
      }
      byte[] response="{\"access_token\":\"native.fixture.token\",\"token_type\":\"Bearer\",\"expires_in\":300,\"scope\":\"gateway.invoke\"}".getBytes(StandardCharsets.UTF_8);
      exchange.getResponseHeaders().add("Content-Type","application/json");
      exchange.sendResponseHeaders(200,response.length);exchange.getResponseBody().write(response);exchange.close();
    });
    server.start();
    try {
      var cfg=new GatewayOAuthProperties(true,URI.create("http://127.0.0.1:"+server.getAddress().getPort()+"/token"),
          "native-workload",credential,"gateway.invoke",Duration.ofSeconds(2),Duration.ofSeconds(10),32768);
      // HTTP loopback is an existing package-private fixture mechanism only.
      var source=new ClientCredentialsTokenSource(cfg,new ObjectMapper(),Clock.systemUTC(),true);
      if(accepted){
        if(!source.get().equals("native.fixture.token") || !source.get().equals("native.fixture.token") || calls.get()!=1)
          throw new AssertionError("NATIVE_CREDENTIAL_AND_SINGLE_GRANT_CACHE_REQUIRED");
      }else{
        try {source.get();throw new AssertionError("INVALID_NATIVE_CREDENTIAL_WAS_ACCEPTED");}
        catch(BoundedGatewayClient.ProviderFailure failure){
          if(!failure.getMessage().equals("GATEWAY_CREDENTIAL_FILE_INVALID"))throw new AssertionError("EXACT_NATIVE_CUSTODY_DENIAL_REQUIRED");
        }
        if(calls.get()!=0)throw new AssertionError("NO_NETWORK_BEFORE_NATIVE_CUSTODY_REQUIRED");
      }
      System.out.println("NATIVE_GATEWAY_CREDENTIAL_CONTRACT=PASS");
    }finally{server.stop(0);}
  }
  private static void realIam(Path credential,String scenario) {
    try {
      URI issuer=URI.create(System.getProperty("ouf.native.iamIssuer"));
      if(!issuer.getScheme().equals("http") || !issuer.getHost().equals("127.0.0.1")
          || !issuer.getPath().equals("/realms/ouf-native-provider") || issuer.getUserInfo()!=null
          || issuer.getQuery()!=null || issuer.getFragment()!=null)throw new AssertionError("EXACT_LOOPBACK_IAM_FIXTURE_REQUIRED");
      var cfg=new GatewayOAuthProperties(true,URI.create(issuer+"/protocol/openid-connect/token"),"native-workload",credential,
          "gateway.invoke",Duration.ofSeconds(5),Duration.ofSeconds(10),32768);
      var source=new ClientCredentialsTokenSource(cfg,new ObjectMapper(),Clock.systemUTC(),true);
      String token=source.get();
      if(!token.equals(source.get()) || !NativeIssuedWorkloadAdmission.accepts(token,issuer.toString(),"ouf-native-gateway"))
        throw new AssertionError("REAL_ISSUED_WORKLOAD_AND_CACHE_ADMISSION_REQUIRED");
      if(scenario.equals("real-iam-wrong-audience")){
        if(NativeIssuedWorkloadAdmission.accepts(token,issuer.toString(),"unapproved-audience"))
          throw new AssertionError("WRONG_REAL_BEARER_AUDIENCE_WAS_ACCEPTED");
      }else if(scenario.equals("real-iam-invalid-signature")){
        String[] parts=token.split("\\.",-1);
        parts[2]=(parts[2].charAt(0)=='A'?'B':'A')+parts[2].substring(1);
        if(NativeIssuedWorkloadAdmission.accepts(String.join(".",parts),issuer.toString(),"ouf-native-gateway"))
          throw new AssertionError("ALTERED_REAL_BEARER_SIGNATURE_WAS_ACCEPTED");
      }else if(!scenario.equals("real-iam"))throw new AssertionError("EXACT_NATIVE_IAM_SCENARIO_REQUIRED");
    }catch(Exception failure){throw new AssertionError("NATIVE_WORKLOAD_BEARER_ADMISSION_UNPROVEN");}
  }
}

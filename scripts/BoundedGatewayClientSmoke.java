import com.sun.net.httpserver.HttpServer;
import it.comune.trieste.ouf.semantic.adapters.discovery.BoundedGatewayClient;
import java.net.*;
import java.time.Duration;
import java.util.Set;

public class BoundedGatewayClientSmoke {
  public static void main(String[] args) throws Exception {
    HttpServer server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);
    server.createContext("/ok",x->{byte[] b="{}".getBytes();x.getResponseHeaders().add("Content-Type","application/json");x.sendResponseHeaders(200,b.length);x.getResponseBody().write(b);x.close();});
    server.createContext("/redirect",x->{x.getResponseHeaders().add("Location","https://example.invalid");x.sendResponseHeaders(302,-1);x.close();});
    server.start();URI base=URI.create("http://127.0.0.1:"+server.getAddress().getPort());var client=new BoundedGatewayClient(Duration.ofSeconds(1));
    try {
      if(client.get(base,base.resolve("/ok"),Duration.ofSeconds(1),16,Set.of("application/json")).body().length!=2)throw new AssertionError("bounded response");
      boolean rejected=false;try{client.get(base,base.resolve("/redirect"),Duration.ofSeconds(1),16,Set.of("application/json"));}catch(BoundedGatewayClient.ProviderFailure e){rejected="PROVIDER_REDIRECT_FORBIDDEN".equals(e.getMessage());}
      if(!rejected)throw new AssertionError("redirect not rejected");
      System.out.println("PASS BoundedGatewayClient: same-origin response and redirect rejection");
    } finally {server.stop(0);}
  }
}

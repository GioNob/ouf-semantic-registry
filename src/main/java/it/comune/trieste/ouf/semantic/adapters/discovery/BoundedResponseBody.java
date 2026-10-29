package it.comune.trieste.ouf.semantic.adapters.discovery;

import java.io.ByteArrayOutputStream;
import java.net.http.HttpResponse;
import java.nio.ByteBuffer;
import java.util.List;
import java.util.concurrent.*;
import java.util.concurrent.Flow;

/** Bounds both allocation and elapsed time, including receipt after response headers. */
final class BoundedResponseBody implements HttpResponse.BodySubscriber<byte[]> {
  private final int limit;
  private final CompletableFuture<byte[]> result=new CompletableFuture<>();
  private final ByteArrayOutputStream bytes=new ByteArrayOutputStream();
  private Flow.Subscription subscription;
  private BoundedResponseBody(int limit){this.limit=limit;}
  static HttpResponse.BodyHandler<byte[]> handler(int limit) {
    if(limit<1)throw new IllegalArgumentException("positive response bound required");
    return info->new BoundedResponseBody(limit);
  }
  static HttpResponse<byte[]> send(java.net.http.HttpClient client,java.net.http.HttpRequest request,int limit) throws Exception {
    var future=client.sendAsync(request,handler(limit));
    try{return future.get(request.timeout().orElseThrow().toMillis(),TimeUnit.MILLISECONDS);}
    catch(ExecutionException e){if(e.getCause() instanceof BoundedGatewayClient.ProviderFailure failure)throw failure;throw e;}
    finally{if(!future.isDone())future.cancel(true);}
  }
  public CompletionStage<byte[]> getBody(){return result;}
  public void onSubscribe(Flow.Subscription s){subscription=s;s.request(1);}
  public void onNext(List<ByteBuffer> buffers){
    for(ByteBuffer buffer:buffers){
      if(buffer.remaining()>limit-bytes.size()){
        subscription.cancel();result.completeExceptionally(
            new BoundedGatewayClient.ProviderFailure("PROVIDER_RESPONSE_TOO_LARGE"));return;
      }
      byte[] chunk=new byte[buffer.remaining()];buffer.get(chunk);bytes.writeBytes(chunk);
    }
    subscription.request(1);
  }
  public void onError(Throwable error){result.completeExceptionally(error);}
  public void onComplete(){result.complete(bytes.toByteArray());}
}

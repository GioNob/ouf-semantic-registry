package it.comune.trieste.ouf.semantic.adapters.discovery;

import it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic.Origin;
import java.net.URI;
import java.net.http.HttpResponse;

/** Trusted integration point for authenticated, exchange-bound evidence of the producing hop. */
@FunctionalInterface
public interface RateLimitOriginVerifier {
  Origin verifiedOrigin(String method, URI target, HttpResponse.ResponseInfo response);

  default Origin verifiedOrigin(String method, URI target, String exchangeId, HttpResponse.ResponseInfo response) {
    return verifiedOrigin(method, target, response);
  }

  /** A verifier that requires the outstanding exchange. Old callers cannot supply that evidence. */
  @FunctionalInterface
  interface ExchangeBound extends RateLimitOriginVerifier {
    @Override Origin verifiedOrigin(String method, URI target, String exchangeId, HttpResponse.ResponseInfo response);

    @Override default Origin verifiedOrigin(String method, URI target, HttpResponse.ResponseInfo response) {
      return Origin.UNKNOWN;
    }
  }

  RateLimitOriginVerifier UNATTESTED = (method,target,response) -> Origin.UNKNOWN;
}

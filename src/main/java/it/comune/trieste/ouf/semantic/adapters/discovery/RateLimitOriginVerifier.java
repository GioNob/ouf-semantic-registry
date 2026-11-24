package it.comune.trieste.ouf.semantic.adapters.discovery;

import it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic.Origin;
import java.net.URI;
import java.net.http.HttpResponse;

/** Trusted integration point for authenticated, exchange-bound evidence of the producing hop. */
@FunctionalInterface
public interface RateLimitOriginVerifier {
  Origin verifiedOrigin(String method, URI target, HttpResponse.ResponseInfo response);
  RateLimitOriginVerifier UNATTESTED = (method,target,response) -> Origin.UNKNOWN;
}

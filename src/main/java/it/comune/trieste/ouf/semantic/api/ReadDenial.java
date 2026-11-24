package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.authorization.OwnerAuthorization;
import it.comune.trieste.ouf.authorization.ResourceContext;
import jakarta.servlet.http.HttpServletRequest;
import java.util.LinkedHashMap;
import java.util.Set;
import org.slf4j.Logger;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

/** Public denial codes and log fields for the two Gateway receipt domains. */
enum ReadDenial {
  READ("SEM_READ", Set.of(SemanticReadDelegation.SEARCH, SemanticReadDelegation.BATCH, "ouf.semantic.consultation.read")),
  DISCOVERY("SEM_DISCOVERY", Set.of("ouf.semantic.discovery", "ouf.semantic.discovery.status", "ouf.semantic.discovery.candidates"));

  static final String ROUTE_CAPABILITY = ReadDenial.class.getName() + ".routeCapability";
  private static final Set<String> POLICY_CODES = Set.of("TENANT_MISMATCH", "CAPABILITY_NOT_DECLARED",
      "ACTOR_NOT_ALLOWED", "SCOPE_MISSING", "DATA_LABEL_REQUIRED", "HUMAN_REQUIRED", "EXPLICIT_DENY",
      "NO_APPLICABLE_GRANT", "STALE_POLICY_BUNDLE", "NO_POLICY_BUNDLE");
  final Set<String> capabilities;
  private final String receiptCode, policyFallback;

  ReadDenial(String prefix, Set<String> capabilities) {
    this.receiptCode = prefix + "_RECEIPT_INVALID";
    this.policyFallback = prefix + "_POLICY_DENIED";
    this.capabilities = capabilities;
  }

  enum Reason { SIGNATURE, EXPIRED, PATH, CAPABILITY, CLAIMS, SCOPE, BODY_HASH, MALFORMED }

  static final class InvalidReceipt extends SecurityException {
    private final Reason reason;
    private InvalidReceipt(String code, Reason reason) {
      super(code);
      this.reason = reason;
    }
  }

  /** Owner policy denial that keeps the bundle version of the decision, never free text. */
  static final class PolicyDenied extends SecurityException {
    private final long policyVersion;
    private PolicyDenied(String capability, String code, long policyVersion) {
      super("CAPABILITY_DENIED:" + capability + ":" + code);
      this.policyVersion = policyVersion;
    }
  }

  /** {@link OwnerAuthorization#require} with the version of the bundle that decided. */
  static void require(OwnerAuthorization owner, String capability, ResourceContext resource) {
    var decision = owner.decide(capability, resource);
    if (!decision.allowed()) throw new PolicyDenied(capability, decision.decisionCode(), decision.bundleVersion());
  }

  InvalidReceipt invalid(Reason reason) {
    return new InvalidReceipt(receiptCode, reason);
  }

  ResponseEntity<?> respond(Logger log, SecurityException denied, HttpServletRequest request) {
    Object bound = request.getAttribute(ROUTE_CAPABILITY);
    String routeCapability = bound instanceof String value && capabilities.contains(value) ? value : null;
    return respond(log, denied, routeCapability, "");
  }

  ResponseEntity<?> respond(Logger log, SecurityException denied, String routeCapability, String batchLogFields) {
    var body = new LinkedHashMap<String,Object>();
    String message = denied.getMessage();
    if (receiptCode.equals(message)) {
      var reason = denied instanceof InvalidReceipt invalid ? invalid.reason : Reason.MALFORMED;
      body.put("code", receiptCode);
      body.put("denial", "RECEIPT");
      log.info("decision=DENY denial=RECEIPT capability={} reason={}{}", routeCapability, reason, batchLogFields);
    } else {
      String code = policyFallback;
      String capability = null;
      if (message != null && message.startsWith("CAPABILITY_DENIED:")) {
        String[] fields = message.split(":", 3);
        if (fields.length == 3 && !fields[1].isEmpty()) {
          if (POLICY_CODES.contains(fields[2])) code = fields[2];
          if (fields[1].equals(routeCapability) ||
              (SemanticReadDelegation.BATCH.equals(routeCapability) && SemanticReadDelegation.SEARCH.equals(fields[1])))
            capability = fields[1];
        }
      }
      long version = denied instanceof PolicyDenied policy ? policy.policyVersion : 0;
      body.put("code", code);
      body.put("denial", "POLICY");
      if (capability != null) body.put("capability", capability);
      if (version > 0) body.put("policyVersion", version);
      log.info("decision=DENY denial=POLICY capability={} policyCode={}{}{}", capability == null ? routeCapability : capability,
          code, version > 0 ? " policyVersion=" + version : "", batchLogFields);
    }
    return ResponseEntity.status(403).contentType(MediaType.APPLICATION_JSON).body(body);
  }
}

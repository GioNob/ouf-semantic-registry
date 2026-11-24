package it.comune.trieste.ouf.semantic.api;

import static it.comune.trieste.ouf.semantic.api.ReadDenial.READ;
import it.comune.trieste.ouf.semantic.api.ReadDenial.Reason;
import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.authorization.*;
import jakarta.servlet.http.HttpServletRequest;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.time.Instant;
import java.util.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** Gateway/owner key only: MCP never receives this signing key. Read-only MAC domain. */
@Component
public class SemanticReadDelegation {
  private final ObjectMapper json;
  private final String issuer,audience,workload;
  private final byte[] key;
  static final String SEARCH = "ouf.semantic.search";
  static final String BATCH = "ouf.semantic.search.batch";
  public record Receipt(int v,String purpose,String method,String path,String bodyHash,String capability,
      long iat,long exp,String issuer,String audience,String workload,String subject,String tenant,
      String acr,String roles,String scope){}
  public SemanticReadDelegation(ObjectMapper json,
      @Value("${ouf.semantic.delegation.key-file:}") String file,
      @Value("${ouf.iam.issuer:}") String issuer,@Value("${ouf.iam.audience:}") String audience,
      @Value("${ouf.semantic.delegation.workload:}") String workload) {
    this.json=json.copy().enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
      .enable(com.fasterxml.jackson.core.JsonParser.Feature.STRICT_DUPLICATE_DETECTION);
    this.issuer=issuer;this.audience=audience;this.workload=workload;
    try {
      String value=file.isBlank()?"":Files.readString(Path.of(file)).trim();
      if(!file.isBlank() && (!value.matches("[0-9a-fA-F]{64}")||issuer.isBlank()||audience.isBlank()||workload.isBlank()))
        throw new IllegalStateException("SEM_READ_DELEGATION_CONFIG_INVALID");
      key=value.getBytes(StandardCharsets.US_ASCII);
    } catch(java.io.IOException e){throw new IllegalStateException("SEM_READ_DELEGATION_KEY_UNAVAILABLE",e);}
  }
  public PrincipalContext verify(String proof,String path,String capability,byte[] body) {
    if(body==null || body.length>65536)throw READ.invalid(Reason.MALFORMED);
    return signed(proof,path,capability).bind(digest(body));
  }
  record SignedRead(String capability,String bodyHash,long expires,PrincipalContext principal) {
    PrincipalContext bind(String actualDigest) {
      if(expires<=Instant.now().getEpochSecond()) throw READ.invalid(Reason.EXPIRED);
      if(!bodyHash.equals(actualDigest)) throw READ.invalid(Reason.BODY_HASH);
      return principal;
    }
  }
  SignedRead signed(HttpServletRequest request,String capability) {
    return signed(request.getHeader("X-OUF-Semantic-Read-Receipt"),request.getRequestURI(),capability);
  }
  private SignedRead signed(String proof,String path,String capability) {
    try {
      if (!READ.capabilities.contains(capability)) throw READ.invalid(Reason.CAPABILITY);
      if (key.length != 64 || proof == null || proof.length() > 16384)
        throw READ.invalid(Reason.MALFORMED);
      var parts=proof.split("\\.",-1);
      if(parts.length!=2||!parts[0].matches("[A-Za-z0-9_-]+")||!parts[1].matches("[A-Za-z0-9_-]+"))
        throw READ.invalid(Reason.MALFORMED);
      var mac=Mac.getInstance("HmacSHA256");mac.init(new SecretKeySpec(key,"HmacSHA256"));
      if(!MessageDigest.isEqual(mac.doFinal(("ouf-semantic-read-owner-v1."+parts[0]).getBytes(StandardCharsets.US_ASCII)),
          Base64.getUrlDecoder().decode(parts[1])))throw READ.invalid(Reason.SIGNATURE);
      Receipt r=json.readValue(Base64.getUrlDecoder().decode(parts[0]),Receipt.class);
      long now=Instant.now().getEpochSecond();
      if (!path.equals(r.path())) throw READ.invalid(Reason.PATH);
      if (!capability.equals(r.capability())) throw READ.invalid(Reason.CAPABILITY);
      if (r.exp() <= now) throw READ.invalid(Reason.EXPIRED);
      if(r.v()!=1||!"semantic-read-owner".equals(r.purpose())||!"POST".equals(r.method())
          ||r.iat()>now||r.iat()<r.exp()-30||!issuer.equals(r.issuer())||!audience.equals(r.audience())
          ||!workload.equals(r.workload())||r.bodyHash()==null||!r.bodyHash().matches("[0-9a-f]{64}")
          ||!text(r.subject(),256)||!text(r.tenant(),256)||!text(r.acr(),256)||!text(r.scope(),8192))
        throw READ.invalid(Reason.CLAIMS);
      var roles=new TreeSet<String>();
      if(r.roles()!=null&&!r.roles().isEmpty())for(String role:r.roles().split(" ",-1)) {
        if(!role.matches("[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}")||!roles.add(role)||roles.size()>32)
          throw READ.invalid(Reason.CLAIMS);
      }
      var scopes=new HashSet<>(Arrays.asList(r.scope().split(" +")));
      String scope=switch(capability) {
        case BATCH -> SEARCH;
        case "ouf.semantic.consultation.read" -> "ouf.semantic.read";
        default -> capability;
      };
      if(!scopes.contains(scope))throw READ.invalid(Reason.SCOPE);
      var principal=new PrincipalContext(r.subject(),r.tenant(),PrincipalContext.ActorType.HUMAN,r.workload(),r.acr(),
          r.issuer(),r.audience(),scopes,new PrincipalContext.IdentityClaims(roles,r.acr(),Set.of(),null));
      return new SignedRead(capability,r.bodyHash(),r.exp(),principal);
    } catch (ReadDenial.InvalidReceipt invalid) {
      throw invalid;
    } catch (Exception malformed) {
      throw READ.invalid(Reason.MALFORMED);
    }
  }
  static String digest(byte[] bytes) {
    return HexFormat.of().formatHex(sha256().digest(bytes));
  }
  static MessageDigest sha256() {
    try { return MessageDigest.getInstance("SHA-256"); }
    catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
  }
  static boolean matchesDispatch(JsonNode envelope,String capability,String operation) {
    return envelope!=null && capability.equals(envelope.path("CapabilityID").textValue())
        && ("capability://"+capability).equals(envelope.path("GatewayBindingRef").textValue())
        && "semantic".equals(envelope.path("Owner").textValue()) && operation.equals(envelope.path("OperationClass").textValue());
  }
  OwnerAuthorization authorize(HttpServletRequest request,byte[] raw,String capability,String resourceType) {
    if(raw.length>65536)throw READ.invalid(Reason.MALFORMED);
    return authorize(request,signed(request,capability),digest(raw),resourceType);
  }
  OwnerAuthorization authorize(HttpServletRequest request,SignedRead signed,String actualDigest,String resourceType) {
    var principal=signed.bind(actualDigest);
    String capability=signed.capability();
    request.setAttribute(ServletAuthorization.TRUSTED_PRINCIPAL,new TrustedPrincipal(principal));
    var owner=OwnerAuthorization.bind(request);
    var resource=new ResourceContext(resourceType,null,principal.tenantId(),null,Map.of("module","SEMANTIC"));
    ReadDenial.require(owner,capability,resource);
    if(BATCH.equals(capability))ReadDenial.require(owner,SEARCH,resource);
    return owner;
  }
  private static boolean text(String s,int max){return s!=null&&!s.isBlank()&&s.length()<=max&&s.chars().noneMatch(Character::isISOControl);}
}

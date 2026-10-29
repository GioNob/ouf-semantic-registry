package it.comune.trieste.ouf.semantic.api;

import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.authorization.PrincipalContext;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.time.Instant;
import java.util.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** Gateway/owner key only: MCP never receives this signing key. Discovery-only MAC domain; publication/adoption are excluded. */
@Component
public class SemanticDiscoveryDelegation {
  private final ObjectMapper json;
  private final String issuer,audience,workload;
  private final byte[] key;
  public record Receipt(int v,String purpose,String method,String path,String bodyHash,String capability,
      long iat,long exp,String issuer,String audience,String workload,String subject,String tenant,
      String acr,String roles,String scope){}
  public SemanticDiscoveryDelegation(ObjectMapper json,
      @Value("${ouf.semantic.discovery-delegation.key-file:}") String file,
      @Value("${ouf.iam.issuer:}") String issuer,@Value("${ouf.iam.audience:}") String audience,
      @Value("${ouf.semantic.discovery-delegation.workload:}") String workload) {
    this.json=json.copy().enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
      .enable(com.fasterxml.jackson.core.JsonParser.Feature.STRICT_DUPLICATE_DETECTION);
    this.issuer=issuer;this.audience=audience;this.workload=workload;
    try {
      String value=file.isBlank()?"":Files.readString(Path.of(file)).trim();
      if(!file.isBlank() && (!value.matches("[0-9a-fA-F]{64}")||issuer.isBlank()||audience.isBlank()||workload.isBlank()))
        throw new IllegalStateException("SEM_DISCOVERY_DELEGATION_CONFIG_INVALID");
      key=value.getBytes(StandardCharsets.US_ASCII);
    } catch(java.io.IOException e){throw new IllegalStateException("SEM_DISCOVERY_DELEGATION_KEY_UNAVAILABLE",e);}
  }
  public PrincipalContext verify(String proof,String path,String capability,byte[] body) {
    try {
      if(key.length!=64 || !Set.of("ouf.semantic.discovery","ouf.semantic.discovery.status","ouf.semantic.discovery.candidates").contains(capability)
          ||proof==null||proof.length()>16384||body.length>65536)throw new SecurityException();
      var parts=proof.split("\\.",-1);
      if(parts.length!=2||!parts[0].matches("[A-Za-z0-9_-]+")||!parts[1].matches("[A-Za-z0-9_-]+"))throw new SecurityException();
      var mac=Mac.getInstance("HmacSHA256");mac.init(new SecretKeySpec(key,"HmacSHA256"));
      if(!MessageDigest.isEqual(mac.doFinal(("ouf-semantic-discovery-owner-v1."+parts[0]).getBytes(StandardCharsets.US_ASCII)),
          Base64.getUrlDecoder().decode(parts[1])))throw new SecurityException();
      Receipt r=json.readValue(Base64.getUrlDecoder().decode(parts[0]),Receipt.class);
      long now=Instant.now().getEpochSecond();
      if(r.v()!=1||!"semantic-discovery-owner".equals(r.purpose())||!"POST".equals(r.method())
          ||!path.equals(r.path())||!capability.equals(r.capability())||r.iat()>now||r.exp()<=now
          ||r.exp()<=r.iat()||r.exp()-r.iat()>30||!issuer.equals(r.issuer())||!audience.equals(r.audience())
          ||!workload.equals(r.workload())||!HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)).equals(r.bodyHash())
          ||!text(r.subject(),256)||!text(r.tenant(),256)||!text(r.acr(),256)||!text(r.scope(),8192))throw new SecurityException();
      var roles=new TreeSet<String>();
      if(r.roles()!=null&&!r.roles().isEmpty())for(String role:r.roles().split(" ",-1)) {
        if(!role.matches("[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}")||!roles.add(role)||roles.size()>32)throw new SecurityException();
      }
      var scopes=new HashSet<>(Arrays.asList(r.scope().split(" +")));
      String scope="ouf.semantic.discovery";
      if(!scopes.contains(scope))throw new SecurityException();
      return new PrincipalContext(r.subject(),r.tenant(),PrincipalContext.ActorType.HUMAN,r.workload(),r.acr(),
          r.issuer(),r.audience(),scopes,new PrincipalContext.IdentityClaims(roles,r.acr(),Set.of(),null));
    }catch(Exception e){throw new SecurityException("SEM_DISCOVERY_RECEIPT_INVALID");}
  }
  private static boolean text(String s,int max){return s!=null&&!s.isBlank()&&s.length()<=max&&s.chars().noneMatch(Character::isISOControl);}
}

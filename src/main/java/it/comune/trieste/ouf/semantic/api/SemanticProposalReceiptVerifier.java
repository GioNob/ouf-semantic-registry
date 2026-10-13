package it.comune.trieste.ouf.semantic.api;

import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.authorization.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.time.*;
import java.util.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** Purpose-bound Gateway receipt. MCP never receives this key. */
@Component
public class SemanticProposalReceiptVerifier {
  private final ObjectMapper json;
  private final String issuer,audience,workload;
  private final byte[] key;
  private final Clock clock;
  public record Receipt(int v,String purpose,String method,String path,String bodyHash,String capability,
      long iat,long exp,String issuer,String audience,String workload,String subject,String tenant,String actor,
      String acr,String roles,String scope,String idempotencyKey){}
  public record Verified(TrustedPrincipal principal,String idempotencyKey,byte[] arguments){}
  @org.springframework.beans.factory.annotation.Autowired
  public SemanticProposalReceiptVerifier(ObjectMapper json,
      @Value("${ouf.semantic.proposal-receipt.key-file:}") String file,
      @Value("${ouf.semantic.proposal-receipt.issuer:}") String issuer,
      @Value("${ouf.semantic.proposal-receipt.audience:}") String audience,
      @Value("${ouf.semantic.proposal-receipt.workload:}") String workload){
    this(json,readKey(file),issuer,audience,workload,Clock.systemUTC());
  }
  SemanticProposalReceiptVerifier(ObjectMapper json,byte[] key,String issuer,String audience,String workload,Clock clock){
    this.json=json.copy().enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
        .enable(com.fasterxml.jackson.core.JsonParser.Feature.STRICT_DUPLICATE_DETECTION);
    this.key=key.clone();this.issuer=issuer;this.audience=audience;this.workload=workload;this.clock=clock;
  }
  private static byte[] readKey(String file){
    if(file.isBlank())return new byte[0];
    try{
      Path p=Path.of(file);if(!p.isAbsolute()||!p.normalize().equals(p))throw new IllegalArgumentException();
      for(Path a=p.getParent();a!=null;a=a.getParent()){
        var m=Files.readAttributes(a,"unix:uid,mode",LinkOption.NOFOLLOW_LINKS);
        if(Files.isSymbolicLink(a)||!Files.isDirectory(a,LinkOption.NOFOLLOW_LINKS)
            ||((Number)m.get("uid")).intValue()!=0||(((Number)m.get("mode")).intValue()&0022)!=0)throw new IllegalArgumentException();
      }
      var before=Files.readAttributes(p,"unix:uid,mode,nlink,size,ino,dev,lastModifiedTime,ctime",LinkOption.NOFOLLOW_LINKS);
      if(Files.isSymbolicLink(p)||!Files.isRegularFile(p,LinkOption.NOFOLLOW_LINKS)
          ||((Number)before.get("uid")).intValue()!=0||!Set.of(0400,0440,0600,0640).contains(((Number)before.get("mode")).intValue()&0777)
          ||((Number)before.get("nlink")).intValue()!=1||((Number)before.get("size")).longValue()>128)throw new IllegalArgumentException();
      byte[] raw=new byte[129];int n;
      try(var channel=Files.newByteChannel(p,Set.of(StandardOpenOption.READ,LinkOption.NOFOLLOW_LINKS))){n=channel.read(java.nio.ByteBuffer.wrap(raw));}
      if(!before.equals(Files.readAttributes(p,"unix:uid,mode,nlink,size,ino,dev,lastModifiedTime,ctime",LinkOption.NOFOLLOW_LINKS)))throw new IllegalArgumentException();
      String value=new String(raw,0,Math.max(n,0),StandardCharsets.US_ASCII).trim();
      if(!value.matches("[0-9a-fA-F]{64}"))throw new IllegalArgumentException();return value.getBytes(StandardCharsets.US_ASCII);
    }catch(Exception e){throw new IllegalStateException("SEM_PROPOSAL_KEY_CUSTODY_INVALID");}
  }
  public Verified verify(String proof,String path,byte[] raw){
    try{
      if(key.length!=64||issuer.isBlank()||audience.isBlank()||workload.isBlank()||proof==null||proof.length()>16384||raw.length>65536)throw new SecurityException();
      String[] parts=proof.split("\\.",-1);
      if(parts.length!=2||!parts[0].matches("[A-Za-z0-9_-]+")||!parts[1].matches("[A-Za-z0-9_-]+"))throw new SecurityException();
      var mac=Mac.getInstance("HmacSHA256");mac.init(new SecretKeySpec(key,"HmacSHA256"));
      if(!MessageDigest.isEqual(mac.doFinal(("ouf-semantic-proposal-owner-v1."+parts[0]).getBytes(StandardCharsets.US_ASCII)),Base64.getUrlDecoder().decode(parts[1])))throw new SecurityException();
      var r=json.readValue(Base64.getUrlDecoder().decode(parts[0]),Receipt.class);
      String cap=switch(path){case "/api/semantic/v1/proposal-commands/create"->"ouf.semantic.propose";
        case "/api/semantic/v1/proposal-commands/read"->"ouf.semantic.read";
        case "/api/semantic/v1/proposal-commands/validate"->"ouf.semantic.review.prepare";
        case "/api/semantic/v1/proposal-commands/review"->"ouf.semantic.approval.request";default->throw new SecurityException();};
      long now=clock.instant().getEpochSecond();
      if(r.v()!=1||!"semantic-proposal-owner".equals(r.purpose())||!"POST".equals(r.method())||!path.equals(r.path())||!cap.equals(r.capability())
          ||r.iat()>now||r.exp()<=now||r.exp()<=r.iat()||r.exp()-r.iat()>30||!issuer.equals(r.issuer())||!audience.equals(r.audience())
          ||!workload.equals(r.workload())||!HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(r.bodyHash())
          ||r.subject()==null||r.subject().isBlank()||r.subject().length()>256||r.tenant()==null||r.tenant().isBlank()||r.tenant().length()>256
          ||r.acr()==null||r.acr().isBlank()||!Set.of("HUMAN","AI_AGENT","SERVICE").contains(r.actor())
          ||r.idempotencyKey()==null||!r.idempotencyKey().matches("[A-Za-z0-9_:.-]{1,128}"))throw new SecurityException();
      if(r.scope()==null||r.scope().length()>8192)throw new SecurityException();
      var scopes=new HashSet<>(Arrays.asList(r.scope().split(" +")));if(!scopes.contains(cap))throw new SecurityException();
      var roles=new TreeSet<String>();if(r.roles()!=null&&!r.roles().isEmpty())for(String role:r.roles().split(" ",-1)){
        if(!role.matches("[A-Za-z0-9_:./-]{1,128}")||!roles.add(role)||roles.size()>32)throw new SecurityException();
      }
      JsonNode envelope=json.readTree(raw);JsonNode args=envelope.required("Arguments");
      if(!args.isObject()||!r.idempotencyKey().equals(envelope.required("IdempotencyKey").asText()))throw new SecurityException();
      String transportCap=path.endsWith("/read")?"ouf.semantic.proposal.read":cap;
      if(!transportCap.equals(envelope.required("CapabilityID").asText())||!"semantic".equals(envelope.required("Owner").asText())
          ||!("capability://"+transportCap).equals(envelope.required("GatewayBindingRef").asText())
          ||!(path.endsWith("/read")?"READ":"COMMAND").equals(envelope.required("OperationClass").asText()))throw new SecurityException();
      var identity=envelope.required("Identity");
      if(!r.subject().equals(identity.required("PrincipalID").asText())||!r.tenant().equals(identity.required("TenantID").asText())||!r.actor().equals(identity.required("ActorType").asText()))throw new SecurityException();
      // commandKey is the stable caller intent, not an owner DTO field.
      var copy=((com.fasterxml.jackson.databind.node.ObjectNode)args).deepCopy();
      if(!path.endsWith("/read")){if(!r.idempotencyKey().equals(copy.required("commandKey").asText()))throw new SecurityException();copy.remove("commandKey");}
      var principal=new PrincipalContext(r.subject(),r.tenant(),PrincipalContext.ActorType.valueOf(r.actor()),r.workload(),r.acr(),r.issuer(),r.audience(),scopes,
          new PrincipalContext.IdentityClaims(roles,r.acr(),Set.of(),null));
      return new Verified(new TrustedPrincipal(principal),r.idempotencyKey(),json.writeValueAsBytes(copy));
    }catch(Exception e){throw new SecurityException("SEM_PROPOSAL_RECEIPT_INVALID");}
  }
}

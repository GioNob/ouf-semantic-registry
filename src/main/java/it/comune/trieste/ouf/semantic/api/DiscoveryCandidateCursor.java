package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.ArtifactService;
import it.comune.trieste.ouf.semantic.application.DiscoveryService.CandidatePosition;
import java.nio.ByteBuffer;
import java.security.MessageDigest;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.Base64;
import java.util.UUID;

final class DiscoveryCandidateCursor {
  private static final byte VERSION=1;
  private static final int FRAME_SIZE=34;
  private static final int MAC_SIZE=32;
  static final int ENCODED_SIZE=(FRAME_SIZE+MAC_SIZE)*4/3;
  private static final Base64.Encoder ENCODER=Base64.getUrlEncoder().withoutPadding();
  private final SemanticDiscoveryDelegation delegation;

  record Options(boolean compact,boolean includeState) {}
  record Continuation(CandidatePosition position,Options options) {}

  DiscoveryCandidateCursor(SemanticDiscoveryDelegation delegation) {
    this.delegation=delegation;
  }

  String encode(Continuation cursor,byte[] binding) {
    var position=cursor.position();
    UUID id=position.candidateId();
    int flags=(cursor.options().compact()?1:0)|(cursor.options().includeState()?2:0);
    byte[] frame=ByteBuffer.allocate(FRAME_SIZE).put(VERSION).put((byte)flags)
        .putLong(position.evidenceVersion()).putLong(id.getMostSignificantBits()).putLong(id.getLeastSignificantBits())
        .putLong(position.expiresAt().toEpochMilli()).array();
    return ENCODER.encodeToString(ByteBuffer.allocate(FRAME_SIZE+MAC_SIZE)
        .put(frame).put(delegation.candidateCursorMac(binding,frame)).array());
  }

  Continuation decode(String token,byte[] binding,Instant now) {
    if(token.length()!=ENCODED_SIZE)throw invalid();
    byte[] raw;
    try {
      raw=Base64.getUrlDecoder().decode(token);
    } catch(IllegalArgumentException e){throw invalid();}
    if(raw.length!=FRAME_SIZE+MAC_SIZE || !ENCODER.encodeToString(raw).equals(token))throw invalid();
    byte[] frame=Arrays.copyOf(raw,FRAME_SIZE);
    if(!MessageDigest.isEqual(delegation.candidateCursorMac(binding,frame),Arrays.copyOfRange(raw,FRAME_SIZE,raw.length)))
      throw invalid();
    var data=ByteBuffer.wrap(frame);
    if(data.get()!=VERSION)throw invalid();
    byte flags=data.get();
    if((flags & ~3)!=0)throw invalid();
    long version=data.getLong();
    var candidate=new UUID(data.getLong(),data.getLong());
    Instant expires=Instant.ofEpochMilli(data.getLong());
    if(!expires.isAfter(now))throw new ArtifactService.Conflict("SEM_DISCOVERY_CURSOR_EXPIRED");
    return new Continuation(new CandidatePosition(version,candidate,expires),new Options((flags&1)!=0,(flags&2)!=0));
  }

  static Instant deadline(Instant now,Instant evidenceExpiresAt) {
    Instant ttl=now.plus(Duration.ofMinutes(5));
    return ttl.isBefore(evidenceExpiresAt)?ttl:evidenceExpiresAt;
  }

  private static IllegalArgumentException invalid(){
    return new IllegalArgumentException("SEM_DISCOVERY_CURSOR_INVALID");
  }
}

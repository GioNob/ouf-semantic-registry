package it.comune.trieste.ouf.semantic.api;

import jakarta.servlet.*;
import jakarta.servlet.http.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.Principal;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class SemanticProposalReceiptFilter extends OncePerRequestFilter {
  private final SemanticProposalReceiptVerifier verifier;
  public SemanticProposalReceiptFilter(SemanticProposalReceiptVerifier verifier){this.verifier=verifier;}
  @Override protected boolean shouldNotFilter(HttpServletRequest request){
    return !request.getRequestURI().startsWith("/api/semantic/v1/proposal-commands/")
        ||request.getHeader("X-OUF-Semantic-Proposal-Receipt")==null;
  }
  @Override protected void doFilterInternal(HttpServletRequest request,HttpServletResponse response,FilterChain chain)throws IOException,ServletException{
    final SemanticProposalReceiptVerifier.Verified verified;
    try{
      if(!"POST".equals(request.getMethod()))throw new SecurityException();
      byte[] body=request.getInputStream().readNBytes(65537);
      verified=verifier.verify(request.getHeader("X-OUF-Semantic-Proposal-Receipt"),request.getRequestURI(),body);
    }catch(SecurityException e){response.setStatus(403);response.setContentType("application/problem+json");response.getWriter().write("{\"code\":\"SEM_PROPOSAL_RECEIPT_INVALID\",\"status\":403}");return;}
    request.setAttribute(it.comune.trieste.ouf.authorization.ServletAuthorization.TRUSTED_PRINCIPAL,verified.principal());
    byte[] args=verified.arguments();
    chain.doFilter(new HttpServletRequestWrapper(request){
      @Override public Principal getUserPrincipal(){return verified.principal();}
      @Override public String getHeader(String name){if("Idempotency-Key".equalsIgnoreCase(name))return verified.idempotencyKey();return super.getHeader(name);}
      @Override public int getContentLength(){return args.length;}
      @Override public long getContentLengthLong(){return args.length;}
      @Override public BufferedReader getReader(){return new BufferedReader(new InputStreamReader(new ByteArrayInputStream(args),StandardCharsets.UTF_8));}
      @Override public ServletInputStream getInputStream(){
        var bytes=new ByteArrayInputStream(args);
        return new ServletInputStream(){public int read(){return bytes.read();}public boolean isFinished(){return bytes.available()==0;}public boolean isReady(){return true;}public void setReadListener(ReadListener listener){throw new UnsupportedOperationException();}};
      }
    },response);
  }
}

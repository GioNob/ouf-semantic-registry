package it.comune.trieste.ouf.semantic.application;

import java.util.concurrent.atomic.AtomicBoolean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(prefix="ouf.semantic.discovery-worker",name="enabled",havingValue="true",matchIfMissing=true)
public class DiscoveryWorker {
  private final DiscoveryService service;
  private final AtomicBoolean running=new AtomicBoolean();
  public DiscoveryWorker(DiscoveryService service){this.service=service;}
  @Scheduled(fixedDelayString="${ouf.semantic.discovery-worker.fixed-delay:2s}")
  public void poll(){if(!running.compareAndSet(false,true))return;try{while(service.executeOne()>0){}}finally{running.set(false);}}
}

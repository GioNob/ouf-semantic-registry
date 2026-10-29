package it.comune.trieste.ouf.semantic.application;

import java.util.concurrent.atomic.AtomicBoolean;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(prefix="ouf.semantic.discovery-worker",name="enabled",havingValue="true",matchIfMissing=true)
public class DiscoveryWorker {
  private final DiscoveryService service;
  private final int batchSize;
  private final AtomicBoolean running=new AtomicBoolean();
  public DiscoveryWorker(DiscoveryService service){this(service,8);}
  @Autowired
  public DiscoveryWorker(DiscoveryService service,
      @Value("${ouf.semantic.discovery-worker.batch-size:8}") int batchSize){
    if(batchSize<1 || batchSize>32)throw new IllegalArgumentException("SEM_DISCOVERY_BATCH_SIZE_INVALID");
    this.service=service;this.batchSize=batchSize;
  }
  @Scheduled(fixedDelayString="${ouf.semantic.discovery-worker.fixed-delay:2s}")
  public void poll(){
    if(!running.compareAndSet(false,true))return;
    try{
      for(int claimed=0;claimed<batchSize && !Thread.currentThread().isInterrupted();claimed++)
        if(service.executeOne()==0)break;
    }finally{running.set(false);}
  }
}

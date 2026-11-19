package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;
import it.comune.trieste.ouf.semantic.application.DiscoveryService;
import it.comune.trieste.ouf.semantic.application.DiscoveryWorker;
import java.util.concurrent.*;
import org.junit.jupiter.api.Test;

class DiscoveryWorkerBoundedTest {
  @Test void backlogYieldsAfterEightClaimsThenContinuesNextPoll(){
    var service=mock(DiscoveryService.class);when(service.executeOne()).thenReturn(1);
    var worker=new DiscoveryWorker(service);worker.poll();verify(service,times(8)).executeOne();
    worker.poll();verify(service,times(16)).executeOne();
  }
  @Test void emptyQueueDoesNotConsumeTheWholeBatch(){
    var service=mock(DiscoveryService.class);when(service.executeOne()).thenReturn(1,0);
    new DiscoveryWorker(service,4).poll();verify(service,times(2)).executeOne();
  }
  @Test void interruptedWorkerDoesNotClaimAndPreservesInterruption(){
    var service=mock(DiscoveryService.class);Thread.currentThread().interrupt();
    try{new DiscoveryWorker(service).poll();verifyNoInteractions(service);assertThat(Thread.currentThread().isInterrupted()).isTrue();}
    finally{Thread.interrupted();}
  }
  @Test void failureReleasesLocalInvocationFence(){
    var service=mock(DiscoveryService.class);when(service.executeOne()).thenThrow(new IllegalStateException("fixture")).thenReturn(0);
    var worker=new DiscoveryWorker(service);
    assertThatThrownBy(worker::poll).isInstanceOf(IllegalStateException.class);
    worker.poll();verify(service,times(2)).executeOne();
  }
  @Test void concurrentPollCannotDrainAnotherBatch()throws Exception {
    var entered=new CountDownLatch(1);var release=new CountDownLatch(1);
    var service=mock(DiscoveryService.class);
    when(service.executeOne()).thenAnswer(invocation->{entered.countDown();if(!release.await(2,TimeUnit.SECONDS))throw new AssertionError("fixture timeout");return 0;});
    var worker=new DiscoveryWorker(service);var executor=Executors.newSingleThreadExecutor();
    try{var first=executor.submit(worker::poll);assertThat(entered.await(2,TimeUnit.SECONDS)).isTrue();worker.poll();
      verify(service,times(1)).executeOne();release.countDown();first.get(2,TimeUnit.SECONDS);
    }finally{release.countDown();executor.shutdownNow();}
  }
  @Test void invalidConfiguredBatchIsRejected(){
    var service=mock(DiscoveryService.class);
    for(int bound:new int[]{0,-1,33,Integer.MAX_VALUE})assertThatThrownBy(()->new DiscoveryWorker(service,bound)).hasMessage("SEM_DISCOVERY_BATCH_SIZE_INVALID");
  }
}

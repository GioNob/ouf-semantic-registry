package it.comune.trieste.ouf.semantic;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class SemanticRegistryApplication {
  public static void main(String[] args) { SpringApplication.run(SemanticRegistryApplication.class, args); }
}

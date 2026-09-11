package it.comune.trieste.ouf.fixture;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class GatewayFixtureApplication {
  public static void main(String[] args) { SpringApplication.run(GatewayFixtureApplication.class,args); }
}

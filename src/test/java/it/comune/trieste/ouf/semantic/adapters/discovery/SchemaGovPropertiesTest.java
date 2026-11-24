package it.comune.trieste.ouf.semantic.adapters.discovery;

import static org.assertj.core.api.Assertions.*;
import java.util.List;
import java.util.stream.IntStream;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import org.springframework.boot.test.context.TestConfiguration;

class SchemaGovPropertiesTest {
  @TestConfiguration(proxyBeanMethods=false)
  @EnableConfigurationProperties(SchemaGovProperties.class)
  static class Binding {}

  private final ApplicationContextRunner context=new ApplicationContextRunner().withUserConfiguration(Binding.class);
  private static final String PROPERTY="ouf.semantic.providers.schema-gov.namespace-prefixes=";

  @Test void bindsBothDelimitersAndMatchesLiteralNonEmptySuffix(){
    context.withPropertyValues(PROPERTY+"https://a.example.test/è/,https://b.example.test/v#").run(ctx->{
      var cfg=ctx.getBean(SchemaGovProperties.class);
      assertThat(cfg.admits("https://a.example.test/è/term")).isTrue();
      assertThat(cfg.admits("https://b.example.test/v#term")).isTrue();
      assertThat(cfg.admits("https://b.example.test/v#")).isFalse();
      assertThat(cfg.admits("https://b.example.test/v/term")).isFalse();
      assertThat(cfg.admits("https://A.example.test/è/term")).isFalse();
    });
  }

  static Stream<String> invalidSettings(){
    String prefix="https://example.test/";
    return Stream.concat(Stream.of("",prefix+","+prefix,"relative/",prefix+"missing-delimiter",
        prefix+"a".repeat(2048)+"/",prefix+"%xx/",String.join(",",
            IntStream.range(0,33).mapToObj(i->prefix+i+"/").toList())),
        List.of("<",">","\"","{","}","|","\\","^","`","\u0085").stream().map(c->prefix+c+"/"));
  }

  @Test void acceptsTheInclusiveListAndIriLengthLimits(){
    String base="https://example.test/";
    String longest=base+"a".repeat(2047-base.length())+"/";
    var values=Stream.concat(Stream.of(longest),IntStream.range(1,32).mapToObj(i->base+i+"/")).toList();
    context.withPropertyValues(PROPERTY+String.join(",",values)).run(ctx->
        assertThat(ctx.getBean(SchemaGovProperties.class).namespacePrefixes()).containsExactlyElementsOf(values));
  }

  @ParameterizedTest @MethodSource("invalidSettings")
  void rejectsInvalidConfigurationAtStartup(String setting){
    context.withPropertyValues(PROPERTY+setting).run(ctx->assertThat(ctx).hasFailed());
  }
}

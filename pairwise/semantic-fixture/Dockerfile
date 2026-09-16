FROM maven:3.9.11-eclipse-temurin-21 AS build
WORKDIR /build
COPY pom.xml ./
COPY src ./src
COPY contracts ./contracts
RUN timeout --signal=TERM --kill-after=30s 15m mvn -B -ntp test-compile org.apache.maven.plugins:maven-dependency-plugin:3.8.1:copy-dependencies -DincludeScope=test -DoutputDirectory=target/dependencies
FROM eclipse-temurin:21-jre
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin ouf
WORKDIR /app
COPY --from=build /build/target/classes /app/classes
COPY --from=build /build/target/test-classes /app/test-classes
COPY --from=build /build/target/dependencies /app/lib
USER 10001:10001
ENTRYPOINT ["java","-XX:MaxRAMPercentage=75","-cp","/app/classes:/app/test-classes:/app/lib/*","it.comune.trieste.ouf.pairwise.AuthenticatedSemanticFixture"]

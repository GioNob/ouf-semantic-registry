FROM maven:3.9.11-eclipse-temurin-21 AS build
WORKDIR /workspace
COPY pom.xml .
COPY src src
RUN mvn -B -ntp clean package -DskipTests
FROM eclipse-temurin:21-jre
RUN useradd --system --uid 10002 --no-create-home fixture
WORKDIR /app
COPY --from=build /workspace/target/semantic-provider-gateway-fixture-1.0.0.jar app.jar
USER 10002:10002
ENTRYPOINT ["java","-jar","/app/app.jar"]

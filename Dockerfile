FROM maven:3.9.11-eclipse-temurin-21 AS build
WORKDIR /build
ENV MAVEN_OPTS="-Dmaven.wagon.http.connectionTimeout=10000 -Dmaven.wagon.http.readTimeout=30000 -Djava.net.preferIPv4Stack=true"
COPY pom.xml ./
RUN timeout --signal=TERM --kill-after=30s 10m mvn -B -ntp -DskipTests dependency:go-offline
COPY src ./src
COPY contracts ./contracts
RUN timeout --signal=TERM --kill-after=30s 15m mvn -B -ntp -DskipTests package

FROM eclipse-temurin:21-jre
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin ouf
WORKDIR /app
COPY --from=build /build/target/semantic-registry-*.jar /app/application.jar
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["java","-XX:MaxRAMPercentage=75","-jar","/app/application.jar"]

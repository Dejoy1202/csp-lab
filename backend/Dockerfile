ARG MAVEN_IMAGE=maven:3.9.11-eclipse-temurin-21
ARG JAVA_IMAGE=eclipse-temurin:21-jre-jammy
FROM ${MAVEN_IMAGE} AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN --mount=type=cache,target=/root/.m2 mvn -B -q verify
FROM ${JAVA_IMAGE}
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/* && useradd -r -u 10001 app
WORKDIR /app
COPY --from=build /app/target/csp-lab-backend-0.1.0.jar app.jar
USER 10001
EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=65", "-jar", "/app/app.jar"]

FROM maven:3.9.9-eclipse-temurin-17 AS build
WORKDIR /build
COPY pom.xml .
COPY src ./src
RUN mvn -B clean verify

FROM eclipse-temurin:17-jre-jammy
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
WORKDIR /app
COPY --from=build /build/target/convertflow.jar /app/convertflow.jar
USER 10001:10001
ENV APP_PORT=8080
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/convertflow.jar"]

FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /src
COPY pom.xml .
COPY src ./src
RUN mvn -B package
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /src/target/ordermesh-1.0.0.jar app.jar
EXPOSE 8080
USER 10001
ENTRYPOINT ["java", "-jar", "app.jar"]

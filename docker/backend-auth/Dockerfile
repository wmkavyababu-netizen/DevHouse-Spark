# Multi-stage Dockerfile for TARANG Spring Boot Auth Service
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /build

# Copy pom.xml and download dependencies
COPY backend-auth/pom.xml .
RUN mvn dependency:go-offline -B || true

# Copy source code and package application
COPY backend-auth/src ./src
RUN mvn clean package -DskipTests

# Runtime stage
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# Non-root user for security
RUN addgroup -S tarang && adduser -S tarang -G tarang
USER tarang

COPY --from=builder /build/target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-Djava.security.egd=file:/dev/./urandom", "-jar", "app.jar"]

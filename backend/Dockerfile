# Use official OpenJDK image as the base image
FROM eclipse-temurin:17-jdk-alpine

# Set working directory
WORKDIR /app

# Copy maven executable and project files
COPY mvnw .
COPY .mvn .mvn
COPY pom.xml .
COPY src src

# Add a volume pointing to /tmp for temporary files
VOLUME /tmp

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Create directories for logs
RUN mkdir -p logs/archived

# Set environment variables
ENV JAVA_OPTS=""
ENV OPENAI_API_KEY=""

# Run the application
ENTRYPOINT ["sh", "-c", "java ${JAVA_OPTS} -jar /app/target/tax-law-assistant-1.0.0-SNAPSHOT.jar"]

# Build stage (uncomment if you want to build inside Docker)
# RUN ./mvnw clean package -DskipTests

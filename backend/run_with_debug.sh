#!/bin/bash
# Run the Spring Boot application with debug output
# Make this script executable with: chmod +x run_with_debug.sh

# Set OpenAI API key if not already set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "OpenAI API key not set. Please set it first with:"
    echo "export OPENAI_API_KEY=your_api_key_here"
    exit 1
fi

# Run with debug flags
./mvnw spring-boot:run -Dmaven.pomFile=pom.xml -Dspring-boot.run.arguments="--logging.level.com.ai.taxlaw=DEBUG --debug"

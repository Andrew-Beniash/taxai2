# Tax Law Assistant - Backend API

This is the Spring Boot backend for the AI-Powered Tax Law Assistant. It provides a REST API for processing tax-related queries using a Retrieval-Augmented Generation (RAG) system with OpenAI integration.

## Features

- REST API for handling tax law queries
- Integration with OpenAI for generating responses
- RAG system integration for fact-based, citation-backed answers
- Structured logging for monitoring query patterns and performance
- Docker support for easy deployment

## Getting Started

### Prerequisites

- Java 17 or higher
- Maven 3.6 or higher
- Docker (optional, for containerized deployment)
- OpenAI API key

### Environment Setup

1. Clone the repository
2. Set up the OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_openai_api_key
   ```

### Building and Running

#### Using the Run Script

```bash
# On macOS/Linux
chmod +x run.sh
./run.sh

# On Windows
run.bat
```

#### Using Maven Directly

```bash
cd backend
mvn clean package
java -jar target/tax-law-assistant-1.0.0-SNAPSHOT.jar
```

#### Using Docker

```bash
docker-compose up -d
```

## API Endpoints

### Query Tax Law Information

```
POST /api/query
```

Request body:
```json
{
  "query": "What are the tax deductions for home office?",
  "context": "Optional additional context"
}
```

Response:
```json
{
  "answer": "Based on IRS Publication 17 and relevant tax code sections...",
  "citations": [
    {
      "source": "IRS",
      "title": "Publication 17: Your Federal Income Tax",
      "excerpt": "For use in preparing 2023 Returns",
      "url": "https://www.irs.gov/pub/irs-pdf/p17.pdf",
      "referenceId": "pub17_2023"
    }
  ],
  "processingTimeMs": 1250
}
```

### Health Check

```
GET /api/health
```

### Status

```
GET /api/status
```

## Configuration

Configuration options are available in `src/main/resources/application.properties`:

- `server.port`: The port the API runs on (default: 8080)
- `openai.api.key`: The OpenAI API key (set via environment variable)
- `openai.model`: The OpenAI model to use (default: gpt-4o)
- `rag.api.url`: The URL of the RAG system API (default: http://localhost:5000)

## Security Notes

- The OpenAI API key should be kept secure and never committed to version control.
- In production, use a proper secrets management system.
- Always set the API key via environment variables or secure configuration.

## Running Tests

```bash
mvn test
```

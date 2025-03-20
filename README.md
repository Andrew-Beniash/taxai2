# AI-Powered Tax Law Assistant

A browser extension for tax-related queries with an autonomous AI agent to maintain a Retrieval-Augmented Generation (RAG) database.

## Project Overview

This system allows users to receive fact-based, citation-backed responses by referencing IRS tax codes, case laws, and firm-specific policies through:

1. A browser extension for easy access
2. An autonomous AI agent for RAG database updates
3. A high-performance RAG core engine

## Setup Instructions

### Prerequisites

- JDK 17+ (for Backend API)
- C++ compiler (for RAG Engine)
- Node.js 16+ (for Browser Extension)
- Python 3.8+ (for AI Agent)
- Docker and Docker Compose

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd taxai
```

2. Set up the development environment using Docker:
```bash
docker-compose up
```

This will start all the required services:
- Backend API (Java/Spring Boot)
- RAG Engine (C++)
- AI Agent (Python)

### Development Setup

For local development outside Docker:

#### Backend API (Java/Spring Boot)
```bash
cd backend
./mvnw spring-boot:run
```

#### RAG Engine (C++)
```bash
cd rag-engine
mkdir build && cd build
cmake ..
make
./rag-engine-service
```

#### AI Agent (Python)
```bash
cd ai-agent
pip install -r requirements.txt
python src/main.py
```

#### Browser Extension (JavaScript)
```bash
cd browser-extension
npm install
npm run build
```
Then load the extension from the `dist` directory in Chrome/Edge/Firefox.

### Testing

Run the test suite:
```bash
./run-tests.sh
```

## Project Structure

- `browser-extension/` - Chrome extension UI
- `backend/` - Java/Spring Boot API
- `rag-engine/` - C++ RAG implementation
- `ai-agent/` - Python autonomous agent
- `database/` - SQLite/DuckDB schemas
- `docker/` - Docker configurations
- `tests/` - Unit and integration tests

## API Documentation

See [API_Documentation.md](./API_Documentation.md) for details on available endpoints.

## License

[License details]
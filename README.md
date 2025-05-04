# AI-Powered Tax Law Assistant

An AI-powered browser extension and autonomous agent system for tax law assistance, leveraging RAG technology.

## Project Structure

- `backend/`: Spring Boot backend API
- `browser-extension/`: Chrome extension for the UI
- `rag-engine/`: RAG (Retrieval Augmented Generation) engine using FAISS and ONNX
- `ai-agent/`: Autonomous agent for monitoring tax law changes
- `database/`: Database schemas and migrations
- `tests/`: Test suites for all components
- `docs/`: Project documentation

## Getting Started

### Prerequisites

- JDK 17 or higher
- Python 3.8 or higher
- Node.js 14 or higher
- C++ compiler (for RAG Engine)
- Docker and Docker Compose

### Environment Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd taxai
   ```

2. Set up your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

3. Build and run the backend:
   ```bash
   cd backend
   ./mvnw spring-boot:run
   ```

4. Build and load the browser extension:
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `browser-extension` directory

## Testing OpenAI Integration

To verify that the OpenAI integration is working:

```bash
# Make the test scripts executable
chmod +x test-openai.sh run-openai-test.sh

# Run the shell test script
./test-openai.sh

# Or run the Java test utility
./run-openai-test.sh
```

See [OpenAI Integration Testing](docs/OPENAI_INTEGRATION_TESTING.md) for more details.

## Development

This project follows a modular architecture with the following components:

1. **Browser Extension**: Provides the UI for users to query the AI
2. **Backend API**: Handles requests and orchestrates the AI response generation
3. **RAG Engine**: Performs efficient retrieval from the tax law knowledge base
4. **AI Agent**: Monitors and updates the knowledge base with new tax laws

Follow the [Development Plan](docs/development-plan.md) for detailed implementation steps.

## License

[License information]

## Contributors

[Contributor information]

# Developer Notes - AI-Powered Tax Law Assistant

## Overview

This document contains important technical insights, best practices, and implementation guidance for developers working on the AI-Powered Tax Law Assistant project. These notes cover key architectural decisions, performance optimizations, and development workflows.

## Architecture Decisions

### 1. Local-First Development Strategy

We've adopted a local-first development approach for several reasons:

- **Rapid Iteration**: Enables developers to test changes instantly without cloud deployment delays
- **Cost Efficiency**: Minimizes cloud computing costs during development phases
- **Privacy**: Allows working with sensitive tax data locally without cloud transmission
- **Performance Testing**: Better control over hardware variables for accurate benchmarking

```
browser-extension → REST API → RAG Engine → Vector DB
                                ↓
                        Autonomous AI Agent
```

This approach allows seamless transition to cloud deployment later while optimizing developer experience now.

### 2. C++ for Performance-Critical Components

Our decision to implement the RAG engine core in C++ was driven by:

- **Vector Search Performance**: FAISS with C++ offers 10-20x faster vector search than Python equivalents
- **Memory Efficiency**: Better control over memory allocation for large embedding datasets
- **ONNX Runtime**: C++ implementation of ONNX Runtime has lower latency than Python
- **Portability**: Can be compiled for various platforms without Python dependency

When working with the C++ components, always use the CMake build system rather than direct compilation to ensure consistent builds across environments.

### 3. Browser Extension Architecture

The browser extension follows a modular architecture:

- **Background Script**: Long-running process for API communication
- **Content Scripts**: Inject functionality into web pages (highlighting, context menu)
- **Popup UI**: React-based interface for user interactions
- **Storage Manager**: Handles IndexedDB for local memo storage

This separation of concerns allows different team members to work on various extension components simultaneously without conflicts.

## Performance Optimizations

### 1. FAISS Vector Index Configuration

Our FAISS implementation uses Hierarchical Navigable Small World (HNSW) indexing with the following configuration:

```cpp
// Recommended configuration for ~100K tax documents
faiss::IndexHNSWFlat index(vector_dim, 32); // 32 is M parameter (connections per node)
index.hnsw.efConstruction = 40;  // Controls index quality (higher = better but slower)
index.hnsw.efSearch = 16;        // Controls search quality (higher = better but slower)
```

These settings balance retrieval accuracy with performance. Don't set `efSearch` too high (>64) in the initial implementation as it will significantly impact query latency. For the prototype phase, we're optimizing for sub-100ms vector search time.

### 2. Embedded Document Chunking Strategy

Tax documents are chunked following these guidelines:

- **Chunk Size**: 512 tokens per chunk with 128 token overlap
- **Semantic Boundaries**: Chunks respect section and paragraph boundaries
- **Metadata Preservation**: Each chunk maintains its source document and position
- **Citation Information**: Section numbers, publication IDs, and page numbers are stored as metadata

This strategy ensures that retrieved chunks contain enough context for accurate answers while maintaining traceability to source documents.

### 3. Browser Extension Optimizations

To ensure a responsive UI experience:

- **Lazy Loading**: Components are loaded only when needed
- **Debounced Queries**: Text highlighting queries are debounced (300ms delay)
- **IndexedDB Pagination**: Memo lists are paginated (20 items per page)
- **Web Worker Processing**: Heavy text processing happens in a separate thread

## Code Style and Best Practices

### 1. Java Coding Standards

For Java components (Backend API, AI Agent):

- Follow Google Java Style Guide
- Use constructor dependency injection rather than field injection
- Prefer immutable objects when possible
- Use Optional<T> for nullable return values rather than null
- Implement proper exception handling with custom exceptions

Example pattern for service implementation:

```java
@Service
public class TaxQueryServiceImpl implements TaxQueryService {
    private final RAGClient ragClient;
    private final QueryValidator validator;
    
    // Constructor injection
    @Autowired
    public TaxQueryServiceImpl(RAGClient ragClient, QueryValidator validator) {
        this.ragClient = ragClient;
        this.validator = validator;
    }
    
    @Override
    public QueryResponse processQuery(QueryRequest request) {
        // Validate
        validator.validate(request);
        
        // Process
        RAGResponse ragResponse = ragClient.query(request.getQuery());
        
        // Transform
        return mapToQueryResponse(ragResponse);
    }
    
    private QueryResponse mapToQueryResponse(RAGResponse ragResponse) {
        // Mapping logic
    }
}
```

### 2. C++ Best Practices

For C++ components (RAG Engine, Vector Store):

- Follow Google C++ Style Guide
- Use smart pointers (std::unique_ptr, std::shared_ptr) instead of raw pointers
- Implement RAII (Resource Acquisition Is Initialization) pattern
- Use namespaces to organize code
- Prefer modern C++ features (auto, range-based for loops, lambda expressions)

Example pattern for error handling:

```cpp
class VectorStoreException : public std::runtime_error {
public:
    explicit VectorStoreException(const std::string& message)
        : std::runtime_error(message) {}
};

std::vector<int> VectorStore::search(const std::vector<float>& query_vector, int k) {
    try {
        // Validate input
        if (query_vector.size() != dimension_) {
            throw VectorStoreException("Query vector dimension mismatch");
        }
        
        // Perform search
        std::vector<float> distances(k);
        std::vector<int> indices(k);
        index_->search(1, query_vector.data(), k, distances.data(), indices.data());
        
        return indices;
    } catch (const faiss::FaissException& e) {
        throw VectorStoreException(std::string("FAISS error: ") + e.what());
    } catch (const std::exception& e) {
        throw VectorStoreException(std::string("Unexpected error: ") + e.what());
    }
}
```

### 3. JavaScript Best Practices

For browser extension components:

- Use ESLint with Airbnb config
- Implement modern ES6+ features but maintain browser compatibility
- Use React hooks rather than class components
- Implement state management with React Context API
- Use TypeScript for type safety

Example pattern for API calls:

```javascript
// apiService.js
const API_BASE_URL = 'http://localhost:8080/api';

export const queryTaxInfo = async (query) => {
  try {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error?.message || 'Unknown error');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};
```

## Development Workflow

### 1. Local Development Setup

Set up the complete development environment with Docker Compose:

```bash
# Clone the repository
git clone https://github.com/your-org/ai-tax-law-assistant.git

# Navigate to project directory
cd ai-tax-law-assistant

# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps
```

The services will be available at:
- Backend API: http://localhost:8080
- RAG Engine: http://localhost:5000
- AI Agent (monitoring UI): http://localhost:5001

### 2. Development Workflow

Follow this workflow for making changes:

1. Create a feature branch from `develop`
2. Make your changes with appropriate tests
3. Run local tests with `./run_tests.sh`
4. Submit a pull request to `develop`
5. Address code review feedback
6. Once approved, merge to `develop`

For major features, create a new feature branch from develop with the naming convention: `feature/short-description`.

### 3. Testing Strategy

Our testing pyramid:

- **Unit Tests**: Test individual classes and methods
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: Test complete user flows

Aim for the following coverage:
- Backend API: 90%+ unit test coverage
- RAG Engine: 80%+ unit test coverage
- Browser Extension: 70%+ component test coverage

Test automation runs on every pull request using GitHub Actions.

## Security Considerations

While security is not a primary focus for the prototype, keep these principles in mind:

1. **Input Validation**: Sanitize all user inputs, especially queries passed to the AI
2. **Error Handling**: Don't expose sensitive information in error messages
3. **Local Storage**: Encrypt sensitive data stored in IndexedDB
4. **API Design**: Prepare for future authentication/authorization implementation

## Performance Benchmarks

Target performance metrics for the prototype:

- API Query Response Time: < 2 seconds
- Vector Search Latency: < 100ms
- Browser Extension UI Responsiveness: < 100ms for interactions
- Document Processing Time: < 5 seconds per page

Use the benchmark scripts in the `tests/benchmarks` directory to measure performance during development.

## Common Issues and Solutions

### 1. FAISS Memory Issues

If you encounter memory issues with FAISS:

```cpp
// Reduce memory usage with memory flag
faiss::IndexHNSWFlat index(vector_dim, 32);
index.hnsw.efConstruction = 24;  // Reduced from 40
index.hnsw.efSearch = 8;         // Reduced from 16
```

### 2. Browser Extension Hot Reloading

For faster extension development, use the extension reloader:

```bash
# From the browser-extension directory
npm run watch
```

Then install the Extension Reloader plugin for your browser and click it after making changes.

### 3. Java Spring Boot Memory Configuration

If the Spring Boot application is using too much memory:

```
# Add to application.properties
spring.jvm.memory=-Xmx512m -XX:MaxMetaspaceSize=128m
```

## Future Improvements

Areas for future enhancement after the prototype phase:

1. **Cloud Deployment**: Migrate to containerized cloud infrastructure
2. **Authentication**: Implement OAuth2 or API key authentication
3. **Multi-User Support**: Add user accounts and personalization
4. **Performance Optimization**: Further optimize RAG pipeline for sub-second responses
5. **UI/UX Enhancements**: Improve browser extension interface based on user feedback

## Architecture Decision Records

For significant architecture decisions, create an ADR (Architecture Decision Record) in the `docs/adrs` directory following this template:

```markdown
# ADR-001: Use FAISS for Vector Storage

## Status
Accepted

## Context
We need an efficient vector database for embedding storage and similarity search.

## Decision
We will use FAISS (Facebook AI Similarity Search) for our vector storage needs.

## Rationale
- High-performance C++ implementation
- Support for multiple index types (flat, HNSW, IVF)
- Active maintenance and community support
- Easy integration with our C++ backend

## Consequences
- Requires C++ expertise for customization
- Higher development complexity than Python alternatives
- Better performance characteristics for production
```

---

Remember to update these developer notes as the project evolves. Last updated: March 20, 2025.

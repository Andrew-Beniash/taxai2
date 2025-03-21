# AI Model Integration

This document explains the implementation of the AI Model Integration component for the Tax Law Assistant. This component connects the RAG system with OpenAI models to provide accurate, context-aware tax law responses with proper citations.

## Components Overview

The AI Model Integration consists of three main components:

1. **AIModelService.java** - Orchestrates the integration between RAG and OpenAI
2. **ResponseFormatter.java** - Ensures responses are properly formatted with inline citations
3. **CitationManager.java** - Validates and manages citation accuracy and relevance

## How It Works

### 1. Context-Aware Retrieval Process

1. The user submits a tax law query through the browser extension
2. The query is processed by the backend API
3. The AIModelService retrieves relevant tax law documents from the RAG system
4. The retrieved documents are formatted as context for the OpenAI model
5. The OpenAI model generates a response based on the user query and the context
6. The response is processed to ensure proper citation formatting
7. Citations are validated and enhanced for context-awareness
8. The final response is returned to the user with inline citations

```
┌────────────┐     ┌────────────┐     ┌────────────┐
│   User     │────▶│  Backend   │────▶│    RAG     │
│   Query    │     │    API     │     │  System    │
└────────────┘     └────────────┘     └────────────┘
                         │                  │
                         │                  ▼
                         │            ┌────────────┐
                         │            │ Retrieved  │
                         │            │ Documents  │
                         │            └────────────┘
                         │                  │
                         ▼                  ▼
                   ┌────────────┐     ┌────────────┐
                   │  OpenAI    │◀────│  Context   │
                   │   Model    │     │ Preparation│
                   └────────────┘     └────────────┘
                         │
                         ▼
                   ┌────────────┐     ┌────────────┐
                   │ Response   │────▶│  Citation  │
                   │ Formatting │     │ Validation │
                   └────────────┘     └────────────┘
                                           │
                                           ▼
                                     ┌────────────┐
                                     │   Final    │
                                     │  Response  │
                                     └────────────┘
```

### 2. Citation Formatting

Citations are formatted in two ways:

1. **Inline Citations**: Citations appear as superscript references in the response text, e.g., `[¹]`
2. **Citation Footnotes**: A list of sources appears at the end of the response with links to the original documents

Example:
```
According to the Internal Revenue Code [<sup>usc_26_61</sup>], gross income includes all income from whatever source derived.

<hr>
<strong>Sources:</strong>
<ul>
<li><strong>usc_26_61:</strong> US Tax Code, 26 U.S. Code § 61 - Gross income defined [<a href="https://www.law.cornell.edu/uscode/text/26/61" target="_blank">Link</a>]</li>
</ul>
```

### 3. Context-Aware Citations

The CitationManager ensures that citations are:

- **Accurate**: Only referencing documents that actually support the statement
- **Relevant**: Connected to the specific tax law concept being discussed
- **Complete**: Covering all factual claims in the response

## Configuration

The AI Model integration can be configured through the `application.properties` file:

```properties
# OpenAI Configuration
openai.api.key=your-api-key
openai.api.url=https://api.openai.com/v1/chat/completions
openai.model=gpt-4

# RAG Configuration
rag.api.url=http://localhost:5000
```

## Usage Example

```java
// Inject the AIModelService
@Autowired
private AIModelService aiModelService;

// Generate a response with context-aware citations
String query = "What income must I report on my tax return?";
String response = aiModelService.generateResponse(query);
```

## Testing

The AI Model Integration includes comprehensive unit tests to ensure:

1. Proper integration between RAG and OpenAI
2. Accurate citation formatting and validation
3. Graceful error handling

To run the tests:
```bash
cd backend
./mvnw test -Dtest=AIModelServiceTest
```

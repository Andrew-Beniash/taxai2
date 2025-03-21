# AI-Powered Tax Law Assistant API Documentation

## Overview

This document provides comprehensive information about the REST APIs available in the AI-Powered Tax Law Assistant application. The API serves as the communication layer between the browser extension and the RAG (Retrieval-Augmented Generation) system, allowing users to query tax-related information with fact-based, citation-backed responses.

## Base URL

For local development:
```
http://localhost:8080/api
```

## Authentication

Currently, the API does not require authentication for local development. When moving to production, implement an API key or OAuth2 authentication mechanism.

## API Endpoints

### 1. Query Tax Information

Retrieves AI-generated answers to tax-related queries with citations from authoritative sources.

**Endpoint:** `POST /query`

**Request Body:**
```json
{
  "query": "What are the current rules for home office deduction?",
  "contextUrl": "https://www.irs.gov/businesses/small-businesses-self-employed/home-office-deduction" // Optional
}
```

**Parameters:**
- `query` (Required): The tax-related question from the user
- `contextUrl` (Optional): URL of the page where the query was made, providing context

**Response:**
```json
{
  "answer": "For the home office deduction, you must use a portion of your home exclusively and regularly for business. You can calculate the deduction using either the simplified method ($5 per square foot, up to 300 square feet) or the regular method (based on the percentage of home used for business).",
  "citations": [
    {
      "source": "IRS Publication 587",
      "text": "To qualify to deduct expenses for business use of your home, you must use part of your home exclusively and regularly for business.",
      "url": "https://www.irs.gov/publications/p587"
    }
  ],
  "relatedQueries": [
    "What is the simplified method for home office deduction?",
    "How to calculate home office percentage?"
  ]
}
```

**Status Codes:**
- `200 OK`: Query processed successfully
- `400 Bad Request`: Invalid query format
- `500 Internal Server Error`: Server error processing the request

### 2. Save Quick Memo

Saves a user-created memo based on an AI response for future reference.

**Endpoint:** `POST /memos`

**Request Body:**
```json
{
  "title": "Home Office Deduction Rules",
  "content": "Must use space exclusively and regularly for business. Two calculation methods available: simplified ($5 per sq ft, max 300 sq ft) or regular (percentage based).",
  "tags": ["deduction", "home office"],
  "sourceQuery": "What are the current rules for home office deduction?"
}
```

**Response:**
```json
{
  "id": "memo-12345",
  "title": "Home Office Deduction Rules",
  "created": "2025-03-20T14:30:00Z",
  "status": "saved"
}
```

**Status Codes:**
- `201 Created`: Memo saved successfully
- `400 Bad Request`: Invalid memo format
- `500 Internal Server Error`: Server error saving the memo

### 3. Get Recent IRS Updates

Retrieves the latest updates to tax laws and regulations monitored by the autonomous AI agent.

**Endpoint:** `GET /updates`

**Parameters:**
- `limit` (Optional): Number of updates to return (default: 10)
- `since` (Optional): Only show updates after this date (format: YYYY-MM-DD)

**Response:**
```json
{
  "updates": [
    {
      "title": "New Guidance on Section 179 Deductions",
      "summary": "The IRS has provided updated guidance on Section 179 property deductions for tax year 2025",
      "publicationDate": "2025-02-15",
      "source": "IRS Revenue Procedure 2025-12",
      "url": "https://www.irs.gov/pub/irs-drop/rp-25-12.pdf"
    }
  ],
  "totalUpdates": 1
}
```

**Status Codes:**
- `200 OK`: Updates retrieved successfully
- `404 Not Found`: No updates available
- `500 Internal Server Error`: Server error retrieving updates

## Error Handling

All API endpoints return error responses in the following format:

```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "The provided query is empty or invalid",
    "details": "Queries must contain at least 10 characters and be related to tax matters"
  }
}
```

Common error codes:
- `INVALID_INPUT`: Invalid request parameters
- `PROCESSING_ERROR`: Error processing the request
- `NOT_FOUND`: Requested resource not found
- `RATE_LIMIT_EXCEEDED`: Too many requests

## Versioning

The API version is included in the response headers:

```
X-API-Version: 1.0.0
```

## Rate Limiting

To prevent abuse, the API implements rate limiting:
- 30 requests per minute per IP address
- 500 requests per day per IP address

Rate limit headers:
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 29
X-RateLimit-Reset: 1616973392
```

## Usage Examples

### Example 1: Query for Tax Information with cURL

```bash
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What documentation do I need for charitable donations?"}'
```

### Example 2: Save a Memo with cURL

```bash
curl -X POST http://localhost:8080/api/memos \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Charitable Donation Documentation",
    "content": "For donations under $250: bank record, receipt, or other reliable written record. For donations $250+: written acknowledgment from charity required.",
    "tags": ["charity", "donation", "documentation"]
  }'
```

### Example 3: Retrieve Recent Updates with cURL

```bash
curl -X GET "http://localhost:8080/api/updates?limit=5&since=2025-01-01"
```

## C++ Client Example

```cpp
#include <cpr/cpr.h>
#include <nlohmann/json.hpp>
#include <iostream>

using json = nlohmann::json;

std::string queryTaxAssistant(const std::string& query) {
    json requestBody;
    requestBody["query"] = query;
    
    auto response = cpr::Post(
        cpr::Url{"http://localhost:8080/api/query"},
        cpr::Header{{"Content-Type", "application/json"}},
        cpr::Body{requestBody.dump()}
    );
    
    if (response.status_code == 200) {
        json responseJson = json::parse(response.text);
        return responseJson["answer"].get<std::string>();
    } else {
        return "Error: " + std::to_string(response.status_code);
    }
}

int main() {
    std::string query = "What are the current rules for home office deduction?";
    std::string result = queryTaxAssistant(query);
    std::cout << result << std::endl;
    return 0;
}
```

## Java Client Example

```java
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.web.client.RestTemplate;

public class TaxApiClient {
    private final String baseUrl = "http://localhost:8080/api";
    private final RestTemplate restTemplate = new RestTemplate();
    
    public String queryTaxInfo(String query) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        String requestJson = String.format("{\"query\": \"%s\"}", query);
        HttpEntity<String> request = new HttpEntity<>(requestJson, headers);
        
        String url = baseUrl + "/query";
        ResponseEntity<String> response = restTemplate.postForEntity(url, request, String.class);
        
        // Process response
        return response.getBody();
    }
}
```

## JavaScript Client Example

```javascript
async function queryTaxAssistant(query) {
    try {
        const response = await fetch('http://localhost:8080/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.answer;
    } catch (error) {
        console.error('Error querying tax assistant:', error);
        return null;
    }
}

// Usage example
queryTaxAssistant('What documentation do I need for charitable donations?')
    .then(answer => console.log(answer))
    .catch(error => console.error(error));
```

## API Changes and Deprecation Policy

- APIs are versioned using semantic versioning (MAJOR.MINOR.PATCH)
- Backward-compatible changes increment MINOR version
- Breaking changes increment MAJOR version
- Deprecated endpoints remain available for at least 6 months
- Deprecation notices are provided in response headers using `X-API-Deprecated` header

## Support and Contact

For API support or issues, please contact the development team through:
- GitHub Issues: [AI Tax Law Assistant Repository](https://github.com/your-org/ai-tax-law-assistant)
- Email: api-support@yourdomain.com

---

This documentation is subject to change as the application evolves. Last updated: March 20, 2025.

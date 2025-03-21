package com.ai.taxlaw.tests;

import com.ai.taxlaw.model.QueryRequest;
import com.ai.taxlaw.model.QueryResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;

import java.util.Map;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

/**
 * API Tests for the Tax Law Assistant REST API.
 * These tests focus on the functionality of the API endpoints,
 * verifying proper handling of requests and responses.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
public class ApiTest {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    private String baseUrl;

    @BeforeEach
    public void setUp() {
        baseUrl = "http://localhost:" + port + "/api";
    }

    /**
     * Test that the health endpoint returns the correct status.
     */
    @Test
    public void testHealthEndpoint() {
        ResponseEntity<String> response = restTemplate.getForEntity(
                baseUrl + "/health", String.class);
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals("Tax Law AI API is running", response.getBody());
    }

    /**
     * Test that the status endpoint returns the expected data structure.
     */
    @Test
    public void testStatusEndpoint() {
        ResponseEntity<Map> response = restTemplate.getForEntity(
                baseUrl + "/status", Map.class);
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        
        Map<String, Object> statusData = response.getBody();
        assertNotNull(statusData);
        assertEquals("online", statusData.get("status"));
        assertNotNull(statusData.get("version"));
        assertNotNull(statusData.get("timestamp"));
    }

    /**
     * Test sending a valid query and receiving a proper response.
     */
    @Test
    @Timeout(value = 10, unit = TimeUnit.SECONDS)
    public void testValidQuery() {
        QueryRequest request = new QueryRequest();
        request.setQuery("What is the standard deduction for 2024?");
        
        ResponseEntity<QueryResponse> response = restTemplate.postForEntity(
                baseUrl + "/query", request, QueryResponse.class);
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        
        QueryResponse queryResponse = response.getBody();
        assertNotNull(queryResponse);
        assertNotNull(queryResponse.getAnswer());
        assertFalse(queryResponse.getAnswer().isEmpty());
        assertTrue(queryResponse.getProcessingTimeMs() > 0);
    }

    /**
     * Test sending an empty query and verifying proper error handling.
     */
    @Test
    public void testEmptyQuery() {
        QueryRequest request = new QueryRequest();
        request.setQuery("");
        
        ResponseEntity<QueryResponse> response = restTemplate.postForEntity(
                baseUrl + "/query", request, QueryResponse.class);
        
        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
    }

    /**
     * Test sending a query with context and verifying it's properly processed.
     */
    @Test
    @Timeout(value = 10, unit = TimeUnit.SECONDS)
    public void testQueryWithContext() {
        QueryRequest request = new QueryRequest();
        request.setQuery("What deductions am I eligible for?");
        request.setContext("I am self-employed with a home office and made $120,000 last year.");
        
        ResponseEntity<QueryResponse> response = restTemplate.postForEntity(
                baseUrl + "/query", request, QueryResponse.class);
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        
        QueryResponse queryResponse = response.getBody();
        assertNotNull(queryResponse);
        assertNotNull(queryResponse.getAnswer());
        assertFalse(queryResponse.getAnswer().isEmpty());
        
        // The answer should contain relevant information based on the context
        String answer = queryResponse.getAnswer().toLowerCase();
        assertTrue(answer.contains("self-employed") || answer.contains("home office") || 
                   answer.contains("deduction"));
    }

    /**
     * Test that the response includes relevant citations.
     */
    @Test
    @Timeout(value = 10, unit = TimeUnit.SECONDS)
    public void testQueryResponseHasCitations() {
        QueryRequest request = new QueryRequest();
        request.setQuery("What is the tax rate for capital gains in 2024?");
        
        ResponseEntity<QueryResponse> response = restTemplate.postForEntity(
                baseUrl + "/query", request, QueryResponse.class);
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        
        QueryResponse queryResponse = response.getBody();
        assertNotNull(queryResponse);
        assertNotNull(queryResponse.getCitations());
        assertFalse(queryResponse.getCitations().isEmpty());
        
        // Check that at least one citation has required fields
        queryResponse.getCitations().stream().findFirst().ifPresent(citation -> {
            assertNotNull(citation.getSource());
            assertNotNull(citation.getTitle());
            assertFalse(citation.getSource().isEmpty());
            assertFalse(citation.getTitle().isEmpty());
        });
    }

    /**
     * Test performance requirements - response time should be reasonable.
     */
    @Test
    @Timeout(value = 5, unit = TimeUnit.SECONDS)
    public void testPerformance() {
        QueryRequest request = new QueryRequest();
        request.setQuery("What are tax brackets for 2024?");
        
        long startTime = System.currentTimeMillis();
        
        ResponseEntity<QueryResponse> response = restTemplate.postForEntity(
                baseUrl + "/query", request, QueryResponse.class);
        
        long endTime = System.currentTimeMillis();
        long totalTime = endTime - startTime;
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        
        // Verify that the total request/response time is within acceptable limits
        assertTrue(totalTime < 5000, "API response time exceeds 5 seconds: " + totalTime + "ms");
        
        // Verify that the reported processing time matches actual time
        QueryResponse queryResponse = response.getBody();
        assertNotNull(queryResponse);
        assertTrue(queryResponse.getProcessingTimeMs() <= totalTime);
    }
}

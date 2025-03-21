package com.ai.taxlaw.tests;

import com.ai.taxlaw.model.Citation;
import com.ai.taxlaw.model.QueryRequest;
import com.ai.taxlaw.model.QueryResponse;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.junit.jupiter.api.Timeout;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/**
 * End-to-End Integration Tests for the Tax Law Assistant
 * 
 * These tests validate the entire system from the API layer through to the RAG retrieval
 * system and back, ensuring all components work together correctly.
 * 
 * The tests verify:
 * - Proper connectivity between the API and RAG components
 * - Accuracy of retrieval results
 * - End-to-end query processing
 * - System performance and reliability
 * - Response quality metrics
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
public class IntegrationTest {

    @LocalServerPort
    private int port;

    private TestRestTemplate restTemplate = new TestRestTemplate();
    private RestTemplate plainRestTemplate = new RestTemplate();
    
    private String baseUrl;
    private String ragServiceUrl = "http://localhost:5000";  // Default RAG service URL

    // Test data
    private List<String> taxQueries = new ArrayList<>();
    private List<String> expectedKeywords = new ArrayList<>();
    
    @BeforeAll
    public void setUp() {
        baseUrl = "http://localhost:" + port + "/api";
        
        // Initialize test data
        setupTestQueries();
        
        // Wait for services to be ready
        waitForServices();
    }
    
    /**
     * Set up a list of tax-related queries for testing.
     */
    private void setupTestQueries() {
        // Simple tax questions with expected keywords in response
        taxQueries.add("What is the standard deduction for married filing jointly?");
        expectedKeywords.add("married filing jointly");
        
        taxQueries.add("How are capital gains taxed?");
        expectedKeywords.add("capital gain");
        
        taxQueries.add("What tax deductions are available for self-employed individuals?");
        expectedKeywords.add("self-employ");
        
        taxQueries.add("When is the tax filing deadline for 2024?");
        expectedKeywords.add("deadline");
        
        taxQueries.add("What are the requirements for claiming a dependent?");
        expectedKeywords.add("dependent");
    }
    
    /**
     * Wait for all required services to be up and running.
     */
    private void waitForServices() {
        // Wait for API to be ready
        waitForService(baseUrl + "/health", "API", 30);
        
        // Wait for RAG service to be ready
        waitForService(ragServiceUrl + "/health", "RAG", 30);
    }
    
    /**
     * Helper method to wait for a service to become available.
     * 
     * @param url The URL to check
     * @param serviceName The name of the service (for logging)
     * @param maxRetries Maximum number of retries
     */
    private void waitForService(String url, String serviceName, int maxRetries) {
        int retries = 0;
        while (retries < maxRetries) {
            try {
                HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
                connection.setRequestMethod("GET");
                connection.setConnectTimeout(1000);
                connection.connect();
                
                int code = connection.getResponseCode();
                if (code == 200) {
                    System.out.println(serviceName + " service is up and running");
                    return;
                }
            } catch (IOException e) {
                // Service not yet available
            }
            
            try {
                System.out.println("Waiting for " + serviceName + " service to start... (attempt " + (retries + 1) + "/" + maxRetries + ")");
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            
            retries++;
        }
        
        System.err.println("WARNING: " + serviceName + " service may not be available. Tests might fail.");
    }
    
    /**
     * Test basic connectivity between components.
     */
    @Test
    public void testComponentConnectivity() {
        // Check API availability
        ResponseEntity<String> apiResponse = restTemplate.getForEntity(
                baseUrl + "/health", String.class);
        assertEquals(HttpStatus.OK, apiResponse.getStatusCode());
        
        // Check RAG service availability
        try {
            ResponseEntity<String> ragResponse = plainRestTemplate.getForEntity(
                    ragServiceUrl + "/health", String.class);
            assertEquals(HttpStatus.OK, ragResponse.getStatusCode());
        } catch (Exception e) {
            fail("RAG service is not available: " + e.getMessage());
        }
    }
    
    /**
     * Test end-to-end query processing with a simple tax question.
     */
    @Test
    @Timeout(value = 15, unit = TimeUnit.SECONDS)
    public void testEndToEndQuery() {
        QueryRequest request = new QueryRequest();
        request.setQuery("What is the standard deduction for single filers?");
        
        ResponseEntity<QueryResponse> response = restTemplate.postForEntity(
                baseUrl + "/query", request, QueryResponse.class);
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        
        QueryResponse queryResponse = response.getBody();
        assertNotNull(queryResponse);
        assertNotNull(queryResponse.getAnswer());
        assertFalse(queryResponse.getAnswer().isEmpty());
        
        // Check that the response contains relevant keywords
        String answer = queryResponse.getAnswer().toLowerCase();
        assertTrue(answer.contains("standard deduction") || answer.contains("single filer"));
        
        // Check that response includes citations
        assertFalse(queryResponse.getCitations().isEmpty());
    }
    
    /**
     * Test the quality of responses for multiple tax queries.
     */
    @Test
    @Timeout(value = 60, unit = TimeUnit.SECONDS)
    public void testMultipleQueriesResponseQuality() {
        for (int i = 0; i < taxQueries.size(); i++) {
            String query = taxQueries.get(i);
            String expectedKeyword = expectedKeywords.get(i);
            
            QueryRequest request = new QueryRequest();
            request.setQuery(query);
            
            ResponseEntity<QueryResponse> response = restTemplate.postForEntity(
                    baseUrl + "/query", request, QueryResponse.class);
            
            assertEquals(HttpStatus.OK, response.getStatusCode(), 
                    "Query should be processed successfully: " + query);
            
            QueryResponse queryResponse = response.getBody();
            assertNotNull(queryResponse);
            
            // Check for relevant content in the response
            String answer = queryResponse.getAnswer().toLowerCase();
            assertTrue(answer.contains(expectedKeyword.toLowerCase()),
                    "Response for '" + query + "' should contain '" + expectedKeyword + "'");
            
            // Response should have citations
            List<Citation> citations = queryResponse.getCitations();
            assertFalse(citations.isEmpty(), "Response should have citations");
            
            // Check citation quality
            for (Citation citation : citations) {
                assertNotNull(citation.getSource(), "Citation should have a source");
                assertFalse(citation.getSource().isEmpty(), "Citation source should not be empty");
                
                assertNotNull(citation.getTitle(), "Citation should have a title");
                assertFalse(citation.getTitle().isEmpty(), "Citation title should not be empty");
                
                if (citation.getUrl() != null && !citation.getUrl().isEmpty()) {
                    assertTrue(citation.getUrl().startsWith("http"), 
                            "Citation URL should be a valid URL");
                }
            }
            
            // Response should be generated within a reasonable time
            assertTrue(queryResponse.getProcessingTimeMs() < 10000,
                    "Processing time should be less than 10 seconds");
            
            // Give the system a brief break between queries to avoid overloading
            try {
                Thread.sleep(500);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }
    
    /**
     * Test response consistency by sending the same query multiple times.
     */
    @Test
    @Timeout(value = 30, unit = TimeUnit.SECONDS)
    public void testResponseConsistency() {
        String query = "What are the tax brackets for 2024?";
        QueryRequest request = new QueryRequest();
        request.setQuery(query);
        
        List<String> responses = new ArrayList<>();
        
        // Send the same query 3 times
        for (int i = 0; i < 3; i++) {
            ResponseEntity<QueryResponse> response = restTemplate.postForEntity(
                    baseUrl + "/query", request, QueryResponse.class);
            
            assertEquals(HttpStatus.OK, response.getStatusCode());
            
            QueryResponse queryResponse = response.getBody();
            assertNotNull(queryResponse);
            
            responses.add(queryResponse.getAnswer());
            
            // Give the system a brief break between queries
            try {
                Thread.sleep(500);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
        
        // Responses should be consistent (not necessarily identical, but similar)
        // We'll check if they all contain the same key phrases
        List<String> keyPhrases = List.of("tax bracket", "2024", "income", "rate");
        
        for (String response : responses) {
            String lowerResponse = response.toLowerCase();
            for (String phrase : keyPhrases) {
                assertTrue(lowerResponse.contains(phrase), 
                        "All responses should contain key phrase: " + phrase);
            }
        }
    }
    
    /**
     * Test the system's ability to handle invalid or malformed queries.
     */
    @Test
    public void testErrorHandling() {
        // Test with an empty query
        QueryRequest emptyRequest = new QueryRequest();
        emptyRequest.setQuery("");
        
        ResponseEntity<QueryResponse> emptyResponse = restTemplate.postForEntity(
                baseUrl + "/query", emptyRequest, QueryResponse.class);
        
        assertEquals(HttpStatus.BAD_REQUEST, emptyResponse.getStatusCode(),
                "Empty queries should return a 400 Bad Request");
        
        // Test with a non-tax related query
        QueryRequest irrelevantRequest = new QueryRequest();
        irrelevantRequest.setQuery("Tell me about the history of pizza");
        
        ResponseEntity<QueryResponse> irrelevantResponse = restTemplate.postForEntity(
                baseUrl + "/query", irrelevantRequest, QueryResponse.class);
        
        assertEquals(HttpStatus.OK, irrelevantResponse.getStatusCode());
        
        QueryResponse queryResponse = irrelevantResponse.getBody();
        assertNotNull(queryResponse);
        
        // The response should indicate that the query is not tax-related
        String answer = queryResponse.getAnswer().toLowerCase();
        assertTrue(answer.contains("tax") || answer.contains("unable to") || 
                   answer.contains("not related to") || answer.contains("outside the scope"),
                "Response should indicate the query is not about tax law");
    }
    
    /**
     * Test the system's performance under load with concurrent queries.
     */
    @Test
    @Timeout(value = 60, unit = TimeUnit.SECONDS)
    public void testConcurrentQueryPerformance() throws InterruptedException {
        int numThreads = 5;
        int queriesPerThread = 2;
        
        // Create threads to send concurrent queries
        List<Thread> threads = new ArrayList<>();
        List<Exception> exceptions = new ArrayList<>();
        
        for (int i = 0; i < numThreads; i++) {
            final int threadIndex = i;
            Thread thread = new Thread(() -> {
                try {
                    for (int j = 0; j < queriesPerThread; j++) {
                        // Get a query from our test data, cycling through them
                        String query = taxQueries.get((threadIndex + j) % taxQueries.size());
                        
                        QueryRequest request = new QueryRequest();
                        request.setQuery(query);
                        
                        ResponseEntity<QueryResponse> response = restTemplate.postForEntity(
                                baseUrl + "/query", request, QueryResponse.class);
                        
                        assertEquals(HttpStatus.OK, response.getStatusCode(),
                                "Query should be processed successfully: " + query);
                        
                        QueryResponse queryResponse = response.getBody();
                        assertNotNull(queryResponse, "Response should not be null");
                        assertNotNull(queryResponse.getAnswer(), "Answer should not be null");
                        assertFalse(queryResponse.getAnswer().isEmpty(), "Answer should not be empty");
                    }
                } catch (Exception e) {
                    synchronized (exceptions) {
                        exceptions.add(e);
                    }
                }
            });
            
            threads.add(thread);
            thread.start();
        }
        
        // Wait for all threads to complete
        for (Thread thread : threads) {
            thread.join();
        }
        
        // Check if any exceptions occurred
        if (!exceptions.isEmpty()) {
            fail("Exceptions occurred during concurrent testing: " + 
                 exceptions.stream()
                     .map(Exception::getMessage)
                     .collect(Collectors.joining(", ")));
        }
    }
    
    /**
     * Test the system's ability to handle complex, multi-part tax questions.
     */
    @Test
    @Timeout(value = 20, unit = TimeUnit.SECONDS)
    public void testComplexQuery() {
        String complexQuery = "I'm self-employed, work from home, and made $85,000 last year. " +
                "What deductions am I eligible for and how do I calculate my estimated tax payments?";
        
        QueryRequest request = new QueryRequest();
        request.setQuery(complexQuery);
        
        ResponseEntity<QueryResponse> response = restTemplate.postForEntity(
                baseUrl + "/query", request, QueryResponse.class);
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        
        QueryResponse queryResponse = response.getBody();
        assertNotNull(queryResponse);
        
        String answer = queryResponse.getAnswer().toLowerCase();
        
        // Check that the answer addresses both parts of the question
        assertTrue(answer.contains("deduction") && answer.contains("self-employ"),
                "Answer should address deductions for self-employed");
        
        assertTrue(answer.contains("estimated tax") || answer.contains("quarterly"),
                "Answer should address estimated tax payments");
        
        // Complex query should have multiple citations
        assertTrue(queryResponse.getCitations().size() >= 2,
                "Complex query should have multiple citations");
    }
}

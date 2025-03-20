package com.ai.taxlaw.service;

import com.ai.taxlaw.model.QueryRequest;
import com.ai.taxlaw.model.QueryResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

/**
 * Unit tests for the QueryService class.
 * Tests the business logic for processing tax law queries.
 */
@ExtendWith(MockitoExtension.class)
public class QueryServiceTest {

    @Mock
    private RAGClient ragClient;

    @InjectMocks
    private QueryService queryService;

    @BeforeEach
    public void setup() {
        // Set up property values
        ReflectionTestUtils.setField(queryService, "ragApiUrl", "http://localhost:5000");
        ReflectionTestUtils.setField(queryService, "openAiApiKey", "test-api-key");
    }

    /**
     * Test processing a query with successful retrieval.
     * Should return a response with an answer and citations.
     */
    @Test
    public void testProcessQuery() {
        // Mock RAG client response
        when(ragClient.fetchResponse(anyString())).thenReturn(
                "Based on IRS Publication 17, the answer is that tax filing requirements depend on your filing status."
        );

        // Create test request
        QueryRequest request = new QueryRequest("What are the tax filing requirements?", null);

        // Process the query
        QueryResponse response = queryService.processQuery(request);

        // Verify the response
        assertNotNull(response);
        assertNotNull(response.getAnswer());
        assertTrue(response.getAnswer().contains("tax filing requirements"));
        assertTrue(response.getProcessingTimeMs() > 0);
    }

    /**
     * Test query processing with an exception.
     * Should return a graceful error response.
     */
    @Test
    public void testProcessQueryWithException() {
        // Mock RAG client to throw an exception
        when(ragClient.fetchResponse(anyString())).thenThrow(new RuntimeException("Test exception"));

        // Create test request
        QueryRequest request = new QueryRequest("What are the tax filing requirements?", null);

        // Process the query
        QueryResponse response = queryService.processQuery(request);

        // Verify the response contains an error message
        assertNotNull(response);
        assertNotNull(response.getAnswer());
        assertTrue(response.getAnswer().contains("sorry"));
        assertTrue(response.getProcessingTimeMs() > 0);
    }
}

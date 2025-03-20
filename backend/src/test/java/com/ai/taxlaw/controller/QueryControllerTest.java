package com.ai.taxlaw.controller;

import com.ai.taxlaw.model.QueryRequest;
import com.ai.taxlaw.model.QueryResponse;
import com.ai.taxlaw.service.QueryService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Unit tests for the QueryController class.
 * Tests API endpoints for health, status, and query processing.
 */
@WebMvcTest(QueryController.class)
public class QueryControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private QueryService queryService;

    @Autowired
    private ObjectMapper objectMapper;

    /**
     * Test the health check endpoint.
     * Should return status 200 OK with a simple message.
     */
    @Test
    public void testHealthEndpoint() throws Exception {
        mockMvc.perform(get("/api/health"))
                .andExpect(status().isOk());
    }

    /**
     * Test the status endpoint.
     * Should return status 200 OK with a JSON object containing status info.
     */
    @Test
    public void testStatusEndpoint() throws Exception {
        mockMvc.perform(get("/api/status"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("online"))
                .andExpect(jsonPath("$.version").value("1.0.0"))
                .andExpect(jsonPath("$.timestamp").exists());
    }

    /**
     * Test the query endpoint with a valid request.
     * Should return status 200 OK with a response containing the answer.
     */
    @Test
    public void testQueryEndpoint() throws Exception {
        // Mock service response
        QueryResponse mockResponse = new QueryResponse("This is a test response");
        mockResponse.setProcessingTimeMs(100);

        when(queryService.processQuery(any(QueryRequest.class))).thenReturn(mockResponse);

        // Create test request
        QueryRequest request = new QueryRequest("What are the tax deductions for home office?", null);

        // Perform the test
        mockMvc.perform(post("/api/query")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.answer").value("This is a test response"))
                .andExpect(jsonPath("$.processingTimeMs").exists());
    }

    /**
     * Test the query endpoint with an empty request.
     * Should return status 400 Bad Request.
     */
    @Test
    public void testQueryEndpointWithEmptyQuery() throws Exception {
        // Create test request with empty query
        QueryRequest request = new QueryRequest("", null);

        // Perform the test
        mockMvc.perform(post("/api/query")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }
}

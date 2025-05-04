package com.ai.taxlaw.controller;

import com.ai.taxlaw.model.QueryRequest;
import com.ai.taxlaw.model.QueryResponse;
import com.ai.taxlaw.service.OpenAIService;
import com.ai.taxlaw.service.QueryService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * REST controller for handling tax law queries.
 * This controller provides endpoints for submitting queries and receiving AI-generated responses.
 */
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*") // Enable CORS for browser extension
public class QueryController {
    
    private static final Logger logger = LoggerFactory.getLogger(QueryController.class);
    
    @Autowired
    private QueryService queryService;
    
    @Autowired
    private OpenAIService openAIService;
    
    /**
     * Submit a tax law query and receive an AI-generated response.
     * 
     * @param request The query request with the user's question
     * @return A response entity containing the answer and citations
     */
    @PostMapping("/query")
    public ResponseEntity<QueryResponse> query(@RequestBody QueryRequest request) {
        logger.info("Received query request: {}", request);
        
        if (request.getQuery() == null || request.getQuery().trim().isEmpty()) {
            logger.warn("Received empty query");
            return ResponseEntity.badRequest().build();
        }
        
        try {
            // Use the QueryService to process the query
            QueryResponse response = queryService.processQuery(request);
            logger.info("Generated response: {}", response);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Error processing query: {}", e.getMessage(), e);
            QueryResponse errorResponse = new QueryResponse("An error occurred: " + e.getMessage());
            return ResponseEntity.ok(errorResponse);
        }
    }
    
    /**
     * Test endpoint specifically for testing OpenAI integration.
     * 
     * @param request The test query request
     * @return A response with the OpenAI-generated answer
     */
    @PostMapping("/test/openai")
    public ResponseEntity<Map<String, String>> testOpenAI(@RequestBody Map<String, String> request) {
        logger.info("Received OpenAI test request: {}", request);
        
        String query = request.getOrDefault("query", "What are the basic tax filing deadlines?");
        String context = "Tax filing deadlines vary by entity type. For individuals, the deadline " +
                         "is generally April 15th, but can be extended to October 15th.";
        
        try {
            String response = openAIService.generateResponse(query, context);
            
            Map<String, String> result = Map.of(
                "query", query,
                "response", response
            );
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Error in OpenAI test: {}", e.getMessage(), e);
            return ResponseEntity.ok(Map.of(
                "query", query,
                "response", "Error: " + e.getMessage()
            ));
        }
    }
    
    /**
     * Health check endpoint.
     * 
     * @return A simple status message
     */
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        logger.debug("Health check called");
        return ResponseEntity.ok("Tax Law AI API is running");
    }
    
    /**
     * Simple status check for browser extension to verify API connectivity.
     * 
     * @return API status information
     */
    @GetMapping("/status")
    public ResponseEntity<Object> status() {
        logger.debug("Status check called");
        
        // Return a simple status object
        return ResponseEntity.ok(Map.of(
                "status", "online",
                "version", "1.0.0",
                "timestamp", System.currentTimeMillis()
        ));
    }
}

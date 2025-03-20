package com.ai.taxlaw.controller;

import com.ai.taxlaw.model.QueryRequest;
import com.ai.taxlaw.model.QueryResponse;
import com.ai.taxlaw.service.QueryService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

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
        
        QueryResponse response = queryService.processQuery(request);
        logger.info("Generated response: {}", response);
        
        return ResponseEntity.ok(response);
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

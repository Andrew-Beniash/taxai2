package com.ai.taxlaw.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.ai.taxlaw.service.OpenAIService;

import java.util.Map;
import java.util.HashMap;

/**
 * Controller to test OpenAI API integration.
 * This controller provides endpoints to verify that the OpenAI service
 * is properly configured and functioning.
 */
@RestController
@RequestMapping("/api/test")
public class OpenAITestController {
    
    @Autowired
    private OpenAIService openAIService;
    
    /**
     * Simple endpoint to test the OpenAI API connection.
     * Sends a basic query to OpenAI and returns the response.
     * 
     * @param request A map containing the test query
     * @return The OpenAI response
     */
    @PostMapping("/openai")
    public ResponseEntity<Map<String, String>> testOpenAI(@RequestBody Map<String, String> request) {
        String query = request.getOrDefault("query", "What are the basic tax filing deadlines?");
        String context = "Tax filing deadlines vary by entity type. For individuals, the deadline " +
                         "is generally April 15th, but can be extended to October 15th.";
        
        String response = openAIService.generateResponse(query, context);
        
        Map<String, String> result = new HashMap<>();
        result.put("query", query);
        result.put("response", response);
        
        return ResponseEntity.ok(result);
    }
}

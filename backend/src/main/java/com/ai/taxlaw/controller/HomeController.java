package com.ai.taxlaw.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

/**
 * Controller for the home page and general information.
 */
@RestController
public class HomeController {
    
    /**
     * Root endpoint that provides basic API information.
     * 
     * @return A response with API details
     */
    @GetMapping("/")
    public ResponseEntity<Map<String, Object>> home() {
        Map<String, Object> response = new HashMap<>();
        response.put("name", "Tax Law Assistant API");
        response.put("description", "AI-powered tax law assistant with RAG capabilities");
        response.put("version", "1.0.0");
        response.put("endpoints", new String[] {
            "/api/query - Submit tax law queries (POST)",
            "/api/health - Check API health (GET)",
            "/api/status - Get API status (GET)"
        });
        
        return ResponseEntity.ok(response);
    }
}

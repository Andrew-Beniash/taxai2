package com.ai.taxlaw.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Service to handle communication with the OpenAI API.
 * This service is responsible for sending requests to OpenAI
 * and processing responses for the tax law assistant.
 */
@Service
public class OpenAIService {
    
    private static final Logger logger = LoggerFactory.getLogger(OpenAIService.class);
    
    private final RestTemplate restTemplate;
    
    @Value("${openai.api.url}")
    private String apiUrl;
    
    @Value("${openai.api.key}")
    private String apiKey;
    
    @Value("${openai.model}")
    private String model;
    
    public OpenAIService() {
        this.restTemplate = new RestTemplate();
    }
    
    /**
     * Generate a response from OpenAI based on a query and context.
     * 
     * @param query The user's tax law query
     * @param context Additional context from the RAG system
     * @return The AI-generated response
     */
    public String generateResponse(String query, String context) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("Authorization", "Bearer " + apiKey);
            
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", model);
            
            // Create a system message with instructions
            Map<String, String> systemMessage = new HashMap<>();
            systemMessage.put("role", "system");
            systemMessage.put("content", "You are a helpful tax law assistant. " +
                    "Your responses should be accurate, concise, and backed by authoritative sources. " +
                    "Use the provided tax law context to inform your answers. " +
                    "Always include citations to relevant laws, regulations, or IRS publications. " +
                    "If you are unsure about something, acknowledge the uncertainty rather than making claims.");
            
            // Create a user message with the query and context
            Map<String, String> userMessage = new HashMap<>();
            userMessage.put("role", "user");
            userMessage.put("content", "Query: " + query + "\n\nContext:\n" + context);
            
            requestBody.put("messages", List.of(systemMessage, userMessage));
            requestBody.put("temperature", 0.3); // Low temperature for more factual responses
            requestBody.put("max_tokens", 1000);
            
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            
            logger.debug("Sending request to OpenAI API");
            ResponseEntity<Map> response = restTemplate.postForEntity(apiUrl, request, Map.class);
            
            // Extract the response text
            Map<String, Object> responseBody = response.getBody();
            if (responseBody != null) {
                List<Map<String, Object>> choices = (List<Map<String, Object>>) responseBody.get("choices");
                if (choices != null && !choices.isEmpty()) {
                    Map<String, Object> choice = choices.get(0);
                    Map<String, String> message = (Map<String, String>) choice.get("message");
                    if (message != null) {
                        return message.get("content");
                    }
                }
            }
            
            throw new RuntimeException("Failed to parse OpenAI response");
            
        } catch (Exception e) {
            logger.error("Error calling OpenAI API: {}", e.getMessage(), e);
            return "I'm sorry, I couldn't generate a response to your tax law question at this time. " +
                   "Please try again or consult a tax professional.";
        }
    }
}

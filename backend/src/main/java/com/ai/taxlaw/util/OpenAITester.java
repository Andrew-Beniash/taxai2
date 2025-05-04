package com.ai.taxlaw.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;

/**
 * Utility class to test the OpenAI API connection.
 * This class provides a simple way to verify that the OpenAI API
 * is accessible and functioning correctly.
 * 
 * Run this class as a standalone Java application to test the connection.
 */
public class OpenAITester {
    
    private static final Logger logger = LoggerFactory.getLogger(OpenAITester.class);
    private static final String API_URL = "https://api.openai.com/v1/chat/completions";
    private static final String DEFAULT_MODEL = "gpt-4o";
    
    public static void main(String[] args) {
        // Get the API key from environment variable or prompt the user
        String apiKey = System.getenv("OPENAI_API_KEY");
        if (apiKey == null || apiKey.isEmpty()) {
            System.out.print("Enter your OpenAI API key: ");
            Scanner scanner = new Scanner(System.in);
            apiKey = scanner.nextLine().trim();
            scanner.close();
            
            if (apiKey.isEmpty()) {
                System.err.println("Error: API key is required.");
                System.exit(1);
            }
        }
        
        // Test with a simple tax law query
        String query = "What is the standard deduction for a single filer in 2023?";
        System.out.println("Testing OpenAI API with query: " + query);
        
        try {
            String response = callOpenAI(apiKey, query);
            System.out.println("\nResponse from OpenAI:");
            System.out.println("--------------------");
            System.out.println(response);
            System.out.println("--------------------");
            System.out.println("\nThe OpenAI integration test was successful!");
        } catch (Exception e) {
            System.err.println("Error testing OpenAI API: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
    
    /**
     * Call the OpenAI API with a simple query.
     * 
     * @param apiKey The OpenAI API key
     * @param query The query to send
     * @return The response from OpenAI
     */
    private static String callOpenAI(String apiKey, String query) {
        RestTemplate restTemplate = new RestTemplate();
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("Authorization", "Bearer " + apiKey);
        
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("model", DEFAULT_MODEL);
        
        // Create a system message with instructions
        Map<String, String> systemMessage = new HashMap<>();
        systemMessage.put("role", "system");
        systemMessage.put("content", "You are a helpful tax law assistant. Provide concise and accurate answers.");
        
        // Create a user message with the query
        Map<String, String> userMessage = new HashMap<>();
        userMessage.put("role", "user");
        userMessage.put("content", query);
        
        requestBody.put("messages", List.of(systemMessage, userMessage));
        requestBody.put("temperature", 0.3);
        requestBody.put("max_tokens", 500);
        
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
        
        ResponseEntity<Map> response = restTemplate.postForEntity(API_URL, request, Map.class);
        
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
    }
}

package com.ai.taxlaw.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

/**
 * Tests for the OpenAIService class.
 * These tests verify that the OpenAI service correctly
 * communicates with the OpenAI API and processes responses.
 */
@ExtendWith(MockitoExtension.class)
public class OpenAIServiceTest {

    @Mock
    private RestTemplate restTemplate;

    @InjectMocks
    private OpenAIService openAIService;

    @BeforeEach
    public void setup() {
        // Set required fields via reflection since we're using constructor injection
        // in a real app, these would come from application.properties
        ReflectionTestUtils.setField(openAIService, "apiUrl", "https://api.openai.com/v1/chat/completions");
        ReflectionTestUtils.setField(openAIService, "apiKey", "test-api-key");
        ReflectionTestUtils.setField(openAIService, "model", "gpt-4o");
        ReflectionTestUtils.setField(openAIService, "restTemplate", restTemplate);
    }

    @Test
    public void testGenerateResponse_Success() {
        // Prepare mock response from OpenAI API
        Map<String, Object> responseBody = new HashMap<>();
        
        Map<String, String> message = new HashMap<>();
        message.put("content", "This is a test response from the OpenAI API.");
        message.put("role", "assistant");
        
        Map<String, Object> choice = new HashMap<>();
        choice.put("message", message);
        
        responseBody.put("choices", List.of(choice));
        
        ResponseEntity<Map> mockResponse = new ResponseEntity<>(responseBody, HttpStatus.OK);
        
        // Mock the REST template to return our prepared response
        when(restTemplate.postForEntity(anyString(), any(HttpEntity.class), eq(Map.class)))
                .thenReturn(mockResponse);
        
        // Call the service method
        String result = openAIService.generateResponse("Test query", "Test context");
        
        // Verify the result
        assertNotNull(result);
        assertEquals("This is a test response from the OpenAI API.", result);
    }
    
    @Test
    public void testGenerateResponse_Error() {
        // Mock an exception when calling the OpenAI API
        when(restTemplate.postForEntity(anyString(), any(HttpEntity.class), eq(Map.class)))
                .thenThrow(new RuntimeException("API Error"));
        
        // Call the service method
        String result = openAIService.generateResponse("Test query", "Test context");
        
        // Verify that we get a fallback error message
        assertNotNull(result);
        assertEquals("I'm sorry, I couldn't generate a response to your tax law question at this time. " +
                     "Please try again or consult a tax professional.", result);
    }
}

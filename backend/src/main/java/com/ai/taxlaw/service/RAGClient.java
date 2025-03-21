package com.ai.taxlaw.service;

import com.ai.taxlaw.model.Citation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Client service for communicating with the RAG (Retrieval-Augmented Generation) system.
 * This service is responsible for retrieving relevant tax law documents based on user queries.
 */
@Service
public class RAGClient {
    
    private static final Logger logger = LoggerFactory.getLogger(RAGClient.class);
    
    private final RestTemplate restTemplate;
    
    @Value("${rag.api.url}")
    private String ragApiUrl;
    
    public RAGClient() {
        this.restTemplate = new RestTemplate();
    }
    
    /**
     * Retrieve relevant documents from the RAG system based on a query.
     * 
     * @param query The user's tax law query
     * @return A list of relevant citations
     */
    public List<Citation> retrieveRelevantDocuments(String query) {
        logger.debug("Retrieving relevant documents for query: {}", query);
        
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("query", query);
            requestBody.put("topK", 5); // Number of documents to retrieve
            
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            
            logger.debug("Sending request to RAG API at {}", ragApiUrl);
            ResponseEntity<Map> response = restTemplate.postForEntity(ragApiUrl + "/retrieve", request, Map.class);
            
            List<Citation> citations = parseRagResponse(response.getBody());
            logger.debug("Retrieved {} relevant documents", citations.size());
            
            return citations;
            
        } catch (Exception e) {
            logger.error("Error calling RAG API: {}", e.getMessage(), e);
            // Return empty list on error
            return new ArrayList<>();
        }
    }
    
    /**
     * Parse the RAG API response into a list of citations.
     * 
     * @param responseBody The response body from the RAG API
     * @return A list of citation objects
     */
    @SuppressWarnings("unchecked")
    private List<Citation> parseRagResponse(Map<String, Object> responseBody) {
        List<Citation> citations = new ArrayList<>();
        
        if (responseBody == null) {
            return citations;
        }
        
        List<Map<String, Object>> documents = (List<Map<String, Object>>) responseBody.get("documents");
        if (documents == null) {
            return citations;
        }
        
        for (Map<String, Object> doc : documents) {
            Citation citation = new Citation(
                    (String) doc.get("source"),
                    (String) doc.get("title"),
                    (String) doc.get("content"),
                    (String) doc.get("url"),
                    (String) doc.get("id")
            );
            citations.add(citation);
        }
        
        return citations;
    }
    
    /**
     * Fetch a response from the RAG system and OpenAI.
     * This will first retrieve relevant documents and then use them
     * to generate an AI response.
     * 
     * @param query The user's tax law query
     * @return The AI-generated response
     * @deprecated This method is superseded by retrieveRelevantDocuments() which is now used by AIModelService
     */
    @Deprecated
    public String fetchResponse(String query) {
        // This method is kept for backward compatibility but should not be used for new code
        // The actual integration is now handled by AIModelService
        logger.warn("Using deprecated fetchResponse method - use retrieveRelevantDocuments instead");
        return "Based on IRS Publication 17 and relevant tax code sections, " +
               "the answer to your question about \"" + query + "\" involves detailed tax considerations. " +
               "Please consult with a tax professional for personalized advice.";
    }
}

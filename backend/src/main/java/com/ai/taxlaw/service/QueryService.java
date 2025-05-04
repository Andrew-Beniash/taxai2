package com.ai.taxlaw.service;

import com.ai.taxlaw.model.Citation;
import com.ai.taxlaw.model.QueryRequest;
import com.ai.taxlaw.model.QueryResponse;
import com.ai.taxlaw.service.ai.AIModelService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;


import java.util.ArrayList;
import java.util.List;

/**
 * Service responsible for processing tax law queries.
 * This service interfaces with the RAG system to retrieve relevant tax law information
 * and generate AI responses with proper citations.
 */
@Service
public class QueryService {
    
    private static final Logger logger = LoggerFactory.getLogger(QueryService.class);
    
    @Value("${rag.api.url}")
    private String ragApiUrl;
    
    @Value("${openai.api.key}")
    private String openAiApiKey;
    
    /**
     * Process a tax law query using the RAG system and OpenAI.
     * 
     * @param request The query request containing the user's question
     * @return A response with the answer and relevant citations
     */
    public QueryResponse processQuery(QueryRequest request) {
        long startTime = System.currentTimeMillis();
        logger.info("Processing query: {}", request);
        
        try {
            // Simple implementation that directly uses OpenAI
            // For testing purposes, without the full RAG implementation yet
            String query = request.getQuery();
            String context = "This query is about tax law. Provide accurate information based on US tax regulations.";
            
            // Use OpenAI to generate a response
            String aiResponse = openAIService.generateResponse(query, context);
            
            // Create a response with the AI-generated text
            QueryResponse response = new QueryResponse(aiResponse);
            
            // Add some sample citations for now
            List<Citation> citations = new ArrayList<>();
            citations.add(new Citation(
                "IRS Publication", 
                "Your Federal Income Tax", 
                "The standard deduction is a specific dollar amount that reduces the amount of income on which you are taxed.", 
                "https://www.irs.gov/publications", 
                "IRS-Pub-17"
            ));
            
            response.setCitations(citations);
            
            long processingTime = System.currentTimeMillis() - startTime;
            response.setProcessingTimeMs(processingTime);
            
            logger.info("Query processed successfully in {}ms", processingTime);
            return response;
            
        } catch (Exception e) {
            logger.error("Error processing query: {}", e.getMessage(), e);
            QueryResponse errorResponse = new QueryResponse("Sorry, I couldn't process your tax law query. Please try again.");
            errorResponse.setProcessingTimeMs(System.currentTimeMillis() - startTime);
            return errorResponse;
        }
    }
    
    // The functionality from retrieveRelevantDocuments and generateAIResponse methods
    // has been moved to the AIModelService and RAGClient classes for better separation of concerns
    
    @Autowired
    private RAGClient ragClient;
    
    @Autowired
    private AIModelService aiModelService;
    
    @Autowired
    private OpenAIService openAIService;
    
    /**
     * Retrieve relevant tax law documents based on the query.
     * 
     * @param query The user's tax law query
     * @return A list of relevant citations
     */
    private List<Citation> retrieveRelevantDocuments(String query) {
        return ragClient.retrieveRelevantDocuments(query);
    }
    
    /**
     * Generate an AI response with the retrieved documents.
     * 
     * @param query The user's tax law query
     * @param relevantDocs List of relevant citations
     * @return AI-generated response
     */
    private String generateAIResponse(String query, List<Citation> relevantDocs) {
        return aiModelService.generateResponse(query);
    }
}

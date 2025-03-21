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
            // TODO: Implement actual RAG retrieval logic
            // This is a placeholder for the RAG and OpenAI integration
            
            // 1. Call the RAG system to retrieve relevant tax law documents
            List<Citation> relevantDocs = retrieveRelevantDocuments(request.getQuery());
            
            // 2. Generate response using OpenAI with the retrieved context
            String aiResponse = generateAIResponse(request.getQuery(), relevantDocs);
            
            // 3. Format the response with inline citations
            QueryResponse response = new QueryResponse(aiResponse);
            response.setCitations(relevantDocs);
            
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

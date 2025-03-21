package com.ai.taxlaw.service.ai;

import com.ai.taxlaw.model.Citation;
import com.ai.taxlaw.service.OpenAIService;
import com.ai.taxlaw.service.RAGClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Service that handles the integration between the RAG system and OpenAI model.
 * This service is responsible for:
 * 1. Retrieving relevant tax law documents from the RAG system
 * 2. Preparing the context for the OpenAI model with retrieved documents
 * 3. Sending the query with context to OpenAI
 * 4. Processing the response to ensure it includes proper citations
 */
@Service
public class AIModelService {
    
    private static final Logger logger = LoggerFactory.getLogger(AIModelService.class);
    
    @Autowired
    private RAGClient ragClient;
    
    @Autowired
    private OpenAIService openAIService;
    
    @Autowired
    private ResponseFormatter responseFormatter;
    
    @Autowired
    private CitationManager citationManager;
    
    /**
     * Generate a tax law response with accurate citations.
     * 
     * @param query The user's tax law query
     * @return AI-generated response with context-aware retrieval
     */
    public String generateResponse(String query) {
        logger.info("Generating AI response for query: {}", query);
        
        try {
            // Step 1: Retrieve relevant tax law documents using RAG
            List<Citation> relevantDocs = ragClient.retrieveRelevantDocuments(query);
            logger.debug("Retrieved {} relevant documents from RAG", relevantDocs.size());
            
            if (relevantDocs.isEmpty()) {
                logger.warn("No relevant documents found for query: {}", query);
                return "I couldn't find specific tax law information to answer your question. " +
                       "Please try rephrasing or ask about a different tax topic.";
            }
            
            // Step 2: Prepare context from retrieved documents
            String context = prepareContext(relevantDocs);
            
            // Step 3: Send query with context to OpenAI
            String rawResponse = openAIService.generateResponse(query, context);
            
            // Step 4: Process the response to ensure proper citation formatting
            String formattedResponse = responseFormatter.formatResponse(rawResponse, relevantDocs);
            
            // Step 5: Validate and ensure citations are inline
            return citationManager.validateAndEnrichCitations(formattedResponse, relevantDocs);
            
        } catch (Exception e) {
            logger.error("Error generating AI response: {}", e.getMessage(), e);
            return "I'm sorry, I encountered a technical issue while processing your tax law query. " +
                   "Please try again or consider rephrasing your question.";
        }
    }
    
    /**
     * Prepare context from retrieved documents for the OpenAI model.
     * 
     * @param citations List of relevant document citations
     * @return Formatted context string for the AI model
     */
    private String prepareContext(List<Citation> citations) {
        StringBuilder contextBuilder = new StringBuilder();
        contextBuilder.append("Please use the following tax law information to answer the query:\n\n");
        
        for (int i = 0; i < citations.size(); i++) {
            Citation citation = citations.get(i);
            
            contextBuilder.append("Document ").append(i + 1).append(":\n");
            contextBuilder.append("Source: ").append(citation.getSource()).append("\n");
            contextBuilder.append("Title: ").append(citation.getTitle()).append("\n");
            contextBuilder.append("Reference ID: ").append(citation.getReferenceId()).append("\n");
            contextBuilder.append("Content: ").append(citation.getExcerpt()).append("\n\n");
        }
        
        contextBuilder.append("IMPORTANT INSTRUCTIONS:\n");
        contextBuilder.append("1. Base your answer entirely on the provided documents.\n");
        contextBuilder.append("2. Use inline citations in the format [Source: ReferenceID] directly after any statement sourced from the documents.\n");
        contextBuilder.append("3. If the provided documents don't contain enough information to answer the query, acknowledge this limitation.\n");
        contextBuilder.append("4. Do not fabricate information or citations.\n");
        contextBuilder.append("5. Keep the answer concise but comprehensive.\n");
        
        return contextBuilder.toString();
    }
}

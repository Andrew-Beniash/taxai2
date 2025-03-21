package com.ai.taxlaw.service.ai;

import com.ai.taxlaw.model.Citation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Service responsible for managing citations in AI responses.
 * This service ensures that citations are accurate, properly formatted,
 * and correctly linked to the source documents.
 */
@Service
public class CitationManager {
    
    private static final Logger logger = LoggerFactory.getLogger(CitationManager.class);
    
    // Pattern to identify inline citations
    private static final Pattern CITATION_PATTERN = Pattern.compile("\\[<sup>([^<]+)</sup>\\]");
    
    // Pattern to identify sentences (for context-aware citation validation)
    private static final Pattern SENTENCE_PATTERN = Pattern.compile("([^.!?]+[.!?])");
    
    /**
     * Validate and enrich citations in the AI response.
     * 
     * @param response The formatted AI response
     * @param availableCitations List of available citation objects
     * @return Response with validated and enriched citations
     */
    public String validateAndEnrichCitations(String response, List<Citation> availableCitations) {
        logger.debug("Validating and enriching citations in response");
        
        if (response == null || response.isEmpty()) {
            return "No response was generated.";
        }
        
        // Step 1: Extract all cited reference IDs
        List<String> citedRefIds = extractCitedReferenceIds(response);
        
        // Step 2: Check for missing citations
        List<String> missingRefIds = findMissingReferenceIds(citedRefIds, availableCitations);
        
        if (!missingRefIds.isEmpty()) {
            logger.warn("Found {} missing citation reference IDs: {}", missingRefIds.size(), missingRefIds);
        }
        
        // Step 3: Check for sentences that need citations
        String enrichedResponse = addMissingCitations(response, availableCitations);
        
        // Step 4: Ensure context-aware citations
        return ensureContextAwareCitations(enrichedResponse, availableCitations);
    }
    
    /**
     * Extract all cited reference IDs from the response.
     * 
     * @param response The AI response text
     * @return List of cited reference IDs
     */
    private List<String> extractCitedReferenceIds(String response) {
        List<String> refIds = new ArrayList<>();
        Matcher matcher = CITATION_PATTERN.matcher(response);
        
        while (matcher.find()) {
            refIds.add(matcher.group(1));
        }
        
        return refIds;
    }
    
    /**
     * Find reference IDs in the response that don't match any available citations.
     * 
     * @param citedRefIds List of cited reference IDs
     * @param availableCitations List of available citation objects
     * @return List of missing reference IDs
     */
    private List<String> findMissingReferenceIds(List<String> citedRefIds, List<Citation> availableCitations) {
        List<String> missingRefIds = new ArrayList<>();
        
        for (String refId : citedRefIds) {
            boolean found = false;
            
            for (Citation citation : availableCitations) {
                if (refId.equals(citation.getReferenceId())) {
                    found = true;
                    break;
                }
            }
            
            if (!found) {
                missingRefIds.add(refId);
            }
        }
        
        return missingRefIds;
    }
    
    /**
     * Add citations to sentences that make factual claims but lack citations.
     * 
     * @param response The AI response text
     * @param availableCitations List of available citation objects
     * @return Response with added citations where needed
     */
    private String addMissingCitations(String response, List<Citation> availableCitations) {
        // This is a simplified implementation that could be expanded
        // with NLP techniques for better factual claim detection
        
        // For now, we'll assume the AI model has already added necessary citations
        return response;
    }
    
    /**
     * Ensure that citations are context-aware (relevant to the sentence they're attached to).
     * 
     * @param response The AI response text
     * @param availableCitations List of available citation objects
     * @return Response with improved context-aware citations
     */
    private String ensureContextAwareCitations(String response, List<Citation> availableCitations) {
        if (availableCitations.isEmpty()) {
            return response;
        }
        
        // Create a map of reference IDs to citations for quick lookup
        Map<String, Citation> citationMap = new HashMap<>();
        for (Citation citation : availableCitations) {
            citationMap.put(citation.getReferenceId(), citation);
        }
        
        // Extract sentences from the response
        Matcher sentenceMatcher = SENTENCE_PATTERN.matcher(response);
        StringBuffer enhancedResponse = new StringBuffer();
        
        while (sentenceMatcher.find()) {
            String sentence = sentenceMatcher.group(1);
            
            // Check if sentence has a citation
            Matcher citationMatcher = CITATION_PATTERN.matcher(sentence);
            if (citationMatcher.find()) {
                // Sentence already has a citation
                sentenceMatcher.appendReplacement(enhancedResponse, Matcher.quoteReplacement(sentence));
                continue;
            }
            
            // Determine if sentence makes a factual claim
            // This is a simplified check - in a production system,
            // you would use NLP to better identify factual claims
            boolean isFactualClaim = identifyFactualClaim(sentence);
            
            if (isFactualClaim) {
                // Find the most relevant citation for this sentence
                String bestRefId = findMostRelevantCitation(sentence, citationMap);
                
                if (bestRefId != null) {
                    // Add the citation at the end of the sentence
                    String enhancedSentence = sentence.substring(0, sentence.length() - 1) +
                            String.format(" [<sup>%s</sup>]", bestRefId) + sentence.substring(sentence.length() - 1);
                    sentenceMatcher.appendReplacement(enhancedResponse, Matcher.quoteReplacement(enhancedSentence));
                } else {
                    sentenceMatcher.appendReplacement(enhancedResponse, Matcher.quoteReplacement(sentence));
                }
            } else {
                sentenceMatcher.appendReplacement(enhancedResponse, Matcher.quoteReplacement(sentence));
            }
        }
        
        sentenceMatcher.appendTail(enhancedResponse);
        return enhancedResponse.toString();
    }
    
    /**
     * Simplified method to identify if a sentence makes a factual claim.
     * In a production system, this would be much more sophisticated using NLP.
     * 
     * @param sentence The sentence to analyze
     * @return True if the sentence likely contains a factual claim
     */
    private boolean identifyFactualClaim(String sentence) {
        // Simple heuristic check for factual indicators
        // This is a very basic implementation that could be improved
        
        String lowerSentence = sentence.toLowerCase();
        
        // Check for factual markers like tax terms
        return lowerSentence.contains("tax") || 
               lowerSentence.contains("irs") || 
               lowerSentence.contains("deduction") || 
               lowerSentence.contains("credit") || 
               lowerSentence.contains("filing") || 
               lowerSentence.contains("code section") || 
               lowerSentence.contains("regulation");
    }
    
    /**
     * Find the most relevant citation for a given sentence.
     * This is a simplified implementation that could be expanded with 
     * more sophisticated text similarity or ML-based relevance scoring.
     * 
     * @param sentence The sentence requiring citation
     * @param citationMap Map of reference IDs to citation objects
     * @return The most relevant reference ID or null if none are relevant
     */
    private String findMostRelevantCitation(String sentence, Map<String, Citation> citationMap) {
        String bestRefId = null;
        int highestRelevanceScore = 0;
        
        for (Map.Entry<String, Citation> entry : citationMap.entrySet()) {
            String refId = entry.getKey();
            Citation citation = entry.getValue();
            
            // Simple word overlap scoring for relevance
            // In a production system, you would use semantic similarity
            int relevanceScore = calculateRelevanceScore(sentence, citation.getExcerpt());
            
            if (relevanceScore > highestRelevanceScore) {
                highestRelevanceScore = relevanceScore;
                bestRefId = refId;
            }
        }
        
        // Only return the citation if it has a minimum relevance
        return highestRelevanceScore > 2 ? bestRefId : null;
    }
    
    /**
     * Calculate a simple relevance score between a sentence and a document excerpt.
     * This method counts word overlap as a basic relevance metric.
     * 
     * @param sentence The sentence to find a citation for
     * @param excerpt The document excerpt
     * @return Relevance score based on word overlap
     */
    private int calculateRelevanceScore(String sentence, String excerpt) {
        if (sentence == null || excerpt == null) {
            return 0;
        }
        
        // Convert to lowercase and split into words
        String[] sentenceWords = sentence.toLowerCase().split("\\s+");
        String[] excerptWords = excerpt.toLowerCase().split("\\s+");
        
        // Count overlapping words
        int overlapCount = 0;
        for (String sentenceWord : sentenceWords) {
            // Skip very common words and short words
            if (sentenceWord.length() <= 3 || isCommonWord(sentenceWord)) {
                continue;
            }
            
            for (String excerptWord : excerptWords) {
                if (sentenceWord.equals(excerptWord)) {
                    overlapCount++;
                    break;
                }
            }
        }
        
        return overlapCount;
    }
    
    /**
     * Check if a word is a common word that should be excluded from relevance scoring.
     * 
     * @param word The word to check
     * @return True if it's a common word
     */
    private boolean isCommonWord(String word) {
        // List of common words to exclude from relevance calculation
        String[] commonWords = {"the", "and", "that", "have", "for", "not", "with", "you", "this", "but"};
        
        for (String commonWord : commonWords) {
            if (word.equals(commonWord)) {
                return true;
            }
        }
        
        return false;
    }
}

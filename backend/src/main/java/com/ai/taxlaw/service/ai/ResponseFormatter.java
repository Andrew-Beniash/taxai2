package com.ai.taxlaw.service.ai;

import com.ai.taxlaw.model.Citation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Service responsible for formatting AI responses with proper inline citations.
 * This service ensures that responses are properly formatted with citation markers
 * that reference the source documents to maintain accuracy and credibility.
 */
@Service
public class ResponseFormatter {
    
    private static final Logger logger = LoggerFactory.getLogger(ResponseFormatter.class);
    
    // Regex pattern to identify citation markers in the raw AI response
    private static final Pattern CITATION_PATTERN = Pattern.compile("\\[Source: ([^\\]]+)\\]");
    
    /**
     * Format the raw AI response with proper citation formatting.
     * 
     * @param rawResponse The raw response from the OpenAI model
     * @param citations List of citation objects referenced in the response
     * @return Formatted response with properly styled citations
     */
    public String formatResponse(String rawResponse, List<Citation> citations) {
        logger.debug("Formatting raw AI response with citations");
        
        if (rawResponse == null || rawResponse.isEmpty()) {
            return "No response was generated.";
        }
        
        // Step 1: Check if raw response has citation markers
        if (!hasCitationMarkers(rawResponse)) {
            logger.warn("Raw response has no citation markers, adding disclaimer");
            return addCitationDisclaimer(rawResponse);
        }
        
        // Step 2: Format all citation markers with proper styling
        String formattedResponse = formatCitationMarkers(rawResponse, citations);
        
        // Step 3: Add citation footnotes at the end if needed
        return addCitationFootnotes(formattedResponse, citations);
    }
    
    /**
     * Check if the response contains citation markers.
     * 
     * @param response The AI response text
     * @return True if citation markers are found
     */
    private boolean hasCitationMarkers(String response) {
        Matcher matcher = CITATION_PATTERN.matcher(response);
        return matcher.find();
    }
    
    /**
     * Add a disclaimer when citations are missing.
     * 
     * @param response The original response
     * @return Response with added disclaimer
     */
    private String addCitationDisclaimer(String response) {
        return response + "\n\nNote: This response is based on general tax information " +
               "and may not reflect the most current tax laws or regulations. " +
               "Please consult with a tax professional for specific advice.";
    }
    
    /**
     * Format citation markers with proper styling.
     * 
     * @param response The AI response text
     * @param citations Available citation objects
     * @return Formatted response with styled citation markers
     */
    private String formatCitationMarkers(String response, List<Citation> citations) {
        StringBuffer formattedResponse = new StringBuffer();
        Matcher matcher = CITATION_PATTERN.matcher(response);
        
        while (matcher.find()) {
            String referenceId = matcher.group(1);
            
            // Find matching citation
            Citation citation = findCitationByReferenceId(referenceId, citations);
            
            if (citation != null) {
                // Replace with properly formatted citation
                String formattedCitation = String.format("[<sup>%s</sup>]", referenceId);
                matcher.appendReplacement(formattedResponse, formattedCitation);
            } else {
                // Keep original if no match found
                logger.warn("No matching citation found for reference ID: {}", referenceId);
                matcher.appendReplacement(formattedResponse, matcher.group(0));
            }
        }
        
        matcher.appendTail(formattedResponse);
        return formattedResponse.toString();
    }
    
    /**
     * Add citation footnotes at the end of the response.
     * 
     * @param response The formatted response
     * @param citations Available citation objects
     * @return Response with added citation footnotes
     */
    private String addCitationFootnotes(String response, List<Citation> citations) {
        // Skip if no citations are available
        if (citations == null || citations.isEmpty()) {
            return response;
        }
        
        // Check if any citations are actually used in the response
        boolean citationsUsed = false;
        for (Citation citation : citations) {
            if (response.contains("[<sup>" + citation.getReferenceId() + "</sup>]")) {
                citationsUsed = true;
                break;
            }
        }
        
        if (!citationsUsed) {
            return response;
        }
        
        // Add footnotes section
        StringBuilder footnotes = new StringBuilder("\n\n<hr>\n<strong>Sources:</strong>\n<ul>");
        
        for (Citation citation : citations) {
            if (response.contains("[<sup>" + citation.getReferenceId() + "</sup>]")) {
                footnotes.append("\n<li><strong>")
                        .append(citation.getReferenceId())
                        .append(":</strong> ")
                        .append(citation.getSource())
                        .append(", ")
                        .append(citation.getTitle());
                
                if (citation.getUrl() != null && !citation.getUrl().isEmpty()) {
                    footnotes.append(" [<a href=\"")
                            .append(citation.getUrl())
                            .append("\" target=\"_blank\">Link</a>]");
                }
                
                footnotes.append("</li>");
            }
        }
        
        footnotes.append("\n</ul>");
        return response + footnotes.toString();
    }
    
    /**
     * Find a citation by its reference ID.
     * 
     * @param referenceId The reference ID to search for
     * @param citations List of available citations
     * @return Matching citation or null if not found
     */
    private Citation findCitationByReferenceId(String referenceId, List<Citation> citations) {
        for (Citation citation : citations) {
            if (referenceId.equals(citation.getReferenceId())) {
                return citation;
            }
        }
        return null;
    }
}

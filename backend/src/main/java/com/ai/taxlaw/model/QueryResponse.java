package com.ai.taxlaw.model;

import java.util.List;
import java.util.ArrayList;

/**
 * Represents the response to a tax law query.
 * Contains the AI-generated answer along with citations and sources.
 */
public class QueryResponse {
    
    private String answer;
    private String text; // Added for compatibility with browser extension
    private List<Citation> citations;
    private long processingTimeMs;
    
    public QueryResponse() {
        this.citations = new ArrayList<>();
    }
    
    public QueryResponse(String answer) {
        this.answer = answer;
        this.text = answer; // Set text to the same value for browser extension compatibility
        this.citations = new ArrayList<>();
    }
    
    public String getAnswer() {
        return answer;
    }
    
    public void setAnswer(String answer) {
        this.answer = answer;
        this.text = answer; // Keep text in sync with answer
    }
    
    public List<Citation> getCitations() {
        return citations;
    }
    
    public void setCitations(List<Citation> citations) {
        this.citations = citations;
    }
    
    public void addCitation(Citation citation) {
        this.citations.add(citation);
    }
    
    public String getText() {
        return text;
    }
    
    public void setText(String text) {
        this.text = text;
    }
    
    public long getProcessingTimeMs() {
        return processingTimeMs;
    }
    
    public void setProcessingTimeMs(long processingTimeMs) {
        this.processingTimeMs = processingTimeMs;
    }
    
    @Override
    public String toString() {
        return "QueryResponse{" +
                "answer='" + (answer != null ? answer.substring(0, Math.min(50, answer.length())) + "..." : "null") + '\'' +
                ", text='" + (text != null ? text.substring(0, Math.min(50, text.length())) + "..." : "null") + '\'' +
                ", citations=" + citations.size() +
                ", processingTimeMs=" + processingTimeMs +
                '}';
    }
}

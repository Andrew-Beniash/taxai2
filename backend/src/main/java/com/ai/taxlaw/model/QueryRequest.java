package com.ai.taxlaw.model;

/**
 * Represents a query request from the client.
 * Contains the user's tax-related query text and optional context information.
 */
public class QueryRequest {
    
    private String query;
    private String context;
    
    // Default constructor for JSON deserialization
    public QueryRequest() {
    }
    
    public QueryRequest(String query, String context) {
        this.query = query;
        this.context = context;
    }
    
    public String getQuery() {
        return query;
    }
    
    public void setQuery(String query) {
        this.query = query;
    }
    
    public String getContext() {
        return context;
    }
    
    public void setContext(String context) {
        this.context = context;
    }
    
    @Override
    public String toString() {
        return "QueryRequest{" +
                "query='" + query + '\'' +
                ", context='" + (context != null ? "provided" : "not provided") + '\'' +
                '}';
    }
}

package com.ai.taxlaw.model;

/**
 * Represents a citation to a tax law source.
 * Used to back AI responses with authoritative references.
 */
public class Citation {
    
    private String source;
    private String title;
    private String excerpt;
    private String url;
    private String referenceId;
    
    public Citation() {
    }
    
    public Citation(String source, String title, String excerpt, String url, String referenceId) {
        this.source = source;
        this.title = title;
        this.excerpt = excerpt;
        this.url = url;
        this.referenceId = referenceId;
    }
    
    public String getSource() {
        return source;
    }
    
    public void setSource(String source) {
        this.source = source;
    }
    
    public String getTitle() {
        return title;
    }
    
    public void setTitle(String title) {
        this.title = title;
    }
    
    public String getExcerpt() {
        return excerpt;
    }
    
    public void setExcerpt(String excerpt) {
        this.excerpt = excerpt;
    }
    
    public String getUrl() {
        return url;
    }
    
    public void setUrl(String url) {
        this.url = url;
    }
    
    public String getReferenceId() {
        return referenceId;
    }
    
    public void setReferenceId(String referenceId) {
        this.referenceId = referenceId;
    }
    
    @Override
    public String toString() {
        return "Citation{" +
                "source='" + source + '\'' +
                ", title='" + title + '\'' +
                ", referenceId='" + referenceId + '\'' +
                '}';
    }
}

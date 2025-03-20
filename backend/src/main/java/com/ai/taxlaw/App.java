package com.ai.taxlaw;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Main application class for the AI-Powered Tax Law Assistant backend.
 * This service provides REST endpoints for querying tax information using a
 * Retrieval-Augmented Generation (RAG) system.
 */
@SpringBootApplication
public class App {
    
    private static final Logger logger = LoggerFactory.getLogger(App.class);
    
    public static void main(String[] args) {
        logger.info("Starting AI Tax Law Assistant backend service...");
        SpringApplication.run(App.class, args);
        logger.info("AI Tax Law Assistant backend service started successfully.");
    }
}

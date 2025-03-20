package com.ai.taxlaw.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

/**
 * Configuration for the OpenAI integration.
 * Sets up beans needed for communicating with the OpenAI API.
 */
@Configuration
public class OpenAIConfig {
    
    /**
     * Create a RestTemplate bean for making HTTP requests to the OpenAI API.
     * 
     * @return A configured RestTemplate instance
     */
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}

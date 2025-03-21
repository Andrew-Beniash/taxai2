package com.ai.taxlaw.service.ai;

import com.ai.taxlaw.model.Citation;
import com.ai.taxlaw.service.OpenAIService;
import com.ai.taxlaw.service.RAGClient;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

/**
 * Unit tests for the AIModelService class.
 * Tests the integration between RAG and OpenAI for accurate, citation-backed responses.
 */
class AIModelServiceTest {

    @Mock
    private RAGClient ragClient;

    @Mock
    private OpenAIService openAIService;

    @Mock
    private ResponseFormatter responseFormatter;

    @Mock
    private CitationManager citationManager;

    @InjectMocks
    private AIModelService aiModelService;

    private List<Citation> testCitations;
    private String testRawResponse;
    private String testFormattedResponse;
    private String testValidatedResponse;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);

        // Set up test data
        testCitations = Arrays.asList(
            new Citation(
                "IRS",
                "Publication 17: Your Federal Income Tax",
                "For use in preparing 2023 Returns",
                "https://www.irs.gov/pub/irs-pdf/p17.pdf",
                "pub17_2023"
            ),
            new Citation(
                "US Tax Code",
                "26 U.S. Code § 61 - Gross income defined",
                "Gross income means all income from whatever source derived...",
                "https://www.law.cornell.edu/uscode/text/26/61",
                "usc_26_61"
            )
        );

        testRawResponse = "Based on IRS Publication 17 [Source: pub17_2023], you need to report all income.";
        testFormattedResponse = "Based on IRS Publication 17 [<sup>pub17_2023</sup>], you need to report all income.";
        testValidatedResponse = testFormattedResponse + "\n\n<hr>\n<strong>Sources:</strong>\n<ul>\n<li><strong>pub17_2023:</strong> IRS, Publication 17: Your Federal Income Tax [<a href=\"https://www.irs.gov/pub/irs-pdf/p17.pdf\" target=\"_blank\">Link</a>]</li>\n</ul>";

        // Set up mock behaviors
        when(ragClient.retrieveRelevantDocuments(anyString())).thenReturn(testCitations);
        when(openAIService.generateResponse(anyString(), anyString())).thenReturn(testRawResponse);
        when(responseFormatter.formatResponse(anyString(), anyList())).thenReturn(testFormattedResponse);
        when(citationManager.validateAndEnrichCitations(anyString(), anyList())).thenReturn(testValidatedResponse);
    }

    @Test
    void generateResponse_Success() {
        // Test the happy path
        String query = "How is gross income defined for tax purposes?";
        String result = aiModelService.generateResponse(query);

        // Verify the expected interactions
        verify(ragClient).retrieveRelevantDocuments(query);
        verify(openAIService).generateResponse(eq(query), anyString());
        verify(responseFormatter).formatResponse(testRawResponse, testCitations);
        verify(citationManager).validateAndEnrichCitations(testFormattedResponse, testCitations);

        // Assert the result
        assertEquals(testValidatedResponse, result);
    }

    @Test
    void generateResponse_NoRelevantDocuments() {
        // Test the case where no relevant documents are found
        String query = "Non-tax related query";
        when(ragClient.retrieveRelevantDocuments(query)).thenReturn(Arrays.asList());

        String result = aiModelService.generateResponse(query);

        // Should not call OpenAI if no documents found
        verify(ragClient).retrieveRelevantDocuments(query);
        verify(openAIService, never()).generateResponse(anyString(), anyString());
        verify(responseFormatter, never()).formatResponse(anyString(), anyList());
        verify(citationManager, never()).validateAndEnrichCitations(anyString(), anyList());

        // Assert that a helpful message is returned
        assertTrue(result.contains("couldn't find specific tax law information"));
    }

    @Test
    void generateResponse_ErrorHandling() {
        // Test error handling
        String query = "Tax question that causes an error";
        when(ragClient.retrieveRelevantDocuments(query)).thenThrow(new RuntimeException("Test exception"));

        String result = aiModelService.generateResponse(query);

        // Verify error handling
        verify(ragClient).retrieveRelevantDocuments(query);
        verify(openAIService, never()).generateResponse(anyString(), anyString());

        // Assert that an error message is returned
        assertTrue(result.contains("technical issue"));
    }
}

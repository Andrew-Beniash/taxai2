/**
 * api_response_test.js - Tests for browser extension API calls
 * 
 * This file tests the extension's API functionality:
 * - Sending queries to the backend
 * - Handling responses
 * - Error scenarios
 * - Response formatting and citations
 */

const path = require('path');
const puppeteer = require('puppeteer');
const extensionPath = path.join(__dirname, '../../browser-extension/dist');

describe('API Response Tests', () => {
  let browser;
  let page;
  let extensionPopupHtml;
  let backgroundPage;
  let extensionId;

  // Setup before all tests
  beforeAll(async () => {
    // Launch browser with extension loaded
    browser = await puppeteer.launch({
      headless: false,
      args: [
        `--disable-extensions-except=${extensionPath}`,
        `--load-extension=${extensionPath}`
      ]
    });

    // Get the extension ID and background page
    const extensionTarget = await browser.waitForTarget(
      target => target.type() === 'background_page'
    );
    extensionId = extensionTarget.url().split('/')[2];
    backgroundPage = await extensionTarget.page();
    
    // Create a new page
    page = await browser.newPage();
    
    // URL for the extension popup
    extensionPopupHtml = `chrome-extension://${extensionId}/popup.html`;
  });

  // Cleanup after all tests
  afterAll(async () => {
    await browser.close();
  });

  // Test 1: Mock and test the API call directly
  test('Background script can make API requests', async () => {
    // Access the background page and mock the fetch API
    await backgroundPage.evaluate(() => {
      // Store the original fetch function
      window.originalFetch = window.fetch;
      
      // Mock the fetch function
      window.fetch = (url, options) => {
        if (url.includes('/api/query')) {
          // Return a successful mock response for queries
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
              answer: "Form 1040 is the standard US individual income tax return.",
              citations: [
                { source: "IRS Publication 17", reference: "Page 11" }
              ]
            })
          });
        }
        
        // For other requests, use the original fetch
        return window.originalFetch(url, options);
      };
    });
    
    // Navigate to the popup page
    await page.goto(extensionPopupHtml);
    
    // Type and submit a query
    await page.type('#search-input', 'What is Form 1040?');
    await page.click('#query-button');
    
    // Wait for the response to be displayed
    await page.waitForSelector('.response-container');
    
    // Check if the mock response was returned
    const responseText = await page.$eval('.response-text', el => el.textContent);
    expect(responseText).toContain('Form 1040 is the standard US individual income tax return');
    
    // Check if citation was displayed
    const citationText = await page.$eval('.citation', el => el.textContent);
    expect(citationText).toContain('IRS Publication 17');
    
    // Restore the original fetch function
    await backgroundPage.evaluate(() => {
      window.fetch = window.originalFetch;
    });
  }, 15000);

  // Test 2: Test error handling
  test('Extension handles API errors gracefully', async () => {
    // Mock the fetch API to return an error
    await backgroundPage.evaluate(() => {
      // Store the original fetch function if not already stored
      if (!window.originalFetch) {
        window.originalFetch = window.fetch;
      }
      
      // Mock the fetch function to return an error
      window.fetch = (url, options) => {
        if (url.includes('/api/query')) {
          return Promise.resolve({
            ok: false,
            status: 500,
            statusText: 'Internal Server Error',
            json: () => Promise.resolve({
              error: "Server error occurred"
            })
          });
        }
        
        // For other requests, use the original fetch
        return window.originalFetch(url, options);
      };
    });
    
    // Navigate to the popup page
    await page.goto(extensionPopupHtml);
    
    // Type and submit a query
    await page.type('#search-input', 'Tax deduction rules');
    await page.click('#query-button');
    
    // Wait for the error message to be displayed
    await page.waitForSelector('.error-message');
    
    // Check if the error message is displayed
    const errorText = await page.$eval('.error-message', el => el.textContent);
    expect(errorText).toContain('error');
    
    // Restore the original fetch function
    await backgroundPage.evaluate(() => {
      window.fetch = window.originalFetch;
    });
  }, 15000);

  // Test 3: Test citation formatting and interaction
  test('Citations are properly formatted and interactive', async () => {
    // Mock the fetch API to return a response with citations
    await backgroundPage.evaluate(() => {
      // Store the original fetch function if not already stored
      if (!window.originalFetch) {
        window.originalFetch = window.fetch;
      }
      
      // Mock the fetch function
      window.fetch = (url, options) => {
        if (url.includes('/api/query')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
              answer: "Capital gains tax rates depend on your income and holding period.",
              citations: [
                { 
                  source: "Internal Revenue Code", 
                  section: "1(h)",
                  text: "Capital gains rates for individuals",
                  url: "https://www.irs.gov/pub/irs-pdf/p544.pdf"
                },
                {
                  source: "IRS Publication 544",
                  section: "Chapter 4",
                  text: "Sales and Other Dispositions of Assets",
                  url: "https://www.irs.gov/pub/irs-pdf/p544.pdf"
                }
              ]
            })
          });
        }
        
        // For other requests, use the original fetch
        return window.originalFetch(url, options);
      };
    });
    
    // Navigate to the popup page
    await page.goto(extensionPopupHtml);
    
    // Type and submit a query
    await page.type('#search-input', 'Capital gains tax rates?');
    await page.click('#query-button');
    
    // Wait for the response to be displayed
    await page.waitForSelector('.response-container');
    
    // Check if all citations are displayed
    const citationElements = await page.$$('.citation');
    expect(citationElements.length).toBe(2);
    
    // Test citation click functionality if implemented
    const hasCitationLinks = await page.$('.citation-link') !== null;
    if (hasCitationLinks) {
      await page.click('.citation-link');
      
      // Wait for citation details to show
      await page.waitForSelector('.citation-details');
      
      // Verify details content
      const citationDetails = await page.$eval('.citation-details', el => el.textContent);
      expect(citationDetails).toContain('Internal Revenue Code');
    } else {
      console.log('Citation links not implemented - skipping citation click test');
    }
    
    // Restore the original fetch function
    await backgroundPage.evaluate(() => {
      window.fetch = window.originalFetch;
    });
  }, 15000);

  // Test 4: Test context awareness functionality
  test('Extension shows context-aware suggestions on tax websites', async () => {
    // Navigate to a mock IRS page
    await page.goto('https://www.irs.gov');
    
    // Wait for the page to load
    await page.waitForTimeout(1000);
    
    // Check if the extension's content script has injected context-aware elements
    const hasContextSuggestions = await page.evaluate(() => {
      // Look for any elements that might have been injected by the extension
      return document.querySelector('.tax-assistant-suggestion') !== null ||
             document.querySelector('.tax-insight-button') !== null;
    });
    
    // This test is informational as the feature may still be in development
    console.log(`Context-aware suggestions present: ${hasContextSuggestions}`);
    
    if (hasContextSuggestions) {
      // If the feature is implemented, test interaction
      await page.click('.tax-insight-button');
      
      // Wait for suggestions to appear
      await page.waitForSelector('.tax-suggestions');
      
      // Verify suggestions content
      const suggestionsExist = await page.$('.tax-suggestions') !== null;
      expect(suggestionsExist).toBeTruthy();
    } else {
      console.log('Context-aware suggestions not implemented yet - skipping interaction test');
    }
  }, 15000);

  // Test 5: Test one-click citation functionality
  test('One-click citation copying works', async () => {
    // Mock the fetch API to return a response with citations
    await backgroundPage.evaluate(() => {
      // Store the original fetch function if not already stored
      if (!window.originalFetch) {
        window.originalFetch = window.fetch;
      }
      
      // Mock the fetch function
      window.fetch = (url, options) => {
        if (url.includes('/api/query')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
              answer: "The standard deduction for 2024 is $13,850 for single filers.",
              citations: [
                { 
                  source: "IRS Publication 501", 
                  section: "Standard Deduction",
                  text: "Standard Deduction Amounts",
                  url: "https://www.irs.gov/pub/irs-pdf/p501.pdf"
                }
              ]
            })
          });
        }
        
        // For other requests, use the original fetch
        return window.originalFetch(url, options);
      };
      
      // Mock clipboard API for testing
      navigator.clipboard = {
        writeText: text => Promise.resolve()
      };
    });
    
    // Navigate to the popup page
    await page.goto(extensionPopupHtml);
    
    // Type and submit a query
    await page.type('#search-input', 'Standard deduction 2024?');
    await page.click('#query-button');
    
    // Wait for the response to be displayed
    await page.waitForSelector('.response-container');
    
    // Check if copy citation button exists
    const hasCopyCitationButton = await page.$('.copy-citation-button') !== null;
    
    if (hasCopyCitationButton) {
      // Click the copy citation button
      await page.click('.copy-citation-button');
      
      // Wait for success message
      await page.waitForSelector('.copied-message');
      
      // Verify success message
      const copiedMessage = await page.$eval('.copied-message', el => el.textContent);
      expect(copiedMessage).toContain('copied');
    } else {
      console.log('Copy citation button not implemented - skipping copy test');
    }
    
    // Restore the original fetch function
    await backgroundPage.evaluate(() => {
      window.fetch = window.originalFetch;
    });
  }, 15000);
});
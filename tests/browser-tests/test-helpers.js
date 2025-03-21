/**
 * test-helpers.js - Helper functions for browser extension UI tests
 * 
 * This file contains utility functions to assist with testing common 
 * browser extension scenarios.
 */

/**
 * Helper to create a mock memo database for testing
 * @param {Object} page - Puppeteer page object
 * @param {Array} memos - Array of memo objects to add
 */
async function seedMemoDatabase(page, memos = []) {
  await page.evaluate((testMemos) => {
    return new Promise((resolve, reject) => {
      // Open or create the IndexedDB database
      const request = indexedDB.open('taxAssistantMemos', 1);
      
      // Handle database creation/upgrade
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Create object store if it doesn't exist
        if (!db.objectStoreNames.contains('memos')) {
          const objectStore = db.createObjectStore('memos', { keyPath: 'id', autoIncrement: true });
          objectStore.createIndex('title', 'title', { unique: false });
          objectStore.createIndex('category', 'category', { unique: false });
        }
      };
      
      request.onerror = () => reject(new Error("Failed to open database"));
      
      request.onsuccess = (event) => {
        const db = event.target.result;
        const transaction = db.transaction(['memos'], 'readwrite');
        const objectStore = transaction.objectStore('memos');
        
        // Clear existing data
        objectStore.clear();
        
        // Add each test memo
        let completed = 0;
        testMemos.forEach((memo) => {
          const addRequest = objectStore.add(memo);
          addRequest.onsuccess = () => {
            completed++;
            if (completed === testMemos.length) {
              resolve();
            }
          };
          addRequest.onerror = () => reject(new Error("Failed to add test memo"));
        });
        
        // If no memos to add, resolve immediately
        if (testMemos.length === 0) {
          resolve();
        }
      };
    });
  }, memos);
}

/**
 * Helper to clear the memo database
 * @param {Object} page - Puppeteer page object
 */
async function clearMemoDatabase(page) {
  await page.evaluate(() => {
    return new Promise((resolve, reject) => {
      const request = indexedDB.deleteDatabase('taxAssistantMemos');
      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error("Could not clear memo database"));
    });
  });
}

/**
 * Helper to mock the API response
 * @param {Object} page - Puppeteer page object
 * @param {Object} mockResponse - The mock response to return
 */
async function mockApiResponse(page, mockResponse) {
  await page.evaluate((response) => {
    // Store the original fetch function
    window.originalFetch = window.fetch;
    
    // Replace with mock
    window.fetch = (url, options) => {
      if (url.includes('/api/query')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(response)
        });
      }
      
      // Use original for other requests
      return window.originalFetch(url, options);
    };
  }, mockResponse);
}

/**
 * Helper to restore the original fetch function
 * @param {Object} page - Puppeteer page object
 */
async function restoreApiFetch(page) {
  await page.evaluate(() => {
    if (window.originalFetch) {
      window.fetch = window.originalFetch;
    }
  });
}

/**
 * Helper to wait for network idle (useful for API calls)
 * @param {Object} page - Puppeteer page object
 * @param {Number} timeout - Timeout in milliseconds
 */
async function waitForNetworkIdle(page, timeout = 5000) {
  await page.waitForNetworkIdle({ idleTime: 500, timeout });
}

/**
 * Helper to get the extension popup URL
 * @param {Object} browser - Puppeteer browser object
 * @returns {Promise<string>} - The extension popup URL
 */
async function getExtensionPopupUrl(browser) {
  const extensionTarget = await browser.waitForTarget(
    target => target.type() === 'background_page'
  );
  const extensionId = extensionTarget.url().split('/')[2];
  return `chrome-extension://${extensionId}/popup.html`;
}

// Export all helper functions
module.exports = {
  seedMemoDatabase,
  clearMemoDatabase,
  mockApiResponse,
  restoreApiFetch,
  waitForNetworkIdle,
  getExtensionPopupUrl
};
/**
 * memo_storage_test.js - Tests for memo storage functionality
 * 
 * This file tests the functionality of quick memos within the extension:
 * - Creating and saving new memos
 * - Retrieving stored memos
 * - Categorizing and organizing memos
 * - Testing IndexedDB storage functionality
 */

const path = require('path');
const puppeteer = require('puppeteer');
const extensionPath = path.join(__dirname, '../../browser-extension/dist');

describe('Memo Storage Tests', () => {
  let browser;
  let page;
  let extensionPopupHtml;
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

    // Get the extension ID
    const extensionTarget = await browser.waitForTarget(
      target => target.type() === 'background_page'
    );
    extensionId = extensionTarget.url().split('/')[2];
    
    // Create a new page
    page = await browser.newPage();
    
    // URL for the extension popup
    extensionPopupHtml = `chrome-extension://${extensionId}/popup.html`;
  });

  // Cleanup after all tests
  afterAll(async () => {
    await browser.close();
  });

  // Helper function to clear IndexedDB data for clean tests
  async function clearMemoStorage() {
    await page.evaluate(() => {
      return new Promise((resolve, reject) => {
        const request = indexedDB.deleteDatabase('taxAssistantMemos');
        request.onsuccess = () => resolve();
        request.onerror = () => reject(new Error("Could not clear memo database"));
      });
    });
  }

  // Test 1: Create and save a new memo
  test('Can create and save a new memo', async () => {
    await page.goto(extensionPopupHtml);
    
    // Wait for the page to fully load
    await page.waitForSelector('#search-input');
    
    // Check if there's a memo creation button
    const hasMemoButton = await page.$('#create-memo-button') !== null;
    expect(hasMemoButton).toBeTruthy();
    
    // Click the create memo button
    await page.click('#create-memo-button');
    
    // Wait for the memo modal to appear
    await page.waitForSelector('#memo-modal');
    
    // Fill in memo title and content
    await page.type('#memo-title', 'Test Memo');
    await page.type('#memo-content', 'This is a test memo for automated testing');
    
    // Select a category if available
    const hasCategoryDropdown = await page.$('#memo-category') !== null;
    if (hasCategoryDropdown) {
      await page.select('#memo-category', 'tax-deductions');
    }
    
    // Save the memo
    await page.click('#save-memo-button');
    
    // Wait for success message
    await page.waitForSelector('.success-message');
    
    // Verify success message content
    const successMessage = await page.$eval('.success-message', el => el.textContent);
    expect(successMessage).toContain('Memo saved');
  }, 15000);

  // Test 2: Retrieve stored memos
  test('Can retrieve stored memos', async () => {
    await page.goto(extensionPopupHtml);
    
    // Wait for the page to fully load
    await page.waitForSelector('#search-input');
    
    // Click on the view memos button
    await page.click('#view-memos-button');
    
    // Wait for the memos list to load
    await page.waitForSelector('.memo-list');
    
    // Check if our test memo exists in the list
    const memoExists = await page.evaluate(() => {
      const memoItems = document.querySelectorAll('.memo-item');
      for (const memo of memoItems) {
        if (memo.querySelector('.memo-title').textContent.includes('Test Memo')) {
          return true;
        }
      }
      return false;
    });
    
    expect(memoExists).toBeTruthy();
  }, 15000);

  // Test 3: Verify memo categorization
  test('Memos can be categorized and filtered', async () => {
    await page.goto(extensionPopupHtml);
    
    // Navigate to the memos view
    await page.click('#view-memos-button');
    await page.waitForSelector('.memo-list');
    
    // Check if category filter exists
    const hasCategoryFilter = await page.$('#category-filter') !== null;
    
    if (hasCategoryFilter) {
      // Select the category we used when creating the memo
      await page.select('#category-filter', 'tax-deductions');
      
      // Wait for the list to update
      await page.waitForTimeout(500);
      
      // Verify our test memo is still visible after filtering
      const memoVisibleAfterFilter = await page.evaluate(() => {
        const memoItems = document.querySelectorAll('.memo-item:not(.hidden)');
        for (const memo of memoItems) {
          if (memo.querySelector('.memo-title').textContent.includes('Test Memo')) {
            return true;
          }
        }
        return false;
      });
      
      expect(memoVisibleAfterFilter).toBeTruthy();
    } else {
      console.log('Category filtering not implemented - skipping category filter test');
    }
  }, 15000);

  // Test 4: Test IndexedDB storage directly
  test('Memos are properly stored in IndexedDB', async () => {
    // Check if memo was correctly stored in IndexedDB
    const storedMemo = await page.evaluate(() => {
      return new Promise((resolve, reject) => {
        const request = indexedDB.open('taxAssistantMemos', 1);
        
        request.onerror = () => reject(new Error("Failed to open database"));
        
        request.onsuccess = (event) => {
          const db = event.target.result;
          const transaction = db.transaction(['memos'], 'readonly');
          const objectStore = transaction.objectStore('memos');
          
          // Get all memos
          const getAllRequest = objectStore.getAll();
          
          getAllRequest.onsuccess = () => {
            const memos = getAllRequest.result;
            resolve(memos.find(memo => memo.title === 'Test Memo'));
          };
          
          getAllRequest.onerror = () => reject(new Error("Failed to retrieve memos"));
        };
      });
    });
    
    // Verify the memo was stored correctly
    expect(storedMemo).toBeDefined();
    expect(storedMemo.title).toBe('Test Memo');
    expect(storedMemo.content).toBe('This is a test memo for automated testing');
  }, 15000);

  // Test 5: Test memo deletion
  test('Can delete a memo', async () => {
    await page.goto(extensionPopupHtml);
    
    // Navigate to the memos view
    await page.click('#view-memos-button');
    await page.waitForSelector('.memo-list');
    
    // Find and click the delete button for our test memo
    await page.evaluate(() => {
      const memoItems = document.querySelectorAll('.memo-item');
      for (const memo of memoItems) {
        if (memo.querySelector('.memo-title').textContent.includes('Test Memo')) {
          memo.querySelector('.delete-memo-button').click();
          return;
        }
      }
    });
    
    // Confirm deletion in modal if it exists
    const hasConfirmDialog = await page.$('.confirm-dialog') !== null;
    if (hasConfirmDialog) {
      await page.click('#confirm-delete-button');
    }
    
    // Wait for success message
    await page.waitForSelector('.success-message');
    
    // Wait for the list to update
    await page.waitForTimeout(500);
    
    // Verify the memo was deleted
    const memoStillExists = await page.evaluate(() => {
      const memoItems = document.querySelectorAll('.memo-item');
      for (const memo of memoItems) {
        if (memo.querySelector('.memo-title').textContent.includes('Test Memo')) {
          return true;
        }
      }
      return false;
    });
    
    expect(memoStillExists).toBeFalsy();
  }, 15000);

  // Clean up our test data
  afterAll(async () => {
    await clearMemoStorage();
  });
});
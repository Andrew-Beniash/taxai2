/**
 * Tax Law Assistant - Background Script
 * 
 * This background script handles:
 * 1. Communication with the backend API
 * 2. Setting up context menu items for text selection
 * 3. Coordinating between popup and content scripts
 */

// Configuration
const API_BASE_URL = 'http://localhost:8080/api';

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
  console.log('Tax Law Assistant Extension installed');
  
  // Create context menu items
  chrome.contextMenus.create({
    id: 'queryTaxAI',
    title: 'Ask Tax AI about this',
    contexts: ['selection']
  });
  
  chrome.contextMenus.create({
    id: 'saveTaxMemo',
    title: 'Save as Tax Memo',
    contexts: ['selection']
  });
  
  // Set default options
  chrome.storage.sync.set({
    highlightEnabled: true,
    apiEndpoint: API_BASE_URL
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'queryTaxAI' && info.selectionText) {
    // Query the AI about the selected text
    const query = info.selectionText.trim();
    
    // Send message to the active tab's content script
    chrome.tabs.sendMessage(tab.id, {
      action: 'showLoadingIndicator'
    });
    
    // Query AI
    queryAI(query, { sourceUrl: info.pageUrl })
      .then(response => {
        // Send response to content script to show in sidebar
        chrome.tabs.sendMessage(tab.id, {
          action: 'showSidebar',
          query: query,
          response: response
        });
      })
      .catch(error => {
        console.error('Error querying AI:', error);
        chrome.tabs.sendMessage(tab.id, {
          action: 'showError',
          error: 'Failed to get a response from the AI. Please try again.'
        });
      });
  }
  
  if (info.menuItemId === 'saveTaxMemo' && info.selectionText) {
    // Save the selected text as a memo
    const memo = {
      id: Date.now(),
      title: `Selection from ${new URL(info.pageUrl).hostname}`,
      category: 'general',
      content: info.selectionText.trim(),
      citations: [
        {
          source: new URL(info.pageUrl).hostname,
          reference: info.pageUrl
        }
      ],
      createdAt: new Date().toISOString()
    };
    
    // Save memo to IndexedDB
    saveMemo(memo);
    
    // Show notification
    chrome.tabs.sendMessage(tab.id, {
      action: 'showNotification',
      message: 'Text saved as memo!'
    });
  }
});

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Handle AI queries
  if (message.action === 'queryAI') {
    queryAI(message.query, message.context || {})
      .then(response => {
        sendResponse(response);
      })
      .catch(error => {
        console.error('Error querying AI:', error);
        sendResponse({
          error: 'Failed to get a response from the AI. Please try again.'
        });
      });
    
    // Return true to indicate we'll respond asynchronously
    return true;
  }
  
  // Handle memo saving from content script
  if (message.action === 'saveMemo') {
    saveMemo(message.memo)
      .then(() => {
        sendResponse({ success: true });
      })
      .catch(error => {
        console.error('Error saving memo:', error);
        sendResponse({ 
          success: false, 
          error: 'Failed to save memo.' 
        });
      });
    
    return true;
  }
  
  // Handle text selection events from content script
  if (message.action === 'textSelected') {
    // Could be used to show a UI badge or suggestion
    console.log('Text selected:', message.text.substring(0, 50) + '...');
    
    // No response needed
    return false;
  }
});

/**
 * Query the AI with the given text
 * 
 * @param {string} query - The query text
 * @param {Object} context - Additional context data
 * @returns {Promise} Promise resolving to the AI response
 */
async function queryAI(query, context = {}) {
  try {
    // Get API endpoint from settings
    const settings = await new Promise(resolve => {
      chrome.storage.sync.get({
        apiEndpoint: API_BASE_URL
      }, resolve);
    });
    
    // Make API request
    const response = await fetch(`${settings.apiEndpoint}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: query,
        context: context
      })
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }
    
    const data = await response.json();
    
    // Format response for the UI
    return {
      text: data.text || data.response || 'No response received from the server.',
      citations: data.citations || []
    };
  } catch (error) {
    console.error('Error in queryAI:', error);
    
    // In development, return mock data if API fails
    if (process.env.NODE_ENV === 'development') {
      return getMockResponse(query);
    }
    
    throw error;
  }
}

/**
 * Save a memo using Chrome storage
 * 
 * @param {Object} memo - The memo to save
 * @returns {Promise} Promise resolving when the memo is saved
 */
async function saveMemo(memo) {
  return new Promise((resolve, reject) => {
    // We'll use the popup's IndexedDB by opening the popup
    chrome.runtime.sendMessage({
      action: 'storeBackgroundMemo',
      memo: memo
    }, response => {
      if (chrome.runtime.lastError) {
        // If popup is not open, we'll open it and then try again
        chrome.action.openPopup(() => {
          // Slight delay to ensure popup is loaded
          setTimeout(() => {
            chrome.runtime.sendMessage({
              action: 'storeBackgroundMemo',
              memo: memo
            }, secondResponse => {
              if (chrome.runtime.lastError) {
                reject(chrome.runtime.lastError);
              } else {
                resolve(secondResponse);
              }
            });
          }, 300);
        });
      } else {
        resolve(response);
      }
    });
  });
}

/**
 * Get a mock response for development
 * 
 * @param {string} query - The query text
 * @returns {Object} Mock response
 */
function getMockResponse(query) {
  return {
    text: `This is a simulated AI response to your query: "${query.substring(0, 50)}...". 
    In a real implementation, this would be replaced with responses from the backend API 
    that accesses the RAG database and OpenAI models.`,
    citations: [
      {
        source: 'IRS Publication 17',
        reference: 'Your Federal Income Tax (2022), Page 89'
      },
      {
        source: 'Tax Court Case',
        reference: 'TC Memo 2021-135'
      }
    ]
  };
}

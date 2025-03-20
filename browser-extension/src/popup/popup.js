/**
 * Tax Law Assistant - Popup Script
 * 
 * This script handles the popup UI interactions, including:
 * - Sending queries to the AI via the background script
 * - Displaying AI responses with citations
 * - Managing the tabs (Ask/Memos)
 * - Saving and viewing quick memos
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const queryInput = document.getElementById('query-input');
  const searchButton = document.getElementById('search-button');
  const loadingIndicator = document.getElementById('loading-indicator');
  const resultContent = document.getElementById('result-content');
  const responseText = document.getElementById('response-text');
  const citationsList = document.getElementById('citations-list');
  const saveMemoButton = document.getElementById('save-memo-button');
  const copyButton = document.getElementById('copy-button');
  const tabButtons = document.querySelectorAll('.tab-button');
  const memosContainer = document.getElementById('memos-container');
  const memosList = document.getElementById('memos-list');
  const clearMemosButton = document.getElementById('clear-memos');
  
  // Modal elements
  const memoModal = document.getElementById('memo-modal');
  const closeModal = document.querySelector('.close-modal');
  const memoTitle = document.getElementById('memo-title');
  const memoCategory = document.getElementById('memo-category');
  const confirmSaveMemo = document.getElementById('confirm-save-memo');
  
  // Current state
  let currentResponse = '';
  let currentCitations = [];
  
  // Initialize
  loadMemos();
  
  // Event Listeners
  searchButton.addEventListener('click', handleSearch);
  queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  });
  
  saveMemoButton.addEventListener('click', () => {
    showMemoModal();
  });
  
  copyButton.addEventListener('click', () => {
    copyToClipboard(currentResponse);
    showNotification('Response copied to clipboard!');
  });
  
  // Tab switching
  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      tabButtons.forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
      
      if (button.dataset.tab === 'memos') {
        memosContainer.classList.remove('hidden');
        resultContent.classList.add('hidden');
        loadingIndicator.classList.add('hidden');
      } else {
        memosContainer.classList.add('hidden');
        if (currentResponse) {
          resultContent.classList.remove('hidden');
        }
      }
    });
  });
  
  // Modal events
  closeModal.addEventListener('click', () => {
    memoModal.classList.add('hidden');
  });
  
  confirmSaveMemo.addEventListener('click', saveMemo);
  
  clearMemosButton.addEventListener('click', () => {
    if (confirm('Are you sure you want to clear all memos?')) {
      clearAllMemos();
    }
  });
  
  // Window click to close modal
  window.addEventListener('click', (e) => {
    if (e.target === memoModal) {
      memoModal.classList.add('hidden');
    }
  });
  
  /**
   * Handle search query submission
   */
  function handleSearch() {
    const query = queryInput.value.trim();
    
    if (!query) {
      showNotification('Please enter a question.');
      return;
    }
    
    // Show loading state
    loadingIndicator.classList.remove('hidden');
    resultContent.classList.add('hidden');
    
    // Send message to background script
    chrome.runtime.sendMessage(
      { 
        action: 'queryAI', 
        query: query 
      },
      (response) => {
        if (chrome.runtime.lastError) {
          handleError('Failed to connect to the AI service. Please try again.');
          return;
        }
        
        // Handle response
        handleAIResponse(response);
      }
    );
  }
  
  /**
   * Process and display AI response
   */
  function handleAIResponse(response) {
    loadingIndicator.classList.add('hidden');
    
    if (response.error) {
      handleError(response.error);
      return;
    }
    
    // Display response
    resultContent.classList.remove('hidden');
    responseText.innerHTML = response.text;
    
    // Store current response for later use
    currentResponse = response.text;
    currentCitations = response.citations || [];
    
    // Display citations if available
    citationsList.innerHTML = '';
    if (currentCitations.length > 0) {
      currentCitations.forEach(citation => {
        const citationItem = document.createElement('div');
        citationItem.className = 'citation-item';
        citationItem.textContent = citation.source + ' - ' + citation.reference;
        citationsList.appendChild(citationItem);
      });
    } else {
      citationsList.textContent = 'No specific citations for this response.';
    }
  }
  
  /**
   * Show memo save modal
   */
  function showMemoModal() {
    memoTitle.value = generateMemoTitle();
    memoModal.classList.remove('hidden');
  }
  
  /**
   * Generate a default title for the memo based on current date
   */
  function generateMemoTitle() {
    const now = new Date();
    return `Tax Question - ${now.toLocaleDateString()}`;
  }
  
  /**
   * Save memo to IndexedDB
   */
  function saveMemo() {
    const title = memoTitle.value.trim() || generateMemoTitle();
    const category = memoCategory.value;
    
    const memo = {
      id: Date.now(),
      title: title,
      category: category,
      content: currentResponse,
      citations: currentCitations,
      createdAt: new Date().toISOString()
    };
    
    // Save to IndexedDB
    saveMemoToDb(memo, () => {
      memoModal.classList.add('hidden');
      showNotification('Memo saved successfully!');
      
      // If on memos tab, refresh the list
      if (document.querySelector('.tab-button[data-tab="memos"]').classList.contains('active')) {
        loadMemos();
      }
    });
  }
  
  /**
   * Load and display saved memos
   */
  function loadMemos() {
    getMemos((memos) => {
      memosList.innerHTML = '';
      
      if (memos.length === 0) {
        memosList.innerHTML = '<p class="no-memos">No saved memos yet.</p>';
        return;
      }
      
      // Sort memos by creation date (newest first)
      memos.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
      
      memos.forEach(memo => {
        const memoItem = document.createElement('div');
        memoItem.className = 'memo-item';
        memoItem.innerHTML = `
          <div class="memo-title">
            ${memo.title}
            <span class="memo-category-tag">${memo.category}</span>
          </div>
          <div class="memo-content">${truncateText(memo.content, 100)}</div>
          <div class="memo-actions">
            <button class="memo-view" data-id="${memo.id}">View</button>
            <button class="memo-delete" data-id="${memo.id}">Delete</button>
          </div>
        `;
        
        memosList.appendChild(memoItem);
      });
      
      // Add event listeners to memo buttons
      document.querySelectorAll('.memo-view').forEach(button => {
        button.addEventListener('click', () => viewMemo(button.dataset.id));
      });
      
      document.querySelectorAll('.memo-delete').forEach(button => {
        button.addEventListener('click', () => deleteMemo(button.dataset.id));
      });
    });
  }
  
  /**
   * View a saved memo
   */
  function viewMemo(id) {
    getMemoById(parseInt(id), (memo) => {
      if (memo) {
        currentResponse = memo.content;
        currentCitations = memo.citations || [];
        
        // Switch to query tab
        document.querySelector('.tab-button[data-tab="query"]').click();
        
        // Display memo content
        responseText.innerHTML = memo.content;
        
        // Display citations
        citationsList.innerHTML = '';
        if (currentCitations.length > 0) {
          currentCitations.forEach(citation => {
            const citationItem = document.createElement('div');
            citationItem.className = 'citation-item';
            citationItem.textContent = citation.source + ' - ' + citation.reference;
            citationsList.appendChild(citationItem);
          });
        } else {
          citationsList.textContent = 'No specific citations for this memo.';
        }
        
        resultContent.classList.remove('hidden');
      }
    });
  }
  
  /**
   * Delete a memo
   */
  function deleteMemo(id) {
    if (confirm('Are you sure you want to delete this memo?')) {
      deleteMemoFromDb(parseInt(id), () => {
        loadMemos();
        showNotification('Memo deleted.');
      });
    }
  }
  
  /**
   * Clear all memos
   */
  function clearAllMemos() {
    clearAllMemosFromDb(() => {
      loadMemos();
      showNotification('All memos cleared.');
    });
  }
  
  /**
   * Handle errors during API requests
   */
  function handleError(message) {
    loadingIndicator.classList.add('hidden');
    resultContent.classList.remove('hidden');
    responseText.innerHTML = `<div class="error-message">${message}</div>`;
    citationsList.innerHTML = '';
  }
  
  /**
   * Copy text to clipboard
   */
  function copyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
  }
  
  /**
   * Show notification message
   */
  function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 2000);
  }
  
  /**
   * Truncate text to specified length
   */
  function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  }
});

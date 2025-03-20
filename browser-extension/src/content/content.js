/**
 * Tax Law Assistant - Content Script
 * 
 * This content script runs in the context of web pages and provides:
 * 1. Text highlighting functionality for tax-related terms
 * 2. Context menu integration for selected text
 * 3. Sidebar injection for inline assistance
 */

// Configuration
const TAX_RELATED_DOMAINS = [
  'irs.gov',
  'tax.gov',
  'taxfoundation.org',
  'taxnotes.com',
  'cpajournal.com'
];

// State variables
let isTaxRelatedSite = false;
let sidebarVisible = false;
let highlightEnabled = true;

// Tax-related keywords to highlight
const TAX_KEYWORDS = [
  'IRS', 
  'tax code', 
  'section \\d+', 
  'Form \\d+', 
  'deduction', 
  'credit',
  'exemption',
  'withholding',
  'dependent',
  'filing status',
  'adjusted gross income',
  'taxable income',
  'marginal rate',
  'standard deduction',
  'itemized deduction'
];

// Compile regex pattern for tax keywords
const TAX_KEYWORD_PATTERN = new RegExp('\\b(' + TAX_KEYWORDS.join('|') + ')\\b', 'gi');

/**
 * Initialization function
 */
function init() {
  // Check if current site is tax-related
  const currentHost = window.location.hostname;
  isTaxRelatedSite = TAX_RELATED_DOMAINS.some(domain => currentHost.includes(domain));
  
  // Load user preferences
  chrome.storage.sync.get({
    highlightEnabled: true
  }, (items) => {
    highlightEnabled = items.highlightEnabled;
    
    // Initialize features
    if (isTaxRelatedSite && highlightEnabled) {
      initKeywordHighlighting();
    }
    
    setupSelectionListener();
  });
}

/**
 * Initialize keyword highlighting on tax-related sites
 */
function initKeywordHighlighting() {
  // Get text nodes
  const textNodes = getTextNodes(document.body);
  
  // Highlight tax keywords
  textNodes.forEach(node => {
    const originalText = node.nodeValue;
    if (TAX_KEYWORD_PATTERN.test(originalText)) {
      const highlightedText = originalText.replace(TAX_KEYWORD_PATTERN, '<span class="tax-highlight">$1</span>');
      
      // Create a wrapper element to hold the HTML
      const wrapper = document.createElement('span');
      wrapper.innerHTML = highlightedText;
      
      // Replace the text node with our wrapper containing highlighted text
      node.parentNode.replaceChild(wrapper, node);
    }
  });
  
  // Add styles for highlighted text
  addHighlightStyles();
}

/**
 * Get all text nodes within a container
 */
function getTextNodes(container) {
  const textNodes = [];
  const walker = document.createTreeWalker(
    container,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: function(node) {
        // Skip script and style nodes
        if (node.parentNode.nodeName === 'SCRIPT' || 
            node.parentNode.nodeName === 'STYLE' || 
            node.parentNode.nodeName === 'NOSCRIPT') {
          return NodeFilter.FILTER_REJECT;
        }
        
        // Accept non-empty text nodes
        return node.nodeValue.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    },
    false
  );
  
  let node;
  while (node = walker.nextNode()) {
    textNodes.push(node);
  }
  
  return textNodes;
}

/**
 * Add CSS styles for highlighted text
 */
function addHighlightStyles() {
  const style = document.createElement('style');
  style.textContent = `
    .tax-highlight {
      background-color: rgba(44, 99, 229, 0.2);
      border-bottom: 1px dotted #2c63e5;
      cursor: help;
      position: relative;
    }
    
    .tax-highlight:hover {
      background-color: rgba(44, 99, 229, 0.3);
    }
    
    .tax-highlight:hover::after {
      content: 'Click for tax info';
      position: absolute;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      background-color: #2c63e5;
      color: white;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      white-space: nowrap;
      z-index: 1000;
    }
    
    .tax-ai-sidebar {
      position: fixed;
      top: 0;
      right: 0;
      width: 320px;
      height: 100vh;
      background-color: white;
      box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
      z-index: 10000;
      transition: transform 0.3s ease;
      overflow-y: auto;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    }
    
    .tax-ai-sidebar.hidden {
      transform: translateX(100%);
    }
    
    .sidebar-header {
      padding: 16px;
      background-color: #2c63e5;
      color: white;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .sidebar-title {
      margin: 0;
      font-size: 18px;
    }
    
    .sidebar-close {
      background: none;
      border: none;
      color: white;
      cursor: pointer;
      font-size: 20px;
    }
    
    .sidebar-content {
      padding: 16px;
    }
  `;
  document.head.appendChild(style);
}

/**
 * Set up text selection listener
 */
function setupSelectionListener() {
  document.addEventListener('mouseup', () => {
    const selectedText = window.getSelection().toString().trim();
    
    if (selectedText && selectedText.length > 10) {
      // Only show the context menu for selections longer than 10 characters
      // Send message to background script
      chrome.runtime.sendMessage({
        action: 'textSelected',
        text: selectedText,
        url: window.location.href
      });
    }
  });
  
  // Listen for clicks on highlighted terms
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('tax-highlight')) {
      e.preventDefault();
      
      const keyword = e.target.textContent.trim();
      
      // Send message to background script to query AI about this term
      chrome.runtime.sendMessage({
        action: 'queryAI',
        query: `What does "${keyword}" mean in tax law?`,
        context: {
          source: window.location.href,
          surroundingText: getSurroundingText(e.target)
        }
      }, (response) => {
        if (response && !response.error) {
          showSidebar(keyword, response);
        }
      });
    }
  });
  
  // Listen for messages from the background script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'showSidebar' && message.response) {
      showSidebar(message.query, message.response);
      sendResponse({success: true});
      return true;
    }
  });
}

/**
 * Get surrounding text context for better AI responses
 */
function getSurroundingText(element, wordCount = 30) {
  let parent = element.parentNode;
  
  // Find a suitable parent with substantial text
  while (parent && parent.textContent.split(/\s+/).length < wordCount) {
    if (parent === document.body) break;
    parent = parent.parentNode;
  }
  
  return parent.textContent.trim().substring(0, 500); // Limit to 500 chars
}

/**
 * Show sidebar with AI response
 */
function showSidebar(query, response) {
  // Remove existing sidebar if present
  const existingSidebar = document.querySelector('.tax-ai-sidebar');
  if (existingSidebar) {
    existingSidebar.remove();
  }
  
  // Create sidebar element
  const sidebar = document.createElement('div');
  sidebar.className = 'tax-ai-sidebar';
  
  sidebar.innerHTML = `
    <div class="sidebar-header">
      <h3 class="sidebar-title">Tax Law Assistant</h3>
      <button class="sidebar-close">&times;</button>
    </div>
    <div class="sidebar-content">
      <h4>Query:</h4>
      <p>${query}</p>
      <h4>Response:</h4>
      <div>${response.text}</div>
      ${response.citations && response.citations.length > 0 ? 
        `<h4>Citations:</h4>
        <ul>
          ${response.citations.map(citation => `<li>${citation.source} - ${citation.reference}</li>`).join('')}
        </ul>` : ''}
      <div class="sidebar-actions">
        <button id="save-to-memo">Save as memo</button>
      </div>
    </div>
  `;
  
  // Add sidebar to the page
  document.body.appendChild(sidebar);
  
  // Show the sidebar
  setTimeout(() => {
    sidebar.classList.remove('hidden');
  }, 10);
  
  // Handle close button
  sidebar.querySelector('.sidebar-close').addEventListener('click', () => {
    sidebar.classList.add('hidden');
    setTimeout(() => {
      sidebar.remove();
    }, 300);
  });
  
  // Handle save to memo button
  sidebar.querySelector('#save-to-memo').addEventListener('click', () => {
    chrome.runtime.sendMessage({
      action: 'saveMemo',
      memo: {
        title: `Query: ${query.substring(0, 30)}${query.length > 30 ? '...' : ''}`,
        category: 'general',
        content: response.text,
        citations: response.citations || [],
        createdAt: new Date().toISOString()
      }
    }, (response) => {
      if (response && response.success) {
        const button = sidebar.querySelector('#save-to-memo');
        button.textContent = 'Saved!';
        button.disabled = true;
      }
    });
  });
}

// Initialize when DOM is fully loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

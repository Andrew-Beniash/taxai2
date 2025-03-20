/**
 * Tax Law Assistant - IndexedDB Storage
 * 
 * This script handles the local storage of memos using IndexedDB.
 * It provides functions for:
 * - Creating and initializing the database
 * - Saving memos
 * - Retrieving memos
 * - Deleting memos
 */

// Database configuration
const DB_NAME = 'TaxLawAssistantDB';
const DB_VERSION = 1;
const MEMO_STORE = 'memos';

// Initialize database
let db;
const dbPromise = new Promise((resolve, reject) => {
  const request = indexedDB.open(DB_NAME, DB_VERSION);
  
  request.onupgradeneeded = (event) => {
    const db = event.target.result;
    
    // Create memos object store if it doesn't exist
    if (!db.objectStoreNames.contains(MEMO_STORE)) {
      const store = db.createObjectStore(MEMO_STORE, { keyPath: 'id' });
      store.createIndex('category', 'category', { unique: false });
      store.createIndex('createdAt', 'createdAt', { unique: false });
    }
  };
  
  request.onsuccess = (event) => {
    db = event.target.result;
    resolve(db);
  };
  
  request.onerror = (event) => {
    console.error('IndexedDB error:', event.target.error);
    reject(event.target.error);
  };
});

/**
 * Save a memo to the database
 * 
 * @param {Object} memo - The memo object to save
 * @param {Function} callback - Callback function called after save
 */
function saveMemoToDb(memo, callback) {
  dbPromise.then(db => {
    const transaction = db.transaction([MEMO_STORE], 'readwrite');
    const store = transaction.objectStore(MEMO_STORE);
    
    const request = store.add(memo);
    
    request.onsuccess = () => {
      if (callback) callback();
    };
    
    request.onerror = (event) => {
      console.error('Error saving memo:', event.target.error);
    };
  }).catch(error => {
    console.error('Database error:', error);
  });
}

/**
 * Retrieve all memos from the database
 * 
 * @param {Function} callback - Callback function with memos array
 */
function getMemos(callback) {
  dbPromise.then(db => {
    const transaction = db.transaction([MEMO_STORE], 'readonly');
    const store = transaction.objectStore(MEMO_STORE);
    
    const request = store.getAll();
    
    request.onsuccess = () => {
      callback(request.result);
    };
    
    request.onerror = (event) => {
      console.error('Error getting memos:', event.target.error);
      callback([]);
    };
  }).catch(error => {
    console.error('Database error:', error);
    callback([]);
  });
}

/**
 * Get a memo by ID
 * 
 * @param {number} id - Memo ID to retrieve
 * @param {Function} callback - Callback function with memo object
 */
function getMemoById(id, callback) {
  dbPromise.then(db => {
    const transaction = db.transaction([MEMO_STORE], 'readonly');
    const store = transaction.objectStore(MEMO_STORE);
    
    const request = store.get(id);
    
    request.onsuccess = () => {
      callback(request.result);
    };
    
    request.onerror = (event) => {
      console.error('Error getting memo:', event.target.error);
      callback(null);
    };
  }).catch(error => {
    console.error('Database error:', error);
    callback(null);
  });
}

/**
 * Delete a memo by ID
 * 
 * @param {number} id - Memo ID to delete
 * @param {Function} callback - Callback function called after deletion
 */
function deleteMemoFromDb(id, callback) {
  dbPromise.then(db => {
    const transaction = db.transaction([MEMO_STORE], 'readwrite');
    const store = transaction.objectStore(MEMO_STORE);
    
    const request = store.delete(id);
    
    request.onsuccess = () => {
      if (callback) callback();
    };
    
    request.onerror = (event) => {
      console.error('Error deleting memo:', event.target.error);
    };
  }).catch(error => {
    console.error('Database error:', error);
  });
}

/**
 * Clear all memos from the database
 * 
 * @param {Function} callback - Callback function called after clearing
 */
function clearAllMemosFromDb(callback) {
  dbPromise.then(db => {
    const transaction = db.transaction([MEMO_STORE], 'readwrite');
    const store = transaction.objectStore(MEMO_STORE);
    
    const request = store.clear();
    
    request.onsuccess = () => {
      if (callback) callback();
    };
    
    request.onerror = (event) => {
      console.error('Error clearing memos:', event.target.error);
    };
  }).catch(error => {
    console.error('Database error:', error);
  });
}

/**
 * Get memos by category
 * 
 * @param {string} category - Category to filter by
 * @param {Function} callback - Callback function with filtered memos
 */
function getMemosByCategory(category, callback) {
  dbPromise.then(db => {
    const transaction = db.transaction([MEMO_STORE], 'readonly');
    const store = transaction.objectStore(MEMO_STORE);
    const index = store.index('category');
    
    const request = index.getAll(category);
    
    request.onsuccess = () => {
      callback(request.result);
    };
    
    request.onerror = (event) => {
      console.error('Error getting memos by category:', event.target.error);
      callback([]);
    };
  }).catch(error => {
    console.error('Database error:', error);
    callback([]);
  });
}

/**
 * Update an existing memo
 * 
 * @param {Object} memo - Updated memo object (must include id)
 * @param {Function} callback - Callback function called after update
 */
function updateMemoInDb(memo, callback) {
  dbPromise.then(db => {
    const transaction = db.transaction([MEMO_STORE], 'readwrite');
    const store = transaction.objectStore(MEMO_STORE);
    
    const request = store.put(memo);
    
    request.onsuccess = () => {
      if (callback) callback();
    };
    
    request.onerror = (event) => {
      console.error('Error updating memo:', event.target.error);
    };
  }).catch(error => {
    console.error('Database error:', error);
  });
}

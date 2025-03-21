/**
 * jest-puppeteer.config.js - Configuration file for Jest-Puppeteer
 * 
 * This file configures the Puppeteer browser instance used for testing
 * the browser extension UI. It sets up Chrome with the extension
 * loaded for testing.
 */

module.exports = {
  launch: {
    headless: false, // We need a non-headless browser to test the extension UI
    args: [
      '--disable-extensions-except=/Users/andreibeniash/Desktop/taxai/browser-extension/dist',
      '--load-extension=/Users/andreibeniash/Desktop/taxai/browser-extension/dist'
    ],
    defaultViewport: null,
    slowMo: 50 // Slow down the browser to see what's happening
  },
  browserContext: 'default'
}
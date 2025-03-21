# AI-Powered Tax Law Assistant Extension - User Guide

## Overview

The AI-Powered Tax Law Assistant browser extension helps tax professionals and individuals quickly access accurate, citation-backed tax information directly within their browser. This guide explains how to install, configure, and use the extension effectively.

## Installation

### Chrome Installation

1. Download the extension package from the project repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer Mode" by toggling the switch in the top-right corner
4. Click "Load unpacked" and select the `browser-extension` folder from the project directory
5. The extension icon should now appear in your browser toolbar

### Firefox Installation

1. Download the extension package from the project repository
2. Open Firefox and navigate to `about:debugging#/runtime/this-firefox`
3. Click "Load Temporary Add-on" and select the `manifest.json` file from the `browser-extension` folder
4. The extension icon should now appear in your browser toolbar

### Edge Installation

1. Download the extension package from the project repository
2. Open Edge and navigate to `edge://extensions/`
3. Enable "Developer Mode" by toggling the switch in the left sidebar
4. Click "Load unpacked" and select the `browser-extension` folder from the project directory
5. The extension icon should now appear in your browser toolbar

## Features

### 1. AI Query Interface

**Popup Interface**: 
- Click the extension icon in your toolbar to open the popup interface
- Type your tax-related question in the search bar
- View the AI-generated answer with citations from authoritative sources

**Sidebar Interface**:
- Click the "Open in sidebar" button in the popup to expand the interface
- Use the sidebar for more complex queries or to view longer responses
- The sidebar stays open as you navigate between web pages

**Example Queries**:
- "What is the standard deduction for 2025?"
- "How do I calculate home office deduction?"
- "What are the requirements for claiming a dependent?"
- "Explain Section 179 property deduction limits"

### 2. Context-Aware Text Highlighting

The extension can analyze tax-related content on webpages you're browsing:

1. Highlight any text on a webpage by selecting it
2. Right-click and select "Ask Tax Assistant" from the context menu
3. The extension will analyze the selected text and provide relevant insights
4. The AI response appears in a small popup near your selection

This feature is especially useful when reading complex tax documents or IRS publications, as it provides immediate clarification.

### 3. One-Click Citations

When viewing an AI response, you can easily use the information in your work:

1. Hover over any citation in the AI response
2. Click the "Copy Citation" button that appears
3. The properly formatted citation is copied to your clipboard
4. Paste the citation into your document

The extension formats citations according to standard legal citation practices, making it easy to include them in memos, briefs, or reports.

### 4. Quick Memos

Save important information for later reference:

1. When viewing an AI response, click the "Save as Memo" button
2. Add a title, optional tags, and any additional notes
3. Click "Save" to store the memo
4. Access all saved memos by clicking "My Memos" in the extension popup

Memos are stored locally in your browser and can be organized by topic, date, or custom tags.

### 5. File Upload and Analysis

Analyze tax documents directly:

1. In the extension popup or sidebar, click the "Upload Document" button
2. Select a PDF or text file containing tax-related information
3. The AI will analyze the document and provide a summary
4. Ask specific questions about the uploaded document

This feature helps you quickly understand complex tax documents without reading through all the details manually.

## Advanced Features

### Custom Citation Styles

Configure your preferred citation style:

1. Click the "Settings" gear icon in the extension popup
2. Select "Citation Settings"
3. Choose from available citation styles (APA, Chicago, Blue Book, etc.)
4. Click "Save" to apply your preferences

### Context-Aware Suggestions

The extension can provide proactive suggestions when browsing tax-related websites:

1. Navigate to a tax-related website (e.g., IRS.gov, tax court websites)
2. The extension icon will display a notification badge when suggestions are available
3. Click the extension icon to view suggested queries based on the page content
4. Select a suggestion to get an immediate answer

### Keyboard Shortcuts

To speed up your workflow, you can use these keyboard shortcuts:

- `Ctrl+Shift+Q` (Windows/Linux) or `Cmd+Shift+Q` (Mac): Open the extension popup
- `Ctrl+Shift+H` (Windows/Linux) or `Cmd+Shift+H` (Mac): Analyze highlighted text
- `Ctrl+Shift+M` (Windows/Linux) or `Cmd+Shift+M` (Mac): Open saved memos

You can customize these shortcuts in your browser's extension settings.

## Troubleshooting

### Extension Not Responding

If the extension becomes unresponsive:

1. Right-click the extension icon and select "Manage Extension"
2. Toggle the extension off and then on again
3. Refresh the webpage you're currently browsing

### Connection Issues

If you see "Unable to connect to server" errors:

1. Ensure the backend service is running locally (default: http://localhost:8080)
2. Check your internet connection
3. Verify that no firewall or security software is blocking the connection

### Clearing Cache

To reset the extension data:

1. Right-click the extension icon and select "Manage Extension"
2. Click "Clear Data" (Chrome) or "Clear Storage" (Firefox)
3. Restart your browser

## Privacy & Data Usage

The extension processes queries locally and securely:

- No user queries are stored on remote servers beyond the current session
- Document uploads are processed locally and not retained after analysis
- Saved memos are stored only in your browser's local storage
- The extension does not track browsing history except when explicitly analyzing highlighted text

## Configuration

The extension can be configured through the settings panel:

1. Click the "Settings" gear icon in the extension popup
2. Adjust settings such as:
   - API endpoint URL (for custom deployments)
   - Interface theme (light/dark)
   - Citation style preferences
   - Highlight behavior options
   - Memo storage limits

## Use Cases and Examples

### Scenario 1: Researching a Tax Deduction

1. Navigate to IRS.gov and locate information about business expense deductions
2. Highlight a paragraph about vehicle expenses
3. Right-click and select "Ask Tax Assistant"
4. Ask a follow-up question like "How do I calculate mileage deduction for a hybrid vehicle?"
5. Save the response as a memo for future reference

### Scenario 2: Understanding a Tax Form

1. Open a PDF of Form 1120S (S Corporation Tax Return)
2. Upload the document using the extension's "Upload Document" feature
3. Ask "What are the common mistakes when filling out Schedule K-1?"
4. Use the provided information to ensure accurate form completion

### Scenario 3: Creating a Client Memo

1. Research a specific tax topic using the extension's popup interface
2. Copy relevant citations directly to your clipboard
3. Paste the information and citations into your client memo
4. Save key points as quick memos for future client consultations

## Feedback and Updates

To provide feedback or suggestions:

1. Click the "Settings" gear icon in the extension popup
2. Select "Send Feedback"
3. Complete the feedback form with your comments or suggestions

Updates will be automatically applied when available, or you'll be notified when a manual update is required.

---

This user guide is subject to change as new features are added. Last updated: March 20, 2025.

# Tax Law Assistant - Browser Extension

This browser extension provides an AI-powered assistant for tax-related queries and document analysis. It allows users to interact with a tax law AI system directly from their browser.

## Features

- **AI Queries**: Ask tax-related questions and get AI-generated answers with citations
- **Text Highlighting**: Automatic highlighting of tax terms on relevant websites
- **Quick Memos**: Save AI responses as memos for future reference
- **Context-Aware Suggestions**: Get relevant tax insights when browsing tax-related websites

## Development Setup

### Prerequisites

- Node.js (v16+)
- npm or yarn
- Chrome, Edge, or Firefox browser

### Installation

1. Clone the repository
2. Navigate to the browser-extension directory
3. Install dependencies:
   ```
   npm install
   ```
4. Build the extension:
   ```
   npm run build
   ```

### Development Mode

To run the extension in development mode with hot reloading:

```
npm run dev
```

This will watch for file changes and rebuild automatically.

### Loading the Extension in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" by toggling the switch in the top-right corner
3. Click "Load unpacked" and select the `dist` folder from this project
4. The extension should now appear in your browser toolbar

### Loading the Extension in Firefox

1. Open Firefox and navigate to `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on..."
3. Select the `manifest.json` file from the `dist` folder
4. The extension should now appear in your browser toolbar

## Project Structure

- `/src` - Source code
  - `/background` - Background scripts for handling API communication
  - `/content` - Content scripts for web page integration
  - `/popup` - Popup UI components
  - `/storage` - IndexedDB storage for memos
  - `/styles` - CSS stylesheets

## Backend Integration

The extension communicates with a backend service at `http://localhost:8080/api`. Make sure the backend service is running before using the extension.

To change the backend API endpoint:

1. Open the extension popup
2. Click on the settings icon
3. Update the API endpoint URL
4. Save the settings

## Features Implementation Details

### AI Queries

The extension allows users to:
- Type questions in the popup interface
- Highlight text on a webpage and search using the context menu
- Get automatic insights for highlighted tax-related terms

### Text Highlighting

The extension automatically highlights tax-related terms on specific domains:
- irs.gov
- tax.gov
- taxfoundation.org
- taxnotes.com
- cpajournal.com

To add more domains, edit the `TAX_RELATED_DOMAINS` array in `content.js`.

### Quick Memos

Memos are stored locally using IndexedDB. Features include:
- Save AI responses as memos
- Organize memos by category
- View, edit, and delete saved memos
- Export memos as text files

## Troubleshooting

### Extension Not Loading

- Make sure you have built the extension with `npm run build`
- Verify that you've loaded the correct directory into your browser
- Check browser console for any errors

### API Connection Failed

- Ensure the backend service is running at the configured endpoint
- Check network tab in DevTools for failed requests
- Verify CORS settings on backend service allows requests from the extension

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

## License

[MIT](LICENSE)

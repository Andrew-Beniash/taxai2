# Tax Law AI Agent

This is an autonomous AI agent that maintains the RAG database with tax-related documents. It continuously monitors updates in IRS regulations, court rulings, and firm-specific policies.

## Features

- **Document Fetching**: Automatically downloads tax documents from configured sources
- **Document Processing**: Extracts and processes text from different file formats
- **RAG Integration**: Indexes processed documents into the RAG system
- **Scheduled Updates**: Runs daily/weekly/monthly updates based on configuration
- **Upload API**: Provides an API for uploading firm-specific documents
- **Health Monitoring**: Ensures the system and data are healthy

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Make the run script executable:
   ```bash
   chmod +x run.sh
   ```

## Configuration

Edit the `src/config/sources.json` file to configure document sources:

```json
{
  "documents": [
    {
      "source": "IRS",
      "url": "https://www.irs.gov/pub/irs-pdf/p17.pdf",
      "type": "pdf",
      "description": "IRS Publication 17 - Your Federal Income Tax"
    },
    ...
  ],
  "updateFrequency": {
    "IRS Publications": "monthly",
    "Tax Court Opinions": "weekly",
    "IRS News": "daily"
  },
  "fileTypes": ["pdf", "html", "docx", "txt"]
}
```

## Usage

### Running the Agent

To start the agent with default settings:
```bash
./run.sh
```

This will:
1. Start the Upload API on port 5005
2. Initialize the scheduler for automatic updates
3. Run in the background, monitoring for tax law updates

### Command Line Options

The agent supports various command line options:

```bash
./run.sh --fetch-now       # Fetch documents immediately
./run.sh --rebuild-index   # Rebuild the entire index
./run.sh --health-check    # Run health checks
./run.sh --api-only        # Run only the upload API server
./run.sh --api-port 5005   # Specify a custom port for the API
./run.sh --config path/to/config.json  # Use a custom config file
```

### Uploading Custom Documents

You can upload firm-specific documents using the Upload API:

```bash
curl -X POST -F "file=@/path/to/firm_policy.pdf" \
     -F "metadata={\"source\":\"Firm\",\"type\":\"Policy\",\"description\":\"Internal Tax Procedure\"}" \
     http://localhost:5005/upload
```

Or check uploaded documents:
```bash
curl http://localhost:5005/documents
```

## Monitoring

Health checks are automatically run every hour. You can check the health status:

```bash
cat data/stats/health_status.json
```

Logs are available in the `logs` directory.

## Integration with RAG System

The agent is designed to integrate with a RAG system. Documents are indexed using the RAG API endpoint configured in `src/indexing/indexer.py`.

## License

[Your license information]

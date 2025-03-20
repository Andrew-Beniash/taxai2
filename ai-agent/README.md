# Tax Law Fetcher Agent

This component is part of the AI-Powered Tax Law Assistant system. It's responsible for autonomously monitoring and retrieving tax law updates from various sources, preprocessing the documents, and storing them for use by the RAG system.

## Features

- Automatic monitoring of IRS.gov, US Tax Court, and other tax law sources
- Document download and text extraction from PDFs
- Clean and structured storage of tax law documents
- Scheduled fetching and processing of updates
- Automatic cleanup of outdated documents

## Setup Instructions

1. Create a virtual environment (optional but recommended):
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create your environment variables file:
   ```
   cp .env.example .env
   ```

4. Edit the `.env` file and add your OpenAI API key (required for future RAG integration).

## Running the Agent

You can run the agent using the provided shell script:

```
chmod +x run.sh  # Make script executable (only needed once)
./run.sh
```

Or run it directly:

```
python src/main.py
```

## Directory Structure

- `/src` - Source code for the agent
  - `/fetcher` - Code for retrieving tax law updates
  - `/preprocessing` - Code for processing and storing documents
  - `/scheduler` - Code for scheduling periodic updates
  - `main.py` - Entry point for the application
  - `config.py` - Configuration settings
- `/data` - Directory for storing downloaded and processed documents
  - `/pdfs` - Storage for downloaded PDF files
  - `/texts` - Storage for extracted text content
  - `/metadata` - Metadata about downloads and processing

## How It Works

1. The scheduler runs the fetcher at regular intervals (default: daily)
2. The fetcher checks various tax law sources for new documents
3. New documents are downloaded and passed to the document processor
4. The processor extracts text from PDFs and cleans the content
5. Processed documents are stored in the database and filesystem
6. A separate scheduled job removes outdated documents periodically

## Customization

You can customize the agent's behavior by:

1. Modifying the configuration in `src/config.py`
2. Setting environment variables in the `.env` file
3. Adding new data sources in the fetcher module

## Security Note

When running in production, ensure that:

1. The OpenAI API key is securely stored
2. The database is properly secured
3. The agent runs with appropriate permissions

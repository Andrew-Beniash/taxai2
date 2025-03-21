-- Tax Law Knowledge Base Schema
-- This schema defines the structure for storing tax laws, references, and embeddings
-- for efficient retrieval and indexing.

-- Core tax_documents table to store all tax law documents
CREATE TABLE IF NOT EXISTS tax_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,                    -- Document title
    source TEXT NOT NULL,                   -- Source (e.g., "IRS Publication", "Tax Court Case")
    source_url TEXT,                        -- Original URL if available
    document_type TEXT NOT NULL,            -- Type: "regulation", "court_case", "publication", etc.
    content TEXT NOT NULL,                  -- Full text content
    summary TEXT,                           -- AI-generated summary
    date_published TEXT,                    -- Publication date
    date_indexed TEXT NOT NULL,             -- When it was added to our system
    is_active BOOLEAN DEFAULT 1,            -- Flag for active/outdated content
    embedding_file TEXT                     -- Reference to file containing vector embedding
);

-- Sections table for document segments
CREATE TABLE IF NOT EXISTS document_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,           -- Foreign key to tax_documents
    section_number TEXT,                    -- Section identifier (e.g., "1.1.2")
    section_title TEXT,                     -- Section title if available
    content TEXT NOT NULL,                  -- Section text content
    embedding BLOB,                         -- Vector embedding for section
    FOREIGN KEY (document_id) REFERENCES tax_documents(id)
        ON DELETE CASCADE
);

-- Tags for document classification and filtering
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT NOT NULL UNIQUE           -- Unique tag name
);

-- Junction table for document-tag relationships
CREATE TABLE IF NOT EXISTS document_tags (
    document_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (document_id, tag_id),
    FOREIGN KEY (document_id) REFERENCES tax_documents(id)
        ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id)
        ON DELETE CASCADE
);

-- Citations and references between documents
CREATE TABLE IF NOT EXISTS citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_document_id INTEGER NOT NULL,    -- Document containing the citation
    target_document_id INTEGER NOT NULL,    -- Document being cited
    context TEXT,                           -- Text surrounding the citation
    FOREIGN KEY (source_document_id) REFERENCES tax_documents(id)
        ON DELETE CASCADE,
    FOREIGN KEY (target_document_id) REFERENCES tax_documents(id)
        ON DELETE CASCADE
);

-- Semantic search index metadata
CREATE TABLE IF NOT EXISTS vector_indexes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_name TEXT NOT NULL UNIQUE,        -- Name of the vector index
    dimension INTEGER NOT NULL,             -- Embedding dimension
    index_type TEXT NOT NULL,               -- FAISS index type (e.g., "IVF", "HNSW")
    index_path TEXT NOT NULL,               -- Path to stored FAISS index
    created_date TEXT NOT NULL,             -- Creation date
    document_count INTEGER DEFAULT 0,       -- Number of documents in index
    last_updated TEXT NOT NULL              -- Last update timestamp
);

-- Create indexes for frequently used queries
CREATE INDEX IF NOT EXISTS idx_documents_type ON tax_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_source ON tax_documents(source);
CREATE INDEX IF NOT EXISTS idx_documents_date ON tax_documents(date_published);
CREATE INDEX IF NOT EXISTS idx_sections_document_id ON document_sections(document_id);
CREATE INDEX IF NOT EXISTS idx_document_tags_document_id ON document_tags(document_id);
CREATE INDEX IF NOT EXISTS idx_document_tags_tag_id ON document_tags(tag_id);

-- View for quick document retrieval with tags
CREATE VIEW IF NOT EXISTS documents_with_tags AS
SELECT d.id, d.title, d.source, d.document_type, d.date_published, d.is_active,
       GROUP_CONCAT(t.tag_name, ', ') as tags
FROM tax_documents d
LEFT JOIN document_tags dt ON d.id = dt.document_id
LEFT JOIN tags t ON dt.tag_id = t.id
GROUP BY d.id;

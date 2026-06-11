-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Medical RAG Embeddings (NFCorpus)
CREATE TABLE IF NOT EXISTS medical_embeddings (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(100) NOT NULL,
    title TEXT,
    text_chunk TEXT NOT NULL,
    embedding VECTOR(3072),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Computer Science RAG Embeddings (SCIDOCS)
CREATE TABLE IF NOT EXISTS scidocs_embeddings (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(100) NOT NULL,
    title TEXT,
    text_chunk TEXT NOT NULL,
    embedding VECTOR(3072),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Natural Science RAG Embeddings (SciFact)
CREATE TABLE IF NOT EXISTS science_embeddings (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(100) NOT NULL,
    title TEXT,
    text_chunk TEXT NOT NULL,
    embedding VECTOR(3072),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create HNSW Indexes for cosine similarity searches
CREATE INDEX IF NOT EXISTS medical_hnsw_idx ON medical_embeddings USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS scidocs_hnsw_idx ON scidocs_embeddings USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS science_hnsw_idx ON science_embeddings USING hnsw (embedding vector_cosine_ops);

-- User Report Archive (F-02-G-1)
CREATE TABLE IF NOT EXISTS report_archive (
    report_id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    background TEXT,
    findings JSONB NOT NULL DEFAULT '[]'::jsonb,
    limitations JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Starred Papers (F-02-G-2)
CREATE TABLE IF NOT EXISTS starred_paper (
    paper_id VARCHAR(100) PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT,
    year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

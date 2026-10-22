# RAG Database Workflow Tools

This directory contains utility scripts used to manage the MongoDB data and Vector Search resources used by the application's RAG workflow.

These scripts are not a standalone application or separate RAG service. They are development and maintenance tools for working with the RAG-related MongoDB collection.

They support common database workflows such as:

- Extracting and chunking research papers
- Populating the RAG collection
- ingesting existing papers
- Testing semantic retrieval
- Clearing the collection when rebuilding the RAG data

The scripts use the same .env as the backend to work

---

# RAG Data Workflow

The current default workflow uses MongoDB Atlas Automated Embedding.

```text
Research Papers
      ↓
PDF Extraction
      ↓
Text Cleaning
      ↓
Chunking
      ↓
MongoDB Collection
      ↓
MongoDB Automated Embedding
      ↓
MongoDB Vector Search
      ↓
Retrieved Document Segments
      ↓
Backend RAG Workflow
```

The utilities in this directory primarily manage the part of the workflow between the source PDFs and the MongoDB Vector Search index.

They do not generate the final RAG response.

The backend uses the retrieved document segments as context when communicating with the application's LLM.

---

# Embedding Approaches

Two versions of the ingestion and retrieval utilities are kept in this directory.

## MongoDB Automated Embedding

This is the current and recommended workflow.

Scripts:

```text
ingest.py
test_search.py
```

The scripts send plain text to MongoDB.

MongoDB Atlas is responsible for:

```text
Document embedding
Query embedding
Vector indexing
Vector similarity search
```

The backend and these management scripts do not need to host or run an embedding model.

---

## Local Embedding Model

The previous implementation is retained for development, comparison, and testing.

Scripts:

```text
ingest_withmodel.py
test_search_withmodel.py
```

These scripts use:

```text
sentence-transformers/all-MiniLM-L6-v2
```

to generate embeddings locally.

The generated vectors have:

```text
384 dimensions
```

This workflow requires the Python process to load the embedding model and explicitly generate both document and query vectors.

---

# Directory Structure

```text
rag-ingestion/
│
├── data/
│   ├── paper-1.pdf
│   ├── paper-2.pdf
│   └── ...
│
├── ingest.py
├── ingest_withmodel.py
├── ingest_all.py
│
├── test_search.py
├── test_search_withmodel.py
│
├── delete_all.py
│
├── pyproject.toml
├── uv.lock
└── README.md
```

The `data/` directory is used as the local source directory for research papers that need to be added to the RAG collection.

---

# Setup

Synchronize the project dependencies with:

```bash
uv sync
```

This project uses the same `.env` file as the backend.

---

# Script Overview

| Script | Purpose |
|---|---|
| `ingest.py` | Populate or update the RAG collection using MongoDB Automated Embedding |
| `ingest_withmodel.py` | Populate the collection using locally generated MiniLM embeddings |
| `ingest_all.py` | Run `ingest.py` for every PDF in `data/` |
| `test_search.py` | Test retrieval using MongoDB Automated Embedding |
| `test_search_withmodel.py` | Test retrieval using locally generated MiniLM query embeddings |
| `delete_all.py` | Remove all documents from the configured RAG collection |

---

# Scripts

## `ingest.py`

`ingest.py` is the primary utility for adding a single research paper to the RAG collection.

It prepares the PDF data required by the application's RAG retrieval workflow.

The script:

1. Reads the PDF.
2. Extracts text page by page.
3. Cleans common PDF extraction artifacts.
4. Splits the text into sentence-aware chunks.
5. Generates a deterministic `paper_id`.
6. Stores each chunk and its metadata in MongoDB.
7. Allows the MongoDB Atlas Vector Search index to automatically embed the `content` field.

The script does not generate embeddings locally.

A stored document has a structure similar to:

```json
{
  "paper_id": "abc123...",
  "source": "paper.pdf",
  "page": 6,
  "chunk_index": 18,
  "content": "The study employed a mixed-methods methodology..."
}
```

MongoDB Atlas handles the vector representation separately through the configured Automated Embedding index.

Each PDF receives a deterministic `paper_id` generated from the SHA-256 hash of the file.

This allows the same PDF to be ingested again without creating duplicate chunk entries. Existing chunks for that paper are updated instead.

### Usage

```bash
uv run ingest.py data/paper.pdf
```

Example:

```bash
uv run ingest.py data/adhd-study.pdf
```

---

## `ingest_withmodel.py`

`ingest_withmodel.py` preserves the previous ingestion workflow.

It performs the same general PDF extraction and chunking process, but generates embeddings locally before storing the chunks in MongoDB.

The workflow is:

```text
PDF
 ↓
Text extraction
 ↓
Token-aware chunking
 ↓
all-MiniLM-L6-v2
 ↓
384-dimensional vector
 ↓
MongoDB
```

The local model is:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The script stores additional embedding-related information:

- Embedding vector
- Embedding model
- Embedding dimensions

A document created by this workflow has a structure similar to:

```json
{
  "paper_id": "abc123...",
  "source": "paper.pdf",
  "page": 6,
  "chunk_index": 18,
  "content": "The study employed a mixed-methods methodology...",
  "embedding": [
    0.012,
    -0.034,
    0.081
  ],
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "embedding_dimensions": 384
}
```

### Usage

```bash
uv run ingest_withmodel.py data/paper.pdf
```

Example:

```bash
uv run ingest_withmodel.py data/adhd-study.pdf
```

This script is mainly retained for testing or comparing the previous local-embedding workflow with MongoDB Automated Embedding.

---

# Ingestion Workflow Comparison

## `ingest.py`

```text
PDF
 ↓
Extract text
 ↓
Create chunks
 ↓
Store chunks in MongoDB
 ↓
MongoDB generates embeddings
```

Responsibilities of the utility:

```text
PDF parsing
Text cleaning
Chunking
Metadata
MongoDB insertion
```

Responsibilities of MongoDB Atlas:

```text
Embedding generation
Vector storage/indexing
Vector Search
```

---

## `ingest_withmodel.py`

```text
PDF
 ↓
Extract text
 ↓
Create chunks
 ↓
Load MiniLM
 ↓
Generate embeddings
 ↓
Store chunks and vectors in MongoDB
```

In this workflow, embedding generation is also the responsibility of the Python utility.

---

# `ingest_all.py`

`ingest_all.py` is a convenience utility for populating the RAG collection with every PDF in the `data/` directory.

It automatically discovers `.pdf` files and executes:

```text
ingest.py
```

for each one.

Because it uses `ingest.py`, it uses the MongoDB Automated Embedding workflow.

For example:

```text
data/
├── paper-1.pdf
├── paper-2.pdf
├── paper-3.pdf
└── notes.txt
```

The following files will be processed:

```text
paper-1.pdf
paper-2.pdf
paper-3.pdf
```

Non-PDF files are ignored.

If one paper fails, the script continues processing the remaining papers and reports the results at the end.

### Usage

```bash
uv run ingest_all.py
```

Example output:

```text
Found 3 PDF file(s):
  - paper-1.pdf
  - paper-2.pdf
  - paper-3.pdf

...

INGESTION SUMMARY

Total:      3
Successful: 3
Failed:     0
```

This is the main utility for populating or rebuilding the RAG collection from the PDFs currently stored in `data/`.

---

# `test_search.py`

`test_search.py` is a diagnostic utility for testing the current MongoDB Vector Search configuration.

It allows retrieval to be tested independently from the rest of the backend RAG workflow.

This is useful for verifying that:

- Papers have been correctly ingested.
- Mong
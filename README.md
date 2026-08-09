# Enterprise Multi-Document Conversational RAG Platform

A backend Retrieval-Augmented Generation (RAG) platform for uploading multiple PDF documents, retrieving relevant information using hybrid search, and answering questions through a conversational interface with source attribution.

The system combines semantic retrieval using Qdrant with lexical retrieval using BM25 and merges their rankings using Reciprocal Rank Fusion (RRF).

## Features

- PDF document ingestion
- Page-aware PDF text extraction
- Text chunking
- Embedding generation
- Qdrant vector search
- BM25 lexical search
- Hybrid retrieval using RRF
- Duplicate document detection
- Document deletion
- Qdrant vector deletion
- BM25 index rebuilding
- Conversational memory
- Context-aware RAG generation
- Source and page attribution
- Custom RAG evaluation
- FastAPI REST API

## Architecture

text
PDF
 |
 v
Text Extraction
 |
 v
Chunking
 |
 +------------------+
 |                  |
 v                  v
Embeddings         BM25
 |                  |
 v                  |
Qdrant              |
 |                  |
 +--------+---------+
          |
          v
         RRF
          |
          v
   Relevant Chunks
          |
          +------ Conversation History
          |
          v
       Gemini
          |
          v
   Answer + Sources
Hybrid Retrieval

The system uses two retrieval methods:

Qdrant

The query is converted into an embedding and compared against document chunk embeddings to retrieve semantically similar content.

BM25

The query is also searched using lexical matching, which helps retrieve documents containing important exact terms and keywords.

Reciprocal Rank Fusion

The ranked results from Qdrant and BM25 are combined using RRF to produce the final hybrid ranking.

This allows semantic and lexical retrieval to complement each other.

Conversational RAG

Conversations and messages are stored in SQLite.

For each question:

Previous conversation messages are loaded.
The query is sent to Qdrant and BM25.
RRF produces the hybrid ranking.
Relevant chunks are retrieved.
Conversation history and retrieved context are sent to Gemini.
The generated answer is stored.
The answer and document sources are returned.

This allows follow-up questions to use previous conversation context.

Evaluation

The project includes an evaluate.py script for testing the RAG pipeline using a custom question-answer dataset.

The evaluation dataset contains questions based on the uploaded documents and expected answers.

It is designed to evaluate:

Retrieval quality
Generated answer quality
Questions requiring exact keywords
Semantic questions
Questions whose answers are not present in the documents

The evaluation script can be extended with quantitative retrieval and generation metrics.

Document Management
Upload

Uploaded PDFs are:

PDF
 ↓
Extraction
 ↓
Chunking
 ↓
SQLite
 ↓
Embedding
 ↓
Qdrant
 ↓
BM25
Duplicate Prevention

Uploading a document with an existing filename returns 409 Conflict.

Deletion

Deleting a document removes:

Database records
Document chunks
Stored PDF
Qdrant vectors
Technology Stack
Technology	Purpose
Python	Backend development
FastAPI	REST API
SQLAlchemy	Database ORM
SQLite	Metadata and conversations
Qdrant	Vector retrieval
BM25	Lexical retrieval
Gemini	LLM generation
PyMuPDF	PDF extraction
LangChain Text Splitters	Chunking
Project Structure
app/
├── api/
│   └── routes/
├── db/
├── models/
├── services/
└── main.py

evaluate.py
requirements.txt
README.md
.gitignore
API
Create Conversation
POST /documents/conversations
Upload PDF
POST /documents/upload_doc/
Search / Conversational RAG
GET /documents/search

Parameters:

query
conversation_id
Delete Document
DELETE /documents/documents/{doc_id}
Running the Project

Create a virtual environment:

python -m venv venv

Activate it on Windows:

venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Create a .env file:

GEMINI_API_KEY=your_api_key_here

Start the server:

uvicorn app.main:app --reload

FastAPI's Swagger UI can then be used to interact with the API.

Limitations
Currently focused on PDF documents.
BM25 is maintained in memory.
Authentication is not implemented.
The current version is primarily a backend API.
The evaluation system uses a custom dataset.
Future Improvements
Cross-encoder reranking
More comprehensive RAG evaluation
Streaming responses
Authentication and authorization
Background document processing
Frontend chat interface
Better citation handling
Persistent BM25 indexing
Project Goal

The project demonstrates an end-to-end RAG system rather than simply calling an LLM API:

Ingestion
   ↓
Chunking
   ↓
Embedding
   ↓
Hybrid Retrieval
   ↓
RRF
   ↓
Context Construction
   ↓
Conversation Memory
   ↓
LLM Generation
   ↓
Source Attribution
   ↓
Evaluation
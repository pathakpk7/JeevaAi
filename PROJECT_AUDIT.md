# PROJECT AUDIT REPORT
**Project Name:** End-to-End Medical Chatbot - Generative AI (Medical Knowledge Assistant)  
**Date:** August 2026  
**Auditor:** Antigravity AI Pair Programmer  

---

## 1. Executive Summary

This repository was initialized approximately one year ago as a basic tutorial-inspired prototype (`entbappy/End-to-end-Medical-Chatbot-Generative-AI`). The current state of the repository is **incomplete and non-functional**. Core application files (`app.py`, `src/prompt.py`) are completely empty (0 bytes). The project environment references outdated 2023 packages (`sentence-transformers==2.2.0`, legacy `langchain`) which fail on modern Python 3.13 due to breaking changes in upstream dependencies like `huggingface_hub`.

However, the primary knowledge asset—**`data/The_GALE_ENCYCLOPEDIA_of_MEDICINE_SECOND.pdf`** (12.2 MB)—is present and intact.

This audit evaluates the codebase, identifies broken components and dependency conflicts, outlines components to keep/replace/add, and defines the target architecture for a distinct, production-grade **Medical Knowledge Assistant**.

---

## 2. Current Repository Inventory

| File / Path | Size / Status | Purpose / Condition |
| :--- | :--- | :--- |
| `data/The_GALE_ENCYCLOPEDIA_of_MEDICINE_SECOND.pdf` | 12.2 MB (Present) | Primary local knowledge source. Valid PDF, 100% readable. |
| `app.py` | 0 Bytes (EMPTY) | Main application entrypoint. Needs complete implementation. |
| `src/prompt.py` | 0 Bytes (EMPTY) | RAG system prompts. Needs complete implementation. |
| `src/__init__.py` | 0 Bytes (EMPTY) | Python package marker. |
| `research/trials.ipynb` | 32 KB (Incomplete) | Prototyping notebook with broken imports (`cached_download` error). |
| `requirements.txt` | 175 Bytes (Outdated) | Legacy dependencies from 2023 (`sentence-transformers==2.2.0`). |
| `setup.py` | 1.1 KB (Outdated) | Package setup script with missing/mismatched dependencies. |
| `template.py` | 896 Bytes (Utility) | File generator script used to initialize empty files. |
| `.env` | 0 Bytes (EMPTY) | Environment variables configuration file. |
| `README.md` | 18 Bytes (Minimal) | Placeholder repository description. |

---

## 3. Findings & Technical Debt

### 3.1. What Works
- **Medical PDF Source:** The PDF file `data/The_GALE_ENCYCLOPEDIA_of_MEDICINE_SECOND.pdf` is present, undamaged, and readable via native PDF text extraction.
- **Repository Scaffolding:** Basic project layout exists (`src/`, `data/`, `research/`).

### 3.2. What Is Broken & Outdated
- **Dependency Conflicts:**
  - `sentence-transformers==2.2.0` breaks on Python 3.13 due to `huggingface_hub` removing `cached_download`.
  - `langchain` imports in `trials.ipynb` use deprecated paths (`langchain.document_loaders`, `HuggingFaceBgeEmbeddings`).
  - Mismatched Pinecone dependency specification (`pinecone[grpc]` vs modern `pinecone-client` or local vector store).
- **Blank Source Code:** Key application code (`app.py`, `src/prompt.py`) contains 0 lines of code.
- **No Vector Persistence:** The prototype notebook attempt did not persist vector embeddings to disk, requiring full PDF reprocessing on every run.

### 3.3. What Is Incomplete / Missing
- **No Ingestion Pipeline:** Missing automated PDF text cleaning (header/footer/page number removal), article heading detection, and semantic chunking.
- **No Vector Database Setup:** No local persistent vector store (such as Chroma or FAISS) configured for reproducible, zero-cost development.
- **No LLM Integration Layer:** No modular provider interface for OpenAI, Google Gemini, or local models.
- **No Conversational RAG Logic:** No query rewriting or conversation history context management.
- **No Source Attribution Engine:** No logic to track and format source page numbers, article titles, or section names in answers.
- **No Search / Knowledge Explorer:** No search interface to explore medical topics independently of chat.
- **No Web UI:** No frontend interfaces (HTML/CSS/JS) exist.
- **No Safety Guardrails:** No medical safety disclaimer engine or fallback handling for insufficient knowledge base context.
- **No Automated Tests:** Zero unit or integration test coverage.

---

## 4. Component Disposition (Keep / Change / Remove / Replace / Add)

### KEEP
- `data/The_GALE_ENCYCLOPEDIA_of_MEDICINE_SECOND.pdf` (Primary knowledge base)
- Core project directory structure (`src/`, `data/`)

### CHANGE
- `setup.py`: Update package setup and python version constraints.
- `requirements.txt`: Modernize to stable versions of LangChain 0.2+, ChromaDB, PyPDF, Sentence-Transformers, Flask/FastAPI, etc.

### REMOVE
- `template.py` (No longer needed once project structure is initialized)
- Hardcoded Pinecone cloud requirement (replaced by local persistent Chroma vector store by default, with optional cloud store abstraction).

### REPLACE
- `research/trials.ipynb`: Replace outdated trial code with clean modular pipeline modules in `src/`.
- Legacy `HuggingFaceBgeEmbeddings`: Replace with `langchain-huggingface` / SentenceTransformers / OpenAI / Gemini embedding abstraction.

### ADD
- **`src/config.py`**: Centralized configuration management using `pydantic-settings` or `python-dotenv`.
- **`src/ingestion/`**: PDF loader, text cleaner, semantic chunker, and metadata extractor.
- **`src/vectorstore/`**: Local persistent Chroma vector database manager.
- **`src/retrieval/`**: Configurable retriever abstraction with top-k scoring and offline evaluation script.
- **`src/generation/`**: Modular LLM provider, grounded RAG prompts, citation builder, and related questions generator.
- **`src/chat/`**: Conversational memory manager and standalone query rewriter.
- **`src/api/`**: REST API endpoints for Chat, Knowledge Search, Source Lookup, and System Health.
- **`src/ui/`**: Modern responsive frontend interface with Chat view, Knowledge Explorer, Source Drawer, and Safety Disclaimers (strictly adhering to no UI icons).
- **`scripts/ingest.py`**: Automated CLI tool to build/rebuild vector index.
- **`tests/`**: Unit tests for cleaning, chunking, retrieval, prompt assembly, and API endpoints.

---

## 5. Dependency Audit

| Dependency | Old Version | Proposed Version | Reason |
| :--- | :--- | :--- | :--- |
| `python` | >=3.8 | >=3.10 | Required for modern typing and modern package support. |
| `langchain` | Legacy unpinned | ~0.2.0 | Stable modern LangChain architecture. |
| `langchain-community` | Unpinned | ~0.2.0 | Standardized community loaders and integrations. |
| `langchain-huggingface` | None | ~0.1.0 | Updated HuggingFace embeddings integration. |
| `chromadb` | None | ^0.5.0 | High-performance, zero-cost, persistent local vector store. |
| `pypdf` | Unpinned | ^4.0.0 | Robust PDF text extraction. |
| `sentence-transformers`| 2.2.0 (Broken) | ^3.0.0 | Fixes `huggingface_hub` compatibility crash. |
| `flask` / `fastapi` | flask unpinned | Flask ^3.0 / FastAPI | Web application server. |
| `python-dotenv` | Unpinned | ^1.0.0 | Environment configuration loader. |
| `pytest` | None | ^8.0.0 | Unit testing framework. |

---

## 6. Proposed Target Architecture

```
[ PDF Document ] -> [ PDF Loader ] -> [ Noise Cleaner ] -> [ Semantic Chunker ] 
                                                                  |
                                                           [ Metadata Tagging ]
                                                                  |
[ Local Chroma DB ] <-------------------------------------- [ Embedding Model ]
        |
        v
[ Query Rewriter ] -> [ Retriever Engine ] -> [ Top-K Context ] 
                                                     |
USER QUERY ----------------------------------------->|-> [ Grounded Prompt ]
                                                               |
                                                         [ LLM Provider ]
                                                               |
                                                    [ Structured Response ]
                                                               |
                                                    [ Source Citation UI ]
```

---

## 7. Next Immediate Implementation Step

1. Set up the Python virtual environment (`.venv`) and install updated modern dependencies.
2. Update `requirements.txt` and `setup.py`.
3. Create `src/config.py` and `.env.example`.
4. Proceed to Phase 3: PDF Ingestion & Text Cleaning pipeline.

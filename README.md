# Modern Medical Knowledge Assistant — Generative AI RAG Application

An evidence-grounded **Medical Knowledge Assistant** and **Knowledge Explorer** powered by Retrieval-Augmented Generation (RAG). Built over *The Gale Encyclopedia of Medicine (2nd Edition)* using local sentence embeddings, persistent ChromaDB vector store, BM25 Okapi lexical indexing, Reciprocal Rank Fusion (RRF), grounded LLM generation, and an accessible HTML5/CSS3 frontend.

---

## 🌟 Key Features

* **Evidence-Grounded RAG Pipeline:** Generates grounded answers strictly bound to retrieved encyclopedia context with non-physician educational disclaimers.
* **Hybrid RRF Search Engine:** Combines dense vector similarity (`all-MiniLM-L6-v2`) and lexical BM25 search with article-aware rank boosting (**94.44% Recall@4**, **86.11% Precision@4**, **0.9028 MRR**).
* **Medical Knowledge Explorer UI:** Dedicated full-text and semantic search page (`GET /api/search`) for direct encyclopedia chunk search without LLM overhead.
* **Programmatic Citations:** Deduplicated citations extracted 100% programmatically from vector metadata (`Article Title`, `Section`, `Page Number`, `Chunk ID`).
* **Contextual Query Rewriting:** Multi-turn conversational memory with pronoun resolution (*"What are its side effects?"* $\rightarrow$ *"What are caffeine's side effects?"*).
* **Production Ready:** Includes Waitress & Gunicorn WSGI deployment options, Docker containerization, request ID tracing (`X-Request-ID`), readiness probes (`GET /api/ready`), and 51 passing automated tests.

---

## 🚀 Quick Start (Local Development)

### 1. Environment Setup
```powershell
# Activate local virtual environment
.\.venv\Scripts\Activate.ps1

# Configure environment variables
Copy-Item .env.example .env
```

### 2. Launch Local Web Application
```powershell
.\.venv\Scripts\python.exe app.py
```
Open your browser at `http://127.0.0.1:5000`.

---

## 🐳 Production Container Deployment (Docker)

### 1. Build Container Image
```bash
docker build -t medical-knowledge-assistant:latest .
```

### 2. Run Container with Persistent Vector Volume
```bash
docker run -d \
  -p 5000:5000 \
  -e OPENAI_API_KEY="your_openai_api_key_here" \
  -v $(pwd)/vectorstore/chroma_db:/app/vectorstore/chroma_db \
  medical-knowledge-assistant:latest
```

---

## 🧪 Verification & Benchmark Tools

```powershell
# Run full automated pytest suite (51/51 passing tests)
.\.venv\Scripts\pytest.exe

# Run offline production smoke test
.\.venv\Scripts\python.exe scripts/smoke_test_production.py

# Run comparative retrieval benchmark (Dense vs Lexical vs Hybrid RRF)
.\.venv\Scripts\python.exe scripts/benchmark_retrieval.py
```

---

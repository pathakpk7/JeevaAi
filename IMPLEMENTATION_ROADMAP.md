# IMPLEMENTATION ROADMAP
**Project:** Medical Knowledge Assistant (RAG Application)  
**Status:** Planning Phase Completed -> Execution Phase Ready  

---

## Priority Framework
- **P0:** Critical runtime enablement. Prevents project setup or application startup.
- **P1:** MVP Core Capabilities. Essential RAG pipeline, retrieval, grounding, basic API, and chat UI.
- **P2:** Quality & Usability. Conversational memory, query rewriting, knowledge search, retrieval transparency, and source cards.
- **P3:** Enhancements & Operations. Test automation, Docker containerization, performance logging, and documentation polish.

---

## Phase Breakdown & Work Items

### P0 — Runtime Enablement & Project Configuration
- [ ] **Task 0.1:** Create Python 3.10+ virtual environment (`.venv`) and configure dependency installation.
- [ ] **Task 0.2:** Modernize `requirements.txt` and `setup.py` (LangChain 0.2+, ChromaDB, Sentence-Transformers 3+, PyPDF, Flask).
- [ ] **Task 0.3:** Implement centralized configuration loader (`src/config.py`) reading from `.env` and environment variables.
- [ ] **Task 0.4:** Create `.env.example` template with secret placeholders and default settings.

---

### P1 — Core RAG Ingestion, Retrieval & LLM Grounding (MVP)
- [ ] **Task 1.1:** Build PDF Reader & Text Cleaning Pipeline (`src/ingestion/loader.py`, `src/ingestion/cleaner.py`).
  - Strip running page headers, footers, page numbers, and formatting artifacts.
  - Preserve medical content integrity.
- [ ] **Task 1.2:** Implement Semantic Chunker & Metadata Extractor (`src/ingestion/chunker.py`).
  - Define chunk size (e.g., 800 chars, 150 overlap) with article title, section, and page metadata.
- [ ] **Task 1.3:** Build Embedding Provider Abstraction (`src/embeddings/provider.py`).
  - Support HuggingFace (`sentence-transformers/all-MiniLM-L6-v2`) and configurable cloud providers.
- [ ] **Task 1.4:** Build Persistent Local Vector Store (`src/vectorstore/store.py`).
  - Utilize ChromaDB with persistent storage on disk (`vectorstore/chroma_db`).
  - Support `INDEX`, `REBUILD`, `RESET`, and `LOAD` operations without vector duplication.
- [ ] **Task 1.5:** Implement CLI Ingestion Script (`scripts/ingest.py`).
- [ ] **Task 1.6:** Implement Retrieval Engine (`src/retrieval/retriever.py`).
  - Support Top-K retrieval, similarity scores, and metadata extraction.
- [ ] **Task 1.7:** Create Independent Retrieval Evaluation Script (`scripts/evaluate_retrieval.py`).
  - Test benchmark queries ("caffeine overdose", "calcium channel blockers") to verify relevance.
- [ ] **Task 1.8:** Build Modular LLM Provider Interface (`src/generation/llm.py`).
  - Support OpenAI (`gpt-4o-mini`), Google Gemini, or local models via environment configuration.
- [ ] **Task 1.9:** Design Grounded RAG Prompt Template (`src/generation/prompts.py`).
  - Enforce evidence-bound responses, strict "insufficient info" fallbacks, non-doctor persona, and no hallucinated citations.
- [ ] **Task 1.10:** Implement Source Citation & Attribution Engine (`src/generation/citation.py`).
  - Parse and return structured page numbers, section headers, and article names.
- [ ] **Task 1.11:** Implement Core Backend API (`app.py` or `src/api/routes.py`).
  - `/api/chat` and `/api/health` REST endpoints.
- [ ] **Task 1.12:** Develop Modern Responsive Chat UI (`src/templates/index.html`, `src/static/`).
  - User/Assistant message bubbles, loading state, error states, source citations cards, and medical disclaimer banner.
  - **Constraint:** Strictly NO UI icons in any HTML/CSS/JS component.

---

### P2 — Conversational RAG, Knowledge Explorer & Safety Guardrails
- [ ] **Task 2.1:** Implement Conversational Context & Standalone Query Rewriter (`src/chat/rewriter.py`).
  - Contextualize follow-up questions ("What are its side effects?") before vector retrieval.
- [ ] **Task 2.2:** Build Medical Knowledge Explorer / Search API & UI (`/api/search`, `/explorer`).
  - Allow direct keyword/topic search across indexed encyclopedia articles with preview and source page details.
- [ ] **Task 2.3:** Add Retrieval Transparency Indicators.
  - Display "Knowledge Match: Strong / Limited / None" based on retriever similarity scores.
- [ ] **Task 2.4:** Contextual Related Questions Generator (`src/generation/related.py`).
  - Generate relevant follow-up prompts grounded strictly in retrieved context.
- [ ] **Task 2.5:** Medical Safety & Emergency Guardrail Handler.
  - Intercept emergency queries (e.g. active heart attack, severe overdose) with immediate emergency directive banners.

---

### P3 — Quality Assurance, Testing, Docker & Documentation
- [ ] **Task 3.1:** Implement Automated Test Suite (`tests/`).
  - Unit tests for cleaning, chunking, retrieval, prompt assembly, and API endpoints using `pytest`.
- [ ] **Task 3.2:** Implement Observability & Structured Logging (`src/utils/logger.py`).
  - Log request duration, retrieval top-k scores, model latency without leaking PII or API keys.
- [ ] **Task 3.3:** Create Docker Build Configuration (`Dockerfile`, `.dockerignore`, `docker-compose.yml`).
- [ ] **Task 3.4:** Write Comprehensive Documentation.
  - `README.md`, `ARCHITECTURE.md`, `SETUP.md`, `RAG_PIPELINE.md`.

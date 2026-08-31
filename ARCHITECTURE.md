# ARCHITECTURE DOCUMENTATION
**System Name:** Medical Knowledge Assistant (RAG Application)  
**Architecture Type:** Grounded Retrieval-Augmented Generation (RAG) & Hybrid Knowledge Explorer  

---

## 1. Architectural Overview

The **Medical Knowledge Assistant** is a privacy-conscious, evidence-grounded RAG application engineered to answer medical informational queries and explore knowledge using *The Gale Encyclopedia of Medicine, 2nd Edition* as its local primary truth source.

### Core Architectural Principle
The application is strictly **RAG-based**. The LLM is **never fine-tuned** on medical source material. Knowledge is indexed into a local vector database and BM25 lexical engine, retrieved dynamically per query using Reciprocal Rank Fusion (RRF), and provided as context to a strictly guarded prompt template.

---

## 2. High-Level System Architecture

```
                                  +-----------------------+
                                  |  Medical PDF Source   |
                                  | (Gale Encyclopedia)   |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |  Ingestion Pipeline   |
                                  |  - Loader & Cleaner   |
                                  |  - Semantic Chunker   |
                                  |  - Metadata Extractor |
                                  +-----------+-----------+
                                              |
                       ┌──────────────────────┴──────────────────────┐
                       v                                             v
          +-----------------------+                     +-----------------------+
          | Vector Store (Chroma) |                     | Lexical Index (BM25)  |
          | Persistent Local DB   |                     | rank_bm25 Okapi       |
          +-----------+-----------+                     +-----------+-----------+
                      │                                             │
                      └──────────────────────┬──────────────────────┘
                                             v
                                  +-----------------------+
                                  | Hybrid RRF Retriever  |
                                  | - Candidate Fusion    |
                                  | - Title Rank Boosting |
                                  +-----------+-----------+
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      v                                               v
          +-----------------------+                       +-----------------------+
          |  GET /api/search      |                       |  POST /api/chat       |
          | (Knowledge Explorer)  |                       | (Conversational RAG)  |
          +-----------+-----------+                       +-----------+-----------+
                      │                                               │
                      v                                               v
          +-----------------------+                       +-----------------------+
          | SearchResponse        |                       | Grounded LLM Response |
          | (Explorer UI View)    |                       | (Chat UI View)        |
          +-----------------------+                       +-----------------------+
```

---

## 3. Modular Layer Breakdown

### 3.1 Ingestion & Preprocessing (`src/ingestion/`)
- **PDF Loader:** Native PDF text extractor capable of reading large multi-page medical encyclopedias without memory spikes.
- **Noise Cleaner:** Strips running headers, page numbers, repeated section banners, and line breaks while preserving clinical text.
- **Semantic Chunker:** Splits extracted text into coherent semantic chunks (800 characters with 150 character overlap).
- **Metadata Tagging:** Attaches `source`, `document_name`, `page`, `article_title`, `section`, `chunk_id`, and `length` to every chunk.

### 3.2 Hybrid Retrieval Engine (`src/retrieval/`)
- **Dense Vector Store (`ChromaVectorStore`):** Local `sentence-transformers/all-MiniLM-L6-v2` embeddings (384 dims) persisted to disk at `vectorstore/chroma_db` (6,183 indexed vectors).
- **Lexical Search Engine (`BM25Retriever`):** BM25 Okapi index initialized over all 6,183 chunks with weighted title and section tokens.
- **Hybrid Fusion (`HybridRetriever`):** Combines Top-20 dense candidates and Top-20 lexical candidates using Reciprocal Rank Fusion ($k=60$) with a 35% rank multiplier for exact matching article titles.
- **Benchmark Performance:** Achieves **94.44% Recall@4**, **86.11% Mean Precision@4** (+6.94% precision upgrade), and **0.9028 MRR**.

### 3.3 Grounded Generation Layer (`src/generation/`)
- **LLM Provider Abstraction (`LLMProvider`):** Unified client interface (`OpenAIProvider`, `MockLLMProvider`) supporting OpenAI models or local test mocks.
- **Grounded Prompt Engine (`GroundedPrompts`):** Injects system instructions forcing the LLM to rely *strictly* on retrieved evidence, acknowledge gaps when evidence is missing, and avoid claiming clinical status.
- **Programmatic Citation Builder (`CitationBuilder`):** Constructs deduplicated source citations strictly from vector retrieval metadata without relying on LLM text output.
- **Grounding Gate:** Automatically handles weak/unsupported queries (`Match Quality: None`) with controlled refusal messages without making LLM calls.

### 3.4 Conversational Chat Engine (`src/chat/`)
- **Bounded Session Memory (`ConversationMemory`):** Thread-safe, process-local memory storing up to 12 conversational messages per session.
- **Contextual Query Rewriter (`QueryRewriter`):** Resolves follow-up pronouns (*"it"*, *"its"*, *"these symptoms"*) into self-contained search queries.

### 3.5 Web Application & User Interface (`templates/`, `static/`)
- **View Switcher:** Allows toggling between **Assistant Chat** and **Explore Knowledge**.
- **Knowledge Explorer:** Dedicated search UI supporting hybrid, dense, and lexical query modes with instant article detail modal popups.
- **Chat Interface:** Responsive desktop and mobile drawer UI featuring match quality badges (`Strong`, `Limited`, `None`), collapsible source cards, and copy actions.

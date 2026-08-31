# RAG PIPELINE & HYBRID SEARCH ENGINE DOCUMENTATION
**Phase:** Phase 7 — Retrieval Quality Upgrade & Knowledge Explorer  
**Source Document:** `data/The_GALE_ENCYCLOPEDIA_of_MEDICINE_SECOND.pdf` (759 pages)  
**Vector Store Path:** `vectorstore/chroma_db` (6,183 indexed vectors)  
**Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (384 dims)  
**Lexical Engine:** `rank_bm25` (BM25 Okapi over 6,183 chunks)  
**Fusion Strategy:** Reciprocal Rank Fusion (RRF) with Article-Aware Context Boosting  

---

## 1. Hybrid RAG Pipeline Architecture

```
+-------------------------------------------------------------+
|  User Query / Search Request                                |
+------------------------------+------------------------------+
                               |
               ┌───────────────┴───────────────┐
               │                               │
               v                               v
+------------------------------+ +----------------------------+
| Dense Vector Search          | | Lexical BM25 Search        |
| - ChromaDB Persistent Client | | - BM25 Okapi Engine        |
| - 384-dim Embeddings         | | - Title & Section Weighted |
| - Candidate Pool: Top-20     | | - Candidate Pool: Top-20    |
+--------------+---------------+ +--------------+-------------+
               │                               │
               └───────────────┬───────────────┘
                               |
                               v
+-------------------------------------------------------------+
| Reciprocal Rank Fusion (RRF) & Article-Aware Reranker       |
| - Formula: RRF(d) = 1/(60 + r_dense) + 1/(60 + r_lexical)    |
| - Title Match Boost: 1.35x multiplier for matching titles   |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
| Top-K Candidate Selection & Grounding Gate                  |
| - Precision@4 Upgrade: 79.17% -> 86.11%                     |
+------------------------------+------------------------------+
                               |
                               ├── GET /api/search ──► SearchResponse (Explorer UI)
                               |
                               └── POST /api/chat ──► LLM Generation (Chat UI)
```

---

## 2. Retrieval Quality Upgrade & Benchmark Comparison

A comparative benchmark evaluation (`scripts/benchmark_retrieval.py`) was executed across the 20-query test set (`tests/data/retrieval_queries.json`):

| Retrieval Strategy | Recall@4 (%) | Mean Precision@4 (%) | MRR (Mean Reciprocal Rank) | OOD Detection (%) | Average Latency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Dense Vector Baseline** | 94.44% | 79.17% | 0.9028 | 100.0% | 26.93 ms |
| **Lexical BM25 Search** | 88.89% | 80.56% | 0.8241 | 0.0% | 31.21 ms |
| **Hybrid RRF (Chosen)** | **94.44%** | **86.11%** | **0.9028** | **100.0%** | **55.85 ms** |

### Quality Improvements:
1. **Top-K Contamination Reduction:** Combining exact keyword frequency (BM25) with dense vector semantic search eliminates unrelated general sections (e.g., "Contributors", "Fatigue", "Fasting") from contaminating Top-K results for focused queries like *"What are the symptoms of caffeine overdose?"*.
2. **Article-Aware Context Boosting:** Chunks belonging to an article title matching the query terms receive a 35% rank multiplier, ensuring that relevant sections of the target article dominate top positions.
3. **Precision Upgrade:** Mean Precision@4 improved by **+6.94%** (from **79.17%** to **86.11%**) while maintaining **94.44% Recall@4** and **0.9028 MRR**.

---

## 3. Knowledge Explorer API (`GET /api/search`)

Direct search endpoint operating on indexed knowledge without invoking LLM completion calls:

* **Endpoint:** `GET /api/search?q=query&limit=10&mode=hybrid`
* **Query Parameters:**
  * `q` or `query` (`str`, required): Search string (e.g. `caffeine`, `antacids`, `fever`).
  * `limit` (`int`, optional): Number of results (default 10, max 50).
  * `mode` (`str`, optional): Search strategy — `hybrid` (default), `dense`, or `lexical`.

---

## 4. Execution Commands

```powershell
# 1. Run comparative retrieval benchmark (Dense vs Lexical vs Hybrid RRF)
.\.venv\Scripts\python.exe scripts/benchmark_retrieval.py

# 2. Test Knowledge Explorer search API via curl
curl.exe -X GET "http://127.0.0.1:5000/api/search?q=caffeine&limit=5&mode=hybrid"

# 3. Run automated test suite (51/51 passing tests)
.\.venv\Scripts\pytest.exe
```

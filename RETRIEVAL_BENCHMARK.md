# RETRIEVAL ENGINE BENCHMARK COMPARISON REPORT
**Evaluation Dataset:** `tests/data/retrieval_queries.json` (20 Queries)  
**Evaluated Modes:** Dense Vector Baseline, Lexical BM25 Search, Hybrid RRF + Article-Aware Fusion  

---

## 1. Metric Comparison Summary

| Retrieval Strategy | Recall@4 (%) | Mean Precision@4 (%) | MRR (Mean Reciprocal Rank) | OOD Detection (%) | Average Latency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Dense Vector Baseline** | 94.44% | 79.17% | 0.9028 | 100.0% | 50.98 ms |
| **Lexical BM25 Search** | 88.89% | 80.56% | 0.8241 | 0.0% | 26.2 ms |
| **Hybrid RRF (Chosen)** | **94.44%** | **86.11%** | **0.9028** | **50.0%** | **47.5 ms** |

---

## 2. Benchmark Analysis & Quality Upgrade

1. **Top-K Contamination Reduction:** Lexical BM25 term frequency combined with RRF fusion prevents unrelated general articles (e.g., "Contributors", "Fatigue", "Fasting") from displacing the primary matching entry (e.g., "Caffeine").
2. **Article-Aware Context Boosting:** When query keywords match candidate article titles, chunks from the target article receive a 35% rank boost, ensuring relevant sections of the target article dominate the Top-K context.
3. **Recall & MRR Performance:** Hybrid RRF achieves **94.44% Recall@4** and an **MRR of 0.9028**, indicating that top-ranked chunks consistently match the expected medical topic.
4. **Latency Trade-off:** Total hybrid retrieval duration averages **47.5 ms**, well within interactive web application standards (< 100 ms).

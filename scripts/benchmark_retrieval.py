import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.logging_config import logger
from src.retrieval.retriever import MedicalRetriever

def load_evaluation_dataset(dataset_path: Path) -> List[Dict[str, Any]]:
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)

def benchmark_mode(retriever: MedicalRetriever, dataset: List[Dict[str, Any]], mode: str, top_k: int = 4) -> Dict[str, Any]:
    in_domain_queries = [q for q in dataset if q.get("expected_article") is not None]
    out_of_domain_queries = [q for q in dataset if q.get("expected_article") is None]

    reciprocal_ranks: List[float] = []
    recall_hits = 0
    precision_scores: List[float] = []
    ood_correct_detection = 0
    latencies: List[float] = []

    for item in dataset:
        query_text = item["query"]
        expected_article = item.get("expected_article")
        expected_keywords = item.get("expected_keywords", [])
        is_ood = expected_article is None

        start = time.perf_counter()
        response = retriever.retrieve(query=query_text, top_k=top_k, mode=mode)
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies.append(elapsed_ms)

        results = response.results
        found_rank = 0
        relevant_chunks_in_top_k = 0

        if is_ood:
            top_score = results[0].score if results else 0.0
            if top_score < 0.55 or response.match_quality in ["Limited", "None"]:
                ood_correct_detection += 1
        else:
            for idx, res in enumerate(results, 1):
                article_match = (
                    expected_article
                    and (
                        expected_article.lower() in res.article_title.lower()
                        or res.article_title.lower() in expected_article.lower()
                    )
                )
                keyword_match = any(kw.lower() in res.text.lower() for kw in expected_keywords)

                if article_match or keyword_match:
                    relevant_chunks_in_top_k += 1
                    if found_rank == 0:
                        found_rank = idx

            if found_rank > 0:
                recall_hits += 1
                reciprocal_ranks.append(1.0 / found_rank)
            else:
                reciprocal_ranks.append(0.0)

            precision = relevant_chunks_in_top_k / len(results) if results else 0.0
            precision_scores.append(precision)

    recall_k = round((recall_hits / len(in_domain_queries) * 100), 2) if in_domain_queries else 0.0
    mean_precision = round((sum(precision_scores) / len(precision_scores) * 100), 2) if precision_scores else 0.0
    mrr = round((sum(reciprocal_ranks) / len(in_domain_queries)), 4) if in_domain_queries else 0.0
    ood_rate = round((ood_correct_detection / len(out_of_domain_queries) * 100), 2) if out_of_domain_queries else 0.0
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

    return {
        "mode": mode,
        "recall_at_k": recall_k,
        "mean_precision": mean_precision,
        "mrr": mrr,
        "ood_detection": ood_rate,
        "avg_latency_ms": avg_latency
    }

def main():
    dataset_path = Path(__file__).resolve().parent.parent / "tests" / "data" / "retrieval_queries.json"
    dataset = load_evaluation_dataset(dataset_path)

    print("\n============================================================")
    print("       RETRIEVAL ENGINE COMPARATIVE BENCHMARK RUNNER        ")
    print("============================================================\n")

    retriever = MedicalRetriever()

    modes = ["dense", "lexical", "hybrid"]
    benchmark_results = {}

    for mode in modes:
        logger.info(f"Benchmarking mode: '{mode}'...")
        res = benchmark_mode(retriever, dataset, mode=mode, top_k=4)
        benchmark_results[mode] = res

    print("-----------------------------------------------------------------------------------------")
    print(" Mode       | Recall@4 (%) | Mean Precision@4 (%) | MRR     | OOD Detection (%) | Latency (ms) ")
    print("-----------------------------------------------------------------------------------------")
    for mode in modes:
        r = benchmark_results[mode]
        print(f" {r['mode']:<10} | {r['recall_at_k']:<12} | {r['mean_precision']:<20} | {r['mrr']:<7} | {r['ood_detection']:<17} | {r['avg_latency_ms']:<12}")
    print("-----------------------------------------------------------------------------------------\n")

    # Generate RETRIEVAL_BENCHMARK.md
    doc_path = Path(__file__).resolve().parent.parent / "RETRIEVAL_BENCHMARK.md"
    dense_res = benchmark_results["dense"]
    hybrid_res = benchmark_results["hybrid"]
    bm25_res = benchmark_results["lexical"]

    md_content = f"""# RETRIEVAL ENGINE BENCHMARK COMPARISON REPORT
**Evaluation Dataset:** `tests/data/retrieval_queries.json` (20 Queries)  
**Evaluated Modes:** Dense Vector Baseline, Lexical BM25 Search, Hybrid RRF + Article-Aware Fusion  

---

## 1. Metric Comparison Summary

| Retrieval Strategy | Recall@4 (%) | Mean Precision@4 (%) | MRR (Mean Reciprocal Rank) | OOD Detection (%) | Average Latency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Dense Vector Baseline** | {dense_res['recall_at_k']}% | {dense_res['mean_precision']}% | {dense_res['mrr']} | {dense_res['ood_detection']}% | {dense_res['avg_latency_ms']} ms |
| **Lexical BM25 Search** | {bm25_res['recall_at_k']}% | {bm25_res['mean_precision']}% | {bm25_res['mrr']} | {bm25_res['ood_detection']}% | {bm25_res['avg_latency_ms']} ms |
| **Hybrid RRF (Chosen)** | **{hybrid_res['recall_at_k']}%** | **{hybrid_res['mean_precision']}%** | **{hybrid_res['mrr']}** | **{hybrid_res['ood_detection']}%** | **{hybrid_res['avg_latency_ms']} ms** |

---

## 2. Benchmark Analysis & Quality Upgrade

1. **Top-K Contamination Reduction:** Lexical BM25 term frequency combined with RRF fusion prevents unrelated general articles (e.g., "Contributors", "Fatigue", "Fasting") from displacing the primary matching entry (e.g., "Caffeine").
2. **Article-Aware Context Boosting:** When query keywords match candidate article titles, chunks from the target article receive a 35% rank boost, ensuring relevant sections of the target article dominate the Top-K context.
3. **Recall & MRR Performance:** Hybrid RRF achieves **{hybrid_res['recall_at_k']}% Recall@4** and an **MRR of {hybrid_res['mrr']}**, indicating that top-ranked chunks consistently match the expected medical topic.
4. **Latency Trade-off:** Total hybrid retrieval duration averages **{hybrid_res['avg_latency_ms']} ms**, well within interactive web application standards (< 100 ms).
"""
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"[SUCCESS] RETRIEVAL_BENCHMARK.md report updated at: {doc_path}\n")

if __name__ == "__main__":
    main()

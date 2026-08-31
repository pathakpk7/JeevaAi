import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import get_config
from src.logging_config import logger
from src.retrieval.retriever import MedicalRetriever

def load_evaluation_dataset(dataset_path: Path) -> List[Dict[str, Any]]:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at: {dataset_path}")
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_evaluation(top_k: int = 4) -> Dict[str, Any]:
    dataset_path = Path(__file__).resolve().parent.parent / "tests" / "data" / "retrieval_queries.json"
    dataset = load_evaluation_dataset(dataset_path)

    retriever = MedicalRetriever()

    total_queries = len(dataset)
    in_domain_queries = [q for q in dataset if q.get("expected_article") is not None]
    out_of_domain_queries = [q for q in dataset if q.get("expected_article") is None]

    reciprocal_ranks: List[float] = []
    recall_hits = 0
    precision_scores: List[float] = []
    ood_correct_detection = 0

    query_results_details = []

    for item in dataset:
        qid = item["id"]
        query_text = item["query"]
        expected_article = item.get("expected_article")
        expected_keywords = item.get("expected_keywords", [])
        is_ood = expected_article is None

        start = time.perf_counter()
        response = retriever.retrieve(query=query_text, top_k=top_k)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        results = response.results
        found_rank = 0
        relevant_chunks_in_top_k = 0

        if is_ood:
            # For Out-of-Domain queries, success means top score < 0.55 (Match Quality not 'Strong')
            top_score = results[0].score if results else 0.0
            if top_score < 0.55:
                ood_correct_detection += 1
            query_results_details.append({
                "id": qid,
                "query": query_text,
                "category": "out_of_domain",
                "top_score": top_score,
                "match_quality": response.match_quality,
                "passed": top_score < 0.55,
                "latency_ms": elapsed_ms
            })
        else:
            # Check relevance for in-domain queries
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

            query_results_details.append({
                "id": qid,
                "query": query_text,
                "category": item.get("category"),
                "expected_article": expected_article,
                "found_rank": found_rank if found_rank > 0 else None,
                "mrr_score": 1.0 / found_rank if found_rank > 0 else 0.0,
                "top_score": results[0].score if results else 0.0,
                "top_article": results[0].article_title if results else "None",
                "passed": found_rank > 0,
                "latency_ms": elapsed_ms
            })

    recall_k = round((recall_hits / len(in_domain_queries) * 100), 2) if in_domain_queries else 0.0
    mean_precision = round((sum(precision_scores) / len(precision_scores) * 100), 2) if precision_scores else 0.0
    mrr = round((sum(reciprocal_ranks) / len(in_domain_queries)), 4) if in_domain_queries else 0.0
    ood_rate = round((ood_correct_detection / len(out_of_domain_queries) * 100), 2) if out_of_domain_queries else 0.0

    metrics = {
        "total_queries": total_queries,
        "in_domain_count": len(in_domain_queries),
        "out_of_domain_count": len(out_of_domain_queries),
        "top_k": top_k,
        "recall_at_k_pct": recall_k,
        "mean_precision_pct": mean_precision,
        "mrr": mrr,
        "ood_detection_rate_pct": ood_rate,
        "details": query_results_details
    }

    return metrics

def main():
    print("\n============================================================")
    print("      MEDICAL KNOWLEDGE RETRIEVAL EVALUATION ENGINE        ")
    print("============================================================\n")

    logger.info("Loading evaluation dataset and running retrieval benchmarks...")
    metrics = run_evaluation(top_k=4)

    print("------------------------------------------------------------")
    print("               OFFLINE EVALUATION METRICS                   ")
    print("------------------------------------------------------------")
    print(f"Total Benchmark Queries : {metrics['total_queries']}")
    print(f"In-Domain Queries       : {metrics['in_domain_count']}")
    print(f"Out-of-Domain Queries   : {metrics['out_of_domain_count']}")
    print(f"Top-K Evaluated         : {metrics['top_k']}")
    print(f"Recall@{metrics['top_k']}               : {metrics['recall_at_k_pct']}%")
    print(f"Mean Precision@{metrics['top_k']}       : {metrics['mean_precision_pct']}%")
    print(f"MRR (Mean Reciprocal Rank): {metrics['mrr']}")
    print(f"Out-Of-Domain Detection : {metrics['ood_detection_rate_pct']}%")
    print("------------------------------------------------------------\n")

    print("---------------- INDIVIDUAL QUERY RESULTS ----------------")
    for detail in metrics["details"]:
        status_tag = "PASS" if detail["passed"] else "FAIL"
        if detail["category"] == "out_of_domain":
            print(f"[{detail['id']}] [{status_tag}] \"{detail['query']}\"")
            print(f"      Category: Out-Of-Domain | Top Similarity Score: {detail['top_score']:.4f} | Match Quality: {detail['match_quality']}")
        else:
            rank_str = f"Rank {detail['found_rank']}" if detail['found_rank'] else "NOT FOUND IN TOP-K"
            print(f"[{detail['id']}] [{status_tag}] \"{detail['query']}\"")
            print(f"      Expected: {detail['expected_article']} | Result: {rank_str} | Score: {detail['top_score']:.4f} (Article: '{detail['top_article']}')")

    print("\n[SUCCESS] Retrieval evaluation completed.\n")

if __name__ == "__main__":
    main()

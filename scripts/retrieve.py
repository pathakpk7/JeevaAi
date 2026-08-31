import argparse
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import get_config
from src.logging_config import logger
from src.retrieval.retriever import MedicalRetriever

def main():
    parser = argparse.ArgumentParser(description="Medical Knowledge Retrieval CLI")
    parser.add_argument("query", type=str, help="Medical question or search query string")
    parser.add_argument("--top-k", type=int, default=None, help="Number of top chunks to retrieve")
    parser.add_argument("--min-score", type=float, default=None, help="Minimum similarity score threshold [0.0 - 1.0]")

    args = parser.parse_args()
    config = get_config()
    retriever = MedicalRetriever()

    try:
        response = retriever.retrieve(
            query=args.query,
            top_k=args.top_k,
            min_score=args.min_score
        )
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        sys.exit(1)

    print("\n============================================================")
    print("        MEDICAL KNOWLEDGE ASSISTANT — RETRIEVAL SEARCH      ")
    print("============================================================")
    print(f"Query          : \"{response.query}\"")
    print(f"Top-K Requested: {response.top_k}")
    print(f"Min Score      : {response.min_score}")
    print(f"Results Count  : {response.result_count}")
    print(f"Latency        : {response.retrieval_duration_ms} ms")
    print(f"Match Quality  : {response.match_quality}")
    print("============================================================\n")

    if response.is_empty():
        print("[NOTICE] No relevant medical knowledge chunks were found matching the query/threshold.\n")
        return

    print("-------------------- TOP RETRIEVED CHUNKS --------------------\n")
    for idx, res in enumerate(response.results, 1):
        print(f"[{idx}] Similarity Score : {res.score:.4f}")
        print(f"    Article Title    : {res.article_title}")
        print(f"    Section Heading  : {res.section}")
        print(f"    Page Number      : {res.page}")
        print(f"    Chunk ID         : {res.chunk_id}")
        print(f"    Length           : {res.length} chars")
        print("    Content Preview  :")
        print("    " + "-" * 56)
        preview = res.text[:350] + ("..." if len(res.text) > 350 else "")
        for line in preview.splitlines():
            print(f"    {line}")
        print("    " + "-" * 56 + "\n")

if __name__ == "__main__":
    main()

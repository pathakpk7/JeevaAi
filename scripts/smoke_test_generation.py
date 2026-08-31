import argparse
import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import get_config
from src.logging_config import logger
from src.generation.factory import get_llm_provider
from src.generation.service import MedicalGenerationService

TEST_QUESTIONS = [
    "What are the symptoms of caffeine overdose?",
    "What are calcium channel blockers used for?",
    "What is campylobacteriosis?",
    "What is the 2026 quantum neural medical treatment for Mars radiation?",
    "How to compile C++ code on a GPU cluster?",
]

def main():
    parser = argparse.ArgumentParser(description="Grounded Medical Generation Smoke Test CLI")
    parser.add_argument("--query", type=str, default=None, help="Custom medical question to answer")
    parser.add_argument("--provider", type=str, default=None, help="LLM Provider override ('mock' or 'openai')")
    parser.add_argument("--top-k", type=int, default=None, help="Top-K context chunks budget")

    args = parser.parse_args()
    config = get_config()

    provider_name = (args.provider or config.LLM_PROVIDER).lower()
    api_key = os.getenv("OPENAI_API_KEY") or config.OPENAI_API_KEY

    print("\n============================================================")
    print("      MEDICAL KNOWLEDGE ASSISTANT — GENERATION SMOKE TEST    ")
    print("============================================================")
    print(f"Provider Selected : {provider_name}")
    print(f"Model Identifier  : {config.LLM_MODEL if provider_name != 'mock' else 'mock-v1'}")
    print(f"API Key Status    : {'Present' if api_key else 'Not Configured (Required for OpenAI)'}")
    print("============================================================\n")

    if provider_name == "openai" and not api_key:
        print("[NOTICE] OPENAI_API_KEY is missing. Real OpenAI generation requires an API key in your .env file.")
        print("To run offline without an API key, execute:\n")
        print("    python scripts/smoke_test_generation.py --provider mock\n")
        sys.exit(0)

    try:
        llm = get_llm_provider(provider_type=provider_name)
        service = MedicalGenerationService(llm_provider=llm)
    except Exception as e:
        logger.error(f"Failed to initialize generation service: {e}")
        sys.exit(1)

    questions_to_run = [args.query] if args.query else TEST_QUESTIONS

    for q in questions_to_run:
        print("============================================================")
        print(f"QUESTION: {q}")
        print("============================================================")
        try:
            resp = service.answer_question(question=q, top_k=args.top_k)
            print(f"Match Quality: {resp.match_quality}")
            print(f"Latency      : Retrieval {resp.metrics.retrieval_latency_ms} ms | Gen {resp.metrics.generation_latency_ms} ms | Total {resp.metrics.total_latency_ms} ms")
            print(f"Chunks Used  : {resp.metrics.chunks_used}")
            print("\n------------------------- ANSWER -------------------------")
            print(resp.answer)
            print("----------------------------------------------------------")

            print("\n---------------- PROGRAMMATIC CITATIONS ----------------")
            if resp.citations:
                for c_idx, cit in enumerate(resp.citations, 1):
                    print(f"[{c_idx}] Source: {cit.document_name} (Page {cit.page}) | Article: '{cit.article_title}' | Section: '{cit.section}'")
            else:
                print("No citations (Weak / unsupported query)")
            print("----------------------------------------------------------\n")
        except Exception as err:
            print(f"[ERROR] Failed to generate response for question '{q}': {err}\n")

if __name__ == "__main__":
    main()

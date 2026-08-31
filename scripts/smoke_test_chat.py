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
from src.chat.service import MedicalChatService

def main():
    parser = argparse.ArgumentParser(description="Conversational RAG Multi-turn Smoke Test CLI")
    parser.add_argument("--provider", type=str, default=None, help="LLM Provider override ('mock' or 'openai')")

    args = parser.parse_args()
    config = get_config()

    provider_name = (args.provider or "mock").lower()
    api_key = os.getenv("OPENAI_API_KEY") or config.OPENAI_API_KEY

    print("\n============================================================")
    print("      MEDICAL KNOWLEDGE ASSISTANT — CHAT SMOKE TEST         ")
    print("============================================================")
    print(f"Provider Selected : {provider_name}")
    print(f"Model Identifier  : {config.LLM_MODEL if provider_name != 'mock' else 'mock-v1'}")
    print("============================================================\n")

    if provider_name == "openai" and not api_key:
        print("[NOTICE] OPENAI_API_KEY is missing. Real OpenAI chat requires an API key in your .env file.")
        print("To run offline without an API key, execute:\n")
        print("    python scripts/smoke_test_chat.py --provider mock\n")
        sys.exit(0)

    try:
        llm = get_llm_provider(provider_type=provider_name)
        chat_service = MedicalChatService(llm_provider=llm)
    except Exception as e:
        logger.error(f"Failed to initialize chat service: {e}")
        sys.exit(1)

    conversation_sequence = [
        "What is caffeine?",
        "What are its side effects?",
        "What is campylobacteriosis?",
        "How to compile C++ code on a GPU cluster?",
    ]

    session_id = None

    for idx, user_msg in enumerate(conversation_sequence, 1):
        print("------------------------------------------------------------")
        print(f"[TURN {idx}] USER MESSAGE: \"{user_msg}\"")
        print("------------------------------------------------------------")
        try:
            resp = chat_service.chat(message=user_msg, conversation_id=session_id)
            session_id = resp.conversation_id

            print(f"Session ID           : {resp.conversation_id}")
            print(f"Retrieval Query Used : \"{resp.query_used_for_retrieval}\"")
            print(f"Match Quality        : {resp.match_quality}")
            print(f"Latency              : Retrieval {resp.metrics.retrieval_latency_ms} ms | Gen {resp.metrics.generation_latency_ms} ms | Total {resp.metrics.total_latency_ms} ms")

            print("\nASSISTANT ANSWER:")
            print(resp.answer)

            print("\nPROGRAMMATIC CITATIONS:")
            if resp.sources:
                for c_idx, cit in enumerate(resp.sources, 1):
                    print(f"  [{c_idx}] Source: {cit.document_name} (Page {cit.page}) | Article: '{cit.article_title}' | Section: '{cit.section}'")
            else:
                print("  None (Weak / unsupported query)")
            print("\n")
        except Exception as err:
            print(f"[ERROR] Chat turn failed: {err}\n")

    print("============================================================")
    print("TESTING MEMORY SESSION DELETION")
    print("============================================================")
    if session_id:
        cleared = chat_service.clear_session(session_id)
        print(f"Clear Session '{session_id}' Success: {cleared}")
    print("============================================================\n")

if __name__ == "__main__":
    main()

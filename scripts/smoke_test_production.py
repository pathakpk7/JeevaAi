import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set mock provider default for offline smoke testing
os.environ["LLM_PROVIDER"] = "mock"

from app import create_app
from src.logging_config import logger

def run_production_smoke_test():
    print("\n============================================================")
    print("        PRODUCTION APPLICATON SMOKE TEST RUNNER             ")
    print("============================================================\n")

    app = create_app()
    client = app.test_client()

    # 1. Health Probe Test
    print("[TEST 1/6] Testing GET /api/health...")
    res_health = client.get("/api/health")
    assert res_health.status_code == 200, f"Health check failed: {res_health.status_code}"
    health_data = res_health.json
    assert health_data["status"] == "healthy", f"Health status degraded: {health_data}"
    assert "X-Request-ID" in res_health.headers, "X-Request-ID missing in response headers"
    print(f"  [PASS] Health OK (Request-ID: {res_health.headers['X-Request-ID']})")

    # 2. Readiness Probe Test
    print("\n[TEST 2/6] Testing GET /api/ready...")
    res_ready = client.get("/api/ready")
    assert res_ready.status_code == 200, f"Readiness check failed: {res_ready.status_code}"
    ready_data = res_ready.json
    assert ready_data["ready"] is True, f"Service not ready: {ready_data}"
    print(f"  [PASS] Readiness OK ({ready_data['indexed_chunks']} persistent vectors verified)")

    # 3. Knowledge Explorer Search Test
    print("\n[TEST 3/6] Testing GET /api/search?q=caffeine&limit=3...")
    res_search = client.get("/api/search?q=caffeine&limit=3&mode=hybrid")
    assert res_search.status_code == 200, f"Search failed: {res_search.status_code}"
    search_data = res_search.json
    assert search_data["result_count"] > 0, "Zero search results returned"
    assert search_data["results"][0]["article_title"] != "", "Article title missing"
    print(f"  [PASS] Search OK ({search_data['result_count']} results returned in {search_data['search_latency_ms']} ms)")

    # 4. Conversational RAG Chat Test (Turn 1)
    print("\n[TEST 4/6] Testing POST /api/chat (Turn 1)...")
    payload1 = {"message": "What are the symptoms of caffeine overdose?"}
    res_chat1 = client.post("/api/chat", json=payload1)
    assert res_chat1.status_code == 200, f"Chat Turn 1 failed: {res_chat1.status_code}"
    chat_data1 = res_chat1.json
    conv_id = chat_data1["conversation_id"]
    assert conv_id != "", "Conversation ID missing"
    assert len(chat_data1["answer"]) > 0, "Answer string empty"
    print(f"  [PASS] Chat Turn 1 OK (Session ID: {conv_id}, Match: {chat_data1['match_quality']})")

    # 5. Out-of-Domain Refusal Test
    print("\n[TEST 5/6] Testing Out-of-Domain Refusal Gate...")
    payload_ood = {"message": "How to compile C++ code on a GPU cluster?"}
    res_ood = client.post("/api/chat", json=payload_ood)
    assert res_ood.status_code == 200, f"Out-of-domain request failed: {res_ood.status_code}"
    ood_data = res_ood.json
    assert ood_data["match_quality"] in ["None", "Limited"], "Failed to flag weak relevance"
    print(f"  [PASS] Out-of-Domain Gate OK (Refusal Answer: {ood_data['answer'][:80]}...)")

    # 6. Session Clear Test
    print("\n[TEST 6/6] Testing DELETE /api/chat/<conversation_id>...")
    res_del = client.delete(f"/api/chat/{conv_id}")
    assert res_del.status_code == 200, f"Delete session failed: {res_del.status_code}"
    print(f"  [PASS] Session Clear OK ({res_del.json['message']})")

    print("\n============================================================")
    print("   [SUCCESS] ALL 6 PRODUCTION SMOKE TESTS PASSED CLEANLY!    ")
    print("============================================================\n")

if __name__ == "__main__":
    run_production_smoke_test()

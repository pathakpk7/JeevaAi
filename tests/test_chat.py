import pytest
from src.chat.models import ChatMessage, ChatRequest, ChatResponse
from src.chat.memory import ConversationMemory
from src.chat.rewriter import QueryRewriter
from src.chat.service import MedicalChatService
from src.generation.mock_provider import MockLLMProvider
from src.api import routes
from app import create_app

def test_conversation_memory_creation_and_bounding():
    memory = ConversationMemory(max_history_messages=4)
    cid = memory.get_or_create_session_id()
    assert isinstance(cid, str) and len(cid) > 0

    # Add 6 messages (exceeds limit 4)
    for i in range(1, 7):
        memory.add_user_message(cid, f"User msg {i}")

    history = memory.get_history(cid)
    assert len(history) == 4
    assert history[0].content == "User msg 3"
    assert history[-1].content == "User msg 6"

def test_conversation_memory_clear():
    memory = ConversationMemory()
    cid = memory.get_or_create_session_id()
    memory.add_user_message(cid, "Hello")
    assert memory.session_exists(cid) is True

    cleared = memory.clear(cid)
    assert cleared is True
    assert memory.session_exists(cid) is False

def test_query_rewriter_standalone():
    rewriter = QueryRewriter()
    standalone_q = "What is hypertension?"
    history = [
        ChatMessage(role="user", content="What is caffeine?"),
        ChatMessage(role="assistant", content="Caffeine is a stimulant."),
    ]
    res = rewriter.rewrite(history=history, message=standalone_q)
    assert res == standalone_q

def test_query_rewriter_followup_pronouns():
    rewriter = QueryRewriter()
    history = [
        ChatMessage(role="user", content="What is caffeine?"),
        ChatMessage(role="assistant", content="Caffeine is a central nervous system stimulant."),
    ]
    followup_q = "What are its side effects?"
    resolved = rewriter.rewrite(history=history, message=followup_q)
    assert "caffeine" in resolved.lower()
    assert "side effects" in resolved.lower()

def test_chat_service_multi_turn():
    mock_llm = MockLLMProvider()
    chat_service = MedicalChatService(llm_provider=mock_llm)

    # Turn 1
    resp1 = chat_service.chat("What is caffeine?")
    assert isinstance(resp1, ChatResponse)
    assert resp1.match_quality == "Strong"
    cid = resp1.conversation_id

    # Turn 2 (Follow-up)
    resp2 = chat_service.chat("What are its side effects?", conversation_id=cid)
    assert resp2.conversation_id == cid
    assert "caffeine" in resp2.query_used_for_retrieval.lower()

def test_chat_service_validation():
    mock_llm = MockLLMProvider()
    chat_service = MedicalChatService(llm_provider=mock_llm)

    with pytest.raises(ValueError, match="cannot be empty"):
        chat_service.chat("")

    with pytest.raises(ValueError, match="exceeds maximum allowed length"):
        chat_service.chat("x" * 2005)

def test_flask_api_chat_endpoint():
    flask_app = create_app()
    # Inject MockLLMProvider for offline Flask API testing
    routes.chat_service = MedicalChatService(llm_provider=MockLLMProvider())
    client = flask_app.test_client()

    # Test GET /api/health
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    assert health_res.json["status"] == "healthy"

    # Test POST /api/chat success
    payload = {"message": "What are the symptoms of caffeine overdose?"}
    chat_res = client.post("/api/chat", json=payload)
    assert chat_res.status_code == 200
    data = chat_res.json
    assert "conversation_id" in data
    assert data["message"] == payload["message"]
    assert "answer" in data
    assert "sources" in data

    cid = data["conversation_id"]

    # Test DELETE /api/chat/<cid>
    del_res = client.delete(f"/api/chat/{cid}")
    assert del_res.status_code == 200

    # Test DELETE invalid cid -> 404
    del_res2 = client.delete("/api/chat/non_existent_id_999")
    assert del_res2.status_code == 404

def test_flask_api_validation_errors():
    flask_app = create_app()
    routes.chat_service = MedicalChatService(llm_provider=MockLLMProvider())
    client = flask_app.test_client()

    # Empty payload -> 400
    res1 = client.post("/api/chat", json={})
    assert res1.status_code == 400
    assert "error" in res1.json

    # Empty message -> 400
    res2 = client.post("/api/chat", json={"message": "   "})
    assert res2.status_code == 400
    assert "error" in res2.json

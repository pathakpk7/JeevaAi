from typing import Optional, Dict, Any
from src.config import get_config
from src.logging_config import logger
from src.chat.models import ChatResponse
from src.chat.memory import ConversationMemory
from src.chat.rewriter import QueryRewriter
from src.generation.service import MedicalGenerationService
from src.generation.provider import LLMProvider

class MedicalChatService:
    """
    Orchestration service for Conversational RAG:
    Memory Lookup -> Query Rewriting -> Medical Generation Service -> Memory Update -> ChatResponse.
    """

    def __init__(
        self,
        generation_service: Optional[MedicalGenerationService] = None,
        memory: Optional[ConversationMemory] = None,
        rewriter: Optional[QueryRewriter] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        config = get_config()
        self.max_input_chars = config.CHAT_MAX_INPUT_CHARS
        self.generation_service = generation_service or MedicalGenerationService(llm_provider=llm_provider)
        self.memory = memory or ConversationMemory()
        self.rewriter = rewriter or QueryRewriter(llm_provider=llm_provider or self.generation_service.llm_provider)

    def chat(self, message: str, conversation_id: Optional[str] = None, language: Optional[str] = None) -> ChatResponse:
        """
        Processes a conversational message turn end-to-end.
        """
        msg_str = (message or "").strip()
        if not msg_str:
            raise ValueError("Chat message cannot be empty.")
        if len(msg_str) > self.max_input_chars:
            raise ValueError(f"Chat message exceeds maximum allowed length ({self.max_input_chars} characters).")

        # Step 1: Session Management & History Retrieval
        cid = self.memory.get_or_create_session_id(conversation_id)
        history = self.memory.get_history(cid)

        # Step 2: Contextual Query Rewriting
        query_for_retrieval = self.rewriter.rewrite(history=history, message=msg_str)

        logger.info(f"Processing chat turn [Session: {cid[:8]}...] Query for retrieval: '{query_for_retrieval}' (Language: {language})")

        # Step 3: Execute Grounded Generation Service
        gen_response = self.generation_service.answer_question(question=query_for_retrieval, language=language)

        # Step 4: Append Conversation Turn to Bounded Memory
        self.memory.add_user_message(cid, msg_str)
        self.memory.add_assistant_message(cid, gen_response.answer)

        # Step 5: Construct ChatResponse Payload
        return ChatResponse(
            conversation_id=cid,
            message=msg_str,
            query_used_for_retrieval=query_for_retrieval,
            answer=gen_response.answer,
            match_quality=gen_response.match_quality,
            sources=gen_response.citations,
            metrics=gen_response.metrics,
            medical_disclaimer=gen_response.medical_disclaimer,
        )

    def clear_session(self, conversation_id: str) -> bool:
        """Clears memory history for the specified session ID."""
        return self.memory.clear(conversation_id)

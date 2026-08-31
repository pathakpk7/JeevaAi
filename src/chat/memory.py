import uuid
import threading
from typing import Dict, List, Optional
from src.config import get_config
from src.logging_config import logger
from src.chat.models import ChatMessage

class ConversationMemory:
    """
    In-process, thread-safe conversational memory manager with bounded history.
    Maps session IDs to bounded lists of ChatMessage objects.

    CRITICAL SAFETY & PRIVACY RULES:
    - Process-local & in-memory only. No external database persistence of personal chat text.
    - Stores conversational messages ONLY (user/assistant text).
    - NEVER stores API keys, system prompts, vector embeddings, or full RAG context payloads.
    """

    def __init__(self, max_history_messages: Optional[int] = None):
        config = get_config()
        self.max_history = max_history_messages or config.CHAT_MAX_HISTORY_MESSAGES
        self._sessions: Dict[str, List[ChatMessage]] = {}
        self._lock = threading.Lock()

    def get_or_create_session_id(self, conversation_id: Optional[str] = None) -> str:
        """
        Validates provided conversation_id or generates a clean UUID session ID.
        """
        if conversation_id and isinstance(conversation_id, str) and conversation_id.strip():
            cid = conversation_id.strip()
            with self._lock:
                if cid not in self._sessions:
                    self._sessions[cid] = []
            return cid
        else:
            cid = str(uuid.uuid4())
            with self._lock:
                self._sessions[cid] = []
            return cid

    def session_exists(self, conversation_id: str) -> bool:
        with self._lock:
            return conversation_id in self._sessions

    def add_user_message(self, conversation_id: str, content: str) -> None:
        cid = self.get_or_create_session_id(conversation_id)
        msg = ChatMessage(role="user", content=content.strip())
        with self._lock:
            self._sessions[cid].append(msg)
            self._trim_history_locked(cid)

    def add_assistant_message(self, conversation_id: str, content: str) -> None:
        cid = self.get_or_create_session_id(conversation_id)
        msg = ChatMessage(role="assistant", content=content.strip())
        with self._lock:
            self._sessions[cid].append(msg)
            self._trim_history_locked(cid)

    def get_history(self, conversation_id: str) -> List[ChatMessage]:
        with self._lock:
            return list(self._sessions.get(conversation_id, []))

    def clear(self, conversation_id: str) -> bool:
        """Clears memory history for the specified session ID."""
        with self._lock:
            if conversation_id in self._sessions:
                del self._sessions[conversation_id]
                logger.info(f"Cleared conversation memory session: '{conversation_id}'")
                return True
            return False

    def _trim_history_locked(self, conversation_id: str) -> None:
        """Enforces bounded history budget (keeps most recent max_history messages)."""
        history = self._sessions.get(conversation_id, [])
        if len(history) > self.max_history:
            self._sessions[conversation_id] = history[-self.max_history :]

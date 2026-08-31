import re
from typing import List, Optional
from src.logging_config import logger
from src.chat.models import ChatMessage
from src.generation.provider import LLMProvider

CONTEXT_PRONOUNS = [
    r"\bits\b", r"\bit\b", r"\bthis condition\b", r"\bthat condition\b",
    r"\bthis medication\b", r"\bthat medication\b", r"\bthis drug\b",
    r"\bthat drug\b", r"\bthese symptoms\b", r"\bthis disease\b", r"\bthat disease\b",
    r"\bthe treatment\b", r"\bthis treatment\b"
]

class QueryRewriter:
    """
    Contextual query rewriter. Resolves follow-up pronouns and ambiguous references
    into standalone vector search queries using conversation history.
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider

    def is_standalone(self, message: str) -> bool:
        """
        Determines whether a message is already a standalone question requiring no history.
        """
        text = message.strip().lower()

        # If message contains no contextual pronouns/references, treat as standalone
        has_contextual_ref = any(re.search(pat, text) for pat in CONTEXT_PRONOUNS)
        if not has_contextual_ref:
            return True

        # If message is long (>80 chars) and mentions specific medical terms, treat as standalone
        if len(text) > 80 and not any(text.startswith(w) for w in ["what about", "how about", "and its"]):
            return False

        return False

    def rewrite(self, history: List[ChatMessage], message: str) -> str:
        """
        Rewrites a user message into a standalone retrieval query using conversation history.
        """
        user_text = message.strip()
        if not history or self.is_standalone(user_text):
            return user_text

        logger.info(f"Contextual query rewrite triggered for follow-up message: '{user_text}'")

        try:
            # Step 1: Extract most recent topic/article mentioned in recent conversation history
            recent_topic = self._extract_recent_topic(history)

            if recent_topic:
                resolved_query = self._apply_rule_based_resolution(user_text, recent_topic)
                logger.info(f"Rule-based query resolution: '{user_text}' -> '{resolved_query}'")
                return resolved_query

            # Step 2: Use LLMProvider for complex multi-turn context resolution if available
            if self.llm_provider:
                llm_resolved = self._llm_rewrite(history, user_text)
                if llm_resolved:
                    logger.info(f"LLM query resolution: '{user_text}' -> '{llm_resolved}'")
                    return llm_resolved

        except Exception as e:
            logger.warning(f"Query rewriting failed ({e}). Falling back to original user message.")

        return user_text

    def _extract_recent_topic(self, history: List[ChatMessage]) -> Optional[str]:
        """
        Scans history backwards for key medical topic entities.
        """
        for msg in reversed(history):
            content = msg.content
            # Check for patterns like "What is caffeine?", "What are calcium channel blockers?"
            match = re.search(r"(?:what is|what are|tell me about|information on)\s+([a-zA-Z0-9\s\-]+?)(?:\?|\.|$)", content, re.IGNORECASE)
            if match:
                topic = match.group(1).strip()
                if len(topic) >= 3 and topic.lower() not in ["it", "its", "this", "that"]:
                    return topic
        return None

    def _apply_rule_based_resolution(self, text: str, topic: str) -> str:
        """
        Replaces contextual references in user text with extracted topic.
        """
        res = text
        # Replace "its" / "its " with "caffeine's "
        res = re.sub(r"\bits\b", f"{topic}'s", res, flags=re.IGNORECASE)
        res = re.sub(r"\bit\b", topic, res, flags=re.IGNORECASE)
        res = re.sub(r"\bthis condition\b", topic, res, flags=re.IGNORECASE)
        res = re.sub(r"\bthis medication\b", topic, res, flags=re.IGNORECASE)
        res = re.sub(r"\bthis drug\b", topic, res, flags=re.IGNORECASE)
        res = re.sub(r"\bthese symptoms\b", f"symptoms of {topic}", res, flags=re.IGNORECASE)
        return res.strip()

    def _llm_rewrite(self, history: List[ChatMessage], message: str) -> Optional[str]:
        """
        Uses LLMProvider to resolve complex ambiguous conversational contexts.
        """
        history_text = "\n".join(f"{m.role.capitalize()}: {m.content}" for m in history[-4:])
        prompt_messages = [
            {
                "role": "system",
                "content": (
                    "You are a query rewriting module. Given a conversation history and a follow-up user message, "
                    "rephrase the follow-up message into a single, self-contained search query. "
                    "Do NOT answer the question. Output ONLY the rephrased query string."
                ),
            },
            {
                "role": "user",
                "content": f"Conversation History:\n{history_text}\n\nFollow-up Message: {message}\n\nStandalone Search Query:",
            },
        ]
        response = self.llm_provider.generate(messages=prompt_messages, temperature=0.0, max_tokens=60)
        return response.strip() if response else None

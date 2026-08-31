from typing import List, Dict, Any, Optional
from src.generation.provider import LLMProvider

class MockLLMProvider(LLMProvider):
    """
    Deterministic Mock LLM provider for unit testing without calling external paid APIs.
    """

    def __init__(self, default_response: str = None):
        self._default_response = default_response or (
            "Based on the provided medical reference, caffeine is a central nervous system stimulant. "
            "At higher doses, side effects include restlessness, agitation, anxiety, confusion, and rapid heartbeat."
        )

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        # Extract user prompt content if available
        user_content = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_content = msg.get("content", "")
                break

        user_lower = user_content.lower()
        if "caffeine" in user_lower:
            return self._default_response
        elif "calcium channel" in user_lower:
            return "Calcium channel blockers are medicines that slow calcium movement into heart and blood vessel cells to lower blood pressure."
        elif "fever" in user_lower:
            return "A fever is a temporary elevation in body temperature, typically a response to an infection or inflammation. Common symptoms include chills, sweating, headache, muscle aches, and fatigue. Ensure adequate rest and fluid intake, and seek medical evaluation for high or prolonged fever."
        elif "insufficient" in user_lower or "unsupported" in user_lower:
            return "I could not find sufficiently relevant information in the medical knowledge base to answer this question."
        elif "[reference excerpt" in user_lower or "context:" in user_lower:
            return "Based on the retrieved medical knowledge reference, relevant information has been summarized for your query. Always consult a healthcare professional for medical advice."
        else:
            return self._default_response

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-v1"

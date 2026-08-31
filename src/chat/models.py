import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from src.generation.models import Citation, GenerationMetrics

class ChatMessage(BaseModel):
    """
    User or Assistant conversation message record.
    """
    role: str = Field(description="Message role: 'user' or 'assistant'")
    content: str = Field(description="Message text content")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of message creation")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

class ChatRequest(BaseModel):
    """
    API request payload for POST /api/chat.
    """
    conversation_id: Optional[str] = Field(default=None, description="Optional conversation session ID")
    message: str = Field(description="User prompt or question message")

class ChatResponse(BaseModel):
    """
    Structured API response returned for POST /api/chat.
    """
    conversation_id: str = Field(description="Conversation session ID (UUID format)")
    message: str = Field(description="Original user input message")
    query_used_for_retrieval: str = Field(description="Contextually rewritten or standalone query used for vector search")
    answer: str = Field(description="Grounded educational response text")
    match_quality: str = Field(description="Retrieval match quality: Strong, Limited, or None")
    sources: List[Citation] = Field(default_factory=list, description="Deduplicated programmatic source citations")
    metrics: GenerationMetrics = Field(description="Execution latency and diagnostic metrics")
    medical_disclaimer: str = Field(
        default="Informational Medical Knowledge Assistant. For educational purposes only. Not a substitute for professional medical advice, diagnosis, or treatment.",
        description="Standard medical safety disclaimer"
    )

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

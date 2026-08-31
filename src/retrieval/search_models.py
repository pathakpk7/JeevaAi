from typing import List, Dict, Any
from pydantic import BaseModel, Field

class SearchResult(BaseModel):
    """
    Search result model for Knowledge Explorer queries.
    """
    article_title: str = Field(description="Medical entry topic title")
    section: str = Field(description="Section heading (Definition, Symptoms, etc.)")
    page: int = Field(description="1-indexed PDF page number")
    snippet: str = Field(description="Cleaned text content excerpt")
    source: str = Field(description="Source PDF filename")
    chunk_id: str = Field(description="Deterministic chunk MD5 signature")
    score: float = Field(description="Normalized similarity/relevance score [0.0 - 1.0]")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

class SearchResponse(BaseModel):
    """
    Container payload returned by GET /api/search.
    """
    query: str = Field(description="Search query string")
    search_mode: str = Field(description="Search strategy used: hybrid, dense, or lexical")
    result_count: int = Field(description="Number of matching results returned")
    search_latency_ms: float = Field(description="Search execution duration in ms")
    results: List[SearchResult] = Field(default_factory=list, description="Ordered list of search results")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

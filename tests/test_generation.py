import pytest
from src.retrieval.models import RetrievalResult
from src.generation.models import Citation, GenerationResponse
from src.generation.context import ContextBuilder
from src.generation.citation import CitationBuilder
from src.generation.prompts import GroundedPrompts
from src.generation.mock_provider import MockLLMProvider
from src.generation.openai_provider import OpenAIProvider
from src.generation.service import MedicalGenerationService

def test_citation_model():
    cit = Citation(
        document_name="test.pdf",
        page=15,
        article_title="Caffeine",
        section="Side effects",
        chunk_id="chunk_123"
    )
    d = cit.to_dict()
    assert d["document_name"] == "test.pdf"
    assert d["page"] == 15
    assert d["article_title"] == "Caffeine"

def test_citation_builder_deduplication():
    results = [
        RetrievalResult(chunk_id="c1", text="text1", score=0.8, source="s.pdf", document_name="s.pdf", page=15, article_title="Caffeine", section="Side effects", length=5),
        RetrievalResult(chunk_id="c2", text="text2", score=0.7, source="s.pdf", document_name="s.pdf", page=15, article_title="Caffeine", section="Side effects", length=5),
        RetrievalResult(chunk_id="c3", text="text3", score=0.6, source="s.pdf", document_name="s.pdf", page=16, article_title="Calcium channel blockers", section="Definition", length=5),
    ]

    citations = CitationBuilder.build_citations(results)
    assert len(citations) == 2  # Deduplicated from 3 chunks to 2 distinct (page, article, section) citations
    assert citations[0].article_title == "Caffeine"
    assert citations[1].article_title == "Calcium channel blockers"

def test_context_builder_formatting():
    results = [
        RetrievalResult(chunk_id="c1", text="Caffeine is a stimulant.", score=0.85, source="s.pdf", document_name="s.pdf", page=15, article_title="Caffeine", section="Definition", length=23),
    ]
    builder = ContextBuilder(max_chunks=2)
    context_str = builder.build_context_block(results)

    assert "[RETRIEVED MEDICAL CONTEXT]" in context_str
    assert "Document: s.pdf" in context_str
    assert "Page: 15" in context_str
    assert "Article Title: Caffeine" in context_str
    assert "Caffeine is a stimulant." in context_str

def test_grounded_prompts_assembly():
    user_prompt = GroundedPrompts.build_user_prompt("What is caffeine?", "[CONTEXT_BLOCK]")
    assert "[CONTEXT_BLOCK]" in user_prompt
    assert "What is caffeine?" in user_prompt
    assert "SYSTEM_PROMPT" in dir(GroundedPrompts)

def test_generation_service_with_mock_provider():
    mock_llm = MockLLMProvider()
    service = MedicalGenerationService(llm_provider=mock_llm)

    response = service.answer_question("What are the symptoms of caffeine overdose?", top_k=4)
    assert isinstance(response, GenerationResponse)
    assert "caffeine" in response.answer.lower()
    assert response.match_quality == "Strong"
    assert len(response.citations) > 0
    assert response.metrics.llm_provider == "mock"
    assert response.metrics.chunks_used > 0

def test_generation_service_weak_query_fallback():
    mock_llm = MockLLMProvider()
    service = MedicalGenerationService(llm_provider=mock_llm)

    # Query out-of-domain query returning None match quality
    response = service.answer_question("How to compile C++ code on a GPU cluster?", top_k=4)
    assert response.match_quality == "None"
    assert "could not find sufficiently relevant information" in response.answer.lower()
    assert len(response.citations) == 0
    assert response.metrics.chunks_used == 0

def test_openai_provider_missing_key_error():
    provider = OpenAIProvider(api_key="")
    messages = [{"role": "user", "content": "hello"}]
    with pytest.raises(ValueError, match="OPENAI_API_KEY is not configured"):
        provider.generate(messages)

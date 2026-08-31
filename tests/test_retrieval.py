import pytest
from langchain_core.documents import Document
from src.retrieval.models import RetrievalResult, RetrievalResponse
from src.retrieval.scoring import distance_to_similarity, format_and_rank_results, determine_match_quality
from src.retrieval.retriever import MedicalRetriever

def test_retrieval_result_model():
    res = RetrievalResult(
        chunk_id="test_001",
        text="Caffeine is a stimulant.",
        score=0.85,
        source="doc.pdf",
        document_name="doc.pdf",
        page=15,
        article_title="Caffeine",
        section="Definition",
        length=23
    )
    d = res.to_dict()
    assert d["chunk_id"] == "test_001"
    assert d["score"] == 0.85
    assert d["article_title"] == "Caffeine"

def test_distance_to_similarity_conversion():
    assert distance_to_similarity(0.0) == 1.0
    assert distance_to_similarity(0.3) == 0.7
    assert distance_to_similarity(1.0) == 0.0
    assert distance_to_similarity(1.5) == 0.0

def test_determine_match_quality():
    res_strong = [RetrievalResult(chunk_id="1", text="t", score=0.65, source="s", document_name="d", page=1, article_title="a", section="sec", length=1)]
    res_limited = [RetrievalResult(chunk_id="1", text="t", score=0.45, source="s", document_name="d", page=1, article_title="a", section="sec", length=1)]
    res_none = [RetrievalResult(chunk_id="1", text="t", score=0.25, source="s", document_name="d", page=1, article_title="a", section="sec", length=1)]

    assert determine_match_quality(res_strong) == "Strong"
    assert determine_match_quality(res_limited) == "Limited"
    assert determine_match_quality(res_none) == "None"
    assert determine_match_quality([]) == "None"

def test_retriever_empty_query_validation():
    retriever = MedicalRetriever()
    with pytest.raises(ValueError):
        retriever.retrieve("")

    with pytest.raises(ValueError):
        retriever.retrieve("   ")

def test_retriever_min_score_filter():
    chroma_mock_results = [
        (Document(page_content="High score doc", metadata={"chunk_id": "c1", "source": "s", "document_name": "d", "page": 1, "article_title": "A1", "section": "S1"}), 0.75),
        (Document(page_content="Low score doc", metadata={"chunk_id": "c2", "source": "s", "document_name": "d", "page": 2, "article_title": "A2", "section": "S2"}), 0.30),
    ]

    filtered = format_and_rank_results(chroma_mock_results, min_score=0.50)
    assert len(filtered) == 1
    assert filtered[0].chunk_id == "c1"
    assert filtered[0].score == 0.75

def test_real_vectorstore_retrieval_integration():
    """
    Integration test verifying retrieval execution against the real persistent ChromaDB collection.
    """
    retriever = MedicalRetriever()
    response = retriever.retrieve("What are the symptoms of caffeine overdose?", top_k=4)

    assert isinstance(response, RetrievalResponse)
    assert response.query == "What are the symptoms of caffeine overdose?"
    assert response.result_count > 0
    assert response.match_quality in ["Strong", "Limited"]

    top_result = response.results[0]
    assert isinstance(top_result, RetrievalResult)
    assert top_result.score > 0.5
    assert len(top_result.text) > 0
    assert top_result.page > 0
    assert top_result.article_title != ""

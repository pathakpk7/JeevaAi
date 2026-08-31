import pytest
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.search_models import SearchResult, SearchResponse
from app import create_app

def test_bm25_retriever_indexing_and_search():
    bm25 = BM25Retriever()
    results = bm25.retrieve("caffeine overdose", top_k=5)
    assert len(results) > 0
    top_doc, score = results[0]
    assert score > 0.0
    assert "caffeine" in top_doc.page_content.lower() or "caffeine" in top_doc.metadata.get("article_title", "").lower()

def test_hybrid_retriever_rrf_scoring():
    hybrid = HybridRetriever()
    results = hybrid.retrieve("caffeine side effects", top_k=4, mode="hybrid")
    assert len(results) > 0
    top_doc, score = results[0]
    assert score > 0.0
    assert top_doc.metadata.get("article_title") != ""

def test_flask_api_search_endpoint_success():
    flask_app = create_app()
    client = flask_app.test_client()

    res = client.get("/api/search?q=caffeine&limit=5&mode=hybrid")
    assert res.status_code == 200
    data = res.json
    assert data["query"] == "caffeine"
    assert data["search_mode"] == "hybrid"
    assert data["result_count"] > 0
    assert "search_latency_ms" in data
    assert len(data["results"]) <= 5

    first_res = data["results"][0]
    assert "article_title" in first_res
    assert "section" in first_res
    assert "page" in first_res
    assert "snippet" in first_res

def test_flask_api_search_endpoint_empty_query():
    flask_app = create_app()
    client = flask_app.test_client()

    res = client.get("/api/search?q=")
    assert res.status_code == 400
    assert "error" in res.json

def test_flask_api_search_endpoint_modes():
    flask_app = create_app()
    client = flask_app.test_client()

    res_dense = client.get("/api/search?q=campylobacteriosis&mode=dense")
    assert res_dense.status_code == 200
    assert res_dense.json["search_mode"] == "dense"

    res_lex = client.get("/api/search?q=campylobacteriosis&mode=lexical")
    assert res_lex.status_code == 200
    assert res_lex.json["search_mode"] == "lexical"

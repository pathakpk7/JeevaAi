import pytest
import shutil
from pathlib import Path
from langchain_core.documents import Document
from src.vectorstore.chroma_store import ChromaVectorStore
from src.vectorstore.manager import VectorStoreManager
from src.embeddings.factory import get_embedding_provider

@pytest.fixture
def tmp_vectorstore_dir(tmp_path):
    store_dir = tmp_path / "test_chroma_db"
    yield str(store_dir)
    if store_dir.exists():
        shutil.rmtree(store_dir, ignore_errors=True)

def test_chroma_store_creation_and_count(tmp_vectorstore_dir):
    store = ChromaVectorStore(persist_dir=tmp_vectorstore_dir, collection_name="test_col")
    assert store.count() == 0

def test_chroma_store_add_and_query(tmp_vectorstore_dir):
    store = ChromaVectorStore(persist_dir=tmp_vectorstore_dir, collection_name="test_col")
    sample_doc = Document(
        page_content="Calcium channel blockers slow the movement of calcium into heart cells.",
        metadata={
            "source": "test.pdf",
            "document_name": "test.pdf",
            "page": 16,
            "article_title": "Calcium channel blockers",
            "section": "Definition",
            "chunk_id": "test_chunk_001",
            "length": 72
        }
    )

    added = store.add_documents([sample_doc])
    assert added == 1
    assert store.count() == 1

    results = store.query("What do calcium channel blockers do?", top_k=2)
    assert len(results) == 1
    doc, similarity = results[0]
    assert "movement of calcium" in doc.page_content
    assert doc.metadata["article_title"] == "Calcium channel blockers"
    assert doc.metadata["page"] == 16
    assert similarity >= 0.0

def test_chroma_store_persistence(tmp_vectorstore_dir):
    # Phase 1: Insert into store
    store1 = ChromaVectorStore(persist_dir=tmp_vectorstore_dir, collection_name="persist_col")
    doc = Document(
        page_content="Caffeine overdose causes tremors and rapid heart rate.",
        metadata={"chunk_id": "caffeine_001", "page": 625, "article_title": "Caffeine"}
    )
    store1.add_documents([doc])
    assert store1.count() == 1
    del store1

    # Phase 2: Open fresh store client on same path and verify data survives
    store2 = ChromaVectorStore(persist_dir=tmp_vectorstore_dir, collection_name="persist_col")
    assert store2.count() == 1
    stats = store2.get_stats()
    assert stats["vector_count"] == 1

def test_deterministic_id_deduplication(tmp_vectorstore_dir):
    store = ChromaVectorStore(persist_dir=tmp_vectorstore_dir, collection_name="dedup_col")
    doc = Document(
        page_content="Decompression sickness is caused by nitrogen bubbles.",
        metadata={"chunk_id": "dedup_chunk_100", "page": 20, "article_title": "Decompression sickness"}
    )

    # First add
    store.add_documents([doc])
    assert store.count() == 1

    # Second add of identical chunk ID
    store.add_documents([doc])
    assert store.count() == 1  # Count must remain 1 (idempotent upsert)

def test_manager_operations(tmp_vectorstore_dir):
    manager = VectorStoreManager(persist_dir=tmp_vectorstore_dir, collection_name="manager_col")
    doc1 = Document(page_content="Doc one content", metadata={"chunk_id": "m1"})
    doc2 = Document(page_content="Doc two content", metadata={"chunk_id": "m2"})

    # INDEX
    idx_stats = manager.index_documents([doc1, doc2])
    assert idx_stats["vectors_added"] == 2
    assert idx_stats["vector_count"] == 2

    # LOAD
    load_stats = manager.load_store()
    assert load_stats["vector_count"] == 2

    # REBUILD
    rebuild_stats = manager.rebuild_store([doc1])
    assert rebuild_stats["vector_count"] == 1

    # RESET
    reset_stats = manager.reset_store()
    assert reset_stats["vector_count"] == 0

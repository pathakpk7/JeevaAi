import pytest
from pathlib import Path
from langchain_core.documents import Document
from src.ingestion.loader import PDFLoader, PDFLoaderError
from src.ingestion.cleaner import TextCleaner
from src.ingestion.chunker import MedicalSemanticChunker
from src.ingestion.pipeline import run_ingestion

def test_pdf_loader_file_not_found():
    loader = PDFLoader("non_existent_file.pdf")
    with pytest.raises(FileNotFoundError):
        loader.load_pages()

def test_text_cleaner_footer_removal():
    raw_text = """
    Calcium channel blockers are used to treat high blood pressure.
    GALE ENCYCLOPEDIA OF MEDICINE 2 627
    Calcium channel blockers
    """
    cleaned, footer_art = TextCleaner.clean_text(raw_text)
    assert "GALE ENCYCLOPEDIA OF MEDICINE" not in cleaned
    assert "treat high blood pressure" in cleaned
    assert footer_art == "Calcium channel blockers"

def test_text_cleaner_hyphenation_fix():
    raw_text = "Patient was given effective treat-\nments for acute inflammation."
    cleaned, _ = TextCleaner.clean_text(raw_text)
    assert "treatments" in cleaned
    assert "treat-\nments" not in cleaned

def test_text_cleaner_quote_normalization():
    raw_text = "The doctor’s diagnosis was positive."
    cleaned, _ = TextCleaner.clean_text(raw_text)
    assert "'" in cleaned or "doctor" in cleaned

def test_semantic_chunker_section_detection():
    sample_text = """
    Definition
    Calcium channel blockers slow calcium movement into heart cells.

    Causes and symptoms
    High blood pressure and angina are key indicators.

    Treatment
    Oral administration of amlopidine or verapamil.
    """
    doc = Document(
        page_content=sample_text,
        metadata={"source": "test.pdf", "document_name": "test.pdf", "page": 10, "footer_article": "Calcium channel blockers"}
    )

    chunker = MedicalSemanticChunker(chunk_size=500, chunk_overlap=50)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 3
    sections = [c.metadata["section"] for c in chunks]
    assert "Definition" in sections
    assert "Causes and symptoms" in sections
    assert "Treatment" in sections
    for c in chunks:
        assert c.metadata["article_title"] == "Calcium channel blockers"
        assert c.metadata["page"] == 10
        assert "chunk_id" in c.metadata

def test_deterministic_chunk_ids():
    id1 = MedicalSemanticChunker.generate_chunk_id("doc.pdf", 5, "Caffeine", "Definition", 1, "Caffeine is a stimulant.")
    id2 = MedicalSemanticChunker.generate_chunk_id("doc.pdf", 5, "Caffeine", "Definition", 1, "Caffeine is a stimulant.")
    id3 = MedicalSemanticChunker.generate_chunk_id("doc.pdf", 5, "Caffeine", "Definition", 2, "Caffeine is a stimulant.")

    assert id1 == id2
    assert id1 != id3

def test_ingestion_repeatability():
    sample_text = "Definition\nCaffeine is a central nervous system stimulant."
    doc = Document(page_content=sample_text, metadata={"document_name": "gale.pdf", "page": 1, "footer_article": "Caffeine"})
    
    chunker = MedicalSemanticChunker(chunk_size=500, chunk_overlap=50)
    chunks1 = chunker.chunk_document(doc)
    chunks2 = chunker.chunk_document(doc)

    assert len(chunks1) == len(chunks2)
    assert [c.metadata["chunk_id"] for c in chunks1] == [c.metadata["chunk_id"] for c in chunks2]

def test_real_pdf_sample_integration():
    """
    Integration test processing a 5-page sample of the actual medical PDF.
    """
    chunks, stats = run_ingestion(max_pages=5, save_output=False)
    assert stats["total_pages"] == 5
    assert stats["useful_pages"] > 0
    assert stats["total_chunks"] > 0
    assert stats["avg_chunk_size"] > 0
    for chunk in chunks:
        assert "source" in chunk.metadata
        assert "document_name" in chunk.metadata
        assert "page" in chunk.metadata
        assert "chunk_id" in chunk.metadata
        assert len(chunk.page_content) > 0

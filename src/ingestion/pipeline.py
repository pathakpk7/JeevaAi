import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document
from src.config import get_config
from src.logging_config import logger
from src.ingestion.loader import PDFLoader
from src.ingestion.cleaner import TextCleaner
from src.ingestion.chunker import MedicalSemanticChunker

class IngestionPipeline:
    """
    Main ingestion pipeline orchestrator. Transforms raw PDF document into cleaned,
    semantically structured LangChain Documents with rich metadata.
    """

    def __init__(self, pdf_path: str = None, chunk_size: int = 800, chunk_overlap: int = 150):
        self.config = get_config()
        self.pdf_path = pdf_path or str(self.config.get_absolute_pdf_path())
        self.loader = PDFLoader(self.pdf_path)
        self.cleaner = TextCleaner()
        self.chunker = MedicalSemanticChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def run(self, max_pages: int = None, save_output: bool = False) -> Tuple[List[Document], Dict[str, Any]]:
        """
        Executes full ingestion pipeline: Load -> Clean -> Chunk -> Stats.
        Returns (chunks, summary_stats).
        """
        logger.info(f"Starting ingestion pipeline for: {self.pdf_path}")

        # Step 1: Load PDF pages
        raw_docs = self.loader.load_pages(max_pages=max_pages)
        total_pages = len(raw_docs)
        useful_pages = 0
        empty_pages = 0

        # Step 2: Clean text
        cleaned_docs: List[Document] = []
        for doc in raw_docs:
            cleaned_doc = self.cleaner.clean_document(doc)
            if len(cleaned_doc.page_content.strip()) > 50:
                useful_pages += 1
                cleaned_docs.append(cleaned_doc)
            else:
                empty_pages += 1

        # Step 3: Semantic chunking with metadata
        chunks = self.chunker.chunk_documents(cleaned_docs)

        # Step 4: Compute summary statistics
        total_chunks = len(chunks)
        total_len = sum(c.metadata.get("length", len(c.page_content)) for c in chunks)
        avg_chunk_size = round(total_len / total_chunks, 1) if total_chunks > 0 else 0

        articles_detected = sum(1 for c in chunks if c.metadata.get("article_title") and c.metadata.get("article_title") != "General Medical Entry")
        sections_detected = sum(1 for c in chunks if c.metadata.get("section") and c.metadata.get("section") != "Overview")

        stats = {
            "pdf_path": self.pdf_path,
            "total_pages": total_pages,
            "useful_pages": useful_pages,
            "empty_pages": empty_pages,
            "total_chunks": total_chunks,
            "avg_chunk_size": avg_chunk_size,
            "article_coverage_pct": round((articles_detected / total_chunks * 100), 1) if total_chunks > 0 else 0.0,
            "section_coverage_pct": round((sections_detected / total_chunks * 100), 1) if total_chunks > 0 else 0.0,
        }

        logger.info(f"Ingestion complete: {total_chunks} chunks generated from {useful_pages} pages (Avg size: {avg_chunk_size} chars).")

        # Optional: Save JSON artifact to data/processed/
        if save_output:
            self._save_chunks_json(chunks, stats)

        return chunks, stats

    def _save_chunks_json(self, chunks: List[Document], stats: Dict[str, Any]) -> str:
        """
        Saves chunks to data/processed/chunks.json for debugging/inspection.
        """
        output_dir = Path(self.pdf_path).parent.parent / "data" / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "chunks.json"

        data = {
            "stats": stats,
            "chunks": [
                {
                    "chunk_id": c.metadata.get("chunk_id"),
                    "article_title": c.metadata.get("article_title"),
                    "section": c.metadata.get("section"),
                    "page": c.metadata.get("page"),
                    "length": c.metadata.get("length"),
                    "content": c.page_content,
                }
                for c in chunks
            ]
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved processed chunks artifact to: {output_file}")
        return str(output_file)

def run_ingestion(pdf_path: str = None, max_pages: int = None, save_output: bool = False) -> Tuple[List[Document], Dict[str, Any]]:
    """
    Public entrypoint for running ingestion pipeline.
    """
    pipeline = IngestionPipeline(pdf_path=pdf_path)
    return pipeline.run(max_pages=max_pages, save_output=save_output)

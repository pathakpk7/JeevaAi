import hashlib
import re
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.logging_config import logger

KNOWN_SECTIONS = [
    "Definition",
    "Purpose",
    "Description",
    "Causes and symptoms",
    "Causes & symptoms",
    "Diagnosis",
    "Treatment",
    "Alternative treatment",
    "Prognosis",
    "Prevention",
    "Side effects",
    "Interactions",
    "Precautions",
    "Risks",
    "Preparation",
    "Aftercare",
    "Complications",
    "Resources",
    "Key terms",
    "Organizations",
]

class MedicalSemanticChunker:
    """
    Semantic chunker optimized for medical entries. Detects article titles and section headings,
    splits on semantic boundaries, and attaches deterministic metadata and IDs.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "; ", ", ", " "],
            keep_separator=True,
        )

    @staticmethod
    def generate_chunk_id(doc_name: str, page: int, article: str, section: str, chunk_idx: int, content: str) -> str:
        """
        Generates a deterministic unique ID for a chunk based on source metadata and content hash.
        """
        raw_key = f"{doc_name}:{page}:{article}:{section}:{chunk_idx}:{content[:50]}"
        return hashlib.md5(raw_key.encode("utf-8")).hexdigest()

    def detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Parses text into section blocks based on known medical section headings.
        Returns a list of dicts: [{"section": str, "content": str}].
        """
        lines = text.splitlines()
        section_blocks = []
        current_section = "Overview"
        current_lines = []

        section_pattern = re.compile(
            r"^\s*(" + "|".join(re.escape(s) for s in KNOWN_SECTIONS) + r")\s*$",
            re.IGNORECASE
        )

        for line in lines:
            line_str = line.strip()
            match = section_pattern.match(line_str)
            if match:
                if current_lines:
                    block_content = "\n".join(current_lines).strip()
                    if block_content:
                        section_blocks.append({
                            "section": current_section,
                            "content": block_content
                        })
                    current_lines = []
                current_section = match.group(1).capitalize()
            else:
                current_lines.append(line)

        if current_lines:
            block_content = "\n".join(current_lines).strip()
            if block_content:
                section_blocks.append({
                    "section": current_section,
                    "content": block_content
                })

        return section_blocks if section_blocks else [{"section": "Overview", "content": text}]

    def chunk_document(self, doc: Document, current_article: Optional[str] = None) -> List[Document]:
        """
        Splits a single cleaned Document into semantic chunks with enriched metadata.
        """
        text = doc.page_content.strip()
        if not text:
            return []

        base_meta = dict(doc.metadata)
        article_title = (
            current_article
            or base_meta.get("footer_article")
            or base_meta.get("article_title")
            or "General Medical Entry"
        )

        section_blocks = self.detect_sections(text)
        chunks: List[Document] = []
        chunk_counter = 0

        for block in section_blocks:
            section_name = block["section"]
            block_text = block["content"]

            if not block_text:
                continue

            # Split block text if larger than chunk_size
            sub_chunks = self.text_splitter.split_text(block_text)

            for sub_text in sub_chunks:
                clean_sub_text = sub_text.strip()
                if not clean_sub_text:
                    continue

                chunk_counter += 1
                chunk_id = self.generate_chunk_id(
                    doc_name=str(base_meta.get("document_name", "doc")),
                    page=int(base_meta.get("page", 0)),
                    article=article_title,
                    section=section_name,
                    chunk_idx=chunk_counter,
                    content=clean_sub_text,
                )

                chunk_meta = {
                    "source": str(base_meta.get("source", "")),
                    "document_name": str(base_meta.get("document_name", "")),
                    "page": int(base_meta.get("page", 0)),
                    "article_title": article_title,
                    "section": section_name,
                    "chunk_id": chunk_id,
                    "length": len(clean_sub_text),
                }

                chunks.append(Document(page_content=clean_sub_text, metadata=chunk_meta))

        return chunks

    def chunk_documents(self, docs: List[Document]) -> List[Document]:
        """
        Processes a list of cleaned documents into semantic chunks while maintaining article context across pages.
        """
        all_chunks: List[Document] = []
        active_article = None

        for doc in docs:
            footer_art = doc.metadata.get("footer_article")
            if footer_art:
                active_article = footer_art

            page_chunks = self.chunk_document(doc, current_article=active_article)
            all_chunks.extend(page_chunks)

        logger.info(f"Generated {len(all_chunks)} semantic chunks from {len(docs)} pages.")
        return all_chunks

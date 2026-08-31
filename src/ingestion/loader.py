import os
from pathlib import Path
from typing import List, Generator
import pypdf
from langchain_core.documents import Document
from src.config import get_config
from src.logging_config import logger

class PDFLoaderError(Exception):
    """Custom exception raised when PDF loading fails."""
    pass

class PDFLoader:
    """
    Page-by-page PDF loader that extracts raw text and populates core metadata using native pypdf.
    Avoids loading full duplicated copies of large PDFs into memory.
    """
    def __init__(self, pdf_path: str = None):
        config = get_config()
        self.pdf_path = Path(pdf_path) if pdf_path else config.get_absolute_pdf_path()
        self.document_name = self.pdf_path.name

    def validate_source(self) -> None:
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF source file not found at: {self.pdf_path}")
        if not self.pdf_path.is_file():
            raise PDFLoaderError(f"Specified path is not a file: {self.pdf_path}")

    def load_pages(self, max_pages: int = None) -> List[Document]:
        """
        Loads PDF pages into LangChain Document objects with standard metadata.
        """
        self.validate_source()
        logger.info(f"Loading PDF document: {self.pdf_path}")

        try:
            reader = pypdf.PdfReader(str(self.pdf_path))
            total_pdf_pages = len(reader.pages)
        except Exception as e:
            raise PDFLoaderError(f"Failed to open PDF file '{self.pdf_path}': {str(e)}") from e

        documents = []
        limit = min(max_pages, total_pdf_pages) if max_pages else total_pdf_pages

        for idx in range(limit):
            try:
                page_text = reader.pages[idx].extract_text() or ""
            except Exception as page_err:
                logger.warning(f"Error extracting text from page {idx + 1} of {self.document_name}: {page_err}")
                page_text = ""

            metadata = {
                "source": str(self.pdf_path),
                "document_name": self.document_name,
                "page": idx + 1,  # 1-indexed page number
            }
            documents.append(Document(page_content=page_text, metadata=metadata))

        logger.info(f"Successfully loaded {len(documents)} pages from {self.document_name}")
        return documents

    def stream_pages(self, max_pages: int = None) -> Generator[Document, None, None]:
        """
        Stream PDF pages one by one for low-memory processing.
        """
        self.validate_source()
        try:
            reader = pypdf.PdfReader(str(self.pdf_path))
            total_pdf_pages = len(reader.pages)
            limit = min(max_pages, total_pdf_pages) if max_pages else total_pdf_pages

            for idx in range(limit):
                try:
                    page_text = reader.pages[idx].extract_text() or ""
                except Exception as page_err:
                    logger.warning(f"Error extracting text from page {idx + 1}: {page_err}")
                    page_text = ""

                metadata = {
                    "source": str(self.pdf_path),
                    "document_name": self.document_name,
                    "page": idx + 1,
                }
                yield Document(page_content=page_text, metadata=metadata)
        except Exception as e:
            raise PDFLoaderError(f"Error streaming PDF pages from '{self.pdf_path}': {str(e)}") from e

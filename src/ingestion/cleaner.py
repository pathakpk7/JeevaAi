import re
from typing import Tuple, List, Optional
from langchain_core.documents import Document

class TextCleaner:
    """
    Deterministic cleaning layer that removes extraction noise, running headers/footers,
    and formatting artifacts while strictly preserving medical knowledge and meaning.
    """

    FOOTER_PATTERN = re.compile(
        r"GALE\s+ENCYCLOPEDIA\s+OF\s+MEDICINE\s*\d*\s*\d*",
        re.IGNORECASE
    )

    @staticmethod
    def clean_text(raw_text: str) -> Tuple[str, Optional[str]]:
        """
        Cleans raw extracted text and extracts running footer article title if present.
        Returns (cleaned_text, detected_footer_article).
        """
        if not raw_text:
            return "", None

        lines = [line.strip() for line in raw_text.splitlines()]
        cleaned_lines: List[str] = []
        detected_footer_article: Optional[str] = None

        for idx, line in enumerate(lines):
            # Check for footer banner
            if TextCleaner.FOOTER_PATTERN.search(line):
                # The line directly following the footer banner often contains the article title
                if idx + 1 < len(lines) and lines[idx + 1] and not TextCleaner.FOOTER_PATTERN.search(lines[idx + 1]):
                    potential_title = lines[idx + 1].strip()
                    # Only accept as article title if reasonably short and non-numeric
                    if 3 <= len(potential_title) <= 80 and not potential_title.isdigit():
                        detected_footer_article = potential_title
                continue

            # Skip lines that match the detected footer article at the very end of page
            if detected_footer_article and line == detected_footer_article and idx >= len(lines) - 2:
                continue

            cleaned_lines.append(line)

        text = "\n".join(cleaned_lines)

        # Normalize unicode quotes and unicode replacement character (\ufffd)
        text = text.replace("\ufffd", "'").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')

        # Fix hyphenated words broken across line breaks (e.g., "treat-\nments" -> "treatments")
        text = re.sub(r"(\b[a-zA-Z]{2,})-\n([a-zA-Z]{2,}\b)", r"\1\2", text)

        # Normalize multiple spaces (preserving newlines)
        text = re.sub(r"[ \t]+", " ", text)

        # Normalize multiple newlines to standard paragraph breaks (max 2 consecutive newlines)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip(), detected_footer_article

    def clean_document(self, doc: Document) -> Document:
        """
        Cleans a LangChain Document's page content and enriches metadata with detected footer article.
        """
        cleaned_text, footer_article = self.clean_text(doc.page_content)
        metadata = dict(doc.metadata)
        if footer_article:
            metadata["footer_article"] = footer_article

        return Document(page_content=cleaned_text, metadata=metadata)

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    # Application & Server Environment
    APP_ENV: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 5000
    DEBUG: bool = True

    # Data Paths
    PDF_PATH: str = "data/The_GALE_ENCYCLOPEDIA_of_MEDICINE_SECOND.pdf"
    VECTORSTORE_PATH: str = "vectorstore/chroma_db"
    VECTORSTORE_COLLECTION: str = "medical_knowledge"

    # LLM Provider Configuration
    LLM_PROVIDER: str = "openai"  # Options: openai, gemini, local, mock
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_OUTPUT_TOKENS: int = 1024
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Embedding Configuration
    EMBEDDING_PROVIDER: str = "huggingface"  # Options: huggingface, openai, gemini
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Retrieval & Generation Settings
    RETRIEVAL_TOP_K: int = 4
    RETRIEVAL_MIN_SCORE: float = 0.0
    GENERATION_MAX_CONTEXT_CHUNKS: int = 4

    # Conversational Chat Settings
    CHAT_MAX_HISTORY_MESSAGES: int = 12
    CHAT_MAX_INPUT_CHARS: int = 2000
    DEFAULT_LANGUAGE: str = "English"
    MAX_UPLOAD_SIZE_MB: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_absolute_pdf_path(self) -> Path:
        path = Path(self.PDF_PATH)
        if not path.is_absolute():
            project_root = Path(__file__).resolve().parent.parent
            path = project_root / path
        return path

    def get_absolute_vectorstore_path(self) -> Path:
        path = Path(self.VECTORSTORE_PATH)
        if not path.is_absolute():
            project_root = Path(__file__).resolve().parent.parent
            path = project_root / path
        return path

    def validate_pdf_exists(self) -> bool:
        pdf_file = self.get_absolute_pdf_path()
        return pdf_file.exists() and pdf_file.is_file()

def get_config() -> AppConfig:
    return AppConfig()

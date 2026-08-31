import pytest
from pathlib import Path
from src.config import AppConfig, get_config

def test_default_config_loading():
    config = get_config()
    assert isinstance(config, AppConfig)
    assert config.PDF_PATH == "data/The_GALE_ENCYCLOPEDIA_of_MEDICINE_SECOND.pdf"
    assert config.EMBEDDING_PROVIDER == "huggingface"
    assert config.RETRIEVAL_TOP_K == 4

def test_pdf_path_resolution():
    config = get_config()
    abs_path = config.get_absolute_pdf_path()
    assert isinstance(abs_path, Path)
    assert abs_path.name == "The_GALE_ENCYCLOPEDIA_of_MEDICINE_SECOND.pdf"

def test_pdf_exists_validation():
    config = get_config()
    # The project PDF file exists in data/
    assert config.validate_pdf_exists() is True

def test_missing_pdf_handling(monkeypatch):
    config = get_config()
    # Mock PDF_PATH to a non-existent file
    monkeypatch.setattr(config, "PDF_PATH", "data/non_existent_file.pdf")
    assert config.validate_pdf_exists() is False

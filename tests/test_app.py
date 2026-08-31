import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    html_text = response.get_data(as_text=True)
    assert "JeevaAi MedeBot" in html_text
    assert "<!DOCTYPE html>" in html_text

def test_health_check_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["pdf_exists"] is True
    assert "llm_provider" in data
    assert "embedding_provider" in data

def test_health_check_missing_pdf(monkeypatch):
    from src.config import AppConfig
    # Monkeypatch validate_pdf_exists to return False
    monkeypatch.setattr(AppConfig, "validate_pdf_exists", lambda self: False)
    
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        response = c.get("/api/health")
        assert response.status_code == 500
        data = response.get_json()
        assert data["status"] == "degraded"
        assert data["pdf_exists"] is False

def test_upload_report_endpoint(client):
    import io
    data = {
        'file': (io.BytesIO(b"Patient Report: Hemoglobin 14.2 g/dL, Glucose 95 mg/dL. Normal findings."), "lab_report.txt"),
        'language': 'English'
    }
    response = client.post("/api/upload-report", data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    res_json = response.get_json()
    assert res_json["filename"] == "lab_report.txt"
    assert "extracted_text" in res_json
    assert "analysis" in res_json


# PRODUCTION DEPLOYMENT & OPERATIONAL GUIDE
**System Name:** Medical Knowledge Assistant  
**Phase:** Phase 8 — Production Readiness & Packaging  
**WSGI Servers:** Waitress (Windows) / Gunicorn (Linux/Docker)  
**Vector Store:** Persistent ChromaDB (`vectorstore/chroma_db`)  

---

## 1. System Architecture & Component Strategy

The **Medical Knowledge Assistant** is deployed as a WSGI containerized web application serving an evidence-grounded RAG pipeline and a Knowledge Explorer.

### Key Deployment Characteristics:
* **Canonical App Factory:** `app:create_app()` serves as the single initialization point for both development and production.
* **Stateless API Core:** API routes are stateless; session state is managed on client-side or in bounded memory sessions.
* **Generated Infrastructure Isolation:** The persistent vector store (`vectorstore/chroma_db`) is persistent data infrastructure mounted via Docker volume. Container startup never triggers expensive PDF ingestion or re-embedding.

---

## 2. Environment Configuration

Copy `.env.example` to `.env` on production servers.

| Variable Name | Production Setting | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `production` | Enables production mode; suppresses Flask debug messages. |
| `HOST` | `0.0.0.0` | Listens on all container/host network interfaces. |
| `PORT` | `5000` | Exposed HTTP service port. |
| `DEBUG` | `false` | Disables Flask debug mode and stack trace dumps. |
| `LLM_PROVIDER` | `openai` | Primary LLM provider for grounded generation. |
| `LLM_MODEL` | `gpt-4o-mini` | Cost-efficient grounded generation model. |
| `OPENAI_API_KEY` | `sk-proj-...` | Production OpenAI API key (Read exclusively by backend server). |
| `EMBEDDING_PROVIDER` | `huggingface` | Local embedding provider (`all-MiniLM-L6-v2`). |

---

## 3. WSGI Server Execution

### 3.1 Windows Production Server (Waitress)
Run Waitress WSGI server on Windows:

```powershell
.\.venv\Scripts\python.exe -c "import waitress, app; waitress.serve(app.create_app(), host='0.0.0.0', port=5000)"
```

### 3.2 Linux / Docker Container (Gunicorn)
Run Gunicorn WSGI server inside Linux containers:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 --timeout 120 "app:create_app()"
```

---

## 4. Docker Containerization

### 4.1 Build Docker Image
```bash
docker build -t medical-knowledge-assistant:latest .
```

### 4.2 Run Production Container
Mount the persistent vector database directory to `/app/vectorstore/chroma_db`:

```bash
docker run -d \
  --name medical-assistant \
  -p 5000:5000 \
  -e OPENAI_API_KEY="your_production_api_key" \
  -v $(pwd)/vectorstore/chroma_db:/app/vectorstore/chroma_db \
  medical-knowledge-assistant:latest
```

---

## 5. Health & Readiness Probes

Container orchestrators (Kubernetes, AWS ECS, Google Cloud Run) monitor service availability using dedicated endpoints:

* **Liveness Probe (`GET /api/health`):** Fast check verifying HTTP server responsiveness and PDF source file presence.
* **Readiness Probe (`GET /api/ready`):** Verifies that ChromaDB persistent vector collection exists and contains indexed documents (returns HTTP 200 `ready: true`).

---

## 6. Observability & Security Features

* **Request ID Tracing:** Every HTTP request is assigned a unique `X-Request-ID` header, enabling end-to-end log correlation.
* **Security Headers:** Injected into every HTTP response:
  * `X-Content-Type-Options: nosniff`
  * `X-Frame-Options: SAMEORIGIN`
  * `Referrer-Policy: strict-origin-when-cross-origin`
* **API Key Protection:** Zero LLM secrets or API keys are exposed to the frontend browser bundle or written to logs.

---

## 7. Production Verification

Run the production smoke test suite (offline, requires zero paid API keys):

```powershell
.\.venv\Scripts\python.exe scripts/smoke_test_production.py
```

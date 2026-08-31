# LOCAL DEVELOPMENT & WEB APPLICATION SETUP GUIDE
**Project:** End-to-End Medical Knowledge Assistant (Generative AI)  
**Environment:** Isolated Python 3.13 Virtual Environment (`.venv`)  
**OS Target:** Windows (PowerShell)  

---

## 1. Environment Initialization

Ensure the local virtual environment is initialized and dependencies are installed:

```powershell
# Activate local virtual environment
.\.venv\Scripts\Activate.ps1

# Verify Python version (Target: 3.13+)
python --version
```

---

## 2. Configuration Setup

Copy `.env.example` to `.env` and configure settings:

```powershell
Copy-Item .env.example .env
```

### Key `.env` Configuration Variables:

```env
APP_ENV=development
HOST=127.0.0.1
PORT=5000
DEBUG=true

PDF_PATH=data/The_GALE_ENCYCLOPEDIA_of_MEDICINE_SECOND.pdf
VECTORSTORE_PATH=vectorstore/chroma_db
VECTORSTORE_COLLECTION=medical_knowledge

# LLM Provider (options: openai, mock)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.2
LLM_MAX_OUTPUT_TOKENS=1024
OPENAI_API_KEY=your_openai_api_key_here

# Embedding Provider (options: huggingface)
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Retrieval & Generation Settings
RETRIEVAL_TOP_K=4
RETRIEVAL_MIN_SCORE=0.0
GENERATION_MAX_CONTEXT_CHUNKS=4

# Conversational Chat Settings
CHAT_MAX_HISTORY_MESSAGES=12
CHAT_MAX_INPUT_CHARS=2000
```

---

## 3. Launching the Web Application & Server

A single command starts the Flask backend server and serves the frontend web application:

```powershell
.\.venv\Scripts\python.exe app.py
```

* **Web UI URL:** `http://127.0.0.1:5000`
* **Health API:** `http://127.0.0.1:5000/api/health`
* **Chat API:** `http://127.0.0.1:5000/api/chat`
* **Knowledge Explorer Search API:** `http://127.0.0.1:5000/api/search?q=caffeine&limit=10&mode=hybrid`

---

## 4. API Testing via Curl

### 4.1 Knowledge Explorer Search API (`GET /api/search`)
```powershell
curl.exe -X GET "http://127.0.0.1:5000/api/search?q=caffeine&limit=5&mode=hybrid"
```

### 4.2 Conversational Chat Turn 1 (`POST /api/chat`)
```powershell
curl.exe -X POST http://127.0.0.1:5000/api/chat `
  -H "Content-Type: application/json" `
  -d '{\"message\": \"What are the symptoms of caffeine overdose?\"}'
```

### 4.3 Conversational Chat Turn 2 (Follow-up)
```powershell
curl.exe -X POST http://127.0.0.1:5000/api/chat `
  -H "Content-Type: application/json" `
  -d '{\"conversation_id\": \"<RETURNED_UUID>\", \"message\": \"What are its side effects?\"}'
```

---

## 5. CLI & Benchmark Tools

```powershell
# 1. Run full automated test suite (51 passing tests)
.\.venv\Scripts\pytest.exe

# 2. Run comparative retrieval benchmark (Dense vs Lexical vs Hybrid RRF)
.\.venv\Scripts\python.exe scripts/benchmark_retrieval.py

# 3. Multi-turn chat CLI smoke test (Offline Mock provider)
.\.venv\Scripts\python.exe scripts/smoke_test_chat.py --provider mock
```

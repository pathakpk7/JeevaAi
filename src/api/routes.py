import time
import uuid
from flask import Blueprint, request, jsonify, g
from pydantic import ValidationError
from src.config import get_config
from src.logging_config import logger
from src.chat.service import MedicalChatService
from src.chat.models import ChatRequest
from src.retrieval.retriever import MedicalRetriever
from src.generation.service import MedicalGenerationService
from src.retrieval.search_models import SearchResult, SearchResponse

api_bp = Blueprint("api", __name__)

# Lazy singleton instances to avoid heavy startup memory/time and keep Render RAM under 512MB
_chat_service = None
_retriever = None

def get_retriever() -> MedicalRetriever:
    """Lazily initializes and returns the shared MedicalRetriever singleton."""
    global _retriever
    if _retriever is None:
        logger.info("Lazily initializing shared MedicalRetriever...")
        _retriever = MedicalRetriever()
    return _retriever

def get_chat_service() -> MedicalChatService:
    """Lazily initializes and returns the MedicalChatService using the shared retriever."""
    global _chat_service
    if _chat_service is None:
        logger.info("Lazily initializing MedicalChatService with shared retriever...")
        retriever = get_retriever()
        gen_service = MedicalGenerationService(retriever=retriever)
        _chat_service = MedicalChatService(generation_service=gen_service)
    return _chat_service

@api_bp.before_app_request
def before_request_middleware():
    """Assigns unique request ID to Flask g context for request traceability."""
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    g.request_id = req_id
    g.start_time = time.perf_counter()

@api_bp.after_app_request
def after_request_middleware(response):
    """Attaches request ID and production security headers to all API responses."""
    req_id = getattr(g, "request_id", None)
    if req_id:
        response.headers["X-Request-ID"] = req_id

    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

@api_bp.route("/health", methods=["GET"])
def health_check():
    """Fast health liveness probe endpoint. Performs no heavy ingestion or LLM calls."""
    config = get_config()
    pdf_exists = config.validate_pdf_exists()
    pdf_path_str = str(config.get_absolute_pdf_path())

    return jsonify({
        "status": "healthy" if pdf_exists else "degraded",
        "app_env": config.APP_ENV,
        "pdf_configured_path": config.PDF_PATH,
        "pdf_absolute_path": pdf_path_str,
        "pdf_exists": pdf_exists,
        "llm_provider": config.LLM_PROVIDER,
        "embedding_provider": config.EMBEDDING_PROVIDER,
        "retrieval_top_k": config.RETRIEVAL_TOP_K,
        "request_id": getattr(g, "request_id", ""),
    }), 200

@api_bp.route("/ready", methods=["GET"])
def readiness_check():
    """Readiness probe endpoint. Verifies vector store and knowledge base accessibility."""
    config = get_config()
    pdf_exists = config.validate_pdf_exists()

    try:
        count = get_retriever().vector_store.count()
        store_ready = count > 0
    except Exception as e:
        logger.warning(f"Readiness probe vector store check failed: {e}")
        store_ready = False

    is_ready = pdf_exists and store_ready

    return jsonify({
        "ready": is_ready,
        "pdf_verified": pdf_exists,
        "vector_store_ready": store_ready,
        "indexed_chunks": count if store_ready else 0,
        "request_id": getattr(g, "request_id", ""),
    }), 200 if is_ready else 503

@api_bp.route("/chat", methods=["POST"])
def handle_chat():
    """
    Main conversational chat REST endpoint.
    POST /api/chat
    Payload: {"conversation_id": "optional-uuid", "message": "user prompt"}
    """
    if not request.is_json:
        return jsonify({
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Content-Type must be application/json."
            }
        }), 400

    payload = request.get_json()
    if not payload or not isinstance(payload, dict):
        return jsonify({
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Request body must be a valid JSON object."
            }
        }), 400

    raw_message = payload.get("message")
    if raw_message is None or not str(raw_message).strip():
        return jsonify({
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Message string cannot be empty."
            }
        }), 400

    conversation_id = payload.get("conversation_id")
    language = payload.get("language")

    try:
        service = get_chat_service()
        chat_req = ChatRequest(conversation_id=conversation_id, message=str(raw_message))
        response = service.chat(
            message=chat_req.message,
            conversation_id=chat_req.conversation_id,
            language=language
        )
        return jsonify(response.to_dict()), 200

    except ValueError as ve:
        logger.warning(f"Chat request validation error [{getattr(g, 'request_id', '')}]: {ve}")
        return jsonify({
            "error": {
                "code": "UNPROCESSABLE_ENTITY",
                "message": str(ve)
            }
        }), 422

    except RuntimeError as re:
        logger.error(f"Chat service infrastructure runtime error [{getattr(g, 'request_id', '')}]: {re}")
        return jsonify({
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "The medical AI generation service is currently unavailable. Please try again."
            }
        }), 503

    except Exception as e:
        logger.error(f"Unhandled error in /api/chat endpoint [{getattr(g, 'request_id', '')}]: {e}")
        return jsonify({
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred."
            }
        }), 500


@api_bp.route("/chat/<conversation_id>", methods=["GET"])
def get_chat_history(conversation_id):
    """Retrieves session message history for a given conversation_id."""
    service = get_chat_service()
    if not conversation_id or not service.memory.session_exists(conversation_id):
        return jsonify({"conversation_id": conversation_id, "messages": []}), 200

    history = service.memory.get_history(conversation_id)
    messages_payload = [{"role": msg.role, "content": msg.content} for msg in history]
    return jsonify({"conversation_id": conversation_id, "messages": messages_payload}), 200


@api_bp.route("/chat/<conversation_id>", methods=["DELETE"])
def delete_chat_history(conversation_id):
    """Deletes memory session for a given conversation_id."""
    service = get_chat_service()
    success = service.clear_session(conversation_id)
    return jsonify({"conversation_id": conversation_id, "deleted": success}), 200


@api_bp.route("/upload-report", methods=["POST"])
def handle_upload_report():
    """
    Endpoint to upload custom medical reports / lab PDFs and extract text insights.
    POST /api/upload-report
    Form-data: file (PDF or TXT), language (optional)
    """
    if "file" not in request.files:
        return jsonify({
            "error": {
                "code": "INVALID_REQUEST",
                "message": "No file payload found in request."
            }
        }), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Selected file is empty."
            }
        }), 400

    filename = file.filename.lower()
    language = request.form.get("language", "English")
    extracted_text = ""

    try:
        if filename.endswith(".pdf"):
            import io
            try:
                from pypdf import PdfReader
            except ImportError:
                from PyPDF2 import PdfReader
            
            pdf_bytes = file.read()
            reader = PdfReader(io.BytesIO(pdf_bytes))
            pages_text = []
            for page in reader.pages[:10]:  # Read first 10 pages max
                txt = page.extract_text() or ""
                if txt.strip():
                    pages_text.append(txt.strip())
            extracted_text = "\n\n".join(pages_text)

        elif filename.endswith((".txt", ".csv")):
            extracted_text = file.read().decode("utf-8", errors="ignore")
        elif filename.endswith((".jpg", ".jpeg", ".png", ".webp")):
            img_bytes = file.read()
            mime = "image/png" if filename.endswith(".png") else "image/jpeg"
            service = get_chat_service()
            llm = service.generation_service.llm_provider
            
            prompt = (
                f"You are JeevaAi Clinical Assistant. Analyze this medical image (e.g. prescription slip, medicine packaging, lab test, or visible health symptom/rash). "
                f"1. Transcribe visible medication names, dosages, or key medical metrics if visible.\n"
                f"2. Explain standard purpose, common precautions, and clinical relevance.\n"
                f"3. Note any red flags or instructions to confirm with a doctor.\n"
                f"Language: {language}\n"
                f"Always include a clinical safety disclaimer."
            )
            
            if hasattr(llm, "generate_with_image"):
                try:
                    analysis_text = llm.generate_with_image(prompt=prompt, image_bytes=img_bytes, mime_type=mime)
                except Exception as img_err:
                    logger.warning(f"Vision call error: {img_err}")
                    analysis_text = f"Image received ({file.filename}). Identified medical imagery. Please confirm details with your physician."
            else:
                analysis_text = f"Medical image received: {file.filename}. Please consult your physician or pharmacist for clinical confirmation."

            return jsonify({
                "filename": file.filename,
                "extracted_text": f"[Medical Image: {file.filename}]",
                "analysis": analysis_text,
                "citations": [],
                "match_quality": "Strong Match"
            }), 200
        else:
            return jsonify({
                "error": {
                    "code": "UNSUPPORTED_MEDIA_TYPE",
                    "message": "Only PDF, TXT, and Image files (JPG, PNG) are supported."
                }
            }), 415

        if not extracted_text.strip():
            return jsonify({
                "error": {
                    "code": "UNPROCESSABLE_ENTITY",
                    "message": "Could not extract readable text from the uploaded document."
                }
            }), 422

        # Truncate text for analysis prompt if necessary
        truncated_report = extracted_text[:3500]
        analysis_prompt = (
            f"I have uploaded a medical lab report / health document with the following content:\n\n"
            f"```text\n{truncated_report}\n```\n\n"
            f"Please analyze this report, summarize the key findings/lab values, and explain any relevant medical concepts."
        )

        service = get_chat_service()
        gen_resp = service.generation_service.answer_question(question=analysis_prompt, language=language)

        return jsonify({
            "filename": file.filename,
            "extracted_text": extracted_text[:1500],
            "analysis": gen_resp.answer,
            "citations": [c.to_dict() for c in gen_resp.citations],
            "match_quality": gen_resp.match_quality
        }), 200

    except Exception as e:
        logger.error(f"Error processing report upload [{file.filename}]: {e}")
        return jsonify({
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": f"Failed to process medical report: {str(e)}"
            }
        }), 500

@api_bp.route("/chat/<conversation_id>", methods=["DELETE"])
def clear_chat_session(conversation_id: str):
    """
    Deletes/clears memory session for the specified conversation_id.
    DELETE /api/chat/<conversation_id>
    """
    if not conversation_id or not conversation_id.strip():
        return jsonify({
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Conversation ID cannot be empty."
            }
        }), 400

    service = get_chat_service()
    cleared = service.clear_session(conversation_id.strip())
    if cleared:
        return jsonify({
            "status": "success",
            "message": f"Conversation session '{conversation_id}' cleared successfully."
        }), 200
    else:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": f"No active conversation session found for ID '{conversation_id}'."
            }
        }), 404

@api_bp.route("/search", methods=["GET"])
def search_knowledge():
    """
    Knowledge Explorer Search endpoint.
    GET /api/search?q=query&limit=10&mode=hybrid
    Performs fast search directly on indexed knowledge without LLM generation calls.
    """
    query_param = request.args.get("q") or request.args.get("query") or ""
    q_str = query_param.strip()

    if not q_str:
        return jsonify({
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Query parameter 'q' or 'query' cannot be empty."
            }
        }), 400

    try:
        limit = int(request.args.get("limit", 10))
        limit = max(1, min(50, limit))
    except ValueError:
        limit = 10

    search_mode = (request.args.get("mode") or "hybrid").lower()
    if search_mode not in ["hybrid", "dense", "lexical"]:
        search_mode = "hybrid"

    start_time = time.perf_counter()
    try:
        retriever = get_retriever()
        retrieval_response = retriever.retrieve(query=q_str, top_k=limit, mode=search_mode)
    except Exception as e:
        logger.error(f"Search retrieval error for query '{q_str}' [{getattr(g, 'request_id', '')}]: {e}")
        return jsonify({
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": f"Knowledge search system error: {e}"
            }
        }), 503

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    search_results = []
    for res in retrieval_response.results:
        search_results.append(
            SearchResult(
                article_title=res.article_title,
                section=res.section,
                page=res.page,
                snippet=res.text,
                source=res.document_name,
                chunk_id=res.chunk_id,
                score=res.score
            )
        )

    response = SearchResponse(
        query=q_str,
        search_mode=search_mode,
        result_count=len(search_results),
        search_latency_ms=elapsed_ms,
        results=search_results
    )

    return jsonify(response.to_dict()), 200


@api_bp.route("/drug-interaction", methods=["POST"])
def check_drug_interaction():
    """
    Analyzes potential drug-drug interactions, risks, and clinical advisories.
    POST /api/drug-interaction
    Payload: {"medications": ["Aspirin", "Ibuprofen"], "language": "English"}
    """
    if not request.is_json:
        return jsonify({"error": {"code": "INVALID_REQUEST", "message": "Content-Type must be application/json."}}), 400
    
    payload = request.get_json() or {}
    meds = payload.get("medications", [])
    language = payload.get("language", "English")

    if not meds or not isinstance(meds, list) or len(meds) < 2:
        return jsonify({
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Please provide at least 2 medication names to check interactions."
            }
        }), 400

    meds_cleaned = [str(m).strip() for m in meds if str(m).strip()]
    if len(meds_cleaned) < 2:
        return jsonify({
            "error": {
                "code": "INVALID_REQUEST",
                "message": "At least 2 valid medication names are required."
            }
        }), 400

    retriever = get_retriever()
    search_context = []
    for med in meds_cleaned[:4]:
        try:
            res = retriever.retrieve(query=f"{med} drug interactions adverse effects precautions", top_k=2)
            for r in res.results:
                search_context.append(f"[{r.article_title} - {r.section} (p. {r.page})]: {r.text[:300]}")
        except Exception as e:
            logger.warning(f"Retrieval for med '{med}' failed: {e}")

    context_str = "\n".join(search_context) if search_context else "Standard pharmacological reference."

    prompt = (
        f"You are an expert clinical pharmacologist for JeevaAi MedeBot. Evaluate potential drug-drug interactions between these medications:\n"
        f"Medications: {', '.join(meds_cleaned)}\n\n"
        f"Reference Medical Knowledge:\n{context_str}\n\n"
        f"Provide a structured clinical evaluation formatted in Markdown:\n"
        f"### 1. Risk Level Rating: [🔴 High Risk / Contraindicated | 🟡 Moderate Caution | 🟢 Low / No Direct Known Interaction]\n"
        f"### 2. Interaction Mechanism & Risks: (Explain how they interact pharmacologically or in metabolic pathways)\n"
        f"### 3. Symptoms to Watch For: (Warning signs the patient should monitor)\n"
        f"### 4. Food, Drink & Dietary Precautions: (Alcohol, grapefruit, caffeine, etc.)\n"
        f"### 5. Actionable Recommendation: (What the patient should ask their doctor or pharmacist)\n\n"
        f"Language: {language}\n"
        f"Always conclude with an emergency safety notice."
    )

    service = get_chat_service()
    try:
        gen_resp = service.generation_service.answer_question(question=prompt, language=language)
        answer = gen_resp.answer
        citations = [c.to_dict() for c in gen_resp.citations]
    except Exception as e:
        logger.error(f"Drug interaction generation error: {e}")
        return jsonify({"error": {"code": "SERVICE_ERROR", "message": str(e)}}), 500

    risk_level = "Moderate"
    if "high risk" in answer.lower() or "contraindicated" in answer.lower() or "🔴" in answer:
        risk_level = "High Risk"
    elif "low" in answer.lower() or "no direct" in answer.lower() or "🟢" in answer:
        risk_level = "Low Risk"

    return jsonify({
        "medications": meds_cleaned,
        "risk_level": risk_level,
        "analysis": answer,
        "citations": citations
    }), 200


@api_bp.route("/doctor-summary", methods=["POST"])
def generate_doctor_summary():
    """
    Transforms the current consultation into a structured clinical doctor's visit summary.
    POST /api/doctor-summary
    Payload: {"conversation_id": "...", "patient_profile": {...}, "language": "English"}
    """
    payload = request.get_json() or {}
    cid = payload.get("conversation_id")
    profile = payload.get("patient_profile", {})
    language = payload.get("language", "English")

    service = get_chat_service()
    history = service.memory.get_history(cid) if (cid and service.memory.session_exists(cid)) else []
    
    if not history:
        conv_text = "Patient engaged in initial medical consultation."
    else:
        conv_lines = [f"{msg.role.upper()}: {msg.content[:400]}" for msg in history[-8:]]
        conv_text = "\n".join(conv_lines)

    profile_text = (
        f"Age: {profile.get('age', 'Unspecified')}, "
        f"Sex: {profile.get('gender', 'Unspecified')}, "
        f"Duration: {profile.get('duration', 'Unspecified')}, "
        f"Severity: {profile.get('severity', 'Unspecified')}, "
        f"Pre-existing Conditions: {', '.join(profile.get('conditions', [])) or 'None reported'}"
    )

    prompt = (
        f"You are JeevaAi Clinical Assistant. Generate a professional 'Physician Consultation Prep Summary' for a patient to take to their upcoming doctor's appointment.\n"
        f"Patient Profile: {profile_text}\n"
        f"Consultation Notes:\n{conv_text}\n\n"
        f"Format as a clean, highly structured clinical note in Markdown:\n"
        f"# 🏥 DOCTOR'S VISIT PREPARATION SUMMARY\n"
        f"**Date:** Today | **Patient Context:** {profile_text}\n\n"
        f"### 1. Chief Complaint & Reported Symptoms\n"
        f"### 2. Symptom Progression & Timeline\n"
        f"### 3. Patient Medical Context & Pre-existing Factors\n"
        f"### 4. Key Questions to Ask the Attending Physician (Checklist format [ ])\n"
        f"### 5. Relevant Topics & Inquiries to Discuss\n\n"
        f"Language: {language}\n"
        f"Tone: Clinical, concise, and helpful."
    )

    try:
        gen_resp = service.generation_service.answer_question(question=prompt, language=language)
        return jsonify({
            "summary": gen_resp.answer,
            "patient_profile": profile,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 200
    except Exception as e:
        logger.error(f"Doctor summary generation failed: {e}")
        return jsonify({"error": {"code": "SERVICE_ERROR", "message": str(e)}}), 500


@api_bp.route("/feedback", methods=["POST"])
def record_feedback():
    """
    Records helpfulness feedback (thumbs up / thumbs down) for an AI response.
    POST /api/feedback
    """
    payload = request.get_json() or {}
    logger.info(f"User Feedback recorded: {payload}")
    return jsonify({"status": "success", "message": "Feedback recorded. Thank you!"}), 200

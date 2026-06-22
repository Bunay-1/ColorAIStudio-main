from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, List
import os
import time
import logging
from glob import glob
import httpx
from slowapi import Limiter
from slowapi.util import get_remote_address
from utils.models import ReasoningRequest, DocumentIndexRequest
from utils.auth import check_permission, get_current_user
from utils.audit_logger import AuditAction, log_audit_event
from utils.rate_limiter import check_user_rate_limit

router = APIRouter(prefix="/rag", tags=["RAG & Knowledge"])
logger = logging.getLogger("IRM_RAG_Router")
limiter = Limiter(key_func=get_remote_address)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "irm-industrial")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_REQUEST_TIMEOUT", os.environ.get("OLLAMA_TIMEOUT", "120")))

@router.post("/diagnose", dependencies=[Depends(check_permission("analyze"))])
@limiter.limit("20/minute")  # 20 requests per minute per IP (LLM calls are expensive)
async def diagnose(request: ReasoningRequest, req: Request, current_user: dict = Depends(get_current_user)):
    # Check user rate limit (heavy operation)
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "heavy")
    
    icap = req.app.state.icap
    EDGE_MODE = req.app.state.EDGE_MODE
    manager = req.app.state.manager

    sources = []
    retrieved_context = ""
    vision_context = ""

    if request.image_data:
        import base64
        temp_img = f"chat_vision_{int(time.time())}.jpg"
        try:
            img_data = base64.b64decode(request.image_data.split(",")[1] if "," in request.image_data else request.image_data)
            with open(temp_img, "wb") as f:
                f.write(img_data)

            defects = icap.vision_engine.detect_defects(temp_img)
            micro = icap.vision_engine.analyze_micro_defects(temp_img)

            vision_context = f"\n--- VISION AI АНАЛИЗ НА СНИМКАТА ---\n"
            if defects:
                vision_context += f"Открити обекти/дефекти: {', '.join([d['class'] for d in defects])}\n"
            if micro.get('micro_defects_detected'):
                vision_context += f"ViT Детекция: {micro['pattern_recognition']} (Аномалия: {micro['anomaly_score']:.2f})\n"
        except Exception as e:
            logger.error(f"Vision error in chat: {e}")
        finally:
            if os.path.exists(temp_img):
                os.remove(temp_img)

    if request.use_rag:
        retrieved_context, sources = await icap.rag.query(request.prompt, filters=request.filters)

    full_context = f"{vision_context}\n{retrieved_context}\n{request.context}".strip()
    if len(full_context) > 4000:
        full_context = full_context[:4000] + "..."

    system_prompt = (
        "Ти си универсален Industrial Intelligence Assistant. Отговаряй кратко и конкретно на български език.\n\n"
        "ПРАВИЛА:\n"
        "- Използвай предоставения контекст (Input) като приоритет.\n"
        "- Давай конкретни технически параметри.\n"
        "- Обърни специално внимание на секцията 'ГРАФ НА ЗНАНИЕТО', за да откриеш логически връзки между процесите.\n"
        "- ВИНАГИ добавяй секция 'ОБОСНОВКА' в края на отговора си, обясняваща защо AI е стигнал до това заключение (Confidence, Ключови фактори).\n"
        "- Избягвай дълги въведения и обяснения."
    )

    full_prompt = f"### System:\n{system_prompt}\n\n### Instruction:\n{request.prompt}\n\n### Input:\n{full_context}\n\n### Response:\n"

    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            # Проверка на сървъра
            try:
                base_url = OLLAMA_URL.replace("/api/generate", "")
                await client.get(base_url, timeout=2.0)
            except:
                raise Exception("Ollama сървърът не отговаря.")

            ollama_payload = {
                "model": MODEL_NAME,
                "prompt": full_prompt,
                "stream": False,
                "options": {"temperature": request.temperature}
            }
            response = await client.post(OLLAMA_URL, json=ollama_payload)
            data = response.json()
            analysis_text = data.get("response", "").strip()
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        analysis_text = f"[ГРЕШКА] Ollama не е достъпна: {str(e)}"
    
    # Log audit event
    log_audit_event(
        action=AuditAction.DATA_ACCESS,
        user_id=current_user.get("username", "anonymous"),
        user_role=current_user.get("role", "OPERATOR"),
        tenant_id=current_user.get("tenant_id", "default"),
        details={
            "action": "rag_diagnose",
            "use_rag": request.use_rag,
            "use_vision": bool(request.image_data),
            "sources_count": len(sources)
        },
        ip_address=req.client.host if req.client else None
    )

    return {
        "analysis": analysis_text,
        "sources": sources,
        "timestamp": time.time() - start_time,
        "model": MODEL_NAME
    }

@router.post("/index_document", dependencies=[Depends(check_permission("configure"))])
@limiter.limit("10/minute")  # 10 requests per minute per IP (indexing is resource-intensive)
async def index_document(request: DocumentIndexRequest, background_tasks: BackgroundTasks, req: Request, current_user: dict = Depends(get_current_user)):
    # Check user rate limit (heavy operation)
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "heavy")
    
    icap = req.app.state.icap
    manager = req.app.state.manager
    file_path = request.file_path

    supported_extensions = [".pdf", ".docx", ".xlsx", ".xls", ".csv", ".json", ".md", ".html", ".xml", ".tmx", ".zip", ".udb", ".mdb", ".accdb"]

    async def progress_cb(data):
        try:
            await manager.broadcast(data)
        except Exception as e:
            logger.error(f"WS Broadcast error in RAG: {e}")

    if os.path.isdir(file_path):
        files_to_index = []
        for ext in supported_extensions:
            files_to_index.extend(glob(os.path.join(file_path, f"**/*{ext}"), recursive=True))
        files_to_index = list(set(files_to_index))
        for file in files_to_index:
            background_tasks.add_task(icap.rag.index_any, file, progress_cb)
        
        # Log audit event
        log_audit_event(
            action=AuditAction.DATA_MODIFY,
            user_id=current_user.get("username", "anonymous"),
            user_role=current_user.get("role", "OPERATOR"),
            tenant_id=current_user.get("tenant_id", "default"),
            details={
                "action": "index_documents",
                "directory": file_path,
                "files_count": len(files_to_index)
            },
            ip_address=req.client.host if req.client else None
        )
        
        return {"message": f"Започна индексиране на {len(files_to_index)} файла"}
    else:
        background_tasks.add_task(icap.rag.index_any, file_path, progress_cb)
        
        # Log audit event
        log_audit_event(
            action=AuditAction.DATA_MODIFY,
            user_id=current_user.get("username", "anonymous"),
            user_role=current_user.get("role", "OPERATOR"),
            tenant_id=current_user.get("tenant_id", "default"),
            details={
                "action": "index_document",
                "file": file_path
            },
            ip_address=req.client.host if req.client else None
        )
        
        return {"message": f"Започна индексиране на {file_path}"}

@router.get("/stats", dependencies=[Depends(check_permission("view"))])
@limiter.limit("60/minute")  # 60 requests per minute per IP (lightweight endpoint)
async def get_rag_stats(req: Request, current_user: dict = Depends(get_current_user)):
    # Check user rate limit (light operation)
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "light")
    
    icap = req.app.state.icap
    return await icap.rag.get_stats()

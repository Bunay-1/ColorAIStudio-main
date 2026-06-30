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
from utils.circuit_breaker import ollama_breaker
from utils.metrics import request_counter, rag_query_duration_seconds, rag_documents_indexed_total
from utils.auth import check_permission, get_current_user
from utils.audit_logger import AuditAction, log_audit_event
from utils.rate_limiter import check_user_rate_limit
from utils.models import ReasoningRequest, DocumentIndexRequest
from utils.redis_cache import cache
from services import rag_service

router = APIRouter(prefix="/rag", tags=["RAG & Knowledge"])
logger = logging.getLogger("IRM_RAG_Router")
limiter = Limiter(key_func=get_remote_address)

@router.post("/diagnose", dependencies=[Depends(check_permission("analyze"))])
@limiter.limit("20/minute")
async def diagnose(request: ReasoningRequest, req: Request, current_user: dict = Depends(get_current_user)):
    """Ендпоинт за RAG диагностика."""
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "heavy")
    
    # Cache logic stays in router
    cache_key = f"rag_query:{hash(request.query)}:{request.use_rag}:{bool(request.image_data)}"
    if not request.image_data:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            request_counter.labels(endpoint="/rag/diagnose", method="POST", status="success").inc()
            return cached_result

    with rag_query_duration_seconds.labels("diagnose_rag_lookup").time():
        result = await rag_service.query_rag(request, req.app.state.icap, req.app.state.manager)

    if not request.image_data:
        cache.set(cache_key, result, ttl=300)
    
    log_audit_event(
        action=AuditAction.DATA_ACCESS,
        user_id=current_user.get("username", "anonymous"),
        user_role=current_user.get("role", "OPERATOR"),
        tenant_id=current_user.get("tenant_id", "default"),
        details={"action": "rag_diagnose", "use_rag": request.use_rag},
        ip_address=req.client.host if req.client else None
    )
    request_counter.labels(endpoint="/rag/diagnose", method="POST", status="success").inc()
    return result

@router.post("/index_document", dependencies=[Depends(check_permission("configure"))])
@limiter.limit("10/minute")
async def index_document(request: DocumentIndexRequest, background_tasks: BackgroundTasks, req: Request, current_user: dict = Depends(get_current_user)):
    """Ендпоинт за индексиране на документи."""
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "heavy")
    
    response = await rag_service.index_docs(request.file_path, req.app.state.icap, req.app.state.manager, background_tasks)

    log_audit_event(
        action=AuditAction.DATA_MODIFY,
        user_id=current_user.get("username", "anonymous"),
        user_role=current_user.get("role", "OPERATOR"),
        tenant_id=current_user.get("tenant_id", "default"),
        details={"action": "index_document", "path": request.file_path},
        ip_address=req.client.host if req.client else None
    )
    request_counter.labels(endpoint="/rag/index_document", method="POST", status="success").inc()
    return response

@router.get("/stats", dependencies=[Depends(check_permission("view"))])
@limiter.limit("60/minute")  # 60 requests per minute per IP (lightweight endpoint)
async def get_rag_stats(req: Request, current_user: dict = Depends(get_current_user)):
    # Check user rate limit (light operation)
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "light")
    
    icap = req.app.state.icap
    request_counter.labels(endpoint="/rag/stats", method="GET", status="success").inc()
    return await icap.rag.get_stats()

@router.post("/clear-database", dependencies=[Depends(check_permission("configure"))])
async def clear_database(req: Request, current_user: dict = Depends(get_current_user)):
    """Изчиства векторната база данни и състоянието на индексерa."""
    icap = req.app.state.icap
    await icap.rag.reset_collection()
    state_file = "AuditTrail/indexer_state.json"
    if os.path.exists(state_file):
        os.remove(state_file)

    log_audit_event(
        action=AuditAction.DATA_MODIFY,
        user_id=current_user.get("username", "anonymous"),
        user_role=current_user.get("role", "ADMIN"),
        tenant_id=current_user.get("tenant_id", "default"),
        details={"action": "clear_database"},
        ip_address=req.client.host if req.client else None
    )

    return {"message": "Базата данни и индексерът са изчистени успешно."}

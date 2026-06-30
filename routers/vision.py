from fastapi import APIRouter, HTTPException, File, UploadFile, Request
from typing import List, Optional
import time
import os
import logging
from fastapi import Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from utils.auth import check_permission, get_current_user
from utils.audit_logger import AuditAction, log_audit_event
from utils.rate_limiter import check_user_rate_limit
from services import vision_service

router = APIRouter(prefix="/vision", tags=["Vision AI"])
logger = logging.getLogger("IRM_Vision_Router")
limiter = Limiter(key_func=get_remote_address)

@router.post("/analyze", dependencies=[Depends(check_permission("analyze"))])
@limiter.limit("30/minute")
async def vision_analyze(req: Request, file: UploadFile = File(...), generate_map: bool = False, current_user: dict = Depends(get_current_user)):
    """Ендпоинт за визуален анализ на повърхности и дефекти."""
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "heavy")
    
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Файлът е задължителен.")
    
    response = await vision_service.analyze_vision(file, generate_map, req.app.state.icap, req.client.host if req.client else None)
    
    log_audit_event(
        action=AuditAction.DATA_ACCESS,
        user_id=current_user.get("username", "anonymous"),
        user_role=current_user.get("role", "OPERATOR"),
        tenant_id=current_user.get("tenant_id", "default"),
        details={"action": "vision_analyze", "filename": file.filename},
        ip_address=req.client.host if req.client else None
    )
    return response

@router.post("/fusion", dependencies=[Depends(check_permission("analyze"))])
@limiter.limit("10/minute")
async def vision_fusion(req: Request, files: List[UploadFile] = File(...), current_user: dict = Depends(get_current_user)):
    """Ендпоинт за Fusion на изгледи."""
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "heavy")
    
    response = await vision_service.fuse_vision_views(files, req.app.state.icap)

    log_audit_event(
        action=AuditAction.DATA_ACCESS,
        user_id=current_user.get("username", "anonymous"),
        user_role=current_user.get("role", "OPERATOR"),
        tenant_id=current_user.get("tenant_id", "default"),
        details={"action": "vision_fusion", "views_count": len(files)},
        ip_address=req.client.host if req.client else None
    )
    return response

@router.post("/micro_analyze", dependencies=[Depends(check_permission("analyze"))])
@limiter.limit("20/minute")
async def vision_micro_analyze(req: Request, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Ендпоинт за микро-дефекти."""
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "heavy")
    
    response = await vision_service.analyze_micro_vision(file, req.app.state.icap)
    
    log_audit_event(
        action=AuditAction.DATA_ACCESS,
        user_id=current_user.get("username", "anonymous"),
        user_role=current_user.get("role", "OPERATOR"),
        tenant_id=current_user.get("tenant_id", "default"),
        details={"action": "vision_micro_analyze", "filename": file.filename},
        ip_address=req.client.host if req.client else None
    )
    return response

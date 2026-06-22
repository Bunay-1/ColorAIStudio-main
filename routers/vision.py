from fastapi import APIRouter, HTTPException, File, UploadFile, Request
from typing import List, Optional
import time
import os
import cv2
import base64
import logging
from fastapi import Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from utils.auth import check_permission, get_current_user
from utils.audit_logger import AuditAction, log_audit_event
from utils.rate_limiter import check_user_rate_limit

router = APIRouter(prefix="/vision", tags=["Vision AI"])
logger = logging.getLogger("IRM_Vision_Router")
limiter = Limiter(key_func=get_remote_address)

@router.post("/analyze", dependencies=[Depends(check_permission("analyze"))])
@limiter.limit("30/minute")  # 30 requests per minute per IP (computationally intensive)
async def vision_analyze(req: Request, file: UploadFile = File(...), generate_map: bool = False, current_user: dict = Depends(get_current_user)):
    """Ендпоинт за визуален анализ на повърхности и дефекти чрез YOLOv11 & OpenCV."""
    # Check user rate limit (heavy operation)
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "heavy")
    
    # Input validation
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Файлът е задължителен.")
    
    # Validate file extension
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Неподдържан файлов формат. Позволени: {', '.join(allowed_extensions)}")
    
    # Validate file size (max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Файлът е твърде голям. Максимален размер: 10MB")
    
    icap = req.app.state.icap
    temp_path = f"vision_temp_{int(time.time())}_{file.filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(content)

    try:
        defects = icap.vision_engine.detect_defects(temp_path)
        texture = icap.vision_engine.analyze_texture(temp_path)
        gloss = icap.vision_engine.measure_gloss(temp_path)
        coating = icap.vision_engine.detect_uneven_coating(temp_path)

        response = {
            "defects": defects,
            "texture": texture,
            "gloss": gloss,
            "coating_quality": coating,
            "filename": file.filename
        }

        if generate_map:
            heatmap = icap.vision_engine.generate_explainability_map(temp_path, defects)
            if heatmap is not None:
                _, buffer_img = cv2.imencode(".jpg", heatmap)
                response["explainability_map"] = base64.b64encode(buffer_img).decode("utf-8")
        
        # Log audit event
        log_audit_event(
            action=AuditAction.DATA_ACCESS,
            user_id=current_user.get("username", "anonymous"),
            user_role=current_user.get("role", "OPERATOR"),
            tenant_id=current_user.get("tenant_id", "default"),
            details={
                "action": "vision_analyze",
                "filename": file.filename,
                "defects_found": len(defects) if defects else 0
            },
            ip_address=req.client.host if req.client else None
        )

        return response
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/fusion", dependencies=[Depends(check_permission("analyze"))])
@limiter.limit("10/minute")  # 10 requests per minute per IP (very computationally intensive)
async def vision_fusion(req: Request, files: List[UploadFile] = File(...), current_user: dict = Depends(get_current_user)):
    """Ендпоинт за Fusion на изгледи от различни ъгли (намалява false positives)."""
    # Check user rate limit (very heavy operation)
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "heavy")
    
    icap = req.app.state.icap
    temp_paths = []
    try:
        for file in files:
            t_path = f"fusion_temp_{int(time.time())}_{file.filename}"
            with open(t_path, "wb") as b:
                b.write(await file.read())
            temp_paths.append(t_path)

        fused_defects = icap.vision_engine.multi_view_fusion(temp_paths)
        
        # Log audit event
        log_audit_event(
            action=AuditAction.DATA_ACCESS,
            user_id=current_user.get("username", "anonymous"),
            user_role=current_user.get("role", "OPERATOR"),
            tenant_id=current_user.get("tenant_id", "default"),
            details={
                "action": "vision_fusion",
                "views_count": len(files),
                "fused_defects": len(fused_defects) if fused_defects else 0
            },
            ip_address=req.client.host if req.client else None
        )
        
        return {"fused_defects": fused_defects, "views_analyzed": len(temp_paths)}
    finally:
        for p in temp_paths:
            if os.path.exists(p): os.remove(p)

@router.post("/micro_analyze", dependencies=[Depends(check_permission("analyze"))])
@limiter.limit("20/minute")  # 20 requests per minute per IP (computationally intensive)
async def vision_micro_analyze(req: Request, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Ендпоинт за високопрецизен анализ на микро-дефекти чрез ViT."""
    # Check user rate limit (heavy operation)
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "heavy")
    
    icap = req.app.state.icap
    file_path = f"AuditTrail/vision_{int(time.time())}_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # We use the existing engine which might already be loaded
    result = icap.vision_engine.analyze_micro_defects(file_path)
    
    # Log audit event
    log_audit_event(
        action=AuditAction.DATA_ACCESS,
        user_id=current_user.get("username", "anonymous"),
        user_role=current_user.get("role", "OPERATOR"),
        tenant_id=current_user.get("tenant_id", "default"),
        details={
            "action": "vision_micro_analyze",
            "filename": file.filename
        },
        ip_address=req.client.host if req.client else None
    )
    
    return result

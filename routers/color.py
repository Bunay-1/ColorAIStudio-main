from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List, Optional
import os
import time
import random
import numpy as np
try:
    import colour
    COLOUR_AVAILABLE = True
except ImportError:
    COLOUR_AVAILABLE = False
    colour = None
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from services import color_service
from utils.models import ColorAnalysisRequest, TrendRequest
from utils.auth import check_permission, get_current_user
from utils.audit_logger import AuditAction, log_audit_event
from utils.rate_limiter import check_user_rate_limit
from utils.metrics import request_counter, delta_e_duration_seconds
from utils.redis_cache import cache

router = APIRouter(prefix="/color", tags=["Color Analysis"])
logger = logging.getLogger("IRM_Color_Router")
limiter = Limiter(key_func=get_remote_address)

@router.post("/analyze", dependencies=[Depends(check_permission("analyze"))])
@limiter.limit("100/minute")
async def analyze_color(request: ColorAnalysisRequest, req: Request, current_user: dict = Depends(get_current_user)):
    """Ендпоинт за колориметричен анализ."""
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "light")
    
    # Cache logic stays in router
    cache_key = f"delta_e:{request.method}:{tuple(request.lab_sample)}:{tuple(request.lab_standard)}"
    cached_res = cache.get(cache_key)
    if cached_res:
        return cached_res

    response = await color_service.process_color_analysis(
        request, req.app.state.icap, req.app.state.alert_system,
        req.app.state.log_to_audit_trail, req.client.host if req.client else None
    )

    cache.set(cache_key, response, ttl=600)
    
    log_audit_event(
        action=AuditAction.DATA_MODIFY,
        user_id=current_user.get("username", "anonymous"),
        user_role=current_user.get("role", "OPERATOR"),
        tenant_id=current_user.get("tenant_id", "default"),
        details={"batch_id": request.batch_id, "status": response["status"]},
        ip_address=req.client.host if req.client else None
    )
    request_counter.labels(endpoint="/color/analyze", method="POST", status="success").inc()
    return response

@router.post("/predict_trend", dependencies=[Depends(check_permission("analyze"))])
@limiter.limit("50/minute")  # 50 requests per minute per IP
async def predict_trend(request: TrendRequest, req: Request, current_user: dict = Depends(get_current_user)):
    """Ендпоинт за прогнозиране на тренд и дрейф."""
    # Check user rate limit
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "light")
    
    icap = req.app.state.icap
    trend_result = icap.ai_analysis.predict_trend(request.historical_de)
    drift = icap.ai_analysis.drift_predictor(request.historical_de, request.tolerance)
    anomalies = icap.ai_analysis.detect_anomalies(request.historical_de)
    
    # Log audit event
    log_audit_event(
        action=AuditAction.DATA_ACCESS,
        user_id=current_user.get("username", "anonymous"),
        user_role=current_user.get("role", "OPERATOR"),
        tenant_id=current_user.get("tenant_id", "default"),
        details={
            "action": "predict_trend",
            "data_points": len(request.historical_de)
        },
        ip_address=req.client.host if req.client else None
    )

    response = {
        "prediction": trend_result["prediction"],
        "trend": trend_result["trend"],
        "drift_warning": drift,
        "anomalies_indices": anomalies
    }
    request_counter.labels(endpoint="/color/predict_trend", method="POST", status="success").inc()
    return response

@router.post("/recipe_formulation", dependencies=[Depends(check_permission("analyze"))])
@limiter.limit("20/minute")  # 20 requests per minute per IP (computationally intensive)
async def recipe_formulation(request: ColorAnalysisRequest, req: Request, current_user: dict = Depends(get_current_user)):
    """Ендпоинт за AI изчисляване на рецепта."""
    # Check user rate limit (heavy operation)
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "heavy")
    
    icap = req.app.state.icap
    pigment_db = [
        {"name": "Titanium White", "lab": [98, 0, 0]},
        {"name": "Carbon Black", "lab": [5, 0, 0]},
        {"name": "Iron Oxide Red", "lab": [40, 30, 20]},
        {"name": "Iron Oxide Yellow", "lab": [70, 10, 50]},
        {"name": "Phthalo Blue", "lab": [30, -10, -40]},
    ]
    result = icap.ai_analysis.recipe_formulation(request.lab_standard, pigment_db)
    
    # Log audit event
    log_audit_event(
        action=AuditAction.DATA_ACCESS,
        user_id=current_user.get("username", "anonymous"),
        user_role=current_user.get("role", "OPERATOR"),
        tenant_id=current_user.get("tenant_id", "default"),
        details={
            "action": "recipe_formulation",
            "target_lab": request.lab_standard
        },
        ip_address=req.client.host if req.client else None
    )
    
    request_counter.labels(endpoint="/color/recipe_formulation", method="POST", status="success").inc()
    return result

@router.post("/hsi-analyze", dependencies=[Depends(check_permission("analyze"))])
async def hsi_analyze(data: dict, current_user: dict = Depends(get_current_user)):
    """Хиперспектрален анализ на материали [DEMO]."""
    if os.environ.get("ICAP_ENVIRONMENT") == "production":
         raise HTTPException(status_code=403, detail="Този ендпойнт е деактивиран в production среда.")

    return {
        "wavelengths": list(range(400, 1001, 20)),
        "intensities": [random.random() for _ in range(31)],
        "material_identified": "Polymer Composite X1",
        "confidence": 0.94,
        "subsurface_defect": False,
        "note": "Симулирани данни за демо"
    }

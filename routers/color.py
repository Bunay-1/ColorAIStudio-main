from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List, Optional
import time
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
from services.iot_service import get_latest_iot_data
from services.report_service import generate_html_report as svc_generate_html_report
from utils.models import ColorAnalysisRequest, TrendRequest
from utils.auth import check_permission, get_current_user
from utils.audit_logger import AuditAction, log_audit_event
from utils.rate_limiter import check_user_rate_limit
from utils.metrics import request_counter, delta_e_duration_seconds

router = APIRouter(prefix="/color", tags=["Color Analysis"])
logger = logging.getLogger("IRM_Color_Router")
limiter = Limiter(key_func=get_remote_address)

def lab_to_mock_spectrum(lab: List[float], wavelengths: List[int] = None) -> List[float]:
    """
    Convert LAB coordinates to mock spectral data.
    
    Args:
        lab: LAB color coordinates [L, a, b]
        wavelengths: List of wavelengths (default 400-700nm in 10nm steps)
    
    Returns:
        List of spectral values
    """
    if wavelengths is None:
        wavelengths = list(range(400, 701, 10))
    
    L, a, b = lab
    return [max(0, min(1, (L/100) + (a/500)*np.sin(w/50) + (b/500)*np.cos(w/50))) for w in wavelengths]

def lab_to_sd(lab: List[float]):
    """
    Convert LAB coordinates to SpectralDistribution object.
    
    Args:
        lab: LAB color coordinates [L, a, b]
    
    Returns:
        SpectralDistribution object or None if colour-science not available
    """
    if not COLOUR_AVAILABLE:
        return None
    
    wavelengths = np.arange(400, 701, 10)
    values = lab_to_mock_spectrum(lab, wavelengths)
    return colour.SpectralDistribution(dict(zip(wavelengths, values)))

@router.post("/analyze", dependencies=[Depends(check_permission("analyze"))])
@limiter.limit("100/minute")  # 100 requests per minute per IP
async def analyze_color(request: ColorAnalysisRequest, req: Request, current_user: dict = Depends(get_current_user)):
    """Ендпоинт за колориметричен анализ (Delta E и Pass/Fail)."""
    # Check user rate limit
    check_user_rate_limit(current_user.get("username", "anonymous"), current_user.get("role", "OPERATOR"), "light")
    
    # Input validation
    if len(request.lab_sample) != 3 or len(request.lab_standard) != 3:
        raise HTTPException(status_code=400, detail="L*a*b* координатите трябва да имат точно 3 стойности.")
    
    # Validate Lab coordinate ranges
    for i, (sample, standard) in enumerate(zip(request.lab_sample, request.lab_standard)):
        if not isinstance(sample, (int, float)) or not isinstance(standard, (int, float)):
            raise HTTPException(status_code=400, detail=f"Lab координата {i} трябва да е число.")
        if i == 0:  # L* should be 0-100
            if not (0 <= sample <= 100) or not (0 <= standard <= 100):
                raise HTTPException(status_code=400, detail="L* координата трябва да е между 0 и 100.")
        else:  # a* and b* typically -128 to 127
            if not (-128 <= sample <= 127) or not (-128 <= standard <= 127):
                raise HTTPException(status_code=400, detail="a* и b* координати трябва да са между -128 и 127.")
    
    # Validate tolerance
    if request.tolerance <= 0:
        raise HTTPException(status_code=400, detail="Толерансът трябва да е положително число.")
    
    # Validate batch size
    if request.batch_size <= 0:
        raise HTTPException(status_code=400, detail="Размерът на партидата трябва да е положително число.")

    icap = req.app.state.icap
    alert_system = req.app.state.alert_system
    log_to_audit_trail = req.app.state.log_to_audit_trail

    with delta_e_duration_seconds.labels("/color/analyze").time():
        de = icap.color_engine.calculate_delta_e(request.lab_sample, request.lab_standard, request.method)
    status = "Pass" if de <= request.tolerance else "Fail"

    if status == "Fail" and de > request.tolerance * 2:
        alert_system.send_alert(
            f"Критично отклонение в качеството! Партида: {request.batch_id}, ΔE: {de:.4f} (Толеранс: {request.tolerance})",
            level="CRITICAL"
        )

    spc_data = icap.ai_analysis.calculate_spc([0.5, 0.6, 0.4, 0.7, de])

    mi_data = icap.color_engine.calculate_mi(lab_to_sd(request.lab_sample), lab_to_sd(request.lab_standard))

    recommendations = []
    if status == "Fail":
        recommendations = icap.ai_analysis.recommend_correction(
            request.lab_sample,
            request.lab_standard,
            batch_size_kg=request.batch_size
        )

    audit_entry = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "batch_id": request.batch_id,
        "operator_id": request.operator_id,
        "machine_id": request.machine_id,
        "client_id": request.client_id,
        "delta_e": round(float(de), 4),
        "status": status,
        "method": request.method,
        "illuminant": request.illuminant
    }
    log_to_audit_trail(audit_entry)
    
    # Log audit event
    log_audit_event(
        action=AuditAction.DATA_MODIFY,
        user_id=current_user.get("username", "anonymous"),
        user_role=current_user.get("role", "OPERATOR"),
        tenant_id=current_user.get("tenant_id", "default"),
        details={
            "batch_id": request.batch_id,
            "delta_e": round(float(de), 4),
            "status": status
        },
        ip_address=req.client.host if req.client else None
    )

    wavelengths_list = list(range(400, 701, 10))
    closest_ral = icap.color_engine.get_closest_ral(request.lab_sample)

    iot_energy = 0
    latest_iot = get_latest_iot_data()
    if request.machine_id in latest_iot:
        load_str = latest_iot[request.machine_id].get("load", "0%").replace("%", "")
        iot_energy = (float(load_str) / 100.0) * 5.5

    sustainability = icap.ai_analysis.calculate_sustainability_index(
        {"delta_e": float(de)},
        request.batch_size,
        energy_data=iot_energy
    )

    response = {
        "delta_e": float(de),
        "status": status,
        "sustainability": sustainability,
        "method": request.method,
        "closest_ral": closest_ral,
        "ai_recommendations": recommendations,
        "spc_data": spc_data,
        "mi_data": mi_data,
        "spectral_data": {
            "wavelengths": wavelengths_list,
            "sample": lab_to_mock_spectrum(request.lab_sample),
            "standard": lab_to_mock_spectrum(request.lab_standard)
        }
    }

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

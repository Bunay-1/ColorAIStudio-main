"""
Color Service for ICAP Enterprise
=================================
Business logic for colorimetric analysis and spectral data processing.
"""

import os
import time
import numpy as np
import logging
from typing import List
try:
    import colour
    COLOUR_AVAILABLE = True
except ImportError:
    COLOUR_AVAILABLE = False
    colour = None

from services.iot_service import get_latest_iot_data

logger = logging.getLogger("Color_Service")

def lab_to_mock_spectrum(lab: List[float], wavelengths: List[int] = None) -> List[float]:
    """Преобразува LAB в симулирани спектрални данни."""
    if wavelengths is None:
        wavelengths = list(range(400, 701, 10))
    L, a, b = lab
    return [max(0, min(1, (L/100) + (a/500)*np.sin(w/50) + (b/500)*np.cos(w/50))) for w in wavelengths]

def lab_to_sd(lab: List[float]):
    """Преобразува LAB в SpectralDistribution."""
    if not COLOUR_AVAILABLE:
        return None
    wavelengths = np.arange(400, 701, 10)
    values = lab_to_mock_spectrum(lab, wavelengths)
    return colour.SpectralDistribution(dict(zip(wavelengths, values)))

async def process_color_analysis(request, icap_state, alert_system, log_to_audit_trail, client_host):
    """Основна логика за анализ на цвят."""
    de = icap_state.color_engine.calculate_delta_e(request.lab_sample, request.lab_standard, request.method)
    status = "Pass" if de <= request.tolerance else "Fail"

    if status == "Fail" and de > request.tolerance * 2:
        alert_system.send_alert(
            f"Критично отклонение! Партида: {request.batch_id}, ΔE: {de:.4f}",
            level="CRITICAL"
        )

    spc_data = icap_state.ai_analysis.calculate_spc([0.5, 0.6, 0.4, 0.7, de])
    mi_data = icap_state.color_engine.calculate_mi(lab_to_sd(request.lab_sample), lab_to_sd(request.lab_standard))

    recommendations = []
    if status == "Fail":
        recommendations = icap_state.ai_analysis.recommend_correction(
            request.lab_sample, request.lab_standard, batch_size_kg=request.batch_size
        )

    closest_ral = icap_state.color_engine.get_closest_ral(request.lab_sample)

    iot_energy = 0
    latest_iot = get_latest_iot_data()
    if request.machine_id in latest_iot:
        load_str = latest_iot[request.machine_id].get("load", "0%").replace("%", "")
        iot_energy = (float(load_str) / 100.0) * 5.5

    sustainability = icap_state.ai_analysis.calculate_sustainability_index(
        {"delta_e": float(de)}, request.batch_size, energy_data=iot_energy
    )

    return {
        "delta_e": float(de),
        "status": status,
        "sustainability": sustainability,
        "method": request.method,
        "closest_ral": closest_ral,
        "ai_recommendations": recommendations,
        "spc_data": spc_data,
        "mi_data": mi_data,
        "spectral_data": {
            "wavelengths": list(range(400, 701, 10)),
            "sample": lab_to_mock_spectrum(request.lab_sample),
            "standard": lab_to_mock_spectrum(request.lab_standard)
        }
    }

async def predict_trend(request, icap_state):
    """Прогнозира тренд и аномалии в данните."""
    trend_result = icap_state.ai_analysis.predict_trend(request.historical_de)
    drift = icap_state.ai_analysis.drift_predictor(request.historical_de, request.tolerance)
    anomalies = icap_state.ai_analysis.detect_anomalies(request.historical_de)

    return {
        "prediction": trend_result["prediction"],
        "trend": trend_result["trend"],
        "drift_warning": drift,
        "anomalies_indices": anomalies
    }

async def recipe_formulation(request, icap_state):
    """Изчислява рецепта за цвят."""
    pigment_db = [
        {"name": "Titanium White", "lab": [98, 0, 0]},
        {"name": "Carbon Black", "lab": [5, 0, 0]},
        {"name": "Iron Oxide Red", "lab": [40, 30, 20]},
        {"name": "Iron Oxide Yellow", "lab": [70, 10, 50]},
        {"name": "Phthalo Blue", "lab": [30, -10, -40]},
    ]
    return icap_state.ai_analysis.recipe_formulation(request.lab_standard, pigment_db)

async def hsi_analyze(data):
    """Хиперспектрален анализ."""
    if os.environ.get("ICAP_ENVIRONMENT") == "production":
         raise Exception("Този ендпойнт е деактивиран в production среда.")

    import random
    return {
        "wavelengths": list(range(400, 1001, 20)),
        "intensities": [random.random() for _ in range(31)],
        "material_identified": "Polymer Composite X1",
        "confidence": 0.94,
        "subsurface_defect": False,
        "note": "Симулирани данни за демо"
    }

"""
Model Service for ICAP Enterprise
==================================
Business logic for model management and registry.
"""

import os
import json
import logging
from fastapi import HTTPException

logger = logging.getLogger("Model_Service")

async def get_model_registry():
    """Извлича регистъра с AI модели."""
    registry_path = "model_registry.json"
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Грешка при четене на моделния регистър: {e}")
            raise HTTPException(status_code=500, detail="Вътрешна грешка при четене на данни")
    return []

async def get_available_models():
    """Списък с налични за използване модели (симулирани данни)."""
    return {
        "models": [
            {"id": "irm-industrial-v8.9", "name": "IRM Industrial v8.9", "type": "Vision"},
            {"id": "irm-base-v1", "name": "IRM Base v1", "type": "Color"}
        ],
        "note": "Симулирани данни за демо цели"
    }

async def switch_model(name: str):
    """Логика за превключване на модели."""
    if os.environ.get("ICAP_ENVIRONMENT") == "production":
         raise HTTPException(status_code=403, detail="Този ендпойнт е деактивиран в production среда.")
    return {"status": "success", "message": f"Моделът е сменен на {name}"}

"""
Models Router for ICAP Enterprise
=================================
REST API endpoints for model management and registry.
"""

import os
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from utils.auth import get_current_active_user

router = APIRouter(tags=["Models"])
logger = logging.getLogger("Models_Router")

@router.get("/registry", summary="Извличане на регистъра с модели")
async def get_model_registry(current_user: dict = Depends(get_current_active_user)):
    """
    Връща съдържанието на регистъра с AI модели.
    """
    registry_path = "model_registry.json"
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Грешка при четене на моделния регистър: {e}")
            raise HTTPException(status_code=500, detail="Вътрешна грешка при четене на данни")
    return []

@router.get("/list", summary="Списък с налични модели [DEMO]")
async def get_models_list(current_user: dict = Depends(get_current_active_user)):
    """
    Връща списък с наличните за използване модели (симулирани данни).
    """
    return {
        "models": [
            {"id": "irm-industrial-v8.9", "name": "IRM Industrial v8.9", "type": "Vision"},
            {"id": "irm-base-v1", "name": "IRM Base v1", "type": "Color"}
        ],
        "note": "Симулирани данни за демо цели"
    }

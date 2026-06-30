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
from services import model_service

router = APIRouter(tags=["Models"])
logger = logging.getLogger("Models_Router")

@router.get("/registry", summary="Извличане на регистъра с модели")
async def get_model_registry(current_user: dict = Depends(get_current_active_user)):
    """
    Връща съдържанието на регистъра с AI модели.
    """
    return await model_service.get_model_registry()

@router.get("/list", summary="Списък с налични модели [DEMO]")
async def get_models_list(current_user: dict = Depends(get_current_active_user)):
    """
    Връща списък с наличните за използване модели (симулирани данни).
    """
    return await model_service.get_available_models()

@router.post("/switch/{name}", dependencies=[Depends(get_current_active_user)])
async def switch_model(name: str):
    """Превключване към различен AI модел [DEMO]."""
    return await model_service.switch_model(name)

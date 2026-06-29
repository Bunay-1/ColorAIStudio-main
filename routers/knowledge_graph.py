"""
Knowledge Graph Router for ICAP Enterprise
==========================================
REST API endpoints for Knowledge Graph exploration and reasoning.
"""

import os
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from utils.auth import get_current_active_user
from knowledge_graph import IndustrialKG

router = APIRouter(tags=["Knowledge Graph"])
logger = logging.getLogger("KG_Router")

@router.get("/export", summary="Експорт на графа на знанието")
async def kg_export(current_user: dict = Depends(get_current_active_user)):
    """
    Връща целия граф на знанието в JSON формат за визуализация.
    """
    kg_path = "Docs/knowledge_graph.json"
    if os.path.exists(kg_path):
        try:
            with open(kg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Грешка при четене на KG файл: {e}")
            raise HTTPException(status_code=500, detail="Грешка при четене на данни за графа")
    return {"nodes": [], "links": []}

@router.get("/reason/{issue}", summary="Логическо разсъждение върху проблем")
async def kg_reason(issue: str, current_user: dict = Depends(get_current_active_user)):
    """
    Търси логически връзки и причини за даден индустриален проблем в графа.
    """
    try:
        kg = IndustrialKG()
        reasoning_path = kg.find_reasoning_path(issue)
        return {"issue": issue, "reasoning": reasoning_path}
    except Exception as e:
        logger.error(f"Грешка при KG reasoning за '{issue}': {e}")
        raise HTTPException(status_code=500, detail="Грешка при извършване на логически анализ")

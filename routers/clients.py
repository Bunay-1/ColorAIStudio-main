"""
Clients Router for ICAP Enterprise
==================================
REST API endpoints for client management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List
import logging

from app.modules import database
from app.core.models import ClientCreateRequest
from utils.auth import get_current_active_user
from services import client_service

router = APIRouter(tags=["Clients"])
logger = logging.getLogger("Clients_Router")

def get_db():
    """Dependency for database connection."""
    try:
        with database.get_db_connection() as conn:
            yield conn
    except Exception as e:
        logger.error(f"Грешка при свързване с базата данни: {e}")
        raise HTTPException(status_code=500, detail="Грешка в базата данни")

@router.get("/", summary="Извличане на всички клиенти")
async def get_clients(current_user: dict = Depends(get_current_active_user), conn=Depends(get_db)):
    """
    Връща списък с всички регистрирани клиенти.
    """
    try:
        return await client_service.get_all_clients(conn)
    except Exception:
        raise HTTPException(status_code=500, detail="Грешка в базата данни")

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Добавяне на нов клиент")
async def add_client(data: ClientCreateRequest, current_user: dict = Depends(get_current_active_user), conn=Depends(get_db)):
    """
    Добавя нов клиент или обновява съществуващ.
    """
    try:
        return await client_service.create_or_update_client(data, conn)
    except Exception:
        raise HTTPException(status_code=500, detail="Грешка в базата данни")

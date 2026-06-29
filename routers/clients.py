"""
Clients Router for ICAP Enterprise
==================================
REST API endpoints for client management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List
import logging

import database
from app.core.models import ClientCreateRequest
from utils.auth import get_current_active_user

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
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients")
        rows = cursor.fetchall()
        return {row["id"]: dict(row) for row in rows}
    except Exception as e:
        logger.error(f"Грешка в базата данни: {e}")
        raise HTTPException(status_code=500, detail="Грешка в базата данни")

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Добавяне на нов клиент")
async def add_client(data: ClientCreateRequest, current_user: dict = Depends(get_current_active_user), conn=Depends(get_db)):
    """
    Добавя нов клиент или обновява съществуващ.
    """
    try:
        cursor = conn.cursor()
        client_id = data.name.upper().replace(" ", "_")
        cursor.execute("INSERT OR REPLACE INTO clients (id, name, tolerance, preferred_method) VALUES (?, ?, ?, ?)",
                       (client_id, data.name, data.tolerance, data.preferred_method))
        conn.commit()
        return {"message": "Клиентът е добавен/обновен успешно", "id": client_id}
    except Exception as e:
        logger.error(f"Грешка в базата данни: {e}")
        raise HTTPException(status_code=500, detail="Грешка в базата данни")

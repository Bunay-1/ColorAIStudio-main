"""
Client Service for ICAP Enterprise
==================================
Business logic for client management.
"""

import logging
from app.modules import database
from app.core.models import ClientCreateRequest

logger = logging.getLogger("Client_Service")

async def get_all_clients(conn):
    """Извлича всички клиенти от базата данни."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients")
        rows = cursor.fetchall()
        return {row["id"]: dict(row) for row in rows}
    except Exception as e:
        logger.error(f"Грешка при извличане на клиенти: {e}")
        raise e

async def create_or_update_client(data: ClientCreateRequest, conn):
    """Създава или обновява клиент."""
    try:
        cursor = conn.cursor()
        client_id = data.name.upper().replace(" ", "_")
        cursor.execute("INSERT OR REPLACE INTO clients (id, name, tolerance, preferred_method) VALUES (?, ?, ?, ?)",
                       (client_id, data.name, data.tolerance, data.preferred_method))
        conn.commit()
        return {"message": "Клиентът е добавен/обновен успешно", "id": client_id}
    except Exception as e:
        logger.error(f"Грешка при запис на клиент: {e}")
        raise e

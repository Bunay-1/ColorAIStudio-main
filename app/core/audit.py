from app.modules import database
import logging
import sqlite3
from typing import Dict, Any

logger = logging.getLogger("ICAP_API")

def log_to_audit_trail(data: Dict[str, Any]) -> None:
    """Log measurement to audit trail with parameterized queries to prevent SQL injection."""
    try:
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO measurements (timestamp, batch_id, operator_id, machine_id, client_id, delta_e, status, method, illuminant)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('timestamp'), data.get('batch_id'), data.get('operator_id'),
                data.get('machine_id'), data.get('client_id'), data.get('delta_e'),
                data.get('status'), data.get('method'), data.get('illuminant')
            ))
            conn.commit()
    except (sqlite3.IntegrityError, sqlite3.OperationalError) as e:
        logger.error(f"SQL Audit Error: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error in audit trail: {e}", exc_info=True)

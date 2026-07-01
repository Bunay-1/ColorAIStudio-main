"""
GraphQL Router for ICAP Platform
================================
GraphQL endpoint for complex queries and data fetching.
"""

import strawberry
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import Depends, Request
import logging
from app.modules import database
from utils.version import ICAP_VERSION_DISPLAY
from app.modules.color_engine import ColorEngine

logger = logging.getLogger("GraphQLRouter")

# GraphQL Types
@strawberry.type
class MeasurementType:
    id: int
    batch_id: str
    operator_id: str
    machine_id: str
    client_id: str
    delta_e: float
    status: str
    timestamp: datetime
    lab_sample: List[float]
    lab_standard: List[float]

@strawberry.type
class UserType:
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

@strawberry.type
class TenantType:
    id: int
    tenant_id: str
    tenant_name: str
    is_active: bool
    created_at: datetime

@strawberry.type
class QualityMetricType:
    total_measurements: int
    pass_rate: float
    average_delta_e: float
    trend: str

@strawberry.type
class ServiceStatusType:
    name: str
    status: str

@strawberry.type
class SystemStatusType:
    status: str
    version: str
    services: List[ServiceStatusType]

@strawberry.type
class AlertType:
    id: int
    level: str
    title: str
    message: str
    timestamp: datetime

@strawberry.type
class Query:
    @strawberry.field
    def measurements(
        self,
        limit: int = 50,
        offset: int = 0,
        batch_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[MeasurementType]:
        """
        Заявка за измервания с незадължителни филтри.
        """
        try:
            with database.get_db_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM measurements WHERE 1=1"
                params = []

                if batch_id:
                    query += " AND batch_id = ?"
                    params.append(batch_id)

                if status:
                    query += " AND status = ?"
                    params.append(status)

                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [
                    MeasurementType(
                        id=row["id"],
                        batch_id=row["batch_id"],
                        operator_id=row["operator_id"],
                        machine_id=row["machine_id"],
                        client_id=row["client_id"],
                        delta_e=row["delta_e"],
                        status=row["status"],
                        timestamp=datetime.fromisoformat(row["timestamp"]) if isinstance(row["timestamp"], str) else row["timestamp"],
                        lab_sample=json.loads(row["lab_sample"]) if isinstance(row["lab_sample"], str) else [],
                        lab_standard=json.loads(row["lab_standard"]) if isinstance(row["lab_standard"], str) else []
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Грешка при извличане на измервания: {e}")
            return []
    
    @strawberry.field
    def measurement(self, id: int) -> Optional[MeasurementType]:
        """
        Заявка за единично измерване по ID.
        """
        try:
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM measurements WHERE id = ?", (id,))
                row = cursor.fetchone()

                if row:
                    return MeasurementType(
                        id=row["id"],
                        batch_id=row["batch_id"],
                        operator_id=row["operator_id"],
                        machine_id=row["machine_id"],
                        client_id=row["client_id"],
                        delta_e=row["delta_e"],
                        status=row["status"],
                        timestamp=datetime.fromisoformat(row["timestamp"]) if isinstance(row["timestamp"], str) else row["timestamp"],
                        lab_sample=json.loads(row["lab_sample"]) if isinstance(row["lab_sample"], str) else [],
                        lab_standard=json.loads(row["lab_standard"]) if isinstance(row["lab_standard"], str) else []
                    )
                return None
        except Exception as e:
            logger.error(f"Грешка при извличане на измерване: {e}")
            return None
    
    @strawberry.field
    def users(self, limit: int = 50) -> List[UserType]:
        """
        Заявка за всички потребители.
        """
        try:
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users LIMIT ?", (limit,))
                rows = cursor.fetchall()

                return [
                    UserType(
                        id=row["id"],
                        username=row["username"],
                        email=row["email"],
                        role=row["role"],
                        is_active=row["is_active"],
                        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"]
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Грешка при извличане на потребители: {e}")
            return []
    
    @strawberry.field
    def tenants(self, limit: int = 50) -> List[TenantType]:
        """
        Заявка за всички тенанти.
        """
        try:
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tenants LIMIT ?", (limit,))
                rows = cursor.fetchall()

                return [
                    TenantType(
                        id=row["id"],
                        tenant_id=row["tenant_id"],
                        tenant_name=row["tenant_name"],
                        is_active=row["is_active"],
                        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"]
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Грешка при извличане на тенанти: {e}")
            return []
    
    @strawberry.field
    def quality_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> QualityMetricType:
        """
        Заявка за метрики за качество за определен период.
        """
        try:
            with database.get_db_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT
                        COUNT(*) as total,
                        AVG(delta_e) as avg_delta_e,
                        SUM(CASE WHEN status = 'Pass' OR status = 'Успех' THEN 1 ELSE 0 END) as passed
                    FROM measurements
                    WHERE 1=1
                """
                params = []

                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())

                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date.isoformat())

                cursor.execute(query, params)
                row = cursor.fetchone()

                total = row["total"] or 0
                passed = row["passed"] or 0
                avg_delta_e = row["avg_delta_e"] or 0.0
                pass_rate = (passed / total * 100) if total > 0 else 0.0

                # Determine trend (simplified)
                trend = "stable"
                if avg_delta_e > 2.0:
                    trend = "increasing"
                elif avg_delta_e < 1.0:
                    trend = "decreasing"

                return QualityMetricType(
                    total_measurements=total,
                    pass_rate=pass_rate,
                    average_delta_e=avg_delta_e,
                    trend=trend
                )
        except Exception as e:
            logger.error(f"Грешка при извличане на метрики за качество: {e}")
            return QualityMetricType(
                total_measurements=0,
                pass_rate=0.0,
                average_delta_e=0.0,
                trend="unknown"
            )
    
    @strawberry.field
    def system_status(self) -> SystemStatusType:
        """
        Заявка за статус на системата.
        """
        return SystemStatusType(
            status="healthy",
            version=ICAP_VERSION_DISPLAY,
            services=[
                ServiceStatusType(name="database", status="healthy"),
                ServiceStatusType(name="redis", status="healthy"),
                ServiceStatusType(name="qdrant", status="healthy"),
                ServiceStatusType(name="ollama", status="healthy")
            ]
        )
    
    @strawberry.field
    def alerts(
        self,
        limit: int = 50,
        level: Optional[str] = None
    ) -> List[AlertType]:
        """
        Заявка за алерти с незадължителен филтър за ниво.
        """
        try:
            with database.get_db_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM measurements WHERE status != 'Pass' AND status != 'Успех'"
                params = []

                # Using measurements as a source for alerts if audit_logs table is not fully defined
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [
                    AlertType(
                        id=row["id"],
                        level="warning",
                        title=f"Отклонение в партида {row['batch_id']}",
                        message=f"Delta E: {row['delta_e']} надвишава толеранса.",
                        timestamp=datetime.fromisoformat(row["timestamp"]) if isinstance(row["timestamp"], str) else row["timestamp"]
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Грешка при извличане на алерти: {e}")
            return []

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_measurement(
        self,
        batch_id: str,
        operator_id: str,
        machine_id: str,
        client_id: str,
        lab_sample: List[float],
        lab_standard: List[float],
        method: str = "CIE2000"
    ) -> Optional[MeasurementType]:
        """
        Създаване на ново измерване.
        """
        try:
            from app.modules.color_engine import ColorEngine
            engine = ColorEngine()
            delta_e = engine.calculate_delta_e(lab_sample, lab_standard, method)
            
            # Fetch tolerance for client
            tolerance = 1.0
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT tolerance FROM clients WHERE id = ?", (client_id,))
                row = cursor.fetchone()
                if row:
                    tolerance = row["tolerance"]

            status = "Успех" if delta_e <= tolerance else "Неуспех"
            now = datetime.utcnow().isoformat()
            
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO measurements
                    (batch_id, operator_id, machine_id, client_id, delta_e, status, timestamp, method, tenant_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (batch_id, operator_id, machine_id, client_id, delta_e, status, now, method, 'default')
                )
                conn.commit()
                last_id = cursor.lastrowid

                cursor.execute("SELECT * FROM measurements WHERE id = ?", (last_id,))
                row = cursor.fetchone()

                if row:
                    return MeasurementType(
                        id=row["id"],
                        batch_id=row["batch_id"],
                        operator_id=row["operator_id"],
                        machine_id=row["machine_id"],
                        client_id=row["client_id"],
                        delta_e=row["delta_e"],
                        status=row["status"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        lab_sample=lab_sample,
                        lab_standard=lab_standard
                    )
            return None
        except Exception as e:
            logger.error(f"Грешка при създаване на измерване: {e}")
            return None

# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

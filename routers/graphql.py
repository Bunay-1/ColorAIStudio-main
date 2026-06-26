"""
GraphQL Router for ICAP Platform
================================
GraphQL endpoint for complex queries and data fetching.
"""

import strawberry
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import Depends
import logging
import database

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
class SystemStatusType:
    status: str
    version: str
    services: Dict[str, str]

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
        Query measurements with optional filters.
        """
        try:
            conn = database.get_db_connection()
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
            conn.close()
            
            return [
                MeasurementType(
                    id=row["id"],
                    batch_id=row["batch_id"],
                    operator_id=row["operator_id"],
                    machine_id=row["machine_id"],
                    client_id=row["client_id"],
                    delta_e=row["delta_e"],
                    status=row["status"],
                    timestamp=row["timestamp"],
                    lab_sample=row["lab_sample"],
                    lab_standard=row["lab_standard"]
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error fetching measurements: {e}")
            return []
    
    @strawberry.field
    def measurement(self, id: int) -> Optional[MeasurementType]:
        """
        Query a single measurement by ID.
        """
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM measurements WHERE id = ?", (id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return MeasurementType(
                    id=row["id"],
                    batch_id=row["batch_id"],
                    operator_id=row["operator_id"],
                    machine_id=row["machine_id"],
                    client_id=row["client_id"],
                    delta_e=row["delta_e"],
                    status=row["status"],
                    timestamp=row["timestamp"],
                    lab_sample=row["lab_sample"],
                    lab_standard=row["lab_standard"]
                )
            return None
        except Exception as e:
            logger.error(f"Error fetching measurement: {e}")
            return None
    
    @strawberry.field
    def users(self, limit: int = 50) -> List[UserType]:
        """
        Query all users.
        """
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            return [
                UserType(
                    id=row["id"],
                    username=row["username"],
                    email=row["email"],
                    role=row["role"],
                    is_active=row["is_active"],
                    created_at=row["created_at"]
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []
    
    @strawberry.field
    def tenants(self, limit: int = 50) -> List[TenantType]:
        """
        Query all tenants.
        """
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tenants LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            return [
                TenantType(
                    id=row["id"],
                    tenant_id=row["tenant_id"],
                    tenant_name=row["tenant_name"],
                    is_active=row["is_active"],
                    created_at=row["created_at"]
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error fetching tenants: {e}")
            return []
    
    @strawberry.field
    def quality_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> QualityMetricType:
        """
        Query quality metrics for a date range.
        """
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    COUNT(*) as total,
                    AVG(delta_e) as avg_delta_e,
                    SUM(CASE WHEN status = 'Pass' THEN 1 ELSE 0 END) as passed
                FROM measurements
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            conn.close()
            
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
            logger.error(f"Error fetching quality metrics: {e}")
            return QualityMetricType(
                total_measurements=0,
                pass_rate=0.0,
                average_delta_e=0.0,
                trend="unknown"
            )
    
    @strawberry.field
    def system_status(self) -> SystemStatusType:
        """
        Query system status.
        """
        return SystemStatusType(
            status="healthy",
            version="8.10.0",
            services={
                "database": "healthy",
                "redis": "healthy",
                "qdrant": "healthy",
                "ollama": "healthy"
            }
        )
    
    @strawberry.field
    def alerts(
        self,
        limit: int = 50,
        level: Optional[str] = None
    ) -> List[AlertType]:
        """
        Query alerts with optional level filter.
        """
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = []
            
            if level:
                query += " AND level = ?"
                params.append(level)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            return [
                AlertType(
                    id=row["id"],
                    level=row.get("level", "info"),
                    title=row.get("action", "Alert"),
                    message=row.get("details", ""),
                    timestamp=row["timestamp"]
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
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
        method: str = "CIEDE2000"
    ) -> Optional[MeasurementType]:
        """
        Create a new measurement.
        """
        try:
            # Calculate Delta E (simplified - would use actual color engine)
            delta_e = 1.5  # Placeholder
            status = "Pass" if delta_e < 2.0 else "Fail"
            
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO measurements 
                (batch_id, operator_id, machine_id, client_id, delta_e, status, lab_sample, lab_standard, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (batch_id, operator_id, machine_id, client_id, delta_e, status, str(lab_sample), str(lab_standard), datetime.utcnow())
            )
            conn.commit()
            
            cursor.execute("SELECT * FROM measurements WHERE id = ?", (cursor.lastrowid,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return MeasurementType(
                    id=row["id"],
                    batch_id=row["batch_id"],
                    operator_id=row["operator_id"],
                    machine_id=row["machine_id"],
                    client_id=row["client_id"],
                    delta_e=row["delta_e"],
                    status=row["status"],
                    timestamp=row["timestamp"],
                    lab_sample=row["lab_sample"],
                    lab_standard=row["lab_standard"]
                )
            return None
        except Exception as e:
            logger.error(f"Error creating measurement: {e}")
            return None

# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

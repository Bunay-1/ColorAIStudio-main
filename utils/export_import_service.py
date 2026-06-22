"""
Data Export/Import Service for ICAP Enterprise
==============================================
Data export and import functionality for backup, migration, and data transfer.
"""

import sqlite3
import logging
import csv
import json
import io
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import os

logger = logging.getLogger("Export_Import_Service")

class ExportFormat(str, Enum):
    """Export formats."""
    JSON = "json"
    CSV = "csv"
    XML = "xml"

class DataType(str, Enum):
    """Data types for export/import."""
    USERS = "users"
    TENANTS = "tenants"
    MEASUREMENTS = "measurements"
    AUDIT_LOGS = "audit_logs"
    ALL = "all"

@dataclass
class ExportResult:
    """Export result data structure."""
    data_type: DataType
    format: ExportFormat
    record_count: int
    file_size_bytes: int
    exported_at: str
    data: Optional[str] = None
    
    def __post_init__(self):
        if self.exported_at is None:
            self.exported_at = datetime.now().isoformat()

@dataclass
class ImportResult:
    """Import result data structure."""
    data_type: DataType
    format: ExportFormat
    record_count: int
    success_count: int
    failure_count: int
    imported_at: str
    errors: List[str] = None
    
    def __post_init__(self):
        if self.imported_at is None:
            self.imported_at = datetime.now().isoformat()
        if self.errors is None:
            self.errors = []

class ExportImportService:
    """Main export/import service for ICAP Enterprise."""
    
    def __init__(self, db_path: str = None):
        """Initialize export/import service."""
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "..", "icap.db")
    
    def export_data(
        self,
        data_type: DataType,
        format: ExportFormat = ExportFormat.JSON,
        filters: Optional[Dict[str, Any]] = None
    ) -> ExportResult:
        """
        Export data from the database.
        
        Args:
            data_type: Type of data to export
            format: Export format
            filters: Optional filters for data selection
        
        Returns:
            Export result with data
        """
        try:
            if data_type == DataType.USERS:
                data = self._export_users(format, filters)
            elif data_type == DataType.TENANTS:
                data = self._export_tenants(format, filters)
            elif data_type == DataType.MEASUREMENTS:
                data = self._export_measurements(format, filters)
            elif data_type == DataType.AUDIT_LOGS:
                data = self._export_audit_logs(format, filters)
            elif data_type == DataType.ALL:
                data = self._export_all(format, filters)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
            
            logger.info(f"Data exported: {data_type.value} ({format.value})")
            return data
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            raise
    
    def _export_users(
        self,
        format: ExportFormat,
        filters: Optional[Dict[str, Any]] = None
    ) -> ExportResult:
        """Export users data."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM users'
            params = []
            
            if filters:
                if 'role' in filters:
                    query += ' WHERE role = ?'
                    params.append(filters['role'])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            # Convert to list of dicts
            data = [dict(row) for row in rows]
            
            # Format data
            if format == ExportFormat.JSON:
                formatted_data = json.dumps(data, indent=2, default=str)
            elif format == ExportFormat.CSV:
                output = io.StringIO()
                if data:
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                formatted_data = output.getvalue()
            else:
                formatted_data = json.dumps(data, default=str)
            
            return ExportResult(
                data_type=DataType.USERS,
                format=format,
                record_count=len(data),
                file_size_bytes=len(formatted_data.encode()),
                data=formatted_data
            )
            
        except Exception as e:
            logger.error(f"Failed to export users: {e}")
            raise
    
    def _export_tenants(
        self,
        format: ExportFormat,
        filters: Optional[Dict[str, Any]] = None
    ) -> ExportResult:
        """Export tenants data."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM tenants'
            params = []
            
            if filters:
                if 'is_active' in filters:
                    query += ' WHERE is_active = ?'
                    params.append(filters['is_active'])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            data = [dict(row) for row in rows]
            
            if format == ExportFormat.JSON:
                formatted_data = json.dumps(data, indent=2, default=str)
            elif format == ExportFormat.CSV:
                output = io.StringIO()
                if data:
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                formatted_data = output.getvalue()
            else:
                formatted_data = json.dumps(data, default=str)
            
            return ExportResult(
                data_type=DataType.TENANTS,
                format=format,
                record_count=len(data),
                file_size_bytes=len(formatted_data.encode()),
                data=formatted_data
            )
            
        except Exception as e:
            logger.error(f"Failed to export tenants: {e}")
            raise
    
    def _export_measurements(
        self,
        format: ExportFormat,
        filters: Optional[Dict[str, Any]] = None
    ) -> ExportResult:
        """Export measurements data."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM measurements'
            params = []
            
            if filters:
                conditions = []
                if 'start_date' in filters:
                    conditions.append('timestamp >= ?')
                    params.append(filters['start_date'])
                if 'end_date' in filters:
                    conditions.append('timestamp <= ?')
                    params.append(filters['end_date'])
                if 'batch_id' in filters:
                    conditions.append('batch_id = ?')
                    params.append(filters['batch_id'])
                
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' LIMIT 10000'  # Limit to prevent large exports
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            data = [dict(row) for row in rows]
            
            if format == ExportFormat.JSON:
                formatted_data = json.dumps(data, indent=2, default=str)
            elif format == ExportFormat.CSV:
                output = io.StringIO()
                if data:
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                formatted_data = output.getvalue()
            else:
                formatted_data = json.dumps(data, default=str)
            
            return ExportResult(
                data_type=DataType.MEASUREMENTS,
                format=format,
                record_count=len(data),
                file_size_bytes=len(formatted_data.encode()),
                data=formatted_data
            )
            
        except Exception as e:
            logger.error(f"Failed to export measurements: {e}")
            raise
    
    def _export_audit_logs(
        self,
        format: ExportFormat,
        filters: Optional[Dict[str, Any]] = None
    ) -> ExportResult:
        """Export audit logs data."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM audit_logs'
            params = []
            
            if filters:
                conditions = []
                if 'start_date' in filters:
                    conditions.append('timestamp >= ?')
                    params.append(filters['start_date'])
                if 'end_date' in filters:
                    conditions.append('timestamp <= ?')
                    params.append(filters['end_date'])
                if 'user_id' in filters:
                    conditions.append('user_id = ?')
                    params.append(filters['user_id'])
                if 'action' in filters:
                    conditions.append('action = ?')
                    params.append(filters['action'])
                
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' LIMIT 10000'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            data = [dict(row) for row in rows]
            
            if format == ExportFormat.JSON:
                formatted_data = json.dumps(data, indent=2, default=str)
            elif format == ExportFormat.CSV:
                output = io.StringIO()
                if data:
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                formatted_data = output.getvalue()
            else:
                formatted_data = json.dumps(data, default=str)
            
            return ExportResult(
                data_type=DataType.AUDIT_LOGS,
                format=format,
                record_count=len(data),
                file_size_bytes=len(formatted_data.encode()),
                data=formatted_data
            )
            
        except Exception as e:
            logger.error(f"Failed to export audit logs: {e}")
            raise
    
    def _export_all(
        self,
        format: ExportFormat,
        filters: Optional[Dict[str, Any]] = None
    ) -> ExportResult:
        """Export all data types."""
        try:
            all_data = {
                "users": [],
                "tenants": [],
                "measurements": [],
                "audit_logs": []
            }
            
            # Export each data type
            users_result = self._export_users(format, filters)
            all_data["users"] = json.loads(users_result.data) if format == ExportFormat.JSON else []
            
            tenants_result = self._export_tenants(format, filters)
            all_data["tenants"] = json.loads(tenants_result.data) if format == ExportFormat.JSON else []
            
            measurements_result = self._export_measurements(format, filters)
            all_data["measurements"] = json.loads(measurements_result.data) if format == ExportFormat.JSON else []
            
            audit_logs_result = self._export_audit_logs(format, filters)
            all_data["audit_logs"] = json.loads(audit_logs_result.data) if format == ExportFormat.JSON else []
            
            formatted_data = json.dumps(all_data, indent=2, default=str)
            
            return ExportResult(
                data_type=DataType.ALL,
                format=format,
                record_count=len(all_data["users"]) + len(all_data["tenants"]) + len(all_data["measurements"]) + len(all_data["audit_logs"]),
                file_size_bytes=len(formatted_data.encode()),
                data=formatted_data
            )
            
        except Exception as e:
            logger.error(f"Failed to export all data: {e}")
            raise
    
    def import_data(
        self,
        data_type: DataType,
        format: ExportFormat,
        data: str,
        overwrite: bool = False
    ) -> ImportResult:
        """
        Import data into the database.
        
        Args:
            data_type: Type of data to import
            format: Import format
            data: Data to import
            overwrite: Whether to overwrite existing data
        
        Returns:
            Import result
        """
        try:
            if data_type == DataType.USERS:
                result = self._import_users(format, data, overwrite)
            elif data_type == DataType.TENANTS:
                result = self._import_tenants(format, data, overwrite)
            elif data_type == DataType.MEASUREMENTS:
                result = self._import_measurements(format, data, overwrite)
            elif data_type == DataType.AUDIT_LOGS:
                result = self._import_audit_logs(format, data, overwrite)
            else:
                raise ValueError(f"Unsupported data type for import: {data_type}")
            
            logger.info(f"Data imported: {data_type.value} ({format.value})")
            return result
            
        except Exception as e:
            logger.error(f"Failed to import data: {e}")
            raise
    
    def _import_users(
        self,
        format: ExportFormat,
        data: str,
        overwrite: bool
    ) -> ImportResult:
        """Import users data."""
        try:
            if format == ExportFormat.JSON:
                records = json.loads(data)
            elif format == ExportFormat.CSV:
                records = list(csv.DictReader(io.StringIO(data)))
            else:
                records = json.loads(data)
            
            success_count = 0
            failure_count = 0
            errors = []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for record in records:
                try:
                    if overwrite:
                        cursor.execute('''
                            INSERT OR REPLACE INTO users (username, email, role, tenant_id, password_hash, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            record.get('username'),
                            record.get('email'),
                            record.get('role'),
                            record.get('tenant_id'),
                            record.get('password_hash'),
                            record.get('created_at', datetime.now().isoformat())
                        ))
                    else:
                        cursor.execute('''
                            INSERT OR IGNORE INTO users (username, email, role, tenant_id, password_hash, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            record.get('username'),
                            record.get('email'),
                            record.get('role'),
                            record.get('tenant_id'),
                            record.get('password_hash'),
                            record.get('created_at', datetime.now().isoformat())
                        ))
                    
                    success_count += 1
                except Exception as e:
                    failure_count += 1
                    errors.append(f"Failed to import user {record.get('username')}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            return ImportResult(
                data_type=DataType.USERS,
                format=format,
                record_count=len(records),
                success_count=success_count,
                failure_count=failure_count,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Failed to import users: {e}")
            raise
    
    def _import_tenants(
        self,
        format: ExportFormat,
        data: str,
        overwrite: bool
    ) -> ImportResult:
        """Import tenants data."""
        try:
            if format == ExportFormat.JSON:
                records = json.loads(data)
            elif format == ExportFormat.CSV:
                records = list(csv.DictReader(io.StringIO(data)))
            else:
                records = json.loads(data)
            
            success_count = 0
            failure_count = 0
            errors = []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for record in records:
                try:
                    config = json.dumps(record.get('config', {}))
                    
                    if overwrite:
                        cursor.execute('''
                            INSERT OR REPLACE INTO tenants (tenant_id, name, config, is_active, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            record.get('tenant_id'),
                            record.get('name'),
                            config,
                            record.get('is_active', True),
                            record.get('created_at', datetime.now().isoformat())
                        ))
                    else:
                        cursor.execute('''
                            INSERT OR IGNORE INTO tenants (tenant_id, name, config, is_active, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            record.get('tenant_id'),
                            record.get('name'),
                            config,
                            record.get('is_active', True),
                            record.get('created_at', datetime.now().isoformat())
                        ))
                    
                    success_count += 1
                except Exception as e:
                    failure_count += 1
                    errors.append(f"Failed to import tenant {record.get('tenant_id')}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            return ImportResult(
                data_type=DataType.TENANTS,
                format=format,
                record_count=len(records),
                success_count=success_count,
                failure_count=failure_count,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Failed to import tenants: {e}")
            raise
    
    def _import_measurements(
        self,
        format: ExportFormat,
        data: str,
        overwrite: bool
    ) -> ImportResult:
        """Import measurements data."""
        try:
            if format == ExportFormat.JSON:
                records = json.loads(data)
            elif format == ExportFormat.CSV:
                records = list(csv.DictReader(io.StringIO(data)))
            else:
                records = json.loads(data)
            
            success_count = 0
            failure_count = 0
            errors = []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for record in records:
                try:
                    if overwrite:
                        cursor.execute('''
                            INSERT OR REPLACE INTO measurements 
                            (timestamp, batch_id, operator_id, machine_id, client_id, delta_e, status, method, illuminant)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            record.get('timestamp'),
                            record.get('batch_id'),
                            record.get('operator_id'),
                            record.get('machine_id'),
                            record.get('client_id'),
                            record.get('delta_e'),
                            record.get('status'),
                            record.get('method'),
                            record.get('illuminant')
                        ))
                    else:
                        cursor.execute('''
                            INSERT OR IGNORE INTO measurements 
                            (timestamp, batch_id, operator_id, machine_id, client_id, delta_e, status, method, illuminant)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            record.get('timestamp'),
                            record.get('batch_id'),
                            record.get('operator_id'),
                            record.get('machine_id'),
                            record.get('client_id'),
                            record.get('delta_e'),
                            record.get('status'),
                            record.get('method'),
                            record.get('illuminant')
                        ))
                    
                    success_count += 1
                except Exception as e:
                    failure_count += 1
                    errors.append(f"Failed to import measurement: {str(e)}")
            
            conn.commit()
            conn.close()
            
            return ImportResult(
                data_type=DataType.MEASUREMENTS,
                format=format,
                record_count=len(records),
                success_count=success_count,
                failure_count=failure_count,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Failed to import measurements: {e}")
            raise
    
    def _import_audit_logs(
        self,
        format: ExportFormat,
        data: str,
        overwrite: bool
    ) -> ImportResult:
        """Import audit logs data."""
        try:
            if format == ExportFormat.JSON:
                records = json.loads(data)
            elif format == ExportFormat.CSV:
                records = list(csv.DictReader(io.StringIO(data)))
            else:
                records = json.loads(data)
            
            success_count = 0
            failure_count = 0
            errors = []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for record in records:
                try:
                    if overwrite:
                        cursor.execute('''
                            INSERT OR REPLACE INTO audit_logs 
                            (timestamp, user_id, action, tenant_id, ip_address, severity)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            record.get('timestamp'),
                            record.get('user_id'),
                            record.get('action'),
                            record.get('tenant_id'),
                            record.get('ip_address'),
                            record.get('severity')
                        ))
                    else:
                        cursor.execute('''
                            INSERT OR IGNORE INTO audit_logs 
                            (timestamp, user_id, action, tenant_id, ip_address, severity)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            record.get('timestamp'),
                            record.get('user_id'),
                            record.get('action'),
                            record.get('tenant_id'),
                            record.get('ip_address'),
                            record.get('severity')
                        ))
                    
                    success_count += 1
                except Exception as e:
                    failure_count += 1
                    errors.append(f"Failed to import audit log: {str(e)}")
            
            conn.commit()
            conn.close()
            
            return ImportResult(
                data_type=DataType.AUDIT_LOGS,
                format=format,
                record_count=len(records),
                success_count=success_count,
                failure_count=failure_count,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Failed to import audit logs: {e}")
            raise

# Global export/import service instance
export_import_service = ExportImportService()

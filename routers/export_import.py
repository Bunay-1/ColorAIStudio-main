"""
Export/Import Router for ICAP Enterprise
========================================
REST API endpoints for data export and import operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
import logging

from utils.export_import_service import (
    ExportImportService, ExportResult, ImportResult, DataType, ExportFormat
)
from utils.auth import get_current_user, check_permission

router = APIRouter(prefix="/export-import", tags=["Export/Import"])
logger = logging.getLogger("Export_Import_Router")

export_import_service = ExportImportService()

@router.post("/export")
async def export_data(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Export data from the database.
    
    - **data_type**: Type of data to export (users, tenants, measurements, audit_logs, all)
    - **format**: Export format (json, csv)
    - **filters**: Optional filters for data selection
    """
    try:
        # Only admins can export data
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        result = export_import_service.export_data(
            data_type=DataType(data["data_type"]),
            format=ExportFormat(data.get("format", "json")),
            filters=data.get("filters")
        )
        
        return {
            "data_type": result.data_type.value,
            "format": result.format.value,
            "record_count": result.record_count,
            "file_size_bytes": result.file_size_bytes,
            "exported_at": result.exported_at,
            "data": result.data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_data(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Import data into the database.
    
    - **data_type**: Type of data to import (users, tenants, measurements, audit_logs)
    - **format**: Import format (json, csv)
    - **data**: Data to import
    - **overwrite**: Whether to overwrite existing data
    """
    try:
        # Only admins can import data
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        result = export_import_service.import_data(
            data_type=DataType(data["data_type"]),
            format=ExportFormat(data.get("format", "json")),
            data=data["data"],
            overwrite=data.get("overwrite", False)
        )
        
        return {
            "data_type": result.data_type.value,
            "format": result.format.value,
            "record_count": result.record_count,
            "success_count": result.success_count,
            "failure_count": result.failure_count,
            "imported_at": result.imported_at,
            "errors": result.errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data-types")
async def list_data_types(current_user: dict = Depends(get_current_user)):
    """List available data types for export/import."""
    try:
        # Only admins can view data types
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        data_types = [
            {
                "value": dt.value,
                "name": dt.value.replace("_", " ").title(),
                "description": f"{dt.value.replace('_', ' ').title()} data"
            }
            for dt in DataType
        ]
        
        return {"data_types": data_types}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing data types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/formats")
async def list_formats(current_user: dict = Depends(get_current_user)):
    """List available export/import formats."""
    try:
        # Only admins can view formats
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        formats = [
            {
                "value": f.value,
                "name": f.value.upper(),
                "description": f"{f.value.upper()} format"
            }
            for f in ExportFormat
        ]
        
        return {"formats": formats}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing formats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

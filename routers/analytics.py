"""
Analytics Router for ICAP Enterprise
===================================
REST API endpoints for advanced analytics and reporting.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from utils.analytics_service import (
    AnalyticsService, Report, ReportType, ReportFormat, TimePeriod
)
from utils.auth import get_current_user, check_permission

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger("Analytics_Router")

analytics_service = AnalyticsService()

@router.get("/metrics/color-analysis")
async def get_color_analysis_metrics(
    start_date: str = Query(...),
    end_date: str = Query(...),
    tenant_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get color analysis metrics.
    
    - **start_date**: Start date (ISO format)
    - **end_date**: End date (ISO format)
    - **tenant_id**: Filter by tenant ID (optional)
    """
    try:
        metrics = analytics_service.get_color_analysis_analytics(
            start_date=start_date,
            end_date=end_date,
            tenant_id=tenant_id
        )
        
        return {
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp,
                    "metadata": m.metadata
                }
                for m in metrics
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting color analysis metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/user-activity")
async def get_user_activity_metrics(
    start_date: str = Query(...),
    end_date: str = Query(...),
    user_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get user activity metrics.
    
    - **start_date**: Start date (ISO format)
    - **end_date**: End date (ISO format)
    - **user_id**: Filter by user ID (optional)
    """
    try:
        # Non-admins can only see their own metrics
        if current_user["role"] != "ADMIN":
            user_id = current_user["username"]
        
        metrics = analytics_service.get_user_activity_analytics(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        return {
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp,
                    "metadata": m.metadata
                }
                for m in metrics
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting user activity metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/tenant-usage")
async def get_tenant_usage_metrics(
    start_date: str = Query(...),
    end_date: str = Query(...),
    tenant_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get tenant usage metrics.
    
    - **start_date**: Start date (ISO format)
    - **end_date**: End date (ISO format)
    - **tenant_id**: Filter by tenant ID (optional)
    """
    try:
        # Non-admins can only see their tenant's metrics
        if current_user["role"] != "ADMIN":
            tenant_id = current_user.get("tenant_id", "default")
        
        metrics = analytics_service.get_tenant_usage_analytics(
            start_date=start_date,
            end_date=end_date,
            tenant_id=tenant_id
        )
        
        return {
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp,
                    "metadata": m.metadata
                }
                for m in metrics
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting tenant usage metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/system-performance")
async def get_system_performance_metrics(
    start_date: str = Query(...),
    end_date: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Get system performance metrics.
    
    - **start_date**: Start date (ISO format)
    - **end_date**: End date (ISO format)
    """
    try:
        # Only admins can access system performance metrics
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        metrics = analytics_service.get_system_performance_analytics(
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp,
                    "metadata": m.metadata
                }
                for m in metrics
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports")
async def generate_report(
    report: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a report.
    
    - **type**: Report type (color_analysis, vision_analysis, user_activity, tenant_usage, system_performance, compliance, custom)
    - **title**: Report title
    - **description**: Report description
    - **period**: Time period (hourly, daily, weekly, monthly, custom)
    - **start_date**: Start date (ISO format)
    - **end_date**: End date (ISO format)
    - **format**: Output format (json, csv, pdf, html)
    - **tenant_id**: Filter by tenant ID (optional)
    - **user_id**: Filter by user ID (optional)
    """
    try:
        report_obj = analytics_service.generate_report(
            report_type=ReportType(report["type"]),
            title=report["title"],
            description=report["description"],
            period=TimePeriod(report["period"]),
            start_date=report["start_date"],
            end_date=report["end_date"],
            created_by=current_user["username"],
            format=ReportFormat(report.get("format", "json")),
            tenant_id=report.get("tenant_id"),
            user_id=report.get("user_id")
        )
        
        return {
            "id": report_obj.id,
            "type": report_obj.type.value,
            "title": report_obj.title,
            "description": report_obj.description,
            "period": report_obj.period.value,
            "start_date": report_obj.start_date,
            "end_date": report_obj.end_date,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp,
                    "metadata": m.metadata
                }
                for m in report_obj.metrics
            ],
            "created_by": report_obj.created_by,
            "created_at": report_obj.created_at,
            "format": report_obj.format.value
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports")
async def list_reports(
    report_type: Optional[str] = Query(None),
    limit: int = Query(50),
    current_user: dict = Depends(get_current_user)
):
    """
    List reports.
    
    - **report_type**: Filter by report type (optional)
    - **limit**: Maximum number of reports to return
    """
    try:
        report_type_enum = ReportType(report_type) if report_type else None
        
        reports = analytics_service.list_reports(
            report_type=report_type_enum,
            limit=limit
        )
        
        return {
            "reports": [
                {
                    "id": r.id,
                    "type": r.type.value,
                    "title": r.title,
                    "description": r.description,
                    "period": r.period.value,
                    "start_date": r.start_date,
                    "end_date": r.end_date,
                    "metrics_count": len(r.metrics),
                    "created_by": r.created_by,
                    "created_at": r.created_at,
                    "format": r.format.value
                }
                for r in reports
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/{report_id}")
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a report by ID."""
    try:
        report = analytics_service.get_report(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Check permission - users can only see their own reports unless admin
        if current_user["role"] != "ADMIN" and report.created_by != current_user["username"]:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        return {
            "id": report.id,
            "type": report.type.value,
            "title": report.title,
            "description": report.description,
            "period": report.period.value,
            "start_date": report.start_date,
            "end_date": report.end_date,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp,
                    "metadata": m.metadata
                }
                for m in report.metrics
            ],
            "created_by": report.created_by,
            "created_at": report.created_at,
            "format": report.format.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a report."""
    try:
        # Check permission - users can only delete their own reports unless admin
        report = analytics_service.get_report(report_id)
        if report and current_user["role"] != "ADMIN" and report.created_by != current_user["username"]:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        success = analytics_service.delete_report(report_id)
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=404, detail="Report not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
async def get_dashboard_data(
    period: str = Query("daily"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get aggregated dashboard data.
    
    - **period**: Time period (hourly, daily, weekly, monthly)
    """
    try:
        # Calculate date range based on period
        end_date = datetime.now()
        if period == "hourly":
            start_date = end_date - timedelta(hours=24)
        elif period == "daily":
            start_date = end_date - timedelta(days=7)
        elif period == "weekly":
            start_date = end_date - timedelta(weeks=4)
        elif period == "monthly":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)
        
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()
        
        # Get all metrics
        color_metrics = analytics_service.get_color_analysis_analytics(start_date_str, end_date_str)
        user_metrics = analytics_service.get_user_activity_analytics(start_date_str, end_date_str)
        tenant_metrics = analytics_service.get_tenant_usage_analytics(start_date_str, end_date_str)
        
        # System performance metrics (admin only)
        system_metrics = []
        if current_user["role"] == "ADMIN":
            system_metrics = analytics_service.get_system_performance_analytics(start_date_str, end_date_str)
        
        return {
            "period": period,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "color_analysis": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit
                }
                for m in color_metrics
            ],
            "user_activity": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit
                }
                for m in user_metrics
            ],
            "tenant_usage": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit
                }
                for m in tenant_metrics
            ],
            "system_performance": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit
                }
                for m in system_metrics
            ] if current_user["role"] == "ADMIN" else None
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-batch-risk", dependencies=[Depends(get_current_user)])
async def predict_batch_risk(process_params: dict, req: Request):
    """Предсказва риска за качеството на партидата на база параметри на процеса."""
    icap = req.app.state.icap
    try:
        risk_data = icap.ai_analysis.predict_quality_risk(process_params)
        return risk_data
    except Exception as e:
        logger.error(f"Грешка при предсказване на риск: {e}")
        raise HTTPException(status_code=500, detail="Вътрешна грешка при анализ на риска")

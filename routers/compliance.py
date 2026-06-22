"""
Compliance Router for ICAP Enterprise
====================================
REST API endpoints for compliance reporting and management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from utils.compliance_service import (
    ComplianceService, ComplianceReport, ComplianceStandard, ComplianceStatus, ReportFrequency
)
from utils.auth import get_current_user, check_permission

router = APIRouter(prefix="/compliance", tags=["Compliance"])
logger = logging.getLogger("Compliance_Router")

compliance_service = ComplianceService()

@router.post("/reports")
async def generate_compliance_report(
    report: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a compliance report.
    
    - **standard**: Compliance standard (gdpr, soc2, hipaa, iso27001, pci_dss, custom)
    - **title**: Report title
    - **description**: Report description
    - **period_start**: Report period start (ISO format)
    - **period_end**: Report period end (ISO format)
    """
    try:
        # Only admins can generate compliance reports
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        report_obj = compliance_service.generate_compliance_report(
            standard=ComplianceStandard(report["standard"]),
            title=report["title"],
            description=report["description"],
            period_start=report["period_start"],
            period_end=report["period_end"],
            generated_by=current_user["username"]
        )
        
        return {
            "id": report_obj.id,
            "standard": report_obj.standard.value,
            "title": report_obj.title,
            "description": report_obj.description,
            "period_start": report_obj.period_start,
            "period_end": report_obj.period_end,
            "overall_status": report_obj.overall_status.value,
            "overall_score": report_obj.overall_score,
            "checks": [
                {
                    "id": c.id,
                    "control_id": c.control_id,
                    "control_name": c.control_name,
                    "description": c.description,
                    "status": c.status.value,
                    "score": c.score,
                    "findings": c.findings,
                    "last_assessed": c.last_assessed
                }
                for c in report_obj.checks
            ],
            "recommendations": report_obj.recommendations,
            "generated_by": report_obj.generated_by,
            "generated_at": report_obj.generated_at,
            "approved_by": report_obj.approved_by,
            "approved_at": report_obj.approved_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports")
async def list_compliance_reports(
    standard: Optional[str] = Query(None),
    limit: int = Query(50),
    current_user: dict = Depends(get_current_user)
):
    """
    List compliance reports.
    
    - **standard**: Filter by compliance standard
    - **limit**: Maximum number of reports to return
    """
    try:
        # Only admins can view compliance reports
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        standard_enum = ComplianceStandard(standard) if standard else None
        
        reports = compliance_service.list_reports(
            standard=standard_enum,
            limit=limit
        )
        
        return {
            "reports": [
                {
                    "id": r.id,
                    "standard": r.standard.value,
                    "title": r.title,
                    "description": r.description,
                    "period_start": r.period_start,
                    "period_end": r.period_end,
                    "overall_status": r.overall_status.value,
                    "overall_score": r.overall_score,
                    "checks_count": len(r.checks),
                    "generated_by": r.generated_by,
                    "generated_at": r.generated_at,
                    "approved_by": r.approved_by,
                    "approved_at": r.approved_at
                }
                for r in reports
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing compliance reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/{report_id}")
async def get_compliance_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a compliance report by ID."""
    try:
        # Only admins can view compliance reports
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        report = compliance_service.get_report(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {
            "id": report.id,
            "standard": report.standard.value,
            "title": report.title,
            "description": report.description,
            "period_start": report.period_start,
            "period_end": report.period_end,
            "overall_status": report.overall_status.value,
            "overall_score": report.overall_score,
            "checks": [
                {
                    "id": c.id,
                    "control_id": c.control_id,
                    "control_name": c.control_name,
                    "description": c.description,
                    "status": c.status.value,
                    "score": c.score,
                    "findings": c.findings,
                    "evidence": c.evidence,
                    "last_assessed": c.last_assessed,
                    "assessor": c.assessor
                }
                for c in report.checks
            ],
            "recommendations": report.recommendations,
            "generated_by": report.generated_by,
            "generated_at": report.generated_at,
            "approved_by": report.approved_by,
            "approved_at": report.approved_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/reports/{report_id}/approve")
async def approve_compliance_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Approve a compliance report."""
    try:
        # Only admins can approve compliance reports
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        success = compliance_service.approve_report(report_id, current_user["username"])
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=404, detail="Report not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/standards")
async def list_compliance_standards(current_user: dict = Depends(get_current_user)):
    """List available compliance standards."""
    try:
        # Only admins can view compliance standards
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        standards = [
            {
                "value": s.value,
                "name": s.value.upper(),
                "description": f"{s.value.upper()} compliance requirements"
            }
            for s in ComplianceStandard
        ]
        
        return {"standards": standards}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing compliance standards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
async def get_compliance_dashboard(
    current_user: dict = Depends(get_current_user)
):
    """
    Get compliance dashboard summary.
    
    Returns summary of compliance status across all standards.
    """
    try:
        # Only admins can view compliance dashboard
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Get recent reports for each standard
        summary = {}
        
        for standard in ComplianceStandard:
            reports = compliance_service.list_reports(standard=standard, limit=1)
            
            if reports:
                latest_report = reports[0]
                summary[standard.value] = {
                    "overall_status": latest_report.overall_status.value,
                    "overall_score": latest_report.overall_score,
                    "last_report_date": latest_report.generated_at,
                    "checks_count": len(latest_report.checks)
                }
            else:
                summary[standard.value] = {
                    "overall_status": "pending_review",
                    "overall_score": 0.0,
                    "last_report_date": None,
                    "checks_count": 0
                }
        
        return {"summary": summary}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compliance dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

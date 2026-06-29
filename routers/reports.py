"""
Reports Router for ICAP Enterprise
==================================
REST API endpoints for generating and downloading reports.
"""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from typing import Any

from utils.auth import get_current_active_user
from services.report_service import generate_iso_audit_report as svc_gen_iso, generate_html_report as svc_gen_html

router = APIRouter(tags=["Reports"])
logger = logging.getLogger("Reports_Router")

@router.post("/generate-iso", summary="Генериране на ISO одитен доклад")
async def generate_iso_audit_report(current_user: dict = Depends(get_current_active_user)):
    """
    Генерира PDF доклад за съответствие с ISO стандартите.
    """
    try:
        filename = svc_gen_iso()
        return {"filename": filename}
    except Exception as e:
        logger.error(f"Грешка при генериране на ISO доклад: {e}")
        raise HTTPException(status_code=500, detail="Грешка при генериране на отчета")

@router.post("/generate-html", summary="Генериране на HTML доклад за измерване")
async def generate_html_report(request: Any, req: Request, current_user: dict = Depends(get_current_active_user)):
    """
    Генерира детайлен HTML доклад за конкретно измерване на цвят.
    """
    try:
        icap = req.app.state.icap
        de = icap.color_engine.calculate_delta_e(request.lab_sample, request.lab_standard, request.method)
        status = "Успех" if de <= request.tolerance else "Неуспех"
        status_color = "#47ff9c" if status == "Успех" else "#ff4766"

        filename = svc_gen_html(request.dict(), de, status, status_color, icap.color_engine)
        return {"filename": filename}
    except Exception as e:
        logger.error(f"Грешка при генериране на HTML доклад: {e}")
        raise HTTPException(status_code=500, detail="Грешка при генериране на отчета")

@router.get("/download/{filename}", summary="Изтегляне на доклад")
async def download_report(filename: str, current_user: dict = Depends(get_current_active_user)):
    """
    Изтегляне на генериран доклад от директорията AuditTrail.
    """
    base_dir = os.path.realpath("AuditTrail")
    file_path = os.path.realpath(os.path.join(base_dir, filename))

    if not file_path.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Достъпът е забранен")

    if os.path.exists(file_path):
        return FileResponse(file_path)

    raise HTTPException(status_code=404, detail="Докладът не е намерен")

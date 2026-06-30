import os
import json
import logging
import asyncio
import random
from typing import Any, Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, FileResponse
from pydantic import ValidationError

import database
from app.core.models import ClientCreateRequest
from routers import vision, rag, color, training, agents, iot, models, knowledge_graph, reports
from services import (
    client_service, model_service, report_service, vision_service,
    rag_service, color_service, training_service, iot_business_service, agent_service
)
from utils.auth import get_current_active_user

logger = logging.getLogger("ICAP_API")

router = APIRouter(tags=["Legacy"])

DEPRECATED_HEADERS = {"X-API-Deprecated": "true", "Link": "</v1>; rel=\"successor-version\""}

async def wrap_legacy_response(awaitable):
    res = await awaitable
    if isinstance(res, JSONResponse):
        res.headers.update(DEPRECATED_HEADERS)
        return res
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

def get_db():
    """Dependency for database connection."""
    try:
        with database.get_db_connection() as conn:
            yield conn
    except Exception as e:
        logger.error(f"Грешка при свързване с базата данни: {e}")
        raise HTTPException(status_code=500, detail="Грешка в базата данни")

@router.get("/clients", dependencies=[Depends(get_current_active_user)])
async def get_clients(conn=Depends(get_db)):
    try:
        res = await client_service.get_all_clients(conn)
        return JSONResponse(content=res, headers=DEPRECATED_HEADERS)
    except Exception:
        raise HTTPException(status_code=500, detail="Грешка в базата данни")

@router.post("/clients", dependencies=[Depends(get_current_active_user)])
async def add_client(data: ClientCreateRequest, conn=Depends(get_db)):
    try:
        res = await client_service.create_or_update_client(data, conn)
        return JSONResponse(content=res, headers=DEPRECATED_HEADERS)
    except Exception:
        raise HTTPException(status_code=500, detail="Грешка в базата данни")

@router.get("/model_registry", dependencies=[Depends(get_current_active_user)])
async def get_model_registry():
    res = await model_service.get_model_registry()
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/vision_analyze", dependencies=[Depends(get_current_active_user)])
async def legacy_vision_analyze(req: Request, file: UploadFile = File(...)):
    res = await vision_service.analyze_vision(file, False, req.app.state.icap, req.client.host if req.client else None)
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/vision_micro_analyze", dependencies=[Depends(get_current_active_user)])
async def legacy_vision_micro_analyze(req: Request, file: UploadFile = File(...)):
    res = await vision_service.analyze_micro_vision(file, req.app.state.icap)
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.get("/rag_stats", dependencies=[Depends(get_current_active_user)])
async def legacy_rag_stats(req: Request):
    res = await rag_service.get_rag_stats(req.app.state.icap)
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/index_document", dependencies=[Depends(get_current_active_user)])
async def legacy_index_document(request: Any, background_tasks: BackgroundTasks, req: Request):
    res = await rag_service.index_docs(request.file_path, req.app.state.icap, req.app.state.manager, background_tasks)
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/analyze_color", dependencies=[Depends(get_current_active_user)])
async def legacy_analyze_color(request: Any, req: Request):
    res = await color_service.process_color_analysis(
        request, req.app.state.icap, req.app.state.alert_system,
        req.app.state.log_to_audit_trail, req.client.host if req.client else None
    )
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/predict_trend", dependencies=[Depends(get_current_active_user)])
async def legacy_predict_trend(request: Any, req: Request):
    res = await color_service.predict_trend(request, req.app.state.icap)
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/recipe_formulation", dependencies=[Depends(get_current_active_user)])
async def legacy_recipe_formulation(request: Any, req: Request):
    res = await color_service.recipe_formulation(request, req.app.state.icap)
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/train", dependencies=[Depends(get_current_active_user)])
async def legacy_train(request: Any, req: Request):
    res = await training_service.start_training(request, req.app.state)
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.get("/train_status", dependencies=[Depends(get_current_active_user)])
async def legacy_train_status(req: Request):
    res = training_service.get_status(req.app.state)
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/clear_database", dependencies=[Depends(get_current_active_user)])
async def clear_database(req: Request):
    await req.app.state.icap.rag.reset_collection()
    state_file = "AuditTrail/indexer_state.json"
    if os.path.exists(state_file):
        os.remove(state_file)
    return JSONResponse(content={"message": "Базата данни и индексерът са изчистени успешно."}, headers=DEPRECATED_HEADERS)

@router.get("/models_list", dependencies=[Depends(get_current_active_user)])
async def get_models_list():
    res = await model_service.get_available_models()
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/switch_model/{name}", dependencies=[Depends(get_current_active_user)])
async def switch_model(name: str):
    try:
        res = await model_service.switch_model(name)
        return JSONResponse(content=res, headers=DEPRECATED_HEADERS)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail}, headers=DEPRECATED_HEADERS)

@router.post("/predict_batch_risk", dependencies=[Depends(get_current_active_user)])
async def predict_batch_risk(process_params: dict, req: Request):
    return JSONResponse(content=req.app.state.icap.ai_analysis.predict_quality_risk(process_params), headers=DEPRECATED_HEADERS)

@router.post("/agent_task", dependencies=[Depends(get_current_active_user)])
async def legacy_agent_task(request: dict, req: Request):
    res = await agent_service.execute_agent_task(request, req.app.state.icap)
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.get("/kg_export", dependencies=[Depends(get_current_active_user)])
async def kg_export():
    if os.path.exists("Docs/knowledge_graph.json"):
        with open("Docs/knowledge_graph.json", "r") as f:
            return JSONResponse(content=json.load(f), headers=DEPRECATED_HEADERS)
    return JSONResponse(content={"nodes": [], "links": []}, headers=DEPRECATED_HEADERS)

@router.get("/kg_reason/{issue}", dependencies=[Depends(get_current_active_user)])
async def kg_reason(issue: str):
    from knowledge_graph import IndustrialKG
    kg = IndustrialKG()
    return JSONResponse(content={"reasoning": kg.find_reasoning_path(issue)}, headers=DEPRECATED_HEADERS)

@router.post("/hsi_analyze", dependencies=[Depends(get_current_active_user)])
async def hsi_analyze(data: dict):
    try:
        res = await color_service.hsi_analyze(data)
        return JSONResponse(content=res, headers=DEPRECATED_HEADERS)
    except Exception as e:
        return JSONResponse(status_code=403, content={"message": str(e)}, headers=DEPRECATED_HEADERS)

@router.get("/kpi_data", dependencies=[Depends(get_current_active_user)])
async def legacy_kpi_data():
    res = await iot_business_service.get_kpi_data()
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.get("/fleet_status", dependencies=[Depends(get_current_active_user)])
async def legacy_fleet_status():
    res = await iot_business_service.get_fleet_status()
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/generate_iso_audit_report", dependencies=[Depends(get_current_active_user)])
async def generate_iso_audit_report():
    from services.report_service import generate_iso_audit_report as svc_iso
    filename = svc_iso()
    return JSONResponse(content={"filename": filename}, headers=DEPRECATED_HEADERS)

@router.post("/generate_html_report", dependencies=[Depends(get_current_active_user)])
async def generate_html_report(request: Any, req: Request):
    from services.report_service import generate_html_report as svc_gen
    icap = req.app.state.icap
    de = icap.color_engine.calculate_delta_e(request.lab_sample, request.lab_standard, request.method)
    status = "Успех" if de <= request.tolerance else "Неуспех"
    status_color = "#47ff9c" if status == "Успех" else "#ff4766"

    filename = svc_gen(request.dict(), de, status, status_color, icap.color_engine)
    return JSONResponse(content={"filename": filename}, headers=DEPRECATED_HEADERS)

@router.post("/diagnose", dependencies=[Depends(get_current_active_user)])
async def legacy_diagnose(request: Any, req: Request):
    res = await rag_service.query_rag(request, req.app.state.icap, req.app.state.manager)
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.get("/download_report/{filename}", dependencies=[Depends(get_current_active_user)])
async def download_report(filename: str):
    base_dir = os.path.realpath("AuditTrail")
    file_path = os.path.realpath(os.path.join(base_dir, filename))

    if not file_path.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Достъпът е забранен")

    if os.path.exists(file_path):
        return FileResponse(file_path, headers=DEPRECATED_HEADERS)
    raise HTTPException(status_code=404, detail="Отчетът не е намерен")

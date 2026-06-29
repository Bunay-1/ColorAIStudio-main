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
from routers import vision, rag, color, training, agents, iot, models
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
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients")
        rows = cursor.fetchall()
        res = {row["id"]: dict(row) for row in rows}
    except Exception as e:
        logger.error(f"Грешка в базата данни: {e}")
        raise HTTPException(status_code=500, detail="Грешка в базата данни")
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/clients", dependencies=[Depends(get_current_active_user)])
async def add_client(data: ClientCreateRequest, conn=Depends(get_db)):
    try:
        cursor = conn.cursor()
        client_id = data.name.upper().replace(" ", "_")
        cursor.execute("INSERT OR REPLACE INTO clients (id, name, tolerance, preferred_method) VALUES (?, ?, ?, ?)",
                       (client_id, data.name, data.tolerance, data.preferred_method))
        conn.commit()
        res = {"message": "Клиентът е добавен/обновен успешно", "id": client_id}
    except Exception as e:
        logger.error(f"Грешка в базата данни: {e}")
        raise HTTPException(status_code=500, detail="Грешка в базата данни")
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.get("/model_registry", dependencies=[Depends(get_current_active_user)])
async def get_model_registry():
    registry_path = "model_registry.json"
    res = []
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                res = json.load(f)
        except Exception as e:
            logger.error(f"Грешка при четене на моделния регистър: {e}")
            raise HTTPException(status_code=500, detail="Вътрешна грешка при четене на данни")
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/vision_analyze", dependencies=[Depends(get_current_active_user)])
async def legacy_vision_analyze(req: Request, file: UploadFile = File(...)):
    return await wrap_legacy_response(vision.vision_analyze(req, file))

@router.post("/vision_micro_analyze", dependencies=[Depends(get_current_active_user)])
async def legacy_vision_micro_analyze(req: Request, file: UploadFile = File(...)):
    return await wrap_legacy_response(vision.vision_micro_analyze(req, file))

@router.get("/rag_stats", dependencies=[Depends(get_current_active_user)])
async def legacy_rag_stats(req: Request):
    return await wrap_legacy_response(rag.get_rag_stats(req))

@router.post("/index_document", dependencies=[Depends(get_current_active_user)])
async def legacy_index_document(request: Any, background_tasks: BackgroundTasks, req: Request):
    # We use Any for request because DocumentIndexRequest might be harder to import here or might cause circular imports
    # if not handled carefully. But let's try to use the models if possible.
    from utils.models import DocumentIndexRequest
    res = await rag.index_document(request, background_tasks, req)
    stats = await req.app.state.icap.rag.get_stats()
    await req.app.state.manager.broadcast({
        "type": "rag_update",
        "message": f"Започна индексиране на {request.file_path}",
        "stats": stats
    })
    return await wrap_legacy_response(asyncio.sleep(0, result=res))

@router.post("/analyze_color", dependencies=[Depends(get_current_active_user)])
async def legacy_analyze_color(request: Any, req: Request):
    from utils.models import ColorAnalysisRequest
    return await wrap_legacy_response(color.analyze_color(request, req))

@router.post("/predict_trend", dependencies=[Depends(get_current_active_user)])
async def legacy_predict_trend(request: Any, req: Request):
    from utils.models import TrendRequest
    return await wrap_legacy_response(color.predict_trend(request, req))

@router.post("/recipe_formulation", dependencies=[Depends(get_current_active_user)])
async def legacy_recipe_formulation(request: Any, req: Request):
    from utils.models import ColorAnalysisRequest
    return await wrap_legacy_response(color.recipe_formulation(request, req))

@router.post("/train", dependencies=[Depends(get_current_active_user)])
async def legacy_train(request: Any, req: Request):
    from utils.models import TrainRequest
    return await wrap_legacy_response(training.train_model(request, req))

@router.get("/train_status", dependencies=[Depends(get_current_active_user)])
async def legacy_train_status(req: Request):
    return await wrap_legacy_response(asyncio.sleep(0, result=training.get_train_status(req)))

@router.post("/clear_database", dependencies=[Depends(get_current_active_user)])
async def clear_database(req: Request):
    res = await rag.clear_database(req)
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.get("/models_list", dependencies=[Depends(get_current_active_user)])
async def get_models_list():
    res = {
        "models": [
            {"id": "irm-industrial-v8.9", "name": "IRM Industrial v8.9", "type": "Vision"},
            {"id": "irm-base-v1", "name": "IRM Base v1", "type": "Color"}
        ],
        "note": "Симулирани данни за демо цели"
    }
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/switch_model/{name}", dependencies=[Depends(get_current_active_user)])
async def switch_model(name: str):
    try:
        res = await models.switch_model(name)
        return JSONResponse(content=res, headers=DEPRECATED_HEADERS)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail}, headers=DEPRECATED_HEADERS)

from routers import analytics

@router.post("/predict_batch_risk", dependencies=[Depends(get_current_active_user)])
async def predict_batch_risk(process_params: dict, req: Request):
    res = await analytics.predict_batch_risk(process_params, req)
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/agent_task", dependencies=[Depends(get_current_active_user)])
async def legacy_agent_task(request: dict, req: Request):
    return await wrap_legacy_response(agents.execute_agent_task(request, req))

from routers import knowledge_graph

@router.get("/kg_export", dependencies=[Depends(get_current_active_user)])
async def kg_export():
    res = await knowledge_graph.kg_export()
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.get("/kg_reason/{issue}", dependencies=[Depends(get_current_active_user)])
async def kg_reason(issue: str):
    res = await knowledge_graph.kg_reason(issue)
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/hsi_analyze", dependencies=[Depends(get_current_active_user)])
async def hsi_analyze(data: dict):
    try:
        res = await color.hsi_analyze(data)
        return JSONResponse(content=res, headers=DEPRECATED_HEADERS)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail}, headers=DEPRECATED_HEADERS)

@router.get("/kpi_data", dependencies=[Depends(get_current_active_user)])
async def legacy_kpi_data():
    return await wrap_legacy_response(iot.get_kpi_data())

@router.get("/fleet_status", dependencies=[Depends(get_current_active_user)])
async def legacy_fleet_status():
    return await wrap_legacy_response(iot.api_get_fleet_status())

from routers import reports

@router.post("/generate_iso_audit_report", dependencies=[Depends(get_current_active_user)])
async def generate_iso_audit_report():
    res = await reports.generate_iso_audit_report()
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/generate_html_report", dependencies=[Depends(get_current_active_user)])
async def generate_html_report(request: Any, req: Request):
    res = await reports.generate_html_report(request, req)
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

@router.post("/diagnose", dependencies=[Depends(get_current_active_user)])
async def legacy_diagnose(request: Any, req: Request):
    from utils.models import ReasoningRequest
    return await wrap_legacy_response(rag.diagnose(request, req))

@router.get("/download_report/{filename}", dependencies=[Depends(get_current_active_user)])
async def download_report(filename: str):
    res = await reports.download_report(filename)
    # FileResponse requires special handling if wrapped, but here we can just return it or re-wrap headers
    if isinstance(res, FileResponse):
        for k, v in DEPRECATED_HEADERS.items():
            res.headers[k] = v
        return res
    return JSONResponse(content=res, headers=DEPRECATED_HEADERS)

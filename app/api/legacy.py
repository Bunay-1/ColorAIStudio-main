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
from routers import vision, rag, color, training, agents, iot
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
    await req.app.state.icap.rag.reset_collection()
    state_file = "AuditTrail/indexer_state.json"
    if os.path.exists(state_file):
        os.remove(state_file)
    return JSONResponse(content={"message": "Базата данни и индексерът са изчистени успешно."}, headers=DEPRECATED_HEADERS)

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
    # [DEMO]
    if os.environ.get("ICAP_ENVIRONMENT") == "production":
         return JSONResponse(status_code=403, content={"message": "Този ендпойнт е деактивиран в production среда."})
    return JSONResponse(content={"status": "success", "message": f"Моделът е сменен на {name}"}, headers=DEPRECATED_HEADERS)

@router.post("/predict_batch_risk", dependencies=[Depends(get_current_active_user)])
async def predict_batch_risk(process_params: dict, req: Request):
    return JSONResponse(content=req.app.state.icap.ai_analysis.predict_quality_risk(process_params), headers=DEPRECATED_HEADERS)

@router.post("/agent_task", dependencies=[Depends(get_current_active_user)])
async def legacy_agent_task(request: dict, req: Request):
    return await wrap_legacy_response(agents.execute_agent_task(request, req))

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
    # [DEMO]
    if os.environ.get("ICAP_ENVIRONMENT") == "production":
         return JSONResponse(status_code=403, content={"message": "Този ендпойнт е деактивиран в production среда."})
    return JSONResponse(
        content={
            "wavelengths": list(range(400, 1001, 20)),
            "intensities": [random.random() for _ in range(31)],
            "material_identified": "Polymer Composite X1",
            "confidence": 0.94,
            "subsurface_defect": False,
            "note": "Симулирани данни за демо"
        },
        headers=DEPRECATED_HEADERS
    )

@router.get("/kpi_data", dependencies=[Depends(get_current_active_user)])
async def legacy_kpi_data():
    return await wrap_legacy_response(iot.get_kpi_data())

@router.get("/fleet_status", dependencies=[Depends(get_current_active_user)])
async def legacy_fleet_status():
    return await wrap_legacy_response(iot.api_get_fleet_status())

@router.post("/generate_iso_audit_report", dependencies=[Depends(get_current_active_user)])
async def generate_iso_audit_report():
    from services.report_service import generate_iso_audit_report
    filename = generate_iso_audit_report()
    return JSONResponse(content={"filename": filename}, headers=DEPRECATED_HEADERS)

@router.post("/generate_html_report", dependencies=[Depends(get_current_active_user)])
async def generate_html_report(request: Any, req: Request):
    from utils.models import ColorAnalysisRequest
    from services.report_service import generate_html_report as svc_gen
    icap = req.app.state.icap
    de = icap.color_engine.calculate_delta_e(request.lab_sample, request.lab_standard, request.method)
    status = "Успех" if de <= request.tolerance else "Неуспех"
    status_color = "#47ff9c" if status == "Успех" else "#ff4766"

    filename = svc_gen(request.dict(), de, status, status_color, icap.color_engine)
    return JSONResponse(content={"filename": filename}, headers=DEPRECATED_HEADERS)

@router.post("/diagnose", dependencies=[Depends(get_current_active_user)])
async def legacy_diagnose(request: Any, req: Request):
    from utils.models import ReasoningRequest
    return await wrap_legacy_response(rag.diagnose(request, req))

@router.get("/download_report/{filename}", dependencies=[Depends(get_current_active_user)])
async def download_report(filename: str):
    base_dir = os.path.realpath("AuditTrail")
    file_path = os.path.realpath(os.path.join(base_dir, filename))

    if not file_path.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Достъпът е забранен")

    if os.path.exists(file_path):
        return FileResponse(file_path, headers=DEPRECATED_HEADERS)
    raise HTTPException(status_code=404, detail="Отчетът не е намерен")

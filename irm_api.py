"""
Industrial Color AI Platform (ICAP) — Main API Entry Point
==========================================================
Version: 8.11.0 Enterprise
Automated Quality Control and Colorimetric Analysis Platform
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, UploadFile, File, BackgroundTasks, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from dotenv import load_dotenv

from utils.correlation_id import CorrelationIDMiddleware
from utils.tracing import setup_tracing, instrument_fastapi
from utils.multi_tenant import TenantMiddleware
from utils.api_versioning import version_middleware
from utils.version import ICAP_VERSION, ICAP_VERSION_DISPLAY
from utils.logging_config import setup_logging
from utils.config_validator import validate_config, check_service_connectivity

import database
from rag_system import IRM_RAG
from color_engine import ColorEngine
from ai_color_analysis import AIColorAnalysis
from vision_engine import VisionEngine
from agents_system import AgentOrchestrator
from alerting_system import alert_system
from utils.models import ColorAnalysisRequest, TrendRequest, DocumentIndexRequest, TrainRequest, ReasoningRequest

# New Modular Structure
from app.core.state import ICAPState
from app.core.ws_manager import ConnectionManager
from app.core.indexer import background_indexer
from app.core.models import ClientCreateRequest
from app.api import health

# Routers
from routers import vision, rag, agents, training, iot, auth, notifications, analytics, webhooks, compliance, mfa, cache, export_import, websocket, graphql
try:
    from routers import color
    COLOR_ROUTER_AVAILABLE = True
except ImportError:
    color = None
    COLOR_ROUTER_AVAILABLE = False

load_dotenv()

# Logger configuration
environment = os.environ.get("ICAP_ENVIRONMENT", "development")
logger = setup_logging(environment)
logger = logging.getLogger("ICAP_API")

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.ready = False
    logger.info(f"🚀 Стартиране на ICAP Engine (v{ICAP_VERSION_DISPLAY})...")
    
    config_results = validate_config()
    if not config_results["valid"]:
        logger.error("❌ Невалидна конфигурация.")
        if os.environ.get("ICAP_ENVIRONMENT", "production") == "production":
            raise RuntimeError("Невалидна конфигурация в production режим")
    
    service_status = check_service_connectivity()
    app.state.service_status = service_status
    
    icap_state = ICAPState()
    icap_state.rag = IRM_RAG(lightweight=(os.environ.get("ICAP_EDGE_MODE") == "1"))
    await icap_state.rag.initialize()
    icap_state.color_engine = ColorEngine()
    icap_state.vision_engine = VisionEngine(triton_url=os.environ.get("TRITON_SERVER_URL"), lightweight=(os.environ.get("ICAP_EDGE_MODE") == "1"))
    icap_state.ai_analysis = AIColorAnalysis()
    icap_state.agent_orchestrator = AgentOrchestrator(icap_state.ai_analysis, icap_state.vision_engine, icap_state.rag)

    app.state.icap = icap_state
    app.state.manager = ConnectionManager()
    app.state.alert_system = alert_system
    
    # Background tasks
    indexer_task = asyncio.create_task(background_indexer(app.state.icap, app.state.manager))
    
    app.state.ready = True
    logger.info("✅ ICAP API стартирането приключи успешно.")

    yield
    
    # Shutdown
    logger.info("🛑 Спиране на ICAP API...")
    app.state.ready = False
    indexer_task.cancel()
    try:
        await indexer_task
    except asyncio.CancelledError:
        pass

    if icap_state.rag:
        await icap_state.rag.close()
    logger.info("✅ Системата е спряна.")

app = FastAPI(
    title="Industrial Color AI Platform (ICAP) API",
    version=ICAP_VERSION,
    lifespan=lifespan
)

# Middleware & Instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ALLOWED_ORIGINS = os.environ.get("ICAP_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Correlation-ID", "X-Tenant-ID"],
)
app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(version_middleware)

setup_tracing(service_name="icap-api")
instrument_fastapi(app)

# --- Routes v1 ---
# Използваме директно инклудване с префикс, за да споделят app state
app.include_router(auth.router, prefix="/v1/auth", tags=["Auth"])
if COLOR_ROUTER_AVAILABLE:
    app.include_router(color.router, prefix="/v1/color", tags=["Color"])
app.include_router(vision.router, prefix="/v1/vision", tags=["Vision"])
app.include_router(rag.router, prefix="/v1/rag", tags=["RAG"])
app.include_router(agents.router, prefix="/v1/agents", tags=["Agents"])
app.include_router(training.router, prefix="/v1/training", tags=["Training"])
app.include_router(iot.router, prefix="/v1/iot", tags=["IoT"])
app.include_router(notifications.router, prefix="/v1/notifications", tags=["Notifications"])
app.include_router(analytics.router, prefix="/v1/analytics", tags=["Analytics"])
app.include_router(webhooks.router, prefix="/v1/webhooks", tags=["Webhooks"])
app.include_router(compliance.router, prefix="/v1/compliance", tags=["Compliance"])
app.include_router(mfa.router, prefix="/v1/mfa", tags=["MFA"])
app.include_router(cache.router, prefix="/v1/cache", tags=["Cache"])
app.include_router(export_import.router, prefix="/v1/export-import", tags=["Export-Import"])

# GraphQL endpoint
from routers.graphql import schema
from strawberry.fastapi import GraphQLRouter
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

app.include_router(health.router) # Здравни проверки на основно ниво

# --- Legacy Endpoints (Deprecated) ---
DEPRECATED_HEADERS = {"Deprecation": "true", "Link": "</v1>; rel=\"successor-version\""}

@app.get("/clients", tags=["Legacy"])
async def get_clients():
    try:
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients")
            rows = cursor.fetchall()
            return JSONResponse(content={row["id"]: dict(row) for row in rows}, headers=DEPRECATED_HEADERS)
    except Exception as e:
        logger.error(f"Грешка в базата данни: {e}")
        raise HTTPException(status_code=500, detail="Грешка в базата данни")

@app.post("/clients", tags=["Legacy"])
async def add_client(data: ClientCreateRequest):
    try:
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO clients (id, name, tolerance, preferred_method) VALUES (?, ?, ?, ?)",
                           (data.name.upper().replace(" ", "_"), data.name, data.tolerance, data.preferred_method))
            conn.commit()
            return JSONResponse(content={"message": "Клиентът е добавен/обновен успешно"}, headers=DEPRECATED_HEADERS)
    except Exception as e:
        logger.error(f"Грешка в базата данни: {e}")
        raise HTTPException(status_code=500, detail="Грешка в базата данни")

@app.get("/model_registry", tags=["Legacy"])
async def get_model_registry():
    if os.path.exists("model_registry.json"):
        with open("model_registry.json", "r") as f:
            return JSONResponse(content=json.load(f), headers=DEPRECATED_HEADERS)
    return JSONResponse(content=[], headers=DEPRECATED_HEADERS)

@app.post("/vision_analyze", tags=["Legacy"])
async def legacy_vision_analyze(req: Request, file: UploadFile = File(...)):
    return await vision.vision_analyze(req, file)

@app.post("/vision_micro_analyze", tags=["Legacy"])
async def legacy_vision_micro_analyze(req: Request, file: UploadFile = File(...)):
    return await vision.vision_micro_analyze(req, file)

@app.get("/rag_stats", tags=["Legacy"])
async def legacy_rag_stats(req: Request):
    return await rag.get_rag_stats(req)

@app.post("/index_document", tags=["Legacy"])
async def legacy_index_document(request: DocumentIndexRequest, background_tasks: BackgroundTasks, req: Request):
    res = await rag.index_document(request, background_tasks, req)
    stats = await app.state.icap.rag.get_stats()
    await app.state.manager.broadcast({
        "type": "rag_update",
        "message": f"Започна индексиране на {request.file_path}",
        "stats": stats
    })
    return res

@app.post("/analyze_color", tags=["Legacy"])
async def legacy_analyze_color(request: ColorAnalysisRequest, req: Request):
    return await color.analyze_color(request, req)

@app.post("/predict_trend", tags=["Legacy"])
async def legacy_predict_trend(request: TrendRequest, req: Request):
    return await color.predict_trend(request, req)

@app.post("/recipe_formulation", tags=["Legacy"])
async def legacy_recipe_formulation(request: ColorAnalysisRequest, req: Request):
    return await color.recipe_formulation(request, req)

@app.post("/train", tags=["Legacy"])
async def legacy_train(request: TrainRequest, req: Request):
    return await training.train_model(request, req)

@app.get("/train_status", tags=["Legacy"])
async def legacy_train_status(req: Request):
    return training.get_train_status(req)

@app.post("/clear_database", tags=["Legacy"])
async def clear_database():
    await app.state.icap.rag.reset_collection()
    state_file = "AuditTrail/indexer_state.json"
    if os.path.exists(state_file):
        os.remove(state_file)
    return {"message": "Базата данни и индексерът са изчистени успешно."}

@app.get("/models_list", tags=["Legacy"])
async def get_models_list():
    # ДЕМО ЕНДПОЙНТ
    return JSONResponse(
        content={"models": [{"name": "irm-industrial-v8.9"}, {"name": "irm-base-v1"}], "note": "Симулирани данни за демо"},
        headers=DEPRECATED_HEADERS
    )

@app.post("/switch_model/{name}", tags=["Legacy"])
async def switch_model(name: str):
    return {"status": "success", "message": f"Моделът е сменен на {name}"}

@app.post("/predict_batch_risk", tags=["Legacy"])
async def predict_batch_risk(process_params: dict):
    return app.state.icap.ai_analysis.predict_quality_risk(process_params)

@app.post("/agent_task", tags=["Legacy"])
async def legacy_agent_task(request: dict, req: Request):
    return await agents.execute_agent_task(request, req)

@app.get("/kg_export", tags=["Legacy"])
async def kg_export():
    if os.path.exists("Docs/knowledge_graph.json"):
        with open("Docs/knowledge_graph.json", "r") as f:
            return json.load(f)
    return {"nodes": [], "links": []}

@app.get("/kg_reason/{issue}", tags=["Legacy"])
async def kg_reason(issue: str):
    from knowledge_graph import IndustrialKG
    kg = IndustrialKG()
    return {"reasoning": kg.find_reasoning_path(issue)}

@app.post("/hsi_analyze", tags=["Legacy"])
async def hsi_analyze(data: dict):
    # ДЕМО ЕНДПОЙНТ
    import random
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

@app.get("/kpi_data", tags=["Legacy"])
async def legacy_kpi_data():
    return await iot.get_kpi_data()

@app.get("/fleet_status", tags=["Legacy"])
async def legacy_fleet_status():
    return await iot.api_get_fleet_status()

@app.post("/generate_iso_audit_report", tags=["Legacy"])
async def generate_iso_audit_report():
    from services.report_service import generate_iso_audit_report
    filename = generate_iso_audit_report()
    return {"filename": filename}

@app.post("/generate_html_report", tags=["Legacy"])
async def generate_html_report(request: ColorAnalysisRequest, req: Request):
    from services.report_service import generate_html_report as svc_gen
    icap = req.app.state.icap
    de = icap.color_engine.calculate_delta_e(request.lab_sample, request.lab_standard, request.method)
    status = "Успех" if de <= request.tolerance else "Неуспех"
    status_color = "#47ff9c" if status == "Успех" else "#ff4766"

    filename = svc_gen(request.dict(), de, status, status_color, icap.color_engine)
    return {"filename": filename}

@app.post("/diagnose", tags=["Legacy"])
async def legacy_diagnose(request: ReasoningRequest, req: Request):
    return await rag.diagnose(request, req)

@app.get("/download_report/{filename}", tags=["Legacy"])
async def download_report(filename: str):
    from fastapi.responses import FileResponse
    base_dir = os.path.realpath("AuditTrail")
    file_path = os.path.realpath(os.path.join(base_dir, filename))
    
    if not file_path.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Достъпът е забранен")

    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Отчетът не е намерен")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await app.state.manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping": await websocket.send_text("pong")
    except WebSocketDisconnect:
        app.state.manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

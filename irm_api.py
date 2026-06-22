"""
Industrial Color AI Platform (ICAP) — Main API Entry Point
==========================================================
Version: 8.9.5 Enterprise
Automated Quality Control and Colorimetric Analysis Platform
"""

import os
import time
import json
import logging
import asyncio
import threading
import sqlite3
import uvicorn
from typing import List, Dict, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, UploadFile, File, BackgroundTasks
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

# Shared modules
import database
from rag_system import IRM_RAG
from color_engine import ColorEngine
from ai_color_analysis import AIColorAnalysis
from vision_engine import VisionEngine
from agents_system import AgentOrchestrator
from alerting_system import alert_system
from utils.ws_manager import WebSocketHandler
from utils.models import ColorAnalysisRequest, TrendRequest, DocumentIndexRequest, TrainRequest, ReasoningRequest
from utils.config_validator import validate_config, check_service_connectivity
from utils.logging_config import setup_logging

# Routers
try:
    from routers import color, vision, rag, agents, training, iot, auth, notifications, analytics, webhooks, compliance, mfa, cache, export_import
    COLOR_ROUTER_AVAILABLE = True
except ImportError:
    from routers import vision, rag, agents, training, iot, auth, notifications, analytics, webhooks, compliance, mfa, cache, export_import
    color = None
    COLOR_ROUTER_AVAILABLE = False

# Load configuration
load_dotenv()

# Logger configuration - Structured logging
environment = os.environ.get("ICAP_ENVIRONMENT", "development")
logger = setup_logging(environment)
logger = logging.getLogger("ICAP_API")
ws_handler = WebSocketHandler()
logger.addHandler(ws_handler)

# Edge / Offline Optimization
EDGE_MODE = os.environ.get("ICAP_EDGE_MODE", "1") == "1"
LIGHTWEIGHT_MODE = os.environ.get("ICAP_LIGHTWEIGHT", "0") == "1" or EDGE_MODE
TRITON_URL = os.environ.get("TRITON_SERVER_URL")

# --- Audit & Database Core ---
database.init_enterprise_db()

def log_to_audit_trail(data: Dict[str, Any]) -> None:
    """Log measurement to audit trail with parameterized queries to prevent SQL injection."""
    try:
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO measurements (timestamp, batch_id, operator_id, machine_id, client_id, delta_e, status, method, illuminant)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('timestamp'), data.get('batch_id'), data.get('operator_id'),
                data.get('machine_id'), data.get('client_id'), data.get('delta_e'),
                data.get('status'), data.get('method'), data.get('illuminant')
            ))
            conn.commit()
    except (sqlite3.IntegrityError, sqlite3.OperationalError) as e:
        logger.error(f"SQL Audit Error: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error in audit trail: {e}", exc_info=True)

# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all connected clients with error handling."""
        disconnected: List[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"WS Broadcast error: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# --- Application State ---
class ICAPState:
    def __init__(self) -> None:
        self.rag: Optional[IRM_RAG] = None
        self.color_engine: Optional[ColorEngine] = None
        self.vision_engine: Optional[VisionEngine] = None
        self.ai_analysis: Optional[AIColorAnalysis] = None
        self.agent_orchestrator: Optional[AgentOrchestrator] = None

icap_state = ICAPState()

app = FastAPI(
    title="Industrial Color AI Platform (ICAP) API",
    description="""
    Enterprise API for Automated Quality Control and Colorimetric Analysis.
    
    ## Features
    - **Color Analysis**: Delta E calculations, trend prediction, recipe formulation
    - **Vision AI**: Defect detection, micro-defect analysis, multi-view fusion
    - **RAG System**: Document indexing, semantic search, knowledge retrieval
    - **Multi-Agent System**: Quality control, root cause analysis, predictive maintenance
    - **IoT Integration**: MQTT and OPC-UA connectors for real-time sensor data
    
    ## Authentication
    API uses correlation IDs for request tracing. Configure authentication via environment variables.
    
    ## Rate Limiting
    - Default: 100 requests per minute per IP
    - Configurable via ICAP_RATE_LIMIT environment variable
    """,
    version="8.9.3",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "ICAP Support",
        "email": "support@icap-enterprise.com",
    },
    license_info={
        "name": "Enterprise License",
        "url": "https://example.com/license/",
    },
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "Color",
            "description": "Color analysis, Delta E calculations, and recipe formulation"
        },
        {
            "name": "Vision",
            "description": "Vision AI operations for defect detection and analysis"
        },
        {
            "name": "RAG",
            "description": "Retrieval-Augmented Generation for document search and knowledge retrieval"
        },
        {
            "name": "Agents",
            "description": "Multi-agent system for complex reasoning and automation"
        },
        {
            "name": "IoT",
            "description": "IoT connector management and sensor data operations"
        },
        {
            "name": "Training",
            "description": "Model training and fine-tuning operations"
        },
        {
            "name": "Auth",
            "description": "Authentication and authorization endpoints"
        }
    ]
)

# Prometheus Metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - Improved security with default restrictions
DEFAULT_ORIGINS = ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000"]
ALLOWED_ORIGINS = os.environ.get("ICAP_ALLOWED_ORIGINS", ",".join(DEFAULT_ORIGINS)).split(",")
# Remove empty strings and strip whitespace
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]

# Warn if using wildcard in production
if "*" in ALLOWED_ORIGINS and os.environ.get("ICAP_ENVIRONMENT", "development") == "production":
    logger.warning("⚠️  SECURITY WARNING: CORS wildcard (*) is enabled in production mode!")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add correlation ID middleware for request tracing
app.add_middleware(CorrelationIDMiddleware)

# Add tenant middleware for multi-tenancy support
app.add_middleware(TenantMiddleware)

# Add API versioning middleware
app.add_middleware(version_middleware)

# Setup OpenTelemetry distributed tracing
setup_tracing(service_name="icap-api")
instrument_fastapi(app)

# --- Background Tasks ---
async def background_indexer():
    state_file = "AuditTrail/indexer_state.json"
    indexed_files = set()

    base_dir = "./RAG"
    os.makedirs(base_dir, exist_ok=True)

    while True:
        try:
            # Sync with actual DB state if DB was wiped but state file remains
            stats = await icap_state.rag.get_stats()
            if stats.get("total_chunks") == 0 and os.path.exists(state_file):
                logger.info("RAG Database is empty but state file exists. Resetting state file for re-indexing.")
                indexed_files = set()
                if os.path.exists(state_file): os.remove(state_file)
            elif not indexed_files and os.path.exists(state_file):
                try:
                    with open(state_file, "r") as f:
                        loaded = json.load(f)
                        # Normalize paths: ensure consistency (no leading ./)
                        indexed_files = {os.path.normpath(p) for p in loaded}
                except: pass

            found_any_new = False
            for root, _, files in os.walk(base_dir):
                for file in files:
                    # Normalize both current and stored paths for comparison
                    full_path = os.path.join(root, file)
                    rel_path = os.path.normpath(os.path.relpath(full_path, start="."))

                    if rel_path not in indexed_files and file.lower().endswith(('.pdf', '.docx', '.xlsx', '.csv', '.json', '.md')):
                        logger.info(f"Background Indexer: Processing NEW file: {rel_path}")
                        async def progress_cb(data):
                            await manager.broadcast(data)

                        await icap_state.rag.index_any(full_path, progress_callback=progress_cb)
                        indexed_files.add(rel_path)
                        found_any_new = True
                        with open(state_file, "w") as f: json.dump(list(indexed_files), f)

                        # Update stats and broadcast
                        current_stats = await icap_state.rag.get_stats()
                        await manager.broadcast({
                            "type": "rag_update",
                            "last_file": file,
                            "stats": current_stats
                        })

            # Periodically broadcast stats even if no new files
            if not found_any_new:
                await manager.broadcast({"type": "rag_update", "stats": stats})

        except Exception as e:
            logger.error(f"Indexer error: {e}")
        await asyncio.sleep(60)

# --- Lifecycle ---
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting ICAP Engine (v8.9.1)...")
    
    # Validate configuration at startup
    logger.info("🔍 Validating configuration...")
    config_results = validate_config()
    if not config_results["valid"]:
        logger.error("❌ Configuration validation failed. Please fix the errors before starting.")
        # Don't raise exception to allow development mode, but log clearly
        if os.environ.get("ICAP_ENVIRONMENT", "development") == "production":
            raise RuntimeError("Invalid configuration in production mode")
    
    # Check service connectivity
    logger.info("🔍 Checking service connectivity...")
    service_status = check_service_connectivity()
    
    icap_state.rag = IRM_RAG(lightweight=LIGHTWEIGHT_MODE)
    await icap_state.rag.initialize()
    icap_state.color_engine = ColorEngine()
    icap_state.vision_engine = VisionEngine(triton_url=TRITON_URL, lightweight=LIGHTWEIGHT_MODE)
    icap_state.ai_analysis = AIColorAnalysis()
    icap_state.agent_orchestrator = AgentOrchestrator(icap_state.ai_analysis, icap_state.vision_engine, icap_state.rag)

    # Inject into app state
    app.state.icap = icap_state
    app.state.manager = manager
    app.state.alert_system = alert_system
    app.state.log_to_audit_trail = log_to_audit_trail
    app.state.EDGE_MODE = EDGE_MODE
    app.state.service_status = service_status

    asyncio.create_task(background_indexer())
    logger.info("✅ ICAP API is ready.")

# --- Routes ---
app.include_router(auth.router)
if COLOR_ROUTER_AVAILABLE:
    app.include_router(color.router)
else:
    logger.warning("Color router not available - colour-science dependency missing")
app.include_router(vision.router)
app.include_router(rag.router)
app.include_router(agents.router)
app.include_router(training.router)
app.include_router(iot.router)
app.include_router(notifications.router)
app.include_router(analytics.router)
app.include_router(webhooks.router)
app.include_router(compliance.router)
app.include_router(mfa.router)
app.include_router(cache.router)
app.include_router(export_import.router)

# --- Legacy & Global Endpoints ---
@app.get("/clients")
async def get_clients():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients")
    rows = cursor.fetchall()
    conn.close()
    return {row["id"]: dict(row) for row in rows}

@app.post("/clients")
async def add_client(data: dict):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO clients (id, name, tolerance, preferred_method) VALUES (?, ?, ?, ?)",
                   (data["name"].upper().replace(" ", "_"), data["name"], data["tolerance"], data["preferred_method"]))
    conn.commit()
    conn.close()
    return {"message": "Client added/updated"}

@app.get("/model_registry")
async def get_model_registry():
    if os.path.exists("model_registry.json"):
        with open("model_registry.json", "r") as f:
            return json.load(f)
    return []

@app.post("/vision_analyze")
async def legacy_vision_analyze(req: Request, file: UploadFile = File(...)):
    from routers.vision import vision_analyze
    return await vision_analyze(req, file)

@app.post("/vision_micro_analyze")
async def legacy_vision_micro_analyze(req: Request, file: UploadFile = File(...)):
    from routers.vision import vision_micro_analyze
    return await vision_micro_analyze(req, file)

@app.get("/rag_stats")
async def legacy_rag_stats(req: Request):
    from routers.rag import get_rag_stats
    return await get_rag_stats(req)

@app.post("/index_document")
async def legacy_index_document(request: DocumentIndexRequest, background_tasks: BackgroundTasks, req: Request):
    from routers.rag import index_document
    res = await index_document(request, background_tasks, req)

    # Broadcast an immediate update that indexing has started
    stats = await icap_state.rag.get_stats()
    await manager.broadcast({
        "type": "rag_update",
        "message": f"Започна индексиране на {request.file_path}",
        "stats": stats
    })
    return res

@app.post("/analyze_color")
async def legacy_analyze_color(request: ColorAnalysisRequest, req: Request):
    from routers.color import analyze_color
    return await analyze_color(request, req)

@app.post("/predict_trend")
async def legacy_predict_trend(request: TrendRequest, req: Request):
    from routers.color import predict_trend
    return await predict_trend(request, req)

@app.post("/recipe_formulation")
async def legacy_recipe_formulation(request: ColorAnalysisRequest, req: Request):
    from routers.color import recipe_formulation
    return await recipe_formulation(request, req)

@app.post("/train")
async def legacy_train(request: TrainRequest, req: Request):
    from routers.training import train_model
    return await train_model(request, req)

@app.get("/train_status")
async def legacy_train_status(req: Request):
    from routers.training import get_train_status
    return get_train_status(req)

@app.post("/clear_database")
async def clear_database():
    await icap_state.rag.reset_collection()
    # Reset indexer state file
    state_file = "AuditTrail/indexer_state.json"
    if os.path.exists(state_file):
        os.remove(state_file)
    return {"message": "Базата данни и индексерът са изчистени успешно."}

@app.get("/models_list")
async def get_models_list():
    # Симулиран списък с налични модели за демото
    return {"models": [{"name": "irm-industrial-v8.9"}, {"name": "irm-base-v1"}]}

@app.post("/switch_model/{name}")
async def switch_model(name: str):
    return {"status": "success", "message": f"Моделът е сменен на {name}"}

@app.post("/predict_batch_risk")
async def predict_batch_risk(process_params: dict):
    return icap_state.ai_analysis.predict_quality_risk(process_params)

@app.post("/agent_task")
async def legacy_agent_task(request: dict, req: Request):
    from routers.agents import execute_agent_task
    return await execute_agent_task(request, req)

@app.get("/kg_export")
async def kg_export():
    if os.path.exists("Docs/knowledge_graph.json"):
        with open("Docs/knowledge_graph.json", "r") as f:
            return json.load(f)
    return {"nodes": [], "links": []}

@app.get("/kg_reason/{issue}")
async def kg_reason(issue: str):
    from knowledge_graph import IndustrialKG
    kg = IndustrialKG()
    return {"reasoning": kg.find_reasoning_path(issue)}

@app.post("/hsi_analyze")
async def hsi_analyze(data: dict):
    import random
    # Симулиран HSI анализ за демото
    return {
        "wavelengths": list(range(400, 1001, 20)),
        "intensities": [random.random() for _ in range(31)],
        "material_identified": "Polymer Composite X1",
        "confidence": 0.94,
        "subsurface_defect": False
    }

@app.get("/kpi_data")
async def legacy_kpi_data():
    from routers.iot import get_kpi_data
    return await get_kpi_data()

@app.get("/fleet_status")
async def legacy_fleet_status():
    from routers.iot import api_get_fleet_status
    return await api_get_fleet_status()

@app.post("/generate_iso_audit_report")
async def generate_iso_audit_report():
    from services.report_service import generate_iso_audit_report
    filename = generate_iso_audit_report()
    return {"filename": filename}

@app.post("/generate_html_report")
async def generate_html_report(request: ColorAnalysisRequest, req: Request):
    from services.report_service import generate_html_report as svc_gen
    icap = req.app.state.icap
    de = icap.color_engine.calculate_delta_e(request.lab_sample, request.lab_standard, request.method)
    status = "Pass" if de <= request.tolerance else "Fail"
    status_color = "#47ff9c" if status == "Pass" else "#ff4766"

    filename = svc_gen(request.dict(), de, status, status_color, icap.color_engine)
    return {"filename": filename}

@app.post("/diagnose")
async def legacy_diagnose(request: ReasoningRequest, req: Request):
    from routers.rag import diagnose
    return await diagnose(request, req)

@app.get("/download_report/{filename}")
async def download_report(filename: str):
    from fastapi.responses import FileResponse
    path = f"AuditTrail/{filename}"
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Report not found")

@app.get("/health", tags=["Health"])
async def health():
    """
    Comprehensive health check endpoint.
    Checks status of all services and system resources.
    """
    import psutil
    import asyncio
    from datetime import datetime
    
    health_status = {
        "status": "healthy",
        "version": "8.9.3",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
        "resources": {}
    }
    
    # System resources
    try:
        health_status["resources"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "disk_free_gb": psutil.disk_usage('/').free / (1024**3)
        }
    except Exception as e:
        health_status["resources"] = {"error": str(e)}
    
    # Database health
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        health_status["services"]["database"] = "connected"
    except Exception as e:
        health_status["services"]["database"] = f"disconnected: {str(e)}"
        health_status["status"] = "degraded"
    
    # Qdrant health
    try:
        import httpx
        qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{qdrant_url}/health")
            if response.status_code == 200:
                health_status["services"]["qdrant"] = "connected"
            else:
                health_status["services"]["qdrant"] = f"error: status {response.status_code}"
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["qdrant"] = f"disconnected: {str(e)}"
        health_status["status"] = "degraded"
    
    # Ollama health
    try:
        import httpx
        ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ollama_url}/api/tags")
            if response.status_code == 200:
                health_status["services"]["ollama"] = "connected"
            else:
                health_status["services"]["ollama"] = f"error: status {response.status_code}"
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["ollama"] = f"disconnected: {str(e)}"
        health_status["status"] = "degraded"
    
    # RAG system health
    try:
        if icap_state.rag and icap_state.rag.enabled:
            stats = await icap_state.rag.get_stats()
            health_status["services"]["rag"] = {
                "status": "enabled",
                "total_chunks": stats.get("total_chunks", 0),
                "total_files": stats.get("total_files", 0)
            }
        else:
            health_status["services"]["rag"] = "disabled"
    except Exception as e:
        health_status["services"]["rag"] = f"error: {str(e)}"
    
    # Vision engine health
    try:
        if icap_state.vision_engine and icap_state.vision_engine.enabled:
            health_status["services"]["vision_engine"] = "enabled"
        else:
            health_status["services"]["vision_engine"] = "disabled"
    except Exception as e:
        health_status["services"]["vision_engine"] = f"error: {str(e)}"
    
    # Color engine health
    try:
        if icap_state.color_engine:
            health_status["services"]["color_engine"] = "enabled"
        else:
            health_status["services"]["color_engine"] = "disabled"
    except Exception as e:
        health_status["services"]["color_engine"] = f"error: {str(e)}"
    
    return health_status

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping": await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
Industrial Color AI Platform (ICAP) — Main API Entry Point
==========================================================
Version: 8.11.1 Enterprise
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
from app.core.audit import log_to_audit_trail
from app.api import health, legacy

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

    # Initialize Database
    database.init_enterprise_db()
    
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
    app.state.log_to_audit_trail = log_to_audit_trail

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

# Global Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Непредвидена грешка: {exc}", exc_info=True)
    if os.environ.get("ICAP_ENVIRONMENT") == "production":
        return JSONResponse(
            status_code=500,
            content={"detail": "Възникна вътрешна системна грешка. Моля, свържете се с администратор."}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

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

app.include_router(health.router)
app.include_router(legacy.router)

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

import os
import logging
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
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
from utils.version import ICAP_VERSION
from utils.logging_config import setup_logging

from app.core.lifecycle import lifespan
from app.api import health, legacy

# Routers
from routers import vision, rag, agents, training, iot, auth, notifications, analytics, webhooks, compliance, mfa, cache, export_import, websocket, graphql, clients, models
try:
    from routers import color
    COLOR_ROUTER_AVAILABLE = True
except ImportError:
    color = None
    COLOR_ROUTER_AVAILABLE = False

load_dotenv()

# Logger configuration
environment = os.environ.get("ICAP_ENVIRONMENT", "development")
setup_logging(environment)
logger = logging.getLogger("ICAP_API")

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
if environment == "production" and "*" in ALLOWED_ORIGINS:
    logger.error("❌ КРИТИЧНА ГРЕШКА В СИГУРНОСТТА: Използване на wildcard '*' за CORS в production!")
    raise RuntimeError("Wildcard CORS не е разрешен в production среда за по-добра сигурност.")

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
app.include_router(clients.router, prefix="/v1/clients", tags=["Clients"])
app.include_router(models.router, prefix="/v1/models", tags=["Models"])
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

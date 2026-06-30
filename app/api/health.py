from fastapi import APIRouter, Request
from utils.version import ICAP_VERSION_DISPLAY

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check(req: Request):
    """Стандартен health check ендпойнт."""
    service_status = getattr(req.app.state, "service_status", {})
    return {
        "status": "healthy",
        "version": ICAP_VERSION_DISPLAY,
        "services": service_status
    }

@router.get("/livez")
async def liveness_check():
    """Проверка за активност (liveness probe)."""
    return {"status": "alive"}

from fastapi.responses import JSONResponse

@router.get("/readyz")
async def readiness_check(req: Request):
    """Проверка за готовност (readiness probe)."""
    is_ready = getattr(req.app.state, "ready", False)
    if is_ready:
        return {"status": "ready"}
    return JSONResponse(status_code=503, content={"status": "starting"})

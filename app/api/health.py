import os
import psutil
import httpx
from datetime import datetime
from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
import database
from utils.version import ICAP_VERSION_DISPLAY
from utils.retry import retry_async
from utils.circuit_breaker import ollama_breaker, qdrant_breaker, CircuitBreakerOpenError

router = APIRouter()

@router.get("/livez")
async def liveness():
    from utils.metrics import circuit_breaker_state, circuit_breaker_failures, circuit_breaker_last_failure_time

    # Update circuit breaker metrics
    circuit_state_map = {"closed": 0, "half_open": 1, "open": 2}
    circuit_breaker_state.labels(service="ollama").set(circuit_state_map.get(ollama_breaker.get_state_name(), 0))
    circuit_breaker_state.labels(service="qdrant").set(circuit_state_map.get(qdrant_breaker.get_state_name(), 0))

    circuit_breaker_failures.labels(service="ollama").set(ollama_breaker.failures)
    circuit_breaker_failures.labels(service="qdrant").set(qdrant_breaker.failures)

    if ollama_breaker.last_failure_time:
        circuit_breaker_last_failure_time.labels(service="ollama").set(ollama_breaker.last_failure_time)
    if qdrant_breaker.last_failure_time:
        circuit_breaker_last_failure_time.labels(service="qdrant").set(qdrant_breaker.last_failure_time)

    return {
        "status": "alive",
        "version": ICAP_VERSION_DISPLAY,
        "timestamp": datetime.utcnow().isoformat(),
        "startup_complete": True, # Should be dynamic if needed
        "circuit_breakers": {
            "ollama": ollama_breaker.get_state_name(),
            "qdrant": qdrant_breaker.get_state_name()
        }
    }

@router.get("/health")
async def health(request: Request):
    """
    Comprehensive health check endpoint.
    Checks status of all services and system resources.
    """
    icap_state = request.app.state.icap

    health_status = {
        "status": "healthy",
        "version": ICAP_VERSION_DISPLAY,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
        "resources": {}
    }

    # System resources
    try:
        health_status["resources"] = {
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "disk_free_gb": round(psutil.disk_usage('/').free / (1024**3), 2)
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
        qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")

        async def _check_qdrant():
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{qdrant_url.rstrip('/')}/health")
                response.raise_for_status()
                return response

        await qdrant_breaker.call_async(
            lambda: retry_async(
                _check_qdrant,
                retries=2,
                initial_delay=0.5,
                max_delay=2.0,
                backoff=2.0,
                retry_exceptions=(httpx.RequestError, httpx.HTTPStatusError),
            )
        )
        health_status["services"]["qdrant"] = f"connected ({qdrant_breaker.get_state_name()})"
    except CircuitBreakerOpenError as e:
        health_status["services"]["qdrant"] = f"open: {str(e)}"
        health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["qdrant"] = f"disconnected: {str(e)}"
        health_status["status"] = "degraded"

    # Ollama health
    try:
        ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")

        async def _check_ollama():
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{ollama_url.rstrip('/')}/api/tags")
                response.raise_for_status()
                return response

        await ollama_breaker.call_async(
            lambda: retry_async(
                _check_ollama,
                retries=2,
                initial_delay=0.5,
                max_delay=2.0,
                backoff=2.0,
                retry_exceptions=(httpx.RequestError, httpx.HTTPStatusError),
            )
        )
        health_status["services"]["ollama"] = f"connected ({ollama_breaker.get_state_name()})"
    except CircuitBreakerOpenError as e:
        health_status["services"]["ollama"] = f"open: {str(e)}"
        health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["ollama"] = f"disconnected: {str(e)}"
        health_status["status"] = "degraded"

    # RAG system health
    try:
        if icap_state.rag and getattr(icap_state.rag, "enabled", True):
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
        health_status["status"] = "degraded"

    return health_status

@router.get("/readyz")
async def readiness(request: Request):
    import httpx
    from utils.retry import retry_async

    readiness_status = {
        "status": "ready",
        "version": ICAP_VERSION_DISPLAY,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    if not getattr(request.app.state, "ready", False):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not ready",
                "version": ICAP_VERSION_DISPLAY,
                "timestamp": datetime.utcnow().isoformat(),
                "services": {"startup": "still in progress"}
            }
        )

    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        readiness_status["services"]["database"] = "connected"
    except Exception as e:
        readiness_status["services"]["database"] = f"disconnected: {str(e)}"
        readiness_status["status"] = "not ready"
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=readiness_status)

    return readiness_status

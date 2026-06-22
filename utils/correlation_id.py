"""
Correlation ID Middleware
==========================
Middleware for adding correlation IDs to all requests for better tracing and debugging.
"""

import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("CorrelationID")

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to all requests."""
    
    async def dispatch(self, request: Request, call_next):
        # Check if correlation ID exists in headers
        correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID")
        
        # Generate new correlation ID if not present
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Add to request state for use in endpoints
        request.state.correlation_id = correlation_id
        
        # Add to response headers
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        
        # Log with correlation ID
        logger.info(f"Request: {request.method} {request.url.path} - Correlation ID: {correlation_id}")
        
        return response

def get_correlation_id(request: Request) -> str:
    """Helper function to get correlation ID from request."""
    correlation_id = getattr(request.state, "correlation_id", None)
    if not correlation_id:
        correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    return correlation_id

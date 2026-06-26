"""
CSRF Protection Middleware for ICAP Platform v8.10.0
===================================================
Cross-Site Request Forgery protection for state-changing operations
"""

import secrets
import logging
from typing import Optional, Callable
from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ICAP_CSRF")


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware for FastAPI"""
    
    def __init__(
        self,
        app: ASGIApp,
        csrf_cookie_name: str = "csrf_token",
        csrf_header_name: str = "X-CSRF-Token",
        secure: bool = True,
        httponly: bool = False,
        samesite: str = "strict"
    ):
        super().__init__(app)
        self.csrf_cookie_name = csrf_cookie_name
        self.csrf_header_name = csrf_header_name
        self.secure = secure
        self.httponly = httponly
        self.samesite = samesite
        
        # Get exempted paths from environment
        exempted_paths_str = os.environ.get("CSRF_EXEMPT_PATHS", "")
        self.exempted_paths = set(path.strip() for path in exempted_paths_str.split(",") if path.strip())
        
        # Default exempted paths
        self.exempted_paths.update({
            "/health",
            "/livez",
            "/readyz",
            "/metrics",
            "/auth/login",
            "/auth/refresh",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        })
        
        logger.info(f"CSRF middleware initialized with {len(self.exempted_paths)} exempted paths")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and apply CSRF protection"""
        
        # Skip CSRF for safe methods (GET, HEAD, OPTIONS, TRACE)
        if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            return await call_next(request)
        
        # Skip CSRF for exempted paths
        if any(request.url.path.startswith(path) for path in self.exempted_paths):
            return await call_next(request)
        
        # Check CSRF token for state-changing methods
        if request.method in {"POST", "PUT", "DELETE", "PATCH"}:
            csrf_token = request.headers.get(self.csrf_header_name)
            cookie_token = request.cookies.get(self.csrf_cookie_name)
            
            if not csrf_token:
                logger.warning(f"CSRF token missing in header for {request.method} {request.url.path}")
                raise HTTPException(
                    status_code=403,
                    detail="CSRF token missing. Include X-CSRF-Token header."
                )
            
            if not cookie_token:
                logger.warning(f"CSRF token missing in cookie for {request.method} {request.url.path}")
                raise HTTPException(
                    status_code=403,
                    detail="CSRF token missing in cookie. Request a new CSRF token."
                )
            
            # Validate CSRF token
            if not secrets.compare_digest(csrf_token, cookie_token):
                logger.warning(f"CSRF token mismatch for {request.method} {request.url.path}")
                raise HTTPException(
                    status_code=403,
                    detail="CSRF token validation failed."
                )
        
        response = await call_next(request)
        return response
    
    def generate_csrf_token(self) -> str:
        """Generate a new CSRF token"""
        return secrets.token_urlsafe(32)
    
    def set_csrf_cookie(self, response: Response, token: str) -> None:
        """Set CSRF token in response cookie"""
        response.set_cookie(
            key=self.csrf_cookie_name,
            value=token,
            secure=self.secure,
            httponly=self.httponly,
            samesite=self.samesite,
            max_age=3600  # 1 hour
        )


# Global CSRF middleware instance
csrf_middleware = CSRFMiddleware


def get_csrf_exempt_paths() -> set:
    """Get current CSRF exempted paths"""
    return csrf_middleware(None).exempted_paths if csrf_middleware else set()


def add_csrf_exempt_path(path: str) -> None:
    """Add a path to CSRF exemption list"""
    if csrf_middleware:
        csrf_middleware(None).exempted_paths.add(path)
        logger.info(f"Added {path} to CSRF exempted paths")

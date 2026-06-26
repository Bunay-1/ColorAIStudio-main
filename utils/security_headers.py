"""
Security Headers Middleware for ICAP Platform v8.10.0
=====================================================
HTTP security headers for enhanced protection
"""

import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ICAP_SecurityHeaders")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware for FastAPI"""
    
    def __init__(
        self,
        app: ASGIApp,
        csp: str = None,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True
    ):
        super().__init__(app)
        
        # Content Security Policy
        self.csp = csp or os.environ.get(
            "CSP_POLICY",
            "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
            "font-src 'self' data:; connect-src 'self' wss://localhost:8000; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self';"
        )
        
        # HSTS settings
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        
        logger.info("Security headers middleware initialized")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        response = await call_next(request)
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp
        
        # Strict-Transport-Security (HSTS)
        hsts_value = f"max-age={self.hsts_max_age}"
        if self.hsts_include_subdomains:
            hsts_value += "; includeSubDomains"
        if self.hsts_preload:
            hsts_value += "; preload"
        response.headers["Strict-Transport-Security"] = hsts_value
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        # Cross-Origin-Opener-Policy
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        
        # Cross-Origin-Resource-Policy
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # Cache-Control for sensitive endpoints
        if request.url.path in {"/auth/login", "/auth/users", "/auth/tenants"}:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response


# Global security headers middleware instance
security_headers_middleware = SecurityHeadersMiddleware


def get_security_headers() -> dict:
    """Get current security headers configuration"""
    middleware = SecurityHeadersMiddleware(None)
    return {
        "csp": middleware.csp,
        "hsts_max_age": middleware.hsts_max_age,
        "hsts_include_subdomains": middleware.hsts_include_subdomains,
        "hsts_preload": middleware.hsts_preload
    }

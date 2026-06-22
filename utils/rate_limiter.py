"""
Advanced Rate Limiting for ICAP
===============================
Per-user and per-tenant rate limiting with configurable limits.
"""

import time
import logging
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from fastapi import HTTPException, Request, status
from slowapi.util import get_remote_address
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger("RateLimiter")

# Default rate limits (requests per minute)
DEFAULT_LIMITS = {
    "global": 100,  # Global limit
    "per_user": 50,  # Per user limit
    "per_tenant": 200,  # Per tenant limit
    "auth": 10,  # Authentication endpoints
    "heavy": 20,  # Heavy operations (vision, training)
    "light": 100  # Light operations (queries, reads)
}

# Role-based limits (multiplier of default)
ROLE_MULTIPLIERS = {
    "ADMIN": 2.0,  # Admins get 2x limit
    "SUPERVISOR": 1.5,
    "OPERATOR": 1.0,
    "QUALITY_CONTROL": 1.0,
    "MAINTENANCE": 1.0,
    "VIEWER": 0.5  # Viewers get 0.5x limit
}

class RateLimiter:
    """Advanced rate limiter with per-user and per-tenant tracking."""
    
    def __init__(self):
        # Track requests: key -> deque of timestamps
        self.request_history = defaultdict(deque)
        
        # Lock for thread safety
        self._lock = None
        import threading
        self._lock = threading.Lock()
    
    def _get_key(self, identifier: str, limit_type: str) -> str:
        """Generate a unique key for rate limiting."""
        return f"{limit_type}:{identifier}"
    
    def _clean_old_requests(self, key: str, window_seconds: int = 60):
        """Remove requests older than the time window."""
        now = time.time()
        cutoff = now - window_seconds
        
        while self.request_history[key] and self.request_history[key][0] < cutoff:
            self.request_history[key].popleft()
    
    def check_rate_limit(
        self,
        identifier: str,
        limit_type: str = "global",
        limit: Optional[int] = None,
        window_seconds: int = 60
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request should be rate limited.
        
        Args:
            identifier: Unique identifier (user_id, tenant_id, IP, etc.)
            limit_type: Type of limit (global, per_user, per_tenant, etc.)
            limit: Custom limit (overrides default)
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        with self._lock:
            key = self._get_key(identifier, limit_type)
            
            # Get limit
            if limit is None:
                limit = DEFAULT_LIMITS.get(limit_type, DEFAULT_LIMITS["global"])
            
            # Clean old requests
            self._clean_old_requests(key, window_seconds)
            
            # Check current count
            current_count = len(self.request_history[key])
            
            # Calculate remaining
            remaining = max(0, limit - current_count)
            reset_time = time.time() + window_seconds
            
            # Add current request
            self.request_history[key].append(time.time())
            
            is_allowed = current_count < limit
            
            rate_limit_info = {
                "limit": limit,
                "remaining": remaining - 1 if is_allowed else remaining,
                "reset": int(reset_time),
                "window": window_seconds
            }
            
            return is_allowed, rate_limit_info
    
    def get_user_limit(self, user_role: str, limit_type: str) -> int:
        """
        Get rate limit for a specific user role.
        
        Args:
            user_role: User role
            limit_type: Type of limit
            
        Returns:
            Rate limit for the role
        """
        base_limit = DEFAULT_LIMITS.get(limit_type, DEFAULT_LIMITS["global"])
        multiplier = ROLE_MULTIPLIERS.get(user_role, 1.0)
        return int(base_limit * multiplier)
    
    def reset_user_limits(self, user_id: str):
        """Reset rate limits for a specific user."""
        keys_to_remove = [key for key in self.request_history.keys() if f"per_user:{user_id}" in key]
        for key in keys_to_remove:
            del self.request_history[key]
    
    def reset_tenant_limits(self, tenant_id: str):
        """Reset rate limits for a specific tenant."""
        keys_to_remove = [key for key in self.request_history.keys() if f"per_tenant:{tenant_id}" in key]
        for key in keys_to_remove:
            del self.request_history[key]

# Global rate limiter instance
rate_limiter = RateLimiter()

# SlowAPI limiter for backward compatibility
slowapi_limiter = Limiter(key_func=get_remote_address)

def check_rate_limit_dependency(
    limit_type: str = "global",
    limit: Optional[int] = None,
    window_seconds: int = 60
):
    """
    FastAPI dependency for rate limiting.
    
    Args:
        limit_type: Type of rate limit
        limit: Custom limit
        window_seconds: Time window in seconds
    """
    async def rate_limit_dependency(request: Request):
        # Get identifier (IP address for global, user_id for per-user)
        if limit_type == "global":
            identifier = get_remote_address(request)
        else:
            # For per-user/tenant, we need to extract from authenticated user
            # This requires authentication middleware to run first
            identifier = get_remote_address(request)
        
        is_allowed, rate_info = rate_limiter.check_rate_limit(
            identifier=identifier,
            limit_type=limit_type,
            limit=limit,
            window_seconds=window_seconds
        )
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {identifier} ({limit_type})")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": str(rate_info["remaining"]),
                    "X-RateLimit-Reset": str(rate_info["reset"]),
                    "Retry-After": str(window_seconds)
                }
            )
        
        return rate_info
    
    return rate_limit_dependency

def check_user_rate_limit(
    user_id: str,
    user_role: str,
    limit_type: str = "light",
    window_seconds: int = 60
):
    """
    Check rate limit for a specific user.
    
    Args:
        user_id: User ID
        user_role: User role
        limit_type: Type of operation
        window_seconds: Time window in seconds
    """
    limit = rate_limiter.get_user_limit(user_role, limit_type)
    is_allowed, rate_info = rate_limiter.check_rate_limit(
        identifier=user_id,
        limit_type="per_user",
        limit=limit,
        window_seconds=window_seconds
    )
    
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for user {user_id} (role: {user_role})")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {limit_type} operations",
            headers={
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(rate_info["reset"])
            }
        )
    
    return rate_info

def check_tenant_rate_limit(
    tenant_id: str,
    limit_type: str = "light",
    window_seconds: int = 60
):
    """
    Check rate limit for a specific tenant.
    
    Args:
        tenant_id: Tenant ID
        limit_type: Type of operation
        window_seconds: Time window in seconds
    """
    limit = DEFAULT_LIMITS.get("per_tenant", DEFAULT_LIMITS["global"])
    is_allowed, rate_info = rate_limiter.check_rate_limit(
        identifier=tenant_id,
        limit_type="per_tenant",
        limit=limit,
        window_seconds=window_seconds
    )
    
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for tenant {tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Tenant rate limit exceeded for {limit_type} operations",
            headers={
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(rate_info["reset"])
            }
        )
    
    return rate_info

def get_rate_limit_status(identifier: str, limit_type: str = "global") -> Dict[str, int]:
    """
    Get current rate limit status for an identifier.
    
    Args:
        identifier: User ID, tenant ID, or IP address
        limit_type: Type of limit
        
    Returns:
        Rate limit status information
    """
    key = rate_limiter._get_key(identifier, limit_type)
    rate_limiter._clean_old_requests(key)
    
    limit = DEFAULT_LIMITS.get(limit_type, DEFAULT_LIMITS["global"])
    current_count = len(rate_limiter.request_history[key])
    remaining = max(0, limit - current_count)
    
    return {
        "limit": limit,
        "used": current_count,
        "remaining": remaining,
        "reset_time": int(time.time() + 60)
    }

def configure_role_limits(custom_limits: Dict[str, int]):
    """
    Configure custom rate limits for roles.
    
    Args:
        custom_limits: Dictionary of role -> multiplier
    """
    global ROLE_MULTIPLIERS
    ROLE_MULTIPLIERS.update(custom_limits)
    logger.info(f"Updated role rate limits: {custom_limits}")

def configure_operation_limits(custom_limits: Dict[str, int]):
    """
    Configure custom limits for operation types.
    
    Args:
        custom_limits: Dictionary of operation type -> limit
    """
    global DEFAULT_LIMITS
    DEFAULT_LIMITS.update(custom_limits)
    logger.info(f"Updated operation rate limits: {custom_limits}")

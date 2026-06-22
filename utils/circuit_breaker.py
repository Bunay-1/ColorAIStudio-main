"""
Circuit Breaker Pattern for External Services
==============================================
Защита на external services (Ollama, Qdrant, etc.) от cascade failures.
"""

import asyncio
import inspect
import logging
import time
from enum import Enum
from typing import Callable, Any, Optional, Sequence, Type, Union, Tuple

logger = logging.getLogger("CircuitBreaker")

class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is open and calls are blocked."""
    pass

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    def __init__(
        self,
        name: str = "service",
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exceptions: Union[Type[BaseException], Tuple[Type[BaseException], ...]] = Exception,
        half_open_success_threshold: int = 2,
    ):
        """
        Args:
            name: Friendly name for the service protected by the circuit breaker.
            failure_threshold: Number of failures before opening circuit.
            recovery_timeout: Seconds to wait before trying half-open state.
            expected_exceptions: Exception type(s) to track as failures.
            half_open_success_threshold: Number of successful calls required to close from HALF_OPEN.
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        self.half_open_success_threshold = half_open_success_threshold

        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(f"{self.name} circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exceptions as e:
            self._on_failure()
            raise

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async or awaitable function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(f"{self.name} circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            self._on_success()
            return result
        except self.expected_exceptions as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.recovery_timeout

    def _transition_to_half_open(self) -> None:
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        logger.info(f"{self.name} circuit breaker transitioning to HALF_OPEN")

    def _on_success(self):
        """Handle successful call."""
        self.failures = 0
        self.last_failure_time = None
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                logger.info(f"{self.name} circuit breaker CLOSED - service recovered")

    def _on_failure(self):
        """Handle failed call."""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"{self.name} circuit breaker OPEN after {self.failures} failures")

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state

    def get_state_name(self) -> str:
        return self.state.value

    def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time = None
        self.success_count = 0
        logger.info(f"{self.name} circuit breaker manually reset to CLOSED")

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(name={self.name}, state={self.state.value}, "
            f"failures={self.failures}, last_failure_time={self.last_failure_time})"
        )

# Global circuit breaker instances
ollama_breaker = CircuitBreaker(name="Ollama", failure_threshold=3, recovery_timeout=30)
qdrant_breaker = CircuitBreaker(name="Qdrant", failure_threshold=5, recovery_timeout=60)

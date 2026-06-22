import asyncio
import random
import time
from typing import Any, Callable, Optional, Sequence, Type


async def retry_async(
    func: Callable[..., Any],
    *args,
    retries: int = 3,
    initial_delay: float = 0.5,
    max_delay: float = 5.0,
    backoff: float = 2.0,
    jitter: float = 0.1,
    retry_exceptions: Sequence[Type[BaseException]] = (Exception,),
    on_retry: Optional[Callable[[int, BaseException, float], None]] = None,
    **kwargs,
) -> Any:
    """Retry an async callable with exponential backoff.

    Args:
        func: Async callable to execute.
        retries: Total number of attempts.
        initial_delay: Delay before first retry.
        max_delay: Maximum delay between retries.
        backoff: Multiplicative backoff factor.
        jitter: Random jitter to avoid thundering herds.
        retry_exceptions: Exception types that trigger a retry.
        on_retry: Optional callback called before each retry.
        kwargs: Keyword arguments passed to func.
    """
    attempt = 1
    delay = initial_delay
    last_exception = None

    while attempt <= retries:
        try:
            return await func(*args, **kwargs)
        except retry_exceptions as exc:
            last_exception = exc
            if attempt == retries:
                raise
            if on_retry is not None:
                on_retry(attempt, exc, delay)
            sleep_time = delay + random.uniform(0, jitter)
            await asyncio.sleep(sleep_time)
            delay = min(delay * backoff, max_delay)
            attempt += 1

    raise last_exception


def retry(
    func: Callable[..., Any],
    *args,
    retries: int = 3,
    initial_delay: float = 0.5,
    max_delay: float = 5.0,
    backoff: float = 2.0,
    jitter: float = 0.1,
    retry_exceptions: Sequence[Type[BaseException]] = (Exception,),
    on_retry: Optional[Callable[[int, BaseException, float], None]] = None,
    **kwargs,
) -> Any:
    """Retry a synchronous callable with exponential backoff."""
    attempt = 1
    delay = initial_delay
    last_exception = None

    while attempt <= retries:
        try:
            return func(*args, **kwargs)
        except retry_exceptions as exc:
            last_exception = exc
            if attempt == retries:
                raise
            if on_retry is not None:
                on_retry(attempt, exc, delay)
            sleep_time = delay + random.uniform(0, jitter)
            time.sleep(sleep_time)
            delay = min(delay * backoff, max_delay)
            attempt += 1

    raise last_exception

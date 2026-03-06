"""
Retry decorator with exponential back-off for API calls.

Uses tenacity under the hood so callers don't need to implement
retry logic themselves.
"""

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def with_retry(
    max_attempts: int = 4,
    min_wait_seconds: float = 2.0,
    max_wait_seconds: float = 30.0,
    reraise: bool = True,
) -> Callable[[F], F]:
    """Decorator: retry on network errors with exponential back-off.

    Args:
        max_attempts: Total number of attempts before giving up.
        min_wait_seconds: Minimum seconds to wait between retries.
        max_wait_seconds: Maximum seconds to wait between retries.
        reraise: Re-raise the final exception after all retries exhaust.

    Returns:
        Decorated callable with retry logic applied.
    """
    import httpx

    return retry(  # type: ignore[return-value]
        reraise=reraise,
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait_seconds, max=max_wait_seconds),
        retry=retry_if_exception_type((httpx.HTTPError, TimeoutError)),
        before_sleep=lambda retry_state: logger.warning(
            "Retry attempt %d/%d after error: %s",
            retry_state.attempt_number,
            max_attempts,
            retry_state.outcome.exception() if retry_state.outcome else "unknown",
        ),
    )

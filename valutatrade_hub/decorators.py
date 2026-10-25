"""Decorators for ValutaTrade Hub."""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar

from valutatrade_hub.logging_config import get_logger

F = TypeVar("F", bound=Callable[..., Any])


def log_action(action_name: str | None = None) -> Callable[[F], F]:
    """Логирует вызов: имя, аргументы, время. Исключения не глотает."""

    def decorator(func: F) -> F:
        name = action_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger()
            started = time.perf_counter()
            logger.info("START %s args=%s kwargs=%s", name, args, kwargs)
            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                elapsed = time.perf_counter() - started
                logger.error(
                    "FAIL %s after %.4fs: %s: %s",
                    name,
                    elapsed,
                    type(exc).__name__,
                    exc,
                )
                raise
            elapsed = time.perf_counter() - started
            logger.info("OK %s in %.4fs", name, elapsed)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator
"""Debug helpers."""
from __future__ import annotations

import functools
import inspect
import logging
from typing import Any
from typing import Callable

logger = logging.getLogger(__name__)


def log_function_name(function: Callable[..., Any]) -> Callable[..., Any]:
    """Allow to log the function name before each call.

    This is a decorator function.
    """

    @functools.wraps(function)
    def log_and_call_function(*args: Any, **kwargs: Any) -> Any:
        stack_level = len(
            [x for x in inspect.stack() if x[3] != "log_and_call_function"]
        )
        logger.debug(f"{'  ' * stack_level}-> {function.__qualname__}")
        value = function(*args, **kwargs)
        logger.debug(f"{'  ' * stack_level}<- {function.__qualname__}")
        return value

    return log_and_call_function

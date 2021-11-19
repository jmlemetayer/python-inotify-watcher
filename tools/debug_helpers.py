"""Debug helpers."""
import functools
import logging

logger = logging.getLogger(__name__)


def log_function_name(function):
    """Allow to log the function name before each call.

    This is a decorator function.
    """

    @functools.wraps(function)
    def log_and_call_function(*args, **kwargs):
        logger.info(function.__qualname__)
        return function(*args, **kwargs)

    return log_and_call_function

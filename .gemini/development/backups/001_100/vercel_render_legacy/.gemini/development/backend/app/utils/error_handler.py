import functools
import inspect
import logging
import traceback
from typing import Any, Callable, TypeVar, Union
from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse

logger = logging.getLogger(__name__)

T = TypeVar("T")

def handle_agent_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to wrap functions in a try-except block to ensure the server never crashes.
    Reports errors via logging and ensures they can be displayed as toasts on the frontend.
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"Error in {func.__name__}: {error_msg}\n{stack_trace}")
            
            # Check if we have a request object to handle redirection/JSON response
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get("request")

            if request:
                accept = request.headers.get("accept", "")
                if "application/json" in accept:
                    return JSONResponse(
                        status_code=500,
                        content={"status": "error", "message": f"Agent Error: {error_msg}"}
                    )
                
                referer = request.headers.get("referer", "/")
                sep = "&" if "?" in referer else "?"
                return RedirectResponse(
                    url=f"{referer}{sep}error=Agent+Error:+{error_msg.replace(' ', '+')}",
                    status_code=303
                )
            
            # Fallback for non-request context (e.g. background tasks or services)
            # Re-raise so the caller can decide, or return a standardized error object
            raise e

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"Error in {func.__name__}: {error_msg}\n{stack_trace}")
            raise e

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

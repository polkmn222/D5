from __future__ import annotations

import contextvars
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import event


logger = logging.getLogger("web.perf")

_REQUEST_STATE: contextvars.ContextVar["RequestPerfState | None"] = contextvars.ContextVar(
    "web_request_perf_state",
    default=None,
)


def diagnostics_enabled() -> bool:
    override = os.getenv("WEB_PERF_DIAGNOSTICS", "").strip().lower()
    if override in {"0", "false", "no", "off"}:
        return False
    if override in {"1", "true", "yes", "on"}:
        return True
    return not os.getenv("VERCEL") and not os.getenv("RENDER_SERVICE_NAME")


def slow_query_threshold_ms() -> float:
    raw = os.getenv("WEB_PERF_SLOW_QUERY_MS", "").strip()
    if not raw:
        return 150.0
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 150.0


def should_profile_path(path: str) -> bool:
    return not path.startswith(("/ai-agent", "/agent", "/agent-gem", "/static"))


@dataclass
class RequestPerfState:
    method: str
    path: str
    started_at: float
    response_started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status_code: Optional[int] = None
    db_query_count: int = 0
    db_time_ms: float = 0.0


def begin_request(method: str, path: str):
    state = RequestPerfState(method=method, path=path, started_at=time.perf_counter())
    token = _REQUEST_STATE.set(state)
    return state, token


def get_request_state() -> RequestPerfState | None:
    return _REQUEST_STATE.get()


def mark_response_started(status_code: int) -> None:
    state = get_request_state()
    if not state or state.response_started_at is not None:
        return
    state.status_code = status_code
    state.response_started_at = time.perf_counter()


def mark_response_completed(status_code: Optional[int] = None) -> None:
    state = get_request_state()
    if not state:
        return
    if status_code is not None and state.status_code is None:
        state.status_code = status_code
    state.completed_at = time.perf_counter()


def record_query_duration(duration_ms: float) -> None:
    state = get_request_state()
    if not state:
        return
    state.db_query_count += 1
    state.db_time_ms += duration_ms


def build_request_summary(state: RequestPerfState) -> dict[str, float | int | str | None]:
    first_byte_ms = None
    if state.response_started_at is not None:
        first_byte_ms = round((state.response_started_at - state.started_at) * 1000, 2)

    total_ms = None
    if state.completed_at is not None:
        total_ms = round((state.completed_at - state.started_at) * 1000, 2)

    db_ms = round(state.db_time_ms, 2)
    db_share_pct = None
    if total_ms and total_ms > 0:
        db_share_pct = round((db_ms / total_ms) * 100, 1)

    return {
        "method": state.method,
        "path": state.path,
        "status": state.status_code,
        "first_byte_ms": first_byte_ms,
        "total_ms": total_ms,
        "db_queries": state.db_query_count,
        "db_ms": db_ms,
        "db_share_pct": db_share_pct,
    }


def log_request_summary(state: RequestPerfState) -> None:
    summary = build_request_summary(state)
    logger.info(
        "web_perf method=%s path=%s status=%s first_byte_ms=%s total_ms=%s db_queries=%s db_ms=%s db_share_pct=%s",
        summary["method"],
        summary["path"],
        summary["status"],
        summary["first_byte_ms"],
        summary["total_ms"],
        summary["db_queries"],
        summary["db_ms"],
        summary["db_share_pct"],
    )


def attach_sqlalchemy_instrumentation(engine) -> None:
    if getattr(engine, "_web_perf_instrumented", False):
        return

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # noqa: ARG001
        if not diagnostics_enabled():
            return
        conn.info.setdefault("_web_perf_query_start", []).append(time.perf_counter())

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # noqa: ARG001
        if not diagnostics_enabled():
            return
        starts = conn.info.get("_web_perf_query_start")
        if not starts:
            return
        started_at = starts.pop()
        duration_ms = (time.perf_counter() - started_at) * 1000
        record_query_duration(duration_ms)
        if duration_ms >= slow_query_threshold_ms():
            path = get_request_state().path if get_request_state() else "startup"
            sql = " ".join((statement or "").split())
            logger.warning(
                "web_perf_slow_query path=%s duration_ms=%.2f sql=%s",
                path,
                duration_ms,
                sql[:240],
            )

    engine._web_perf_instrumented = True


class RequestTimingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not diagnostics_enabled() or not should_profile_path(path):
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        state, token = begin_request(method, path)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                mark_response_started(int(message.get("status", 200)))
            elif message["type"] == "http.response.body" and not message.get("more_body", False):
                mark_response_completed()
                log_request_summary(state)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            mark_response_completed(status_code=500)
            log_request_summary(state)
            raise
        finally:
            _REQUEST_STATE.reset(token)

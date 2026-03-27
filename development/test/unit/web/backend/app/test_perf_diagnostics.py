from unittest.mock import patch

from web.backend.app.utils import perf_diagnostics


def test_diagnostics_enabled_defaults_on_for_local_runtime():
    with patch.dict("os.environ", {}, clear=True):
        assert perf_diagnostics.diagnostics_enabled() is True


def test_should_profile_path_skips_static_and_agent_mounts():
    assert perf_diagnostics.should_profile_path("/leads") is True
    assert perf_diagnostics.should_profile_path("/static/js/app.js") is False
    assert perf_diagnostics.should_profile_path("/ai-agent/api/chat") is False
    assert perf_diagnostics.should_profile_path("/agent/panel") is False


def test_request_summary_includes_total_and_db_metrics():
    state, token = perf_diagnostics.begin_request("GET", "/contacts")
    try:
        state.started_at = 10.0
        state.response_started_at = 10.12
        state.completed_at = 10.25
        state.status_code = 200
        perf_diagnostics.record_query_duration(20.0)
        perf_diagnostics.record_query_duration(30.0)

        summary = perf_diagnostics.build_request_summary(state)
    finally:
        perf_diagnostics._REQUEST_STATE.reset(token)

    assert summary["method"] == "GET"
    assert summary["path"] == "/contacts"
    assert summary["status"] == 200
    assert summary["first_byte_ms"] == 120.0
    assert summary["total_ms"] == 250.0
    assert summary["db_queries"] == 2
    assert summary["db_ms"] == 50.0
    assert summary["db_share_pct"] == 20.0

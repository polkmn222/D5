#!/bin/bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
APP_ROOT="$PROJECT_ROOT/.gemini/development"
HOST="0.0.0.0"
PORT="${PORT:-8000}"
LOG_FILE="$APP_ROOT/crm.log"
SERVER_PID=""

cleanup() {
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

echo "Initializing D4 CRM..."

if [ -d "$PROJECT_ROOT/.pytest_cache" ] && [ ! -d "$APP_ROOT/.pytest_cache" ]; then
    mkdir -p "$APP_ROOT/.pytest_cache"
    cp -R "$PROJECT_ROOT/.pytest_cache/." "$APP_ROOT/.pytest_cache/" 2>/dev/null || true
    rm -rf "$PROJECT_ROOT/.pytest_cache"
fi

PID_LIST="$(lsof -ti:"$PORT" 2>/dev/null | xargs 2>/dev/null || true)"
if [ -n "$PID_LIST" ]; then
    echo "Port $PORT is already in use by process(es) $PID_LIST. Restarting them..."
    # shellcheck disable=SC2086
    kill -9 $PID_LIST 2>/dev/null || true
    sleep 1
fi

mkdir -p "$APP_ROOT"

cd "$PROJECT_ROOT"
export PYTHONPATH="$APP_ROOT${PYTHONPATH:+:$PYTHONPATH}"

uvicorn api.index:app --host "$HOST" --port "$PORT" > "$LOG_FILE" 2>&1 &
SERVER_PID="$!"

echo "Waiting for server startup..."
for _ in 1 2 3 4 5 6 7 8 9 10; do
    if curl -s "http://127.0.0.1:$PORT/docs" > /dev/null; then
        break
    fi
    sleep 1
done

echo "D4 CRM is live at http://127.0.0.1:$PORT"
if command -v open >/dev/null 2>&1; then
    open "http://127.0.0.1:$PORT"
fi

wait "$SERVER_PID"

#!/usr/bin/env bash
# start.sh — starts LiveKit, backend, and agent in the background.
# Run the frontend separately: cd frontend && npm run dev

set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── 1. LiveKit ────────────────────────────────────────────────────────────────
echo "[1/3] Starting LiveKit..."
docker compose -f "$REPO_ROOT/docker-compose.yml" up -d
echo "      LiveKit ready on ws://localhost:7880"

# ── 2. Backend ────────────────────────────────────────────────────────────────
echo "[2/3] Starting backend..."
cd "$REPO_ROOT/backend"
[ -f .env ] || cp .env.example .env
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "      Backend PID $BACKEND_PID on http://localhost:8000"

# ── 3. Agent ─────────────────────────────────────────────────────────────────
echo "[3/3] Starting agent..."
cd "$REPO_ROOT/agent"
[ -f .env ] || cp .env.example .env
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
.venv/bin/python run_agent.py &
AGENT_PID=$!
echo "      Agent PID $AGENT_PID"

echo ""
echo "All services running. Start the frontend with:"
echo "  cd frontend && npm run dev"
echo ""
echo "To stop: kill $BACKEND_PID $AGENT_PID && docker compose down"

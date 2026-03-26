#!/usr/bin/env bash
# start.sh — starts LiveKit, backend, agent, and frontend.

set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── 1. LiveKit ────────────────────────────────────────────────────────────────
echo "[1/4] Starting LiveKit..."
docker compose -f "$REPO_ROOT/docker-compose.yml" up -d
echo "      LiveKit ready on ws://localhost:7880"

# ── 2. Backend ────────────────────────────────────────────────────────────────
echo "[2/4] Starting backend..."
cd "$REPO_ROOT/backend"
[ -f .env ] || cp .env.example .env
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "      Backend PID $BACKEND_PID on http://localhost:8000"

# ── 3. Agent ─────────────────────────────────────────────────────────────────
echo "[3/4] Starting agent..."
cd "$REPO_ROOT/agent"
[ -f .env ] || cp .env.example .env
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
.venv/bin/python run_agent.py &
AGENT_PID=$!
echo "      Agent PID $AGENT_PID"

# ── 4. Frontend ───────────────────────────────────────────────────────────────
echo "[4/4] Starting frontend..."
cd "$REPO_ROOT/frontend"
[ -f .env ] || cp .env.example .env
npm install --silent
npm run dev &
FRONTEND_PID=$!
echo "      Frontend PID $FRONTEND_PID on http://localhost:5173"

echo ""
echo "All services running. Open http://localhost:5173"
echo ""
echo "To stop: kill $BACKEND_PID $AGENT_PID $FRONTEND_PID && docker compose down"

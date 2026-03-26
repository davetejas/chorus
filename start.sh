#!/usr/bin/env bash
# start.sh — builds and starts all services via Docker Compose.

set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "Starting Chorus (OnboardAI)..."
docker compose -f "$REPO_ROOT/docker-compose.yml" up --build -d

echo ""
echo "All services running."
echo "  Frontend:  http://localhost:5173"
echo "  LiveKit:   ws://localhost:7880"
echo ""
echo "To stop: docker compose down"

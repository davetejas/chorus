import base64
import json
import os

import pytest
from fastapi.testclient import TestClient

# Set env vars before importing the app so load_dotenv doesn't override them
os.environ.setdefault("LIVEKIT_API_KEY", "devkey")
os.environ.setdefault("LIVEKIT_API_SECRET", "devsecret")
os.environ.setdefault("LIVEKIT_URL", "ws://localhost:7880")

from app.main import app  # noqa: E402

client = TestClient(app)


def decode_jwt_payload(token: str) -> dict:
    payload_b64 = token.split(".")[1]
    # Re-pad for standard base64
    padding = 4 - len(payload_b64) % 4
    payload_b64 += "=" * (padding % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))


class TestHealth:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"ok": True}


class TestCreateToken:
    def test_returns_200(self):
        response = client.post("/api/token", json={"room": "demo", "name": "alice"})
        assert response.status_code == 200

    def test_response_contains_required_fields(self):
        response = client.post("/api/token", json={"room": "demo", "name": "alice"})
        body = response.json()
        assert "url" in body
        assert "room" in body
        assert "identity" in body
        assert "token" in body

    def test_token_is_valid_jwt_structure(self):
        response = client.post("/api/token", json={"room": "demo", "name": "alice"})
        token = response.json()["token"]
        parts = token.split(".")
        assert len(parts) == 3
        assert all(len(p) > 0 for p in parts)

    def test_token_payload_has_correct_room_and_grants(self):
        response = client.post("/api/token", json={"room": "demo", "name": "alice"})
        payload = decode_jwt_payload(response.json()["token"])
        assert payload["video"]["roomJoin"] is True
        assert payload["video"]["room"] == "demo"

    def test_response_url_matches_livekit_url(self):
        response = client.post("/api/token", json={"room": "demo", "name": "alice"})
        assert response.json()["url"] == "ws://localhost:7880"

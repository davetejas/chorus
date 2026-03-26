import base64
import json
import os
import sys

import pytest

# Ensure the agent package root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("LIVEKIT_API_KEY", "devkey")
os.environ.setdefault("LIVEKIT_API_SECRET", "devsecret")
os.environ.setdefault("LIVEKIT_URL", "ws://localhost:7880")

from run_agent import make_agent_token, OnboardAI  # noqa: E402


def decode_jwt_payload(token: str) -> dict:
    payload_b64 = token.split(".")[1]
    padding = 4 - len(payload_b64) % 4
    payload_b64 += "=" * (padding % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))


class TestMakeAgentToken:
    def test_returns_non_empty_string(self):
        token = make_agent_token("demo", "onboard-ai", "OnboardAI")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_is_valid_jwt_structure(self):
        token = make_agent_token("demo", "onboard-ai", "OnboardAI")
        parts = token.split(".")
        assert len(parts) == 3
        assert all(len(p) > 0 for p in parts)

    def test_token_payload_has_correct_identity_and_room(self):
        token = make_agent_token("demo", "onboard-ai", "OnboardAI")
        payload = decode_jwt_payload(token)
        assert payload["sub"] == "onboard-ai"
        assert payload["video"]["roomJoin"] is True
        assert payload["video"]["room"] == "demo"
        assert payload["video"]["canPublish"] is True
        assert payload["video"]["canSubscribe"] is True


class TestOnboardAI:
    def test_instantiates_without_error(self):
        agent = OnboardAI()
        assert agent is not None

    def test_instructions_contain_required_onboarding_sections(self):
        agent = OnboardAI()
        instructions = agent.instructions
        assert "OnboardAI" in instructions
        assert "Identity Validation" in instructions
        assert "Access Setup" in instructions

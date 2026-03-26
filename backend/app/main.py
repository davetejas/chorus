import os
import secrets
from datetime import timedelta
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from livekit.api import AccessToken, VideoGrants  # pip install livekit-api


load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app = FastAPI(title="OnboardAI Token Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TokenRequest(BaseModel):
    room: str = Field(min_length=1, max_length=128)
    name: str | None = Field(default=None, max_length=128)
    identity: str | None = Field(default=None, max_length=128)
    kind: Literal["standard", "agent"] = "standard"


class TokenResponse(BaseModel):
    url: str
    room: str
    identity: str
    token: str


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/token", response_model=TokenResponse)
def create_token(req: TokenRequest):
    # Generate an identity if not provided
    identity = req.identity or f"{req.kind}-{secrets.token_urlsafe(8)}"
    name = req.name or identity

    grants = VideoGrants(
        room_join=True,
        room=req.room,
        room_create=True,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,  # required for text streams/data
    )

    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(name)
        .with_kind(req.kind)  # "standard" or "agent"
        .with_grants(grants)
        .with_ttl(timedelta(hours=2))
        .to_jwt()
    )

    return TokenResponse(url=LIVEKIT_URL, room=req.room, identity=identity, token=token)

# Chorus — OnboardAI

An AI-powered video onboarding platform. A user joins a video room and is guided through identity verification, profile creation, and time-limited access setup by an AI agent — fully local, no cloud AI APIs required.

> **Status:** Proof of concept

---

## Overview

Chorus orchestrates two services around a LiveKit real-time video server:

- **Frontend** — React/TypeScript SPA where users join a named room and see a live transcript; generates LiveKit JWTs directly in the browser
- **Agent** — Python process (OnboardAI) that joins the same room and conducts the onboarding session using local STT, LLM, and TTS models

```
User browser
      │  WebRTC (audio/video)
      │  JWT generated in-browser (crypto.subtle)
      ▼
┌──────────────────────────────────────────────────┐
│               LiveKit Server (Docker)            │
└──────────────────────────────────────────────────┘
      ▲  WebRTC (audio/text streams)
      │
┌─────────────┐
│  OnboardAI  │
│   Python    │
│  Whisper STT│
│  Ollama LLM │
│  Piper TTS  │
└─────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React 18, TypeScript, Vite, `@livekit/components-react` |
| Agent | Python, `livekit-agents`, faster-whisper, Piper TTS, Silero VAD |
| Infrastructure | LiveKit server, Docker Compose |

---

## Prerequisites

- **Docker** and Docker Compose
- **Ollama** running locally with a model pulled (e.g. `ollama pull llama3.1`)

No local Python or Node.js installation is required — all services run inside Docker containers.

---

## Quick Start

```bash
./start.sh
```

Or directly:

```bash
docker compose up --build -d
```

Open [http://localhost:5173](http://localhost:5173), enter your name and a room name, and click **Start onboarding**.

To stop all services:

```bash
docker compose down
```

---

## How It Works

1. The user enters their name and a room name in the frontend and clicks **Start onboarding**.
2. The frontend generates a short-lived LiveKit JWT locally using `crypto.subtle` (no backend required).
3. The frontend connects to LiveKit and publishes the user's audio and video.
4. The OnboardAI agent is already running in the same room; it detects the new participant and sends a greeting.
5. The agent pipeline processes each user utterance:
   - **Silero VAD** detects when the user finishes speaking
   - **faster-whisper** transcribes the audio to text (model downloads on first use)
   - **Ollama LLM** generates the agent's response
   - **Piper TTS** converts the response to speech and plays it back (voice downloads on first use)
6. The agent guides the user through three onboarding steps:
   - **Identity verification** — asks the user to face the camera for a photo
   - **Profile creation** — collects name, email, role, and optional portfolio/brand link
   - **Access setup** — explains and confirms time-limited access details
7. Once all information is collected, the agent calls `complete_onboarding` which generates a profile card and sends it to the browser via a LiveKit data channel. The **ProfileViewer** displays it as a full-screen overlay.
8. The **TranscriptPanel** shows the live conversation transcript; the **ChatPanel** allows text messages alongside voice.

---

## Environment Variables

### Agent (`agent/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `LIVEKIT_URL` | `ws://localhost:7880` | LiveKit WebSocket URL (overridden to `ws://livekit:7880` inside Docker) |
| `LIVEKIT_API_KEY` | `devkey` | LiveKit API key |
| `LIVEKIT_API_SECRET` | `devsecret` | LiveKit API secret |
| `ROOM_NAME` | `demo` | Room the agent joins |
| `AGENT_IDENTITY` | `onboard-ai` | Agent participant identity |
| `AGENT_NAME` | `OnboardAI` | Display name |
| `OLLAMA_MODEL` | `llama3.1` | Ollama model to use |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama OpenAI-compatible endpoint (overridden to `host.docker.internal` inside Docker) |
| `WHISPER_MODEL` | `small` | faster-whisper model size (`tiny`/`base`/`small`/`medium`/`large-v3`) |
| `PIPER_MODEL` | `en_US-lessac-medium` | Piper voice name or path to `.onnx` file |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_LIVEKIT_URL` | `ws://localhost:7880` | LiveKit WebSocket URL used by the browser |
| `VITE_LIVEKIT_API_KEY` | `devkey` | LiveKit API key (baked into the frontend build) |
| `VITE_LIVEKIT_API_SECRET` | `devsecret` | LiveKit API secret (baked into the frontend build) |

---

## Project Structure

```
chorus/
├── frontend/                   # React/TypeScript SPA
│   ├── Dockerfile
│   └── src/
│       ├── App.tsx             # App state and routing
│       ├── Join.tsx            # Room join form
│       ├── OnboardRoom.tsx     # Video room layout (video, transcript, chat)
│       ├── TranscriptPanel.tsx # Live conversation transcript
│       ├── ChatPanel.tsx       # Text chat alongside voice
│       ├── ProfileViewer.tsx   # Full-screen profile card overlay (via data channel)
│       └── api.ts              # In-browser JWT generator (crypto.subtle)
├── backend/                    # FastAPI token service (not used in POC)
├── agent/                      # LiveKit AI agent (OnboardAI)
│   ├── Dockerfile
│   ├── run_agent.py            # Agent entry point and onboarding logic
│   ├── stt_faster_whisper.py   # faster-whisper STT plugin
│   └── tts_piper.py            # Piper TTS plugin (Python API, auto-downloads voice)
├── docker-compose.yml          # LiveKit, agent, and frontend
├── livekit.yaml                # LiveKit server configuration
└── start.sh                    # Convenience wrapper for docker compose up --build
```

---

## Troubleshooting

**Agent is silent / not responding**
- Check `docker compose logs agent`. On first run the Whisper and Piper models download automatically — this takes a minute or two before speech processing is active.
- If you see `WARNING: Cannot reach Ollama`, Ollama is not running on the host. Start it with `ollama serve` and ensure the model is pulled: `ollama pull llama3.1`.
- If you see `WARNING: Ollama model 'llama3.1' not found`, run `ollama pull llama3.1`.

**Agent joins but user hears nothing**
- Confirm your browser has microphone permission and audio is not muted.
- Click **Click to enable audio** if the LiveKit prompt appears.

**Frontend can't connect to LiveKit**
- Confirm the LiveKit container is healthy: `docker compose ps`.
- Ports 7880–7882 must be free on the host.

**Room name mismatch**
- The agent joins the room specified by `ROOM_NAME` in `agent/.env` (default: `demo`). The frontend pre-fills the same value. If you change the room name in the UI, update `ROOM_NAME` in `agent/.env` and restart the agent container.

---

## License

See [LICENSE](LICENSE).

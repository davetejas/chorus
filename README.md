# Chorus

An AI-powered video interview platform. A human candidate joins a video room and is interviewed in real-time by an AI agent — fully local, no cloud AI APIs required.

> **Status:** Proof of concept

---

## Overview

Chorus orchestrates three services around a LiveKit real-time video server:

- **Frontend** — React/TypeScript SPA where candidates join a named room and see a live transcript
- **Backend** — Minimal FastAPI service that issues LiveKit access tokens
- **Agent** — Python process that joins the same room and conducts the interview using local STT, LLM, and TTS models

```
Candidate browser
      │  WebRTC (audio/video)
      ▼
┌─────────────┐   token request   ┌──────────────┐
│  Frontend   │ ────────────────► │   Backend    │
│  React/TS   │                   │   FastAPI    │
└─────────────┘                   └──────────────┘
      │  WebRTC                         │ LiveKit SDK
      ▼                                 ▼
┌──────────────────────────────────────────────────┐
│               LiveKit Server (Docker)            │
└──────────────────────────────────────────────────┘
      ▲  WebRTC (audio/text streams)
      │
┌─────────────┐
│    Agent    │
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
| Backend | Python, FastAPI, `livekit-api` |
| Agent | Python, `livekit-agents`, faster-whisper, Piper TTS, Silero VAD |
| Infrastructure | LiveKit server, Docker Compose |

---

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
- **Docker** and Docker Compose
- **Ollama** running locally with a model pulled (e.g. `llama3.1`)
- **Piper TTS** CLI installed and on `$PATH` — [install instructions](https://github.com/rhasspy/piper)
- A Piper voice model — the default is `en_US-lessac-medium` (`.onnx` + `.onnx.json` files in `agent/`)

---

## Quick Start

### 1. Start LiveKit

```bash
docker-compose up -d
```

LiveKit will be available at `ws://localhost:7880`.

### 2. Start the Backend

```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Start the Agent

```bash
cd agent
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_agent.py
```

### 4. Start the Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173), enter a name and room name, and click **Join**.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `LIVEKIT_URL` | `ws://localhost:7880` | LiveKit WebSocket URL |
| `LIVEKIT_API_KEY` | `devkey` | LiveKit API key |
| `LIVEKIT_API_SECRET` | `devsecret` | LiveKit API secret |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins |

### Agent (`agent/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `LIVEKIT_URL` | `ws://localhost:7880` | LiveKit WebSocket URL |
| `LIVEKIT_API_KEY` | `devkey` | LiveKit API key |
| `LIVEKIT_API_SECRET` | `devsecret` | LiveKit API secret |
| `ROOM_NAME` | `demo` | Room the agent joins |
| `AGENT_IDENTITY` | `ai-interviewer` | Agent participant identity |
| `AGENT_NAME` | `AI Interviewer` | Display name |
| `OLLAMA_MODEL` | `llama3.1` | Ollama model to use |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama OpenAI-compatible endpoint |
| `WHISPER_MODEL` | `small` | faster-whisper model size (`tiny`/`base`/`small`/`medium`/`large-v3`) |
| `PIPER_MODEL` | `en_US-lessac-medium` | Piper voice name or path to `.onnx` file |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE` | `http://localhost:8000` | Backend API base URL |

---

## How It Works

1. The candidate enters their name and a room name in the frontend and clicks **Join**.
2. The frontend calls `POST /api/token` on the backend to get a short-lived LiveKit JWT.
3. The frontend connects to LiveKit and publishes the candidate's audio/video.
4. The agent process (already running) detects the new participant and joins the same room.
5. The agent pipeline runs continuously:
   - **Silero VAD** detects when the candidate finishes speaking
   - **faster-whisper** transcribes the audio to text
   - **Ollama LLM** generates the interviewer's response
   - **Piper TTS** converts the response to speech and plays it back
6. Both sides publish text stream segments; the frontend's **TranscriptPanel** displays them in real-time.

The agent conducts a structured 5-question interview, probes vague answers, and summarizes strengths and concerns at the end.

---

## Project Structure

```
chorus/
├── frontend/           # React/TypeScript SPA
│   └── src/
│       ├── App.tsx             # App state and routing
│       ├── Join.tsx            # Room join form
│       ├── InterviewRoom.tsx   # Video conference view
│       ├── TranscriptPanel.tsx # Live transcript display
│       └── api.ts              # Backend API client
├── backend/            # FastAPI token service
│   └── app/
│       └── main.py             # Token generation endpoint
├── agent/              # LiveKit AI agent
│   ├── run_agent.py            # Agent entry point
│   ├── stt_faster_whisper.py  # Whisper STT wrapper
│   └── tts_piper.py           # Piper TTS wrapper
├── docker-compose.yml  # LiveKit server
└── livekit.yaml        # LiveKit configuration
```

---

## License

See [LICENSE](LICENSE).

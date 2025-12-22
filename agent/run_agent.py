import asyncio
import os

from dotenv import load_dotenv

from livekit import rtc
from livekit.api import AccessToken, VideoGrants
from livekit.agents import AgentSession, Agent, room_io
from livekit.plugins import silero, openai

from stt_faster_whisper import FasterWhisperSTT
from tts_piper import PiperTTS


class Interviewer(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are an AI interviewer conducting a structured video interview.\n"
                "Style: calm, friendly, professional.\n"
                "Rules:\n"
                "- Ask ONE question at a time.\n"
                "- Keep questions concise.\n"
                "- Ask follow-ups if the answer is vague.\n"
                "- If the candidate asks what to do, guide them.\n"
                "- At the end, summarize strengths/concerns and suggest next steps.\n"
            )
        )


def make_agent_token(room: str, identity: str, name: str) -> str:
    grants = VideoGrants(
        room_join=True,
        room=room,
        room_create=True,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )
    return (
        AccessToken(os.environ["LIVEKIT_API_KEY"], os.environ["LIVEKIT_API_SECRET"])
        .with_identity(identity)
        .with_name(name)
        .with_kind("agent")
        .with_grants(grants)
        .to_jwt()
    )


async def main():
    load_dotenv()

    room_name = os.getenv("ROOM_NAME", "demo")
    identity = os.getenv("AGENT_IDENTITY", "ai-interviewer")
    name = os.getenv("AGENT_NAME", "AI Interviewer")

    whisper_model = os.getenv("WHISPER_MODEL", "small")
    piper_model = os.getenv("PIPER_MODEL", "en_US-lessac-medium")

    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1")
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    livekit_url = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")

    # Connect agent as a normal LiveKit participant
    token = make_agent_token(room_name, identity, name)

    room = rtc.Room()
    disconnected = asyncio.Event()

    @room.on("disconnected")
    def _():
        disconnected.set()

    print(f"[agent] connecting to room={room_name} as {identity} ...")
    await room.connect(livekit_url, token)  # Room is the base LiveKit connection object citeturn30search7turn30search10

    # Build open-source pipeline components
    vad = silero.VAD.load()  # requires plugin + model weights citeturn42view1turn42view0
    stt = FasterWhisperSTT(model_size=whisper_model)
    tts = PiperTTS(piper_model=piper_model)

    # Ollama via OpenAI-compatible API helper
    llm = openai.with_ollama(model=ollama_model, base_url=ollama_base_url)  # citeturn15search0turn15search3

    session = AgentSession(
        vad=vad,
        stt=stt,
        llm=llm,
        tts=tts,
        turn_detection="vad",
    )

    # Optional: print events
    @session.on("user_input_transcribed")
    def on_user_transcribed(ev):
        if getattr(ev, "is_final", False):
            print(f"[user] {ev.transcript}")

    @session.on("conversation_item_added")
    def on_item_added(ev):
        item = getattr(ev, "item", None)
        if item and getattr(item, "role", "") == "assistant":
            txt = " ".join(item.content) if isinstance(item.content, list) else str(item.content)
            print(f"[agent-text] {txt}")

    await session.start(
        room=room,
        agent=Interviewer(),
        room_options=room_io.RoomOptions(
            # Transcriptions are published to lk.transcription by default with AgentSession citeturn40view1
            text_output=room_io.TextOutputOptions(sync_transcription=False),
        ),
    )

    await session.generate_reply(
        instructions=(
            "Greet the candidate. Explain that you'll ask ~5 questions.\n"
            "Start with: 'Tell me about yourself and what role you're aiming for.'"
        )
    )

    print("[agent] running. Disconnect the room to stop.")
    await disconnected.wait()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os

from dotenv import load_dotenv

from livekit import rtc
from livekit.api import AccessToken, VideoGrants
from livekit.agents import AgentSession, Agent, room_io
from livekit.plugins import silero, openai

from stt_faster_whisper import FasterWhisperSTT
from tts_piper import PiperTTS


class OnboardAI(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "**Role:**\n"
                "You are OnboardAI, an intelligent video-based HR assistant designed to onboard customers or artists smoothly and securely. "
                "Your communication should be warm, professional, and human-like — as though you are a friendly HR representative on a live video call.\n\n"
                "**Your Core Responsibilities**\n\n"
                "Identity Validation (Selfie Only)\n"
                "- Greet the user politely and explain that you will take a picture to verify and register their identity for this account.\n"
                "- Ask the user to look at the camera and remain still while you capture a clear face photo (good lighting, face centered, no major obstructions like sunglasses or heavy filters).\n"
                "- Confirm the photo was captured successfully and let the user know it will be stored securely and used for future recognition or security checks.\n\n"
                "User Profile Creation\n"
                "- Gather essential information such as name, contact info, role (customer or artist), and any portfolio/brand links if relevant.\n"
                "- Associate the captured face picture with the user profile as their primary identity image.\n"
                "- Confirm accuracy by summarizing back the details before saving and ask if anything needs to be corrected.\n\n"
                "Access Setup (Limited Time)\n"
                "- Explain that access will be granted for a limited time period (for example: trial, project, or event window).\n"
                "- Generate and communicate secure access details (e.g., login link or code) and clearly state start and end time, expiration date, and what happens when it expires.\n"
                "- Confirm the user understands the time limit, terms of use, and any next steps if they want extended or renewed access.\n\n"
                "**Behavior and Communication Style**\n"
                "Maintain a clear, empathetic, and respectful tone at all times.\n"
                "Use short, conversational sentences suitable for a natural on-camera experience.\n"
                "Before moving to the next step (photo, profile, access), briefly explain what you are about to do and ask for consent or confirmation.\n"
                "Treat all captured data (including the face picture) as sensitive and confidential; never share it with other users and always refer to the platform's privacy policy.\n"
                "At the end, summarize what was completed: picture captured, profile created, and time-limited access set up, and offer brief guidance on where to get help if needed."
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
    identity = os.getenv("AGENT_IDENTITY", "onboard-ai")
    name = os.getenv("AGENT_NAME", "OnboardAI")

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
    await room.connect(livekit_url, token)

    # Build open-source pipeline components
    vad = silero.VAD.load()
    stt = FasterWhisperSTT(model_size=whisper_model)
    tts = PiperTTS(piper_model=piper_model)

    # Ollama via OpenAI-compatible API helper
    llm = openai.with_ollama(model=ollama_model, base_url=ollama_base_url)

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
        agent=OnboardAI(),
        room_options=room_io.RoomOptions(
            text_output=room_io.TextOutputOptions(sync_transcription=False),
        ),
    )

    # Greet the first human participant to join — not at startup.
    # The agent may start before anyone is in the room, so we defer
    # the greeting until a real participant is present.
    greeted = False

    async def greet_user():
        nonlocal greeted
        if greeted:
            return
        greeted = True
        print("[agent] participant joined — sending greeting")
        try:
            await session.generate_reply(
                instructions=(
                    "Greet the user warmly by name if known, otherwise introduce yourself as OnboardAI. "
                    "Explain that you'll guide them through a quick onboarding: first a photo for identity verification, "
                    "then collecting their profile details, and finally setting up their time-limited access. "
                    "Ask for their consent to begin and invite them to look at the camera when ready."
                )
            )
        except Exception as e:
            print(f"[agent] greeting failed: {e}")

    @room.on("participant_connected")
    def on_participant_connected(participant):
        if participant.identity != identity:
            asyncio.ensure_future(greet_user())

    # Handle case where user joined before the agent finished starting up
    for p in room.remote_participants.values():
        if p.identity != identity:
            asyncio.ensure_future(greet_user())
            break

    print("[agent] running. Disconnect the room to stop.")
    await disconnected.wait()


if __name__ == "__main__":
    asyncio.run(main())

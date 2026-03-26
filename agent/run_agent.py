import asyncio
import datetime
import os

from dotenv import load_dotenv

from livekit import rtc
from livekit.api import AccessToken, VideoGrants
from livekit.agents import AgentSession, Agent, room_io, function_tool
from livekit.plugins import silero, openai

from stt_faster_whisper import FasterWhisperSTT
from tts_piper import PiperTTS


def _generate_profile_html(name: str, email: str, role: str, portfolio: str = "") -> str:
    ts = datetime.datetime.now().strftime("%B %d, %Y at %H:%M")
    portfolio_html = (
        f'<div class="field"><label>Portfolio / Brand</label>'
        f'<span><a href="{portfolio}" target="_blank">{portfolio}</a></span></div>'
        if portfolio else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Onboarding Profile — {name}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: #0f1117; color: #e0e0e0; min-height: 100vh;
           display: flex; align-items: center; justify-content: center; padding: 24px; }}
    .card {{ background: #1a1d2e; border: 1px solid #2a2d3e; border-radius: 16px;
             padding: 40px; max-width: 480px; width: 100%; }}
    .badge {{ display: inline-block; background: #2563eb; color: #fff; font-size: 12px;
              font-weight: 600; padding: 4px 12px; border-radius: 100px; margin-bottom: 24px;
              letter-spacing: 0.05em; text-transform: uppercase; }}
    h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 4px; }}
    .sub {{ color: #888; margin-bottom: 28px; font-size: 14px; }}
    .field {{ background: #12141f; border-radius: 10px; padding: 14px 18px; margin-bottom: 12px; }}
    .field label {{ display: block; font-size: 11px; text-transform: uppercase;
                    letter-spacing: 0.08em; color: #666; margin-bottom: 4px; }}
    .field span {{ font-size: 15px; }}
    .field a {{ color: #60a5fa; text-decoration: none; }}
    .access {{ background: #0d2137; border: 1px solid #1e4a7a; border-radius: 10px;
               padding: 16px 18px; margin-top: 20px; }}
    .access label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em;
                     color: #4a9eff; margin-bottom: 6px; display: block; }}
    .access span {{ font-size: 13px; color: #93c5fd; }}
    .footer {{ margin-top: 24px; font-size: 12px; color: #555; text-align: center; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">Onboarding Complete</div>
    <h1>{name}</h1>
    <p class="sub">Profile created on {ts}</p>
    <div class="field"><label>Email</label><span>{email}</span></div>
    <div class="field"><label>Role</label><span>{role}</span></div>
    {portfolio_html}
    <div class="access">
      <label>Access Details</label>
      <span>Trial access granted for 30 days. A login link has been sent to {email}.</span>
    </div>
    <p class="footer">Your information is stored securely under our privacy policy.</p>
  </div>
</body>
</html>"""


class OnboardAI(Agent):
    def __init__(self, room: rtc.Room) -> None:
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
                "- Gather essential information such as name, email address, role (customer or artist), and any portfolio/brand links if relevant.\n"
                "- Confirm accuracy by summarizing back the details before saving and ask if anything needs to be corrected.\n\n"
                "Access Setup (Limited Time)\n"
                "- Explain that access will be granted for a limited time period (for example: trial, project, or event window).\n"
                "- Confirm the user understands the time limit, terms of use, and any next steps if they want extended or renewed access.\n\n"
                "**Completing Onboarding**\n"
                "Once you have collected the user's name, email address, role, and optionally their portfolio or brand link, "
                "call the complete_onboarding function with the collected data. This generates their profile page and delivers it to them on screen. "
                "After calling it, let the user know their profile has appeared on their screen.\n\n"
                "**Behavior and Communication Style**\n"
                "Maintain a clear, empathetic, and respectful tone at all times.\n"
                "Use short, conversational sentences suitable for a natural on-camera experience.\n"
                "Before moving to the next step, briefly explain what you are about to do and ask for consent or confirmation.\n"
                "Treat all captured data as sensitive and confidential."
            )
        )
        self._room = room

    @function_tool
    async def complete_onboarding(
        self,
        name: str,
        email: str,
        role: str,
        portfolio: str = "",
    ) -> str:
        """Generate the user's profile page and deliver it to their screen.

        Call this once you have collected all required information.

        Args:
            name: The user's full name.
            email: The user's email address.
            role: The user's role — customer or artist.
            portfolio: Optional portfolio or brand URL.
        """
        html = _generate_profile_html(name, email, role, portfolio)
        await self._room.local_participant.publish_data(
            html.encode(),
            topic="onboard.profile",
        )
        print(f"[agent] profile sent for {name} ({email})")
        return "Profile page generated and delivered to the user's screen."


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

    token = make_agent_token(room_name, identity, name)

    room = rtc.Room()
    disconnected = asyncio.Event()

    @room.on("disconnected")
    def _():
        disconnected.set()

    print(f"[agent] connecting to room={room_name} as {identity} ...")
    await room.connect(livekit_url, token)

    vad = silero.VAD.load()
    stt = FasterWhisperSTT(model_size=whisper_model)
    tts = PiperTTS(piper_model=piper_model)
    llm = openai.with_ollama(model=ollama_model, base_url=ollama_base_url)

    session = AgentSession(
        vad=vad,
        stt=stt,
        llm=llm,
        tts=tts,
        turn_detection="vad",
    )

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
        agent=OnboardAI(room=room),
        room_options=room_io.RoomOptions(
            text_output=room_io.TextOutputOptions(sync_transcription=False),
        ),
    )

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

    for p in room.remote_participants.values():
        if p.identity != identity:
            asyncio.ensure_future(greet_user())
            break

    print("[agent] running. Disconnect the room to stop.")
    await disconnected.wait()


if __name__ == "__main__":
    asyncio.run(main())

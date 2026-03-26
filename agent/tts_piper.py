from __future__ import annotations

import asyncio
import uuid

import numpy as np
from piper.voice import PiperVoice
from livekit import rtc
from livekit.agents.tts import TTS, TTSCapabilities, ChunkedStream, AudioEmitter


class _PiperChunkedStream(ChunkedStream):
    async def _run(self, output_emitter: AudioEmitter) -> None:
        frames = await asyncio.to_thread(self._tts._synthesize, self.input_text)

        output_emitter.initialize(
            request_id=str(uuid.uuid4()),
            sample_rate=48000,
            num_channels=1,
            mime_type="audio/raw",
        )

        for fr in frames:
            output_emitter.push(fr.data)
        output_emitter.flush()


class PiperTTS(TTS):
    """
    Non-streaming TTS using the piper Python API.
    Auto-downloads the voice model on first use; cached to ~/.local/share/piper/.
    Produces 48kHz mono frames for WebRTC playout.
    """

    def __init__(self, piper_model: str):
        super().__init__(
            capabilities=TTSCapabilities(streaming=False),
            sample_rate=48000,
            num_channels=1,
        )
        self._piper_model = piper_model
        self._voice: PiperVoice | None = None

    async def aclose(self) -> None:
        return

    def _load_voice(self) -> PiperVoice:
        if self._voice is None:
            print(f"[tts] loading Piper voice '{self._piper_model}'...")
            self._voice = PiperVoice.load(self._piper_model, use_cuda=False)
            print("[tts] Piper voice ready")
        return self._voice

    def _synthesize(self, text: str) -> list[rtc.AudioFrame]:
        voice = self._load_voice()

        # Collect raw PCM (int16 at voice.config.sample_rate Hz, mono)
        raw = b"".join(voice.synthesize_stream_raw(text))
        pcm = np.frombuffer(raw, dtype=np.int16)
        sr = voice.config.sample_rate

        src = rtc.AudioFrame(
            data=pcm.tobytes(),
            sample_rate=sr,
            num_channels=1,
            samples_per_channel=len(pcm),
        )

        # Resample to 48k for WebRTC if needed
        if sr != 48000:
            resampler = rtc.AudioResampler(sr, 48000, quality=rtc.AudioResamplerQuality.HIGH)
            out = list(resampler.push(src))
            out.extend(list(resampler.flush()))
            src = rtc.combine_audio_frames(out) if len(out) > 1 else out[0]

        # Chunk into 20ms (960 samples @ 48k) frames for low-latency playout
        pcm48 = np.frombuffer(src.data, dtype=np.int16)
        frames: list[rtc.AudioFrame] = []
        for i in range(0, len(pcm48), 960):
            part = pcm48[i : i + 960]
            if len(part) == 0:
                continue
            frames.append(rtc.AudioFrame(
                data=part.tobytes(),
                sample_rate=48000,
                num_channels=1,
                samples_per_channel=len(part),
            ))

        return frames

    def synthesize(self, text: str, *, conn_options=None) -> ChunkedStream:
        return _PiperChunkedStream(tts=self, input_text=text, conn_options=conn_options)

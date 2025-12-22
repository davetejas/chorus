from __future__ import annotations

import asyncio
import os
import subprocess
import tempfile
import uuid
import wave

import numpy as np
from livekit import rtc
from livekit.agents.tts import TTS, TTSCapabilities, ChunkedStream, SynthesizedAudioEmitter


class _PiperChunkedStream(ChunkedStream):
    async def _run(self) -> None:
        request_id = str(uuid.uuid4())
        emitter = SynthesizedAudioEmitter(event_ch=self._event_ch, request_id=request_id)

        wav_path = await asyncio.to_thread(self._tts._synthesize_to_wav, self.input_text)

        try:
            frames = await asyncio.to_thread(self._tts._wav_to_frames_48k_mono, wav_path)

            # Emit ~20ms chunks for low-latency playout
            for fr in frames:
                emitter.push(fr)

            emitter.flush()
        finally:
            try:
                os.remove(wav_path)
            except OSError:
                pass


class PiperTTS(TTS):
    """
    Minimal non-streaming TTS using the `piper` CLI from piper-tts.
    Produces 48kHz mono frames for WebRTC playout.
    """

    def __init__(self, piper_model: str):
        super().__init__(
            capabilities=TTSCapabilities(streaming=False),
            sample_rate=48000,
            num_channels=1,
        )
        self._piper_model = piper_model

    async def aclose(self) -> None:
        return

    def synthesize(self, text: str, *, conn_options=None) -> ChunkedStream:
        return _PiperChunkedStream(tts=self, input_text=text, conn_options=conn_options)

    def _synthesize_to_wav(self, text: str) -> str:
        # piper reads text from stdin and writes wav
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.close()

        cmd = ["piper", "--model", self._piper_model, "--output_file", tmp.name]
        proc = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"Piper failed (code={proc.returncode}). stderr:\n{proc.stderr.decode('utf-8', 'ignore')}"
            )
        return tmp.name

    def _wav_to_frames_48k_mono(self, wav_path: str) -> list[rtc.AudioFrame]:
        with wave.open(wav_path, "rb") as wf:
            sr = wf.getframerate()
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            if sampwidth != 2:
                raise RuntimeError(f"Expected 16-bit PCM WAV, got sample width {sampwidth}")
            pcm_bytes = wf.readframes(wf.getnframes())

        pcm = np.frombuffer(pcm_bytes, dtype=np.int16)
        if channels > 1:
            pcm = pcm.reshape(-1, channels).mean(axis=1).astype(np.int16)

        # Build a single AudioFrame at source rate
        src = rtc.AudioFrame(
            data=pcm.tobytes(),
            sample_rate=sr,
            num_channels=1,
            samples_per_channel=int(pcm.shape[0]),
        )

        # Resample to 48k if needed
        if sr != 48000:
            resampler = rtc.AudioResampler(sr, 48000, quality=rtc.AudioResamplerQuality.HIGH)
            out = list(resampler.push(src))
            out.extend(list(resampler.flush()))
            src = rtc.combine_audio_frames(out) if len(out) > 1 else out[0]

        # Chunk into 20ms (960 samples @ 48k) frames
        pcm48 = np.frombuffer(src.data, dtype=np.int16)
        chunk = 960
        frames: list[rtc.AudioFrame] = []
        for i in range(0, len(pcm48), chunk):
            part = pcm48[i : i + chunk]
            if len(part) == 0:
                continue
            fr = rtc.AudioFrame(
                data=part.tobytes(),
                sample_rate=48000,
                num_channels=1,
                samples_per_channel=int(part.shape[0]),
            )
            frames.append(fr)

        return frames

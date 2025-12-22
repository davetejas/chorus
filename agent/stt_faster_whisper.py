from __future__ import annotations

import uuid
from typing import Iterable

import numpy as np
from faster_whisper import WhisperModel

from livekit import rtc
from livekit.agents.stt import STT, STTCapabilities, SpeechEvent, SpeechEventType, SpeechData, RecognitionUsage


def _frames_from_buffer(buffer) -> list[rtc.AudioFrame]:
    # AudioBuffer is "AudioFrame | list[AudioFrame]" in practice.
    if isinstance(buffer, list):
        return buffer
    return [buffer]


class FasterWhisperSTT(STT):
    """
    Minimal non-streaming STT for LiveKit Agents.
    Uses VAD upstream to produce utterance-sized segments, then transcribes.
    """

    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"):
        super().__init__(capabilities=STTCapabilities(streaming=False, interim_results=False))
        self._target_sr = 16000
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)

    async def aclose(self) -> None:
        # faster-whisper doesn't require explicit cleanup for this simple case
        return

    async def _recognize_impl(self, buffer, *, language: str | None, conn_options) -> SpeechEvent:
        frames = _frames_from_buffer(buffer)
        combined = rtc.combine_audio_frames(frames) if len(frames) > 1 else frames[0]

        # Resample to 16k for Whisper
        if combined.sample_rate != self._target_sr:
            resampler = rtc.AudioResampler(
                combined.sample_rate,
                self._target_sr,
                quality=rtc.AudioResamplerQuality.HIGH,
            )
            out_frames = list(resampler.push(combined))
            out_frames.extend(list(resampler.flush()))
            combined = rtc.combine_audio_frames(out_frames) if len(out_frames) > 1 else out_frames[0]

        pcm = np.frombuffer(combined.data, dtype=np.int16)

        # Downmix to mono if needed
        if combined.num_channels > 1:
            pcm = pcm.reshape(-1, combined.num_channels).mean(axis=1).astype(np.int16)

        audio = (pcm.astype(np.float32)) / 32768.0

        segments, info = self._model.transcribe(
            audio,
            language=language,
            vad_filter=True,
        )

        text_parts: list[str] = []
        for seg in segments:
            if seg.text:
                text_parts.append(seg.text.strip())

        transcript = " ".join([t for t in text_parts if t]).strip()
        if not transcript:
            transcript = "(no speech detected)"

        audio_duration = float(combined.samples_per_channel) / float(combined.sample_rate)
        req_id = str(uuid.uuid4())

        return SpeechEvent(
            type=SpeechEventType.FINAL_TRANSCRIPT,
            request_id=req_id,
            alternatives=[
                SpeechData(
                    language=(info.language or language or "en"),
                    text=transcript,
                    start_time=0.0,
                    end_time=audio_duration,
                    confidence=0.0,
                )
            ],
            recognition_usage=RecognitionUsage(audio_duration=audio_duration),
        )

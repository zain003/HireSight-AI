"""Text-to-speech using Edge TTS (free)."""

from __future__ import annotations

from typing import Optional


async def text_to_speech(
    text: str,
    voice: str = "en-US-JennyNeural",
    rate: str = "+0%",
    pitch: str = "+0%",
) -> bytes:
    try:
        import edge_tts

        if not text:
            return b""

        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
        audio_bytes = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]
        return audio_bytes
    except Exception as exc:
        print(f"[TTS] {exc}")
        return b""


class TTSService:
    async def synthesize(
        self,
        text: str,
        voice: str = "en-US-JennyNeural",
        rate: str = "+0%",
        pitch: str = "+0%",
    ) -> bytes:
        return await text_to_speech(text=text, voice=voice, rate=rate, pitch=pitch)

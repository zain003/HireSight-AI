"""Text-to-speech using Edge TTS (free)."""

from __future__ import annotations

from typing import Optional


async def text_to_speech(
    text: str,
    voice: str = "en-US-JennyNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
) -> bytes:
    try:
        import edge_tts

        if not text or not text.strip():
            return b""

        # Ensure rate ends with % and pitch ends with Hz
        r = rate if rate.endswith("%") else f"{rate}%"
        p = pitch if pitch.endswith("Hz") else "+0Hz"

        communicate = edge_tts.Communicate(text=text.strip(), voice=voice, rate=r, pitch=p)
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
        pitch: str = "+0Hz",
    ) -> bytes:
        return await text_to_speech(text=text, voice=voice, rate=rate, pitch=pitch)

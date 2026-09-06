"""Speech-to-text using Groq Whisper with local fallback."""

from __future__ import annotations

import asyncio
import base64
import os
import tempfile
from typing import Optional

_groq_stt = None


def _get_stt_client():
    global _groq_stt
    if _groq_stt is None:
        from groq import Groq
        from app.core.config import settings

        api_key = getattr(settings, "GROQ_API_KEY", None) or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not set. Add it to backend/.env: GROQ_API_KEY=gsk_xxxx"
            )
        _groq_stt = Groq(api_key=api_key)
    return _groq_stt


import re

HALLUCINATION_KEYWORDS = {
    "thank", "thanks", "you", "very", "much", "watching", "for", "please",
    "subscribe", "subtitles", "by", "amara", "org", "bye", "bell", "icon",
    "like", "share", "comment", "video", "channel", "next", "time"
}


def _clean_transcript(text: Optional[str]) -> str:
    if not text:
        return ""
    cleaned = text.strip()
    norm = cleaned.lower()
    
    # Strip punctuation for word analysis
    words_only = re.sub(r"[^\w\s]", "", norm).strip()
    if not words_only:
        return ""
        
    words = words_only.split()
    
    # Check 1: If all words in the output are silence/hallucination keywords
    if all(w in HALLUCINATION_KEYWORDS for w in words):
        return ""
        
    # Check 2: Check if a 1-4 word phrase repeats to constitute the full string (e.g. "Thank you. Thank you. Thank you.")
    for n in range(1, 5):
        if len(words) >= n * 2:
            chunk = words[:n]
            is_repeating = True
            for i in range(0, len(words), n):
                if words[i:i+n] != chunk[:len(words[i:i+n])]:
                    is_repeating = False
                    break
            if is_repeating:
                return ""
                
    return cleaned


async def transcribe_groq_whisper(
    audio_base64: str,
    language: str = "en",
    audio_format: str = "webm",
) -> Optional[str]:
    tmp_path = None
    try:
        audio_bytes = base64.b64decode(audio_base64)
        if len(audio_bytes) < 300:
            return ""
        suffix = f".{audio_format.lstrip('.')}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        loop = asyncio.get_event_loop()

        def _run():
            client = _get_stt_client()
            models = ["whisper-large-v3-turbo", "whisper-large-v3"]
            last_err = None
            for m in models:
                try:
                    with open(tmp_path, "rb") as f:
                        result = client.audio.transcriptions.create(
                            file=(f"audio{suffix}", f.read()),
                            model=m,
                            language=language,
                            response_format="text",
                            temperature=0.0,
                            prompt="Candidate verbal interview response to technical questions.",
                        )
                    raw_text = result.text if hasattr(result, "text") else str(result)
                    return _clean_transcript(raw_text)
                except Exception as exc:
                    last_err = exc
                    # If rate limited on turbo, try whisper-large-v3
                    continue
            if last_err and "rate_limit" in str(last_err).lower():
                print(f"[STT Groq Rate Limit] Backing off: {last_err}")
                return ""
            raise last_err or RuntimeError("Groq whisper transcription failed")

        transcript = await loop.run_in_executor(None, _run)
        return _clean_transcript(transcript)
    except Exception as exc:
        if "rate_limit" not in str(exc).lower():
            print(f"[STT Groq Error] {exc}")
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


async def transcribe_local_whisper(
    audio_base64: str,
    model_size: str = "base",
    language: Optional[str] = "en",
) -> Optional[str]:
    try:
        from faster_whisper import WhisperModel

        audio_bytes = base64.b64decode(audio_base64)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        loop = asyncio.get_event_loop()

        def _run():
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
            segments, _ = model.transcribe(tmp_path, language=language, beam_size=5)
            text = " ".join(seg.text.strip() for seg in segments)
            os.unlink(tmp_path)
            return text

        return await loop.run_in_executor(None, _run)
    except ImportError:
        print("[STT] faster-whisper not installed. Run: pip install faster-whisper")
        return None
    except Exception as exc:
        print(f"[STT Local Error] {exc}")
        return None


async def transcribe_audio(
    audio_base64: Optional[str] = None,
    transcript_text: Optional[str] = None,
    language: str = "en",
    audio_format: str = "webm",
) -> str:
    if transcript_text and transcript_text.strip():
        return transcript_text.strip()

    if not audio_base64:
        return ""

    from app.core.config import settings
    api_key = getattr(settings, "GROQ_API_KEY", None) or os.getenv("GROQ_API_KEY")
    if api_key:
        result = await transcribe_groq_whisper(audio_base64, language, audio_format)
        if result:
            return result

    result = await transcribe_local_whisper(audio_base64, language=language)
    if result:
        return result

    return "[Could not transcribe audio]"


class STTService:
    async def transcribe(
        self,
        audio_base64: Optional[str] = None,
        transcript_text: Optional[str] = None,
        language: str = "en",
        audio_format: str = "webm",
    ) -> str:
        return await transcribe_audio(
            audio_base64=audio_base64,
            transcript_text=transcript_text,
            language=language,
            audio_format=audio_format,
        )

    async def transcribe_groq(
        self, audio_base64: str, language: str = "en", audio_format: str = "webm"
    ) -> Optional[str]:
        return await transcribe_groq_whisper(audio_base64, language, audio_format)

    async def transcribe_local(self, audio_base64: str, language: str = "en") -> Optional[str]:
        return await transcribe_local_whisper(audio_base64, language=language)

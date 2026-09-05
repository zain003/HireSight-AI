"""
Unit and Integration Tests for FEAT-005-BE: Vocal Acoustic & Speech Pattern Analysis Engine
Tests in-memory audio transcode, WPM calculation, pause ratio, semitone pitch variance, and OpenSMILE fallback.
"""
import base64
import io
import wave
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from app.interview.domain.interview_models import ObservableVocalMetrics
from app.interview.services.vocal_analysis import (
    VocalAnalysisService,
    analyze_audio_stream,
)


def _create_synthetic_wav_bytes(
    duration_sec: float = 3.0,
    freq_hz: float = 440.0,
    sr: int = 16000,
    silence_start_sec: float = None,
) -> bytes:
    """Generates synthetic 16kHz mono PCM WAV bytes."""
    total_samples = int(sr * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)
    audio = np.sin(2 * np.pi * freq_hz * t) * 0.5

    if silence_start_sec is not None and silence_start_sec < duration_sec:
        silence_idx = int(silence_start_sec * sr)
        audio[silence_idx:] = 0.0

    audio_int16 = (audio * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()


def test_audio_conversion_synthetic_wav():
    """Convert synthetic WAV bytes and verify decoded sample rate is 16kHz mono."""
    service = VocalAnalysisService()
    wav_bytes = _create_synthetic_wav_bytes(duration_sec=2.0, freq_hz=220.0, sr=16000)

    wav_data, sr = service._convert_to_wav(wav_bytes, audio_format="wav")

    assert wav_data is not None, "WAV decoding should succeed"
    assert sr == 16000, f"Sample rate should be 16000 Hz, got {sr}"
    assert len(wav_data.shape) == 1, "Audio should be single-channel mono"
    assert len(wav_data) == 32000, f"Expected 32000 samples for 2.0s audio, got {len(wav_data)}"


def test_speech_rate_calculation():
    """150 words in 60 seconds returns exactly 150.0 WPM."""
    service = VocalAnalysisService()
    transcript = " ".join([f"word{i}" for i in range(150)])

    wpm = service._calculate_wpm(transcript, duration_sec=60.0)
    assert abs(wpm - 150.0) < 1e-3, f"Expected 150.0 WPM, got {wpm}"

    # Zero duration edge case
    wpm_zero = service._calculate_wpm(transcript, duration_sec=0.0)
    assert wpm_zero == 0.0


def test_pause_ratio_silent_audio():
    """3 seconds of audio with 1.5 seconds silence returns ~0.50 pause ratio."""
    service = VocalAnalysisService()
    # 3.0 seconds total, tone on first 1.5s, silence on second 1.5s
    wav_bytes = _create_synthetic_wav_bytes(duration_sec=3.0, freq_hz=300.0, sr=16000, silence_start_sec=1.5)
    wav_data, sr = service._convert_to_wav(wav_bytes, audio_format="wav")

    pause_ratio = service._calculate_pause_ratio(wav_data, sr=sr)

    assert 0.40 <= pause_ratio <= 0.60, f"Expected ~0.50 pause ratio, got {pause_ratio}"


def test_graceful_fallback_without_opensmile():
    """Disabling OpenSMILE extractor still computes all Librosa acoustic metrics without raising exceptions."""
    service = VocalAnalysisService()
    service.opensmile_extractor = None  # Explicitly simulate missing opensmile binary

    wav_bytes = _create_synthetic_wav_bytes(duration_sec=2.0, freq_hz=440.0, sr=16000)
    b64_audio = base64.b64encode(wav_bytes).decode("utf-8")
    transcript = "This is a test of fallback audio processing."

    metrics = service.analyze_audio_stream_sync(audio_base64=b64_audio, transcript_text=transcript, audio_format="wav")

    assert isinstance(metrics, ObservableVocalMetrics)
    assert metrics.speaking_rate_wpm > 0.0
    assert 0.0 <= metrics.pause_duration_ratio <= 1.0
    assert metrics.vocal_energy_rms > 0.0
    assert metrics.speech_clarity_score > 0.0


def test_no_emotion_labels_in_vocal_metrics():
    """Invariant test: verify ObservableVocalMetrics schema contains strictly physical acoustic measurements."""
    fields = ObservableVocalMetrics.model_fields.keys()

    # Required physical acoustic metrics
    assert "speaking_rate_wpm" in fields
    assert "pause_duration_ratio" in fields
    assert "pitch_semitone_variance" in fields
    assert "vocal_energy_rms" in fields
    assert "speech_clarity_score" in fields
    assert "acoustic_flags" in fields

    # Forbidden speculative terms
    forbidden = ["nervous", "confident", "suspicious", "lying", "emotion", "sentiment", "hesitant_mind"]
    for term in forbidden:
        assert term not in fields, f"Forbidden term '{term}' in ObservableVocalMetrics schema!"


def test_empty_or_silent_audio_returns_graceful_defaults():
    """Empty or None audio stream returns 0.0 scores with graceful acoustic flag."""
    service = VocalAnalysisService()

    metrics = service.analyze_audio_stream_sync(audio_base64=None, transcript_text=None)

    assert isinstance(metrics, ObservableVocalMetrics)
    assert metrics.speaking_rate_wpm == 0.0
    assert metrics.pause_duration_ratio == 0.0
    assert metrics.pitch_semitone_variance == 0.0
    assert metrics.vocal_energy_rms == 0.0
    assert any("No audio" in flag or "silent" in flag for flag in metrics.acoustic_flags)

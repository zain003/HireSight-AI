"""
Vocal Acoustic & Speech Pattern Analysis Engine using SciPy, NumPy, OpenSMILE, and Vosk.
Extracts conversational speech rate (WPM), pause duration ratio, F0 pitch semitone variance,
vocal energy stability, and physical acoustic flags with zero speculative emotion labels.
"""
import asyncio
import base64
import io
import json as json_lib
import os
import tempfile
import wave
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import scipy.io.wavfile
    import scipy.signal
except ImportError:
    scipy = None

try:
    import opensmile
except ImportError:
    opensmile = None

try:
    from vosk import KaldiRecognizer, Model
except ImportError:
    Model = None
    KaldiRecognizer = None

try:
    import librosa
    import soundfile as sf
except ImportError:
    librosa = None
    sf = None

from app.interview.domain.interview_models import ObservableVocalMetrics


@dataclass
class VocalMetrics:
    """Legacy and enhanced vocal analysis metrics from audio."""
    vocal_confidence_score: float  # 0-100 (maps to vocal energy and stability)
    speech_clarity_score: float  # 0-100 (spectral clarity)
    pitch_variance_score: float  # 0-100 (pitch variance)
    speech_rate_score: float  # 0-100 (speech rate optimality)
    pause_pattern_score: float  # 0-100 (pause ratio optimality)
    tone_consistency_score: float  # 0-100 (tone consistency)
    communication_effectiveness: float  # 0-100 (composite score)
    red_flags: List[str]  # Observable acoustic flags
    transcript_confidence: float
    analysis_details: Dict[str, Any] = field(default_factory=dict)
    observable_vocal_metrics: Optional[ObservableVocalMetrics] = None


class VocalAnalysisService:
    """
    Observable Acoustic & Vocal Analysis Engine.
    Extracts WPM, pause ratios, semitone pitch dynamics, and vocal energy RMS.
    """

    def __init__(self):
        self.vosk_model = None
        self.opensmile_extractor = None

        # Initialize OpenSMILE if available
        if opensmile is not None:
            try:
                self.opensmile_extractor = opensmile.Smile(
                    feature_set=opensmile.FeatureSet.GeMAPSv01b,
                    feature_level=opensmile.FeatureLevel.Functionals,
                )
            except Exception as e:
                print(f"[OpenSMILE Init Warning] {e}")

        # Initialize Vosk model if available
        if Model is not None and KaldiRecognizer is not None:
            try:
                model_path = os.getenv("VOSK_MODEL_PATH", "./models/vosk-model-small-en-us-0.15")
                if os.path.exists(model_path):
                    self.vosk_model = Model(model_path)
            except Exception as e:
                print(f"[Vosk Init Warning] {e}")

    async def analyze_audio_stream(
        self,
        audio_base64: Optional[str],
        transcript_text: Optional[str] = None,
        audio_format: str = "webm",
    ) -> ObservableVocalMetrics:
        """
        Asynchronously analyze audio stream and return physical ObservableVocalMetrics.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.analyze_audio_stream_sync(
                audio_base64=audio_base64,
                transcript_text=transcript_text,
                audio_format=audio_format,
            )
        )

    def analyze_audio_stream_sync(
        self,
        audio_base64: Optional[str],
        transcript_text: Optional[str] = None,
        audio_format: str = "webm",
    ) -> ObservableVocalMetrics:
        """
        Synchronously extract physical acoustic metrics from audio bytes.
        """
        if not audio_base64:
            return self._create_empty_observable_metrics("No audio stream provided")

        try:
            audio_bytes = base64.b64decode(audio_base64)
            wav_data, sr = self._convert_to_wav(audio_bytes, audio_format)

            if wav_data is None or len(wav_data) == 0:
                return self._create_empty_observable_metrics("Audio conversion failed or empty data")

            duration_sec = float(len(wav_data)) / float(sr)

            # 1. Speaking rate (WPM)
            speaking_rate_wpm = self._calculate_wpm(transcript_text, duration_sec)

            # 2. Pause duration ratio
            pause_duration_ratio = self._calculate_pause_ratio(wav_data, sr)

            # 3. F0 pitch semitone variance
            pitch_semitone_variance = self._extract_pitch_semitones(wav_data, sr)

            # 4. Vocal energy RMS
            vocal_energy_rms = self._calculate_rms_energy(wav_data)

            # 5. Speech clarity score (0-100)
            speech_clarity_score = self._calculate_clarity_score(wav_data, sr, vocal_energy_rms)

            # 6. Physical acoustic flags
            acoustic_flags = self._generate_acoustic_flags(
                speaking_rate_wpm=speaking_rate_wpm,
                pause_duration_ratio=pause_duration_ratio,
                pitch_semitone_variance=pitch_semitone_variance,
                vocal_energy_rms=vocal_energy_rms,
                duration_sec=duration_sec,
            )

            return ObservableVocalMetrics(
                speaking_rate_wpm=round(speaking_rate_wpm, 2),
                pause_duration_ratio=round(pause_duration_ratio, 3),
                pitch_semitone_variance=round(pitch_semitone_variance, 2),
                vocal_energy_rms=round(vocal_energy_rms, 4),
                speech_clarity_score=round(speech_clarity_score, 2),
                acoustic_flags=acoustic_flags,
            )

        except Exception as e:
            print(f"[Vocal Analysis Error] {e}")
            return self._create_empty_observable_metrics(f"Analysis error: {str(e)}")

    async def analyze_audio(
        self,
        audio_base64: Optional[str],
        transcript_text: Optional[str] = None,
        audio_format: str = "webm",
    ) -> VocalMetrics:
        """
        Backward-compatible method returning VocalMetrics with embedded ObservableVocalMetrics.
        """
        obs_metrics = await self.analyze_audio_stream(
            audio_base64=audio_base64,
            transcript_text=transcript_text,
            audio_format=audio_format,
        )

        # Map to legacy sub-scores
        speech_rate_score = max(0.0, min(100.0, 100.0 - abs(obs_metrics.speaking_rate_wpm - 140.0) * 0.75))
        pause_pattern_score = max(0.0, min(100.0, (1.0 - abs(obs_metrics.pause_duration_ratio - 0.25) * 2.0) * 100.0))
        pitch_score = max(0.0, min(100.0, min(obs_metrics.pitch_semitone_variance * 20.0, 100.0)))
        energy_score = max(0.0, min(100.0, min(obs_metrics.vocal_energy_rms * 500.0, 100.0)))

        composite_effectiveness = round(
            energy_score * 0.25 +
            obs_metrics.speech_clarity_score * 0.35 +
            speech_rate_score * 0.20 +
            pause_pattern_score * 0.20,
            2
        )

        return VocalMetrics(
            vocal_confidence_score=round(energy_score, 2),
            speech_clarity_score=obs_metrics.speech_clarity_score,
            pitch_variance_score=round(pitch_score, 2),
            speech_rate_score=round(speech_rate_score, 2),
            pause_pattern_score=round(pause_pattern_score, 2),
            tone_consistency_score=round(energy_score, 2),
            communication_effectiveness=composite_effectiveness,
            red_flags=obs_metrics.acoustic_flags,
            transcript_confidence=1.0,
            analysis_details={
                "speaking_rate_wpm": obs_metrics.speaking_rate_wpm,
                "pause_duration_ratio": obs_metrics.pause_duration_ratio,
                "pitch_semitone_variance": obs_metrics.pitch_semitone_variance,
                "vocal_energy_rms": obs_metrics.vocal_energy_rms,
                "speech_clarity_score": obs_metrics.speech_clarity_score,
                "opensmile_available": bool(self.opensmile_extractor),
                "vosk_available": bool(self.vosk_model),
            },
            observable_vocal_metrics=obs_metrics,
        )

    def _convert_to_wav(self, audio_data: bytes, audio_format: str) -> Tuple[Optional[np.ndarray], int]:
        """
        Converts in-memory audio bytes to 16kHz mono float32 numpy array.
        """
        if not audio_data:
            return None, 16000

        # 1. Try standard library wave module for PCM WAV
        try:
            buf = io.BytesIO(audio_data)
            with wave.open(buf, "rb") as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                raw_bytes = wf.readframes(n_frames)

                if sampwidth == 2:
                    data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                elif sampwidth == 4:
                    data = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
                else:
                    data = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

                if n_channels > 1:
                    data = data.reshape(-1, n_channels).mean(axis=1)

                if framerate != 16000:
                    data = self._resample_audio(data, orig_sr=framerate, target_sr=16000)
                    framerate = 16000
                return data.astype(np.float32), framerate
        except Exception:
            pass

        # 2. Try scipy.io.wavfile
        try:
            buf = io.BytesIO(audio_data)
            sr, data = scipy.io.wavfile.read(buf)
            if data.dtype == np.int16:
                data = data.astype(np.float32) / 32768.0
            elif data.dtype == np.int32:
                data = data.astype(np.float32) / 2147483648.0
            elif data.dtype == np.uint8:
                data = data.astype(np.float32) / 128.0 - 1.0
            else:
                data = data.astype(np.float32)

            if data.ndim > 1:
                data = np.mean(data, axis=1)

            if sr != 16000:
                data = self._resample_audio(data, orig_sr=sr, target_sr=16000)
                sr = 16000
            return data.astype(np.float32), sr
        except Exception:
            pass

        # 3. Try SoundFile if available
        if sf is not None:
            try:
                buf = io.BytesIO(audio_data)
                data, sr = sf.read(buf, dtype="float32")
                if data.ndim > 1:
                    data = np.mean(data, axis=1)
                if sr != 16000:
                    data = self._resample_audio(data, orig_sr=sr, target_sr=16000)
                    sr = 16000
                return data.astype(np.float32), sr
            except Exception:
                pass

        # 4. Fallback to temp file decoding with Librosa (supports WebM Opus, MP3, etc.)
        if librosa is not None:
            tmp_path = None
            try:
                suffix = f".{audio_format.lstrip('.')}"
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(audio_data)
                    tmp_path = tmp.name

                data, sr = librosa.load(tmp_path, sr=16000, mono=True)
                return data.astype(np.float32), sr
            except Exception as e:
                print(f"[Librosa load error] {e}")
                return None, 16000
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

        return None, 16000

    def _resample_audio(self, data: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
        """Resamples 1D audio array to target sample rate using SciPy or Librosa."""
        if orig_sr == target_sr or len(data) == 0:
            return data

        if librosa is not None:
            return librosa.resample(data, orig_sr=orig_sr, target_sr=target_sr)

        # SciPy resample
        num_target_samples = int(len(data) * float(target_sr) / float(orig_sr))
        try:
            return scipy.signal.resample(data, num_target_samples).astype(np.float32)
        except Exception:
            indices = np.linspace(0, len(data) - 1, num_target_samples)
            return np.interp(indices, np.arange(len(data)), data).astype(np.float32)

    def _calculate_wpm(self, transcript_text: Optional[str], duration_sec: float) -> float:
        """
        Calculates Words Per Minute (WPM) normalized against audio duration.
        """
        if not transcript_text or duration_sec <= 0.0:
            return 0.0

        words = len(transcript_text.strip().split())
        return (words / duration_sec) * 60.0

    def _calculate_pause_ratio(self, wav_data: np.ndarray, sr: int) -> float:
        """
        Calculates pause duration ratio using frame-level short-time energy (STE).
        """
        if wav_data is None or len(wav_data) == 0 or sr <= 0:
            return 0.0

        total_duration = len(wav_data) / float(sr)
        if total_duration <= 0.0:
            return 0.0

        # Frame parameters: 30ms window, 10ms hop
        frame_len = max(64, int(sr * 0.030))
        hop_len = max(32, int(sr * 0.010))

        num_frames = (len(wav_data) - frame_len) // hop_len + 1
        if num_frames <= 0:
            rms = np.sqrt(np.mean(wav_data ** 2))
            return 0.0 if rms > 0.01 else 1.0

        # Compute RMS energy per frame
        frames_energy = []
        for i in range(num_frames):
            start = i * hop_len
            frame = wav_data[start : start + frame_len]
            energy = np.sqrt(np.mean(frame ** 2))
            frames_energy.append(energy)

        frames_energy = np.array(frames_energy)
        max_energy = float(np.max(frames_energy)) if len(frames_energy) > 0 else 0.0

        if max_energy < 1e-4:
            return 1.0  # Entirely silent

        # Dynamic threshold: 25 dB down from peak or absolute noise floor
        silence_threshold = max(0.01, max_energy * 0.08)
        silent_frames = np.sum(frames_energy < silence_threshold)
        pause_ratio = float(silent_frames) / float(num_frames)

        return float(min(1.0, max(0.0, pause_ratio)))

    def _extract_pitch_semitones(self, wav_data: np.ndarray, sr: int) -> float:
        """
        Extracts fundamental frequency (F0) across voiced frames using autocorrelation / YIN
        and computes pitch variance in semitones relative to A440 (440 Hz).
        """
        if wav_data is None or len(wav_data) < 512 or sr <= 0:
            return 0.0

        # Use librosa.pyin if available
        if librosa is not None:
            try:
                f0, _, _ = librosa.pyin(wav_data, fmin=75.0, fmax=500.0, sr=sr)
                valid_f0 = f0[~np.isnan(f0) & (f0 > 75.0)]
                if len(valid_f0) >= 2:
                    semitones = 12.0 * np.log2(valid_f0 / 440.0)
                    return float(np.var(semitones))
            except Exception:
                pass

        # High-performance NumPy autocorrelation pitch estimator
        frame_len = max(256, int(sr * 0.040))  # 40ms frame
        hop_len = max(128, int(sr * 0.020))   # 20ms hop
        min_lag = int(sr / 500.0)             # 500 Hz upper limit
        max_lag = int(sr / 75.0)              # 75 Hz lower limit

        num_frames = (len(wav_data) - frame_len) // hop_len + 1
        pitch_estimates = []

        for i in range(num_frames):
            start = i * hop_len
            frame = wav_data[start : start + frame_len]
            frame_rms = np.sqrt(np.mean(frame ** 2))
            if frame_rms < 0.015:
                continue

            # Normalized autocorrelation
            frame_centered = frame - np.mean(frame)
            autocorr = np.correlate(frame_centered, frame_centered, mode="full")
            autocorr = autocorr[len(frame_centered) - 1 :]

            if len(autocorr) > max_lag and autocorr[0] > 1e-5:
                search_region = autocorr[min_lag : max_lag + 1]
                peak_idx = int(np.argmax(search_region)) + min_lag
                peak_val = autocorr[peak_idx] / autocorr[0]

                # Voiced threshold
                if peak_val > 0.35:
                    freq = float(sr) / float(peak_idx)
                    if 75.0 <= freq <= 500.0:
                        pitch_estimates.append(freq)

        if len(pitch_estimates) >= 2:
            semitones = 12.0 * np.log2(np.array(pitch_estimates) / 440.0)
            return float(np.var(semitones))

        return 0.0

    def _calculate_rms_energy(self, wav_data: np.ndarray) -> float:
        """
        Calculates Root Mean Square (RMS) energy.
        """
        if wav_data is None or len(wav_data) == 0:
            return 0.0
        return float(np.sqrt(np.mean(wav_data ** 2)))

    def _calculate_clarity_score(self, wav_data: np.ndarray, sr: int, rms_energy: float) -> float:
        """
        Computes speech clarity score (0-100) from zero-crossing rate and spectral centroid.
        """
        if len(wav_data) < 512:
            return 50.0

        score = 80.0

        # Zero Crossing Rate
        signs = np.sign(wav_data)
        zero_crossings = np.sum(np.abs(np.diff(signs))) / 2.0
        mean_zcr = float(zero_crossings) / float(len(wav_data))

        # Conversational speech ZCR is typically in [0.03, 0.18]
        if 0.03 <= mean_zcr <= 0.18:
            score += 15.0
        elif mean_zcr < 0.015 or mean_zcr > 0.30:
            score -= 25.0

        if rms_energy < 0.005:
            score -= 30.0
        elif rms_energy > 0.02:
            score += 5.0

        return float(max(0.0, min(100.0, score)))

    def _generate_acoustic_flags(
        self,
        speaking_rate_wpm: float,
        pause_duration_ratio: float,
        pitch_semitone_variance: float,
        vocal_energy_rms: float,
        duration_sec: float,
    ) -> List[str]:
        """
        Generates purely physical, measurable acoustic flags.
        """
        flags = []

        if duration_sec <= 0.0 or vocal_energy_rms < 0.002:
            flags.append("silent_or_empty_audio")
            return flags

        if speaking_rate_wpm > 190.0:
            flags.append("atypical_speech_rate_high")
        elif speaking_rate_wpm < 85.0 and duration_sec > 5.0 and speaking_rate_wpm > 0.0:
            flags.append("atypical_speech_rate_low")

        if pause_duration_ratio > 0.55:
            flags.append("elevated_pause_ratio")

        if pitch_semitone_variance < 0.8 and duration_sec > 5.0:
            flags.append("monotone_pitch")

        if vocal_energy_rms < 0.005:
            flags.append("low_vocal_energy")

        return flags

    def _create_empty_observable_metrics(self, reason: str = "No audio stream provided") -> ObservableVocalMetrics:
        """
        Returns default ObservableVocalMetrics for missing or failed audio streams.
        """
        return ObservableVocalMetrics(
            speaking_rate_wpm=0.0,
            pause_duration_ratio=0.0,
            pitch_semitone_variance=0.0,
            vocal_energy_rms=0.0,
            speech_clarity_score=0.0,
            acoustic_flags=[reason],
        )

    def _create_empty_metrics(self, reason: str = "No audio provided") -> VocalMetrics:
        """
        Returns default legacy VocalMetrics.
        """
        empty_obs = self._create_empty_observable_metrics(reason)
        return VocalMetrics(
            vocal_confidence_score=0.0,
            speech_clarity_score=0.0,
            pitch_variance_score=0.0,
            speech_rate_score=0.0,
            pause_pattern_score=0.0,
            tone_consistency_score=0.0,
            communication_effectiveness=0.0,
            red_flags=[reason],
            transcript_confidence=0.0,
            analysis_details={"error": reason},
            observable_vocal_metrics=empty_obs,
        )


async def analyze_audio_stream(
    audio_base64: Optional[str],
    transcript_text: Optional[str] = None,
    audio_format: str = "webm",
) -> ObservableVocalMetrics:
    """
    Public module function to analyze audio streams and return ObservableVocalMetrics.
    """
    service = VocalAnalysisService()
    return await service.analyze_audio_stream(
        audio_base64=audio_base64,
        transcript_text=transcript_text,
        audio_format=audio_format,
    )

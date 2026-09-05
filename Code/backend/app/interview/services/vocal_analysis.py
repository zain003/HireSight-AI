"""
Vocal and Speech Analysis Service using OpenSMILE and Vosk.
Analyzes speech features, vocal confidence, communication metrics.
"""
import base64
import io
import os
import tempfile
import wave
from typing import Dict, List, Optional
import numpy as np
from dataclasses import dataclass

try:
    import opensmile
except ImportError:
    opensmile = None

try:
    from vosk import Model, KaldiRecognizer
    import json as json_lib
except ImportError:
    Model = None
    KaldiRecognizer = None

try:
    import librosa
    import soundfile as sf
except ImportError:
    librosa = None
    sf = None


@dataclass
class VocalMetrics:
    """Vocal analysis metrics from audio."""
    vocal_confidence_score: float  # 0-100
    speech_clarity_score: float  # 0-100
    pitch_variance_score: float  # 0-100
    speech_rate_score: float  # 0-100 (optimal rate)
    pause_pattern_score: float  # 0-100
    tone_consistency_score: float  # 0-100
    communication_effectiveness: float  # 0-100 (overall)
    red_flags: List[str]
    transcript_confidence: float
    analysis_details: Dict


class VocalAnalysisService:
    """
    Analyzes vocal characteristics using OpenSMILE and Vosk.
    Extracts acoustic features and speech patterns.
    """
    
    def __init__(self):
        self.vosk_model = None
        self.opensmile_extractor = None
        
        # Initialize OpenSMILE
        if opensmile:
            try:
                # Use GeMAPS feature set for voice analysis
                self.opensmile_extractor = opensmile.Smile(
                    feature_set=opensmile.FeatureSet.GeMAPSv01b,
                    feature_level=opensmile.FeatureLevel.Functionals,
                )
            except Exception as e:
                print(f"OpenSMILE initialization warning: {e}")
        
        # Initialize Vosk
        if Model and KaldiRecognizer:
            try:
                # Check for Vosk model path
                model_path = os.getenv("VOSK_MODEL_PATH", "./models/vosk-model-small-en-us-0.15")
                if os.path.exists(model_path):
                    self.vosk_model = Model(model_path)
                else:
                    print(f"Vosk model not found at {model_path}")
            except Exception as e:
                print(f"Vosk initialization warning: {e}")
    
    async def analyze_audio(
        self,
        audio_base64: Optional[str],
        transcript_text: Optional[str],
        audio_format: str = "webm"
    ) -> VocalMetrics:
        """
        Analyze audio for vocal characteristics and speech patterns.
        
        Args:
            audio_base64: Base64-encoded audio data
            transcript_text: Pre-transcribed text (if available)
            audio_format: Audio format (webm, wav, mp3)
            
        Returns:
            VocalMetrics with comprehensive analysis
        """
        if not audio_base64:
            return self._create_empty_metrics("No audio provided")
        
        try:
            # Decode audio
            audio_data = base64.b64decode(audio_base64)
            
            # Convert to WAV format for analysis
            wav_data, sample_rate = self._convert_to_wav(audio_data, audio_format)
            
            if wav_data is None:
                return self._create_empty_metrics("Audio conversion failed")
            
            # 1. OpenSMILE feature extraction
            opensmile_features = self._extract_opensmile_features(wav_data, sample_rate)
            
            # 2. Librosa-based analysis (pitch, energy, rhythm)
            librosa_features = self._extract_librosa_features(wav_data, sample_rate)
            
            # 3. Vosk transcription (if needed)
            vosk_result = None
            if not transcript_text and self.vosk_model:
                vosk_result = self._transcribe_with_vosk(wav_data, sample_rate)
                transcript_text = vosk_result.get("text", "") if vosk_result else ""
            
            # 4. Speech pattern analysis
            speech_patterns = self._analyze_speech_patterns(
                wav_data, 
                sample_rate,
                transcript_text or ""
            )
            
            # Calculate scores
            vocal_confidence = self._calculate_vocal_confidence(
                opensmile_features,
                librosa_features,
                speech_patterns
            )
            
            clarity_score = self._calculate_clarity_score(
                librosa_features,
                speech_patterns
            )
            
            pitch_variance = self._calculate_pitch_variance_score(librosa_features)
            
            speech_rate = self._calculate_speech_rate_score(speech_patterns)
            
            pause_pattern = self._calculate_pause_pattern_score(speech_patterns)
            
            tone_consistency = self._calculate_tone_consistency(librosa_features)
            
            # Overall communication effectiveness
            communication_score = (
                vocal_confidence * 0.3 +
                clarity_score * 0.25 +
                pitch_variance * 0.15 +
                speech_rate * 0.15 +
                pause_pattern * 0.1 +
                tone_consistency * 0.05
            )
            
            # Detect red flags
            red_flags = self._detect_vocal_red_flags(
                vocal_confidence,
                clarity_score,
                speech_rate,
                pause_pattern,
                librosa_features
            )
            
            # Transcript confidence
            transcript_conf = vosk_result.get("confidence", 1.0) if vosk_result else 1.0
            
            return VocalMetrics(
                vocal_confidence_score=round(vocal_confidence, 2),
                speech_clarity_score=round(clarity_score, 2),
                pitch_variance_score=round(pitch_variance, 2),
                speech_rate_score=round(speech_rate, 2),
                pause_pattern_score=round(pause_pattern, 2),
                tone_consistency_score=round(tone_consistency, 2),
                communication_effectiveness=round(communication_score, 2),
                red_flags=red_flags,
                transcript_confidence=round(transcript_conf, 3),
                analysis_details={
                    "audio_duration_sec": len(wav_data) / sample_rate,
                    "sample_rate": sample_rate,
                    "opensmile_available": bool(self.opensmile_extractor),
                    "vosk_available": bool(self.vosk_model),
                    **opensmile_features,
                    **librosa_features,
                    **speech_patterns
                }
            )
            
        except Exception as e:
            print(f"Audio analysis error: {e}")
            return self._create_empty_metrics(f"Analysis error: {str(e)}")
    
    def _convert_to_wav(self, audio_data: bytes, audio_format: str) -> tuple:
        """Convert audio to WAV format."""
        try:
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            try:
                # Load and convert using librosa
                wav_data, sr = librosa.load(tmp_path, sr=16000, mono=True)
                return wav_data, sr
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            print(f"Audio conversion error: {e}")
            return None, None
    
    def _extract_opensmile_features(self, wav_data: np.ndarray, sr: int) -> Dict:
        """Extract acoustic features using OpenSMILE."""
        if not self.opensmile_extractor:
            return {}
        
        try:
            # Save to temp WAV file for OpenSMILE
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            
            sf.write(tmp_path, wav_data, sr)
            
            try:
                # Extract features
                features = self.opensmile_extractor.process_file(tmp_path)
                
                # Convert to dict (take mean of features)
                feature_dict = {}
                for col in features.columns:
                    feature_dict[f"opensmile_{col}"] = float(features[col].mean())
                
                return feature_dict
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            print(f"OpenSMILE extraction error: {e}")
            return {}
    
    def _extract_librosa_features(self, wav_data: np.ndarray, sr: int) -> Dict:
        """Extract audio features using librosa."""
        try:
            features = {}
            
            # Pitch (F0) analysis
            pitches, magnitudes = librosa.piptrack(y=wav_data, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            if pitch_values:
                features["mean_pitch_hz"] = float(np.mean(pitch_values))
                features["pitch_std_hz"] = float(np.std(pitch_values))
                features["pitch_range_hz"] = float(np.ptp(pitch_values))
            else:
                features["mean_pitch_hz"] = 0.0
                features["pitch_std_hz"] = 0.0
                features["pitch_range_hz"] = 0.0
            
            # Energy/Loudness
            rms = librosa.feature.rms(y=wav_data)[0]
            features["mean_energy"] = float(np.mean(rms))
            features["energy_std"] = float(np.std(rms))
            
            # Zero crossing rate (voice quality indicator)
            zcr = librosa.feature.zero_crossing_rate(wav_data)[0]
            features["mean_zcr"] = float(np.mean(zcr))
            
            # Spectral centroid (brightness)
            spectral_centroids = librosa.feature.spectral_centroid(y=wav_data, sr=sr)[0]
            features["mean_spectral_centroid"] = float(np.mean(spectral_centroids))
            
            # Speech/silence ratio
            frame_length = 2048
            hop_length = 512
            energy_threshold = np.mean(rms) * 0.3
            speech_frames = np.sum(rms > energy_threshold)
            total_frames = len(rms)
            features["speech_ratio"] = float(speech_frames / total_frames if total_frames > 0 else 0)
            
            return features
            
        except Exception as e:
            print(f"Librosa extraction error: {e}")
            return {}
    
    def _transcribe_with_vosk(self, wav_data: np.ndarray, sr: int) -> Optional[Dict]:
        """Transcribe audio using Vosk."""
        if not self.vosk_model:
            return None
        
        try:
            # Convert to 16-bit PCM
            wav_int16 = (wav_data * 32767).astype(np.int16)
            
            # Create recognizer
            rec = KaldiRecognizer(self.vosk_model, sr)
            rec.SetWords(True)
            
            # Process audio
            rec.AcceptWaveform(wav_int16.tobytes())
            result = rec.FinalResult()
            
            result_dict = json_lib.loads(result)
            return result_dict
            
        except Exception as e:
            print(f"Vosk transcription error: {e}")
            return None
    
    def _analyze_speech_patterns(
        self, 
        wav_data: np.ndarray, 
        sr: int,
        transcript: str
    ) -> Dict:
        """Analyze speech rate, pauses, and patterns."""
        try:
            duration = len(wav_data) / sr
            
            # Detect speech segments
            intervals = librosa.effects.split(wav_data, top_db=30)
            
            speech_duration = sum((end - start) / sr for start, end in intervals)
            silence_duration = duration - speech_duration
            
            # Calculate speech rate
            word_count = len(transcript.split()) if transcript else 0
            words_per_minute = (word_count / duration) * 60 if duration > 0 else 0
            
            # Pause analysis
            pause_count = len(intervals) - 1
            avg_pause_duration = silence_duration / pause_count if pause_count > 0 else 0
            
            # Speech continuity
            continuity = speech_duration / duration if duration > 0 else 0
            
            return {
                "duration_sec": float(duration),
                "speech_duration_sec": float(speech_duration),
                "silence_duration_sec": float(silence_duration),
                "word_count": word_count,
                "words_per_minute": float(words_per_minute),
                "pause_count": pause_count,
                "avg_pause_duration_sec": float(avg_pause_duration),
                "speech_continuity": float(continuity)
            }
            
        except Exception as e:
            print(f"Speech pattern analysis error: {e}")
            return {}
    
    def _calculate_vocal_confidence(
        self,
        opensmile_features: Dict,
        librosa_features: Dict,
        speech_patterns: Dict
    ) -> float:
        """
        Calculate vocal confidence score based on:
        - Steady pitch
        - Consistent energy
        - Minimal hesitations
        - Good speech continuity
        """
        score = 70.0  # Base score
        
        # Pitch stability (lower std = more confident)
        pitch_std = librosa_features.get("pitch_std_hz", 50)
        if pitch_std < 20:
            score += 10
        elif pitch_std < 40:
            score += 5
        elif pitch_std > 80:
            score -= 10
        
        # Energy consistency
        energy_std = librosa_features.get("energy_std", 0.1)
        if energy_std < 0.05:
            score += 5
        
        # Speech continuity (fewer pauses = more confident)
        continuity = speech_patterns.get("speech_continuity", 0.7)
        if continuity > 0.8:
            score += 10
        elif continuity < 0.5:
            score -= 15
        
        # Speech rate (confident speakers have moderate rate)
        wpm = speech_patterns.get("words_per_minute", 0)
        if 120 <= wpm <= 160:
            score += 10
        elif wpm < 80 or wpm > 200:
            score -= 10
        
        return max(0.0, min(100.0, score))
    
    def _calculate_clarity_score(
        self,
        librosa_features: Dict,
        speech_patterns: Dict
    ) -> float:
        """Calculate speech clarity score."""
        score = 75.0
        
        # Speech ratio (higher = clearer speech)
        speech_ratio = librosa_features.get("speech_ratio", 0.7)
        if speech_ratio > 0.7:
            score += 10
        elif speech_ratio < 0.5:
            score -= 15
        
        # Zero crossing rate (voice quality)
        zcr = librosa_features.get("mean_zcr", 0.1)
        if 0.05 < zcr < 0.15:
            score += 5
        
        # Minimal excessive pauses
        avg_pause = speech_patterns.get("avg_pause_duration_sec", 1.0)
        if avg_pause < 1.0:
            score += 10
        elif avg_pause > 3.0:
            score -= 15
        
        return max(0.0, min(100.0, score))
    
    def _calculate_pitch_variance_score(self, librosa_features: Dict) -> float:
        """
        Calculate pitch variance score.
        Moderate variance is good (expressive), too much/too little is bad.
        """
        pitch_std = librosa_features.get("pitch_std_hz", 30)
        
        # Optimal range: 20-60 Hz standard deviation
        if 20 <= pitch_std <= 60:
            return 85.0
        elif 10 <= pitch_std < 20 or 60 < pitch_std <= 80:
            return 65.0
        elif pitch_std < 10:
            return 40.0  # Monotone
        else:
            return 45.0  # Too variable (nervous)
    
    def _calculate_speech_rate_score(self, speech_patterns: Dict) -> float:
        """
        Calculate speech rate score.
        Optimal: 120-160 words per minute.
        """
        wpm = speech_patterns.get("words_per_minute", 0)
        
        if 120 <= wpm <= 160:
            return 90.0
        elif 100 <= wpm < 120 or 160 < wpm <= 180:
            return 75.0
        elif 80 <= wpm < 100 or 180 < wpm <= 200:
            return 60.0
        elif wpm < 80:
            return 40.0  # Too slow
        else:
            return 35.0  # Too fast
    
    def _calculate_pause_pattern_score(self, speech_patterns: Dict) -> float:
        """Calculate pause pattern score."""
        avg_pause = speech_patterns.get("avg_pause_duration_sec", 1.0)
        continuity = speech_patterns.get("speech_continuity", 0.7)
        
        score = 70.0
        
        # Optimal pause duration: 0.5-2 seconds
        if 0.5 <= avg_pause <= 2.0:
            score += 15
        elif avg_pause > 3.0:
            score -= 20
        
        # Good continuity
        if continuity > 0.75:
            score += 15
        elif continuity < 0.5:
            score -= 15
        
        return max(0.0, min(100.0, score))
    
    def _calculate_tone_consistency(self, librosa_features: Dict) -> float:
        """Calculate tone consistency score."""
        energy_std = librosa_features.get("energy_std", 0.1)
        
        # Lower energy variation = more consistent tone
        if energy_std < 0.03:
            return 85.0
        elif energy_std < 0.06:
            return 70.0
        elif energy_std < 0.1:
            return 55.0
        else:
            return 40.0
    
    def _detect_vocal_red_flags(
        self,
        vocal_confidence: float,
        clarity: float,
        speech_rate: float,
        pause_pattern: float,
        librosa_features: Dict
    ) -> List[str]:
        """Detect vocal red flags."""
        red_flags = []
        
        if vocal_confidence < 50:
            red_flags.append("Low vocal confidence - hesitant or uncertain speech")
        
        if clarity < 50:
            red_flags.append("Poor speech clarity - difficult to understand")
        
        wpm = librosa_features.get("words_per_minute", 0)
        if wpm < 80:
            red_flags.append("Very slow speech rate - possible lack of preparation")
        elif wpm > 200:
            red_flags.append("Very fast speech rate - possible nervousness")
        
        if pause_pattern < 50:
            red_flags.append("Poor pause patterns - excessive hesitations")
        
        # Monotone detection
        pitch_std = librosa_features.get("pitch_std_hz", 30)
        if pitch_std < 15:
            red_flags.append("Monotone speech - lack of vocal expression")
        
        return red_flags
    
    def _create_empty_metrics(self, reason: str) -> VocalMetrics:
        """Create empty metrics when analysis fails."""
        return VocalMetrics(
            vocal_confidence_score=0.0,
            speech_clarity_score=0.0,
            pitch_variance_score=0.0,
            speech_rate_score=0.0,
            pause_pattern_score=0.0,
            tone_consistency_score=0.0,
            communication_effectiveness=0.0,
            red_flags=[f"Vocal analysis unavailable: {reason}"],
            transcript_confidence=0.0,
            analysis_details={"error": reason}
        )

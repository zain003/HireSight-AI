# FEAT-005-BE: Vocal Acoustic & Speech Pattern Analysis Engine — P0

## Layer
Backend

## Goal
Implement a resilient acoustic feature extractor using Librosa and OpenSMILE to compute conversational speech rate (WPM), pause duration ratio, F0 pitch semitone variance, and vocal energy stability.

## Depends on
`000-shared-contracts.md`

## Context pack
```python
class ObservableVocalMetrics(BaseModel):
    speaking_rate_wpm: float
    pause_duration_ratio: float
    pitch_semitone_variance: float
    vocal_energy_rms: float
    speech_clarity_score: float
    acoustic_flags: List[str]
```

## Provides / Exposes
```python
async def analyze_audio_stream(
    audio_base64: Optional[str],
    transcript_text: Optional[str],
    audio_format: str = "webm"
) -> ObservableVocalMetrics: ...
```

## Scope (In)
- In-memory audio transcode supporting WebM, WAV, and MP3 using `soundfile` and `librosa`.
- Words-per-minute (WPM) calculation normalized against conversational baseline (120–160 WPM).
- Silence/pause detector computing pause duration ratio (`total_pause_time / total_audio_duration`).
- F0 fundamental frequency extraction using Librosa pyin algorithm with semitone conversion.
- Fallback to pure Librosa/NumPy feature extraction if OpenSMILE native binary is missing.

## Scope (Out)
- LLM answer grading (covered in `FEAT-007-BE`).
- Frontend WebRTC audio recorder (covered in `FEAT-003-FE`).

## Tech / files to touch
- `backend/app/interview/services/vocal_analysis.py` [MODIFY]
- `backend/app/interview/services/stt_service.py` [MODIFY]

## Tests to write FIRST
- `test_audio_conversion_synthetic_wav`: Convert synthetic WAV bytes and verify sample rate is 16kHz mono.
- `test_speech_rate_calculation`: 150 words in 60 seconds returns exactly 150.0 WPM.
- `test_pause_ratio_silent_audio`: 3 seconds of audio with 1.5 seconds silence returns 0.50 pause ratio.
- `test_graceful_fallback_without_opensmile`: Disabling OpenSMILE extractor still computes all Librosa acoustic metrics.

## Implementation steps
1. Refactor `_convert_to_wav` in `vocal_analysis.py` with in-memory buffer handling and fallback decoder.
2. Implement `_calculate_wpm(transcript, duration_sec)` and `_calculate_pause_ratio(wav_data, sr)`.
3. Enhance pitch extraction with `librosa.pyin` converting Hertz to semitones relative to A440.
4. Update `analyze_audio` to return `ObservableVocalMetrics` with clean error flags.

## Acceptance criteria
- WPM correctly calculates from transcript word count and active audio duration.
- Audio conversion cleanly decodes WebM Opus audio payloads without disk corruption.
- OpenSMILE absence falls back to Librosa pipeline without raising uncaught exceptions.

## Definition of Done
- Unit tests for acoustic extraction pass 100%.
- Audio analysis takes < 250ms for a 30-second audio clip.
- Strict Pydantic typing and zero leftover debug prints.

## Edge cases to handle
- Empty/silent audio buffer → returns 0.0 WPM and `["Empty or silent audio clip"]` flag.
- Extreme background noise → filters high-frequency noise floor before pitch calculation.

## Pre-flight check
- Confirm `000-shared-contracts.md` is approved.

## What's next
- `FEAT-005-VERIFY-vocal-engine.md`
- `FEAT-006-BE-coding-sandbox-hidden-tests.md`

## Ambiguity Resolution Protocol
1. Do NOT silently guess.
2. Log assumption in `specs/DEVIATIONS.md` as: `[FEAT-005-BE] — [ambiguity] — [assumption]`.
3. Stop and flag if data models in `000-shared-contracts.md` require modification.

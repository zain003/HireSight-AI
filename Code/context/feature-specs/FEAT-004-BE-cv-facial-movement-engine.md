# FEAT-004-BE: Observable Computer Vision & Facial Movement Engine — P0

## Layer
Backend

## Goal
Implement a robust, resolution-independent Computer Vision engine using MediaPipe Face Mesh (468 landmarks) to compute normalized eye gaze, 3D head pose stability via `solvePnP`, and observable facial movement dynamics without unsupported psychological claims.

## Depends on
`000-shared-contracts.md`

## Context pack
```python
class ObservableCVMetrics(BaseModel):
    gaze_stability_ratio: float
    head_pose_variance: float
    facial_movement_dynamics: float
    frame_presence_ratio: float
    blink_frequency_cpm: float
    observable_flags: List[str]
```

## Provides / Exposes
```python
def analyze_video_frames(
    frame_base64_list: List[str],
    fps: float = 10.0
) -> ObservableCVMetrics: ...
```

## Scope (In)
- Resolution-independent eye gaze normalization using iris offset divided by inter-ocular eye distance.
- 3D head pose estimation using OpenCV `cv2.solvePnP` with canonical 3D facial model points (nose tip, chin, eye corners, mouth corners).
- Facial movement dynamics computed from eyelid aspect ratio (EAR) for blink rate and lip/eyebrow velocity.
- Strict output of physical observable metrics only; zero pseudoscientific emotion labels.

## Scope (Out)
- Browser camera capture hooks (covered in `FEAT-003-FE`).
- Vocal audio extraction (covered in `FEAT-005-BE`).

## Tech / files to touch
- `backend/app/interview/services/behavioral_analysis.py` [MODIFY]
- `backend/app/interview/domain/interview_models.py` [MODIFY]

## Tests to write FIRST
- `test_gaze_normalization_resolution_invariance`: Assert same relative gaze on 480p and 1080p images yields identical gaze score (±1%).
- `test_solvepnp_head_pose_angles`: Assert frontal face returns pitch, yaw, roll within ±5 degrees of zero.
- `test_empty_frames_returns_graceful_defaults`: Empty frame list returns 0.0 scores with `"No frames provided"` flag without throwing exceptions.

## Implementation steps
1. Refactor `BehavioralAnalysisService._analyze_eye_contact` to divide iris distance by eye-corner distance `dist(p33, p263)`.
2. Replace heuristic 2D head pose with `cv2.solvePnP` using 3D model vertices for indices `[1, 152, 33, 263, 61, 291]`.
3. Implement Eye Aspect Ratio (EAR) blink detector calculating blinks per minute based on temporal frame sequences.
4. Update `analyze_frames` to return `ObservableCVMetrics` with strictly physical measurements.

## Acceptance criteria
- Gaze detection produces identical score when frame is resized from 1920x1080 to 640x360.
- Head pose pitch/yaw/roll output matches `solvePnP` Euler angle decomposition.
- Zero psychological or emotion labels returned in output schema.

## Definition of Done
- Unit tests for resolution invariance and head pose pass 100%.
- OpenCV/MediaPipe execution benchmarked at < 15ms per frame on CPU.
- Zero lint/typecheck errors.

## Edge cases to handle
- Candidate wears glasses or shifts out of frame → detects `frame_presence_ratio < 1.0` gracefully.
- Low-light or blurred frame → catches MediaPipe `None` landmark gracefully.

## Pre-flight check
- Confirm `000-shared-contracts.md` is approved.

## What's next
- `FEAT-004-VERIFY-cv-engine.md`
- `FEAT-005-BE-vocal-acoustic-speech-engine.md`

## Ambiguity Resolution Protocol
1. Do NOT silently guess.
2. Log assumption in `specs/DEVIATIONS.md` as: `[FEAT-004-BE] — [ambiguity] — [assumption]`.
3. Stop and flag if data models in `000-shared-contracts.md` require modification.

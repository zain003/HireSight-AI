"""Face analysis service using OpenCV, MediaPipe, DeepFace, and dlib."""

from __future__ import annotations

import asyncio
import base64
import os
from typing import Dict, List, Optional

import numpy as np

from app.interview.domain.interview_models import EmotionLabel, FrameAnalysisResult

_face_embeddings: Dict[str, np.ndarray] = {}
_verification_threshold = 0.40


def _get_face_embedding(image_bytes: bytes) -> Optional[np.ndarray]:
    try:
        import cv2
        from deepface import DeepFace

        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return None

        try:
            embedding_objs = DeepFace.represent(
                img_path=frame,
                model_name="Facenet",
                enforce_detection=True,
                detector_backend="opencv",
                anti_spoofing=True,
            )
        except TypeError:
            embedding_objs = DeepFace.represent(
                img_path=frame,
                model_name="Facenet",
                enforce_detection=True,
                detector_backend="opencv",
            )

        if embedding_objs:
            first_face = embedding_objs[0]
            if "is_real" in first_face and not first_face["is_real"]:
                print("[FaceEmbedding] Spoof detected: face is not real")
                return None
            return np.array(first_face["embedding"])

        return None
    except Exception as exc:
        print(f"[FaceEmbedding] Failed: {exc}")
        return None


def register_face(image_bytes: bytes, candidate_id: str) -> bool:
    embedding = _get_face_embedding(image_bytes)
    if embedding is not None:
        _face_embeddings[candidate_id] = embedding
        return True
    return False


def verify_face_embedding(image_bytes: bytes, candidate_id: str) -> Dict:
    stored_embedding = _face_embeddings.get(candidate_id)
    if stored_embedding is None:
        return {
            "verified": False,
            "alert": True,
            "distance": 1.0,
            "threshold": _verification_threshold,
            "message": "No registered face found for this candidate",
        }

    current_embedding = _get_face_embedding(image_bytes)
    if current_embedding is None:
        return {
            "verified": False,
            "alert": True,
            "distance": 1.0,
            "threshold": _verification_threshold,
            "message": "No face detected in current image",
        }

    cosine_distance = 1 - np.dot(stored_embedding, current_embedding) / (
        np.linalg.norm(stored_embedding) * np.linalg.norm(current_embedding)
    )

    verified = cosine_distance < _verification_threshold
    return {
        "verified": verified,
        "alert": not verified,
        "distance": float(cosine_distance),
        "threshold": _verification_threshold,
        "message": "Face verified successfully" if verified else "Face does not match registered face",
    }


def clear_face_registration(candidate_id: str) -> bool:
    if candidate_id in _face_embeddings:
        del _face_embeddings[candidate_id]
        return True
    return False


def _decode_frame(frame_b64: str) -> Optional[np.ndarray]:
    try:
        import cv2

        data = base64.b64decode(frame_b64)
        arr = np.frombuffer(data, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:
        return None


def _face_check(frames: List[np.ndarray]) -> dict:
    try:
        import cv2

        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        no_face = multi_face = 0
        sampled = frames[::2]
        for frame in sampled:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(gray, 1.1, 4, minSize=(60, 60))
            if len(faces) == 0:
                no_face += 1
            elif len(faces) > 1:
                multi_face += 1

        total = max(len(sampled), 1)
        return {
            "face_detected": no_face / total < 0.35,
            "no_face_ratio": round(no_face / total, 2),
            "multiple_faces_detected": multi_face > 0,
        }
    except Exception as exc:
        print(f"[FaceCheck] {exc}")
        return {
            "face_detected": True,
            "no_face_ratio": 0.0,
            "multiple_faces_detected": False,
        }


EMOTION_MAP = {
    "happy": EmotionLabel.CONFIDENT,
    "neutral": EmotionLabel.NEUTRAL,
    "surprise": EmotionLabel.ENGAGED,
    "fear": EmotionLabel.NERVOUS,
    "sad": EmotionLabel.NERVOUS,
    "angry": EmotionLabel.SUSPICIOUS,
    "disgust": EmotionLabel.SUSPICIOUS,
}


def _emotion_analysis(frames: List[np.ndarray]) -> dict:
    try:
        from deepface import DeepFace

        tallies: Dict[str, float] = {}
        count = 0
        for frame in frames[::3]:
            try:
                res = DeepFace.analyze(
                    frame, actions=["emotion"], enforce_detection=False, silent=True
                )
                if isinstance(res, list):
                    res = res[0]
                for emo, score in res.get("emotion", {}).items():
                    tallies[emo] = tallies.get(emo, 0) + float(score)
                count += 1
            except Exception:
                continue

        if not count:
            return {"dominant_emotion": EmotionLabel.NEUTRAL, "scores": {}}

        avg = {k: v / count for k, v in tallies.items()}
        top = max(avg, key=avg.get)
        return {
            "dominant_emotion": EMOTION_MAP.get(top, EmotionLabel.NEUTRAL),
            "scores": avg,
        }
    except ImportError:
        print("[Emotion] Install deepface and tf-keras")
        return {"dominant_emotion": EmotionLabel.NEUTRAL, "scores": {}}
    except Exception as exc:
        print(f"[Emotion] {exc}")
        return {"dominant_emotion": EmotionLabel.NEUTRAL, "scores": {}}


def _gaze_estimate(frames: List[np.ndarray]) -> dict:
    try:
        import cv2
        import mediapipe as mp

        mp_fm = mp.solutions.face_mesh
        face_mesh = mp_fm.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
        )

        away = total = 0
        dirs = {"center": 0, "left": 0, "right": 0, "up": 0, "down": 0}
        for frame in frames[::3]:
            try:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = face_mesh.process(rgb)
                total += 1
                if not result.multi_face_landmarks:
                    away += 1
                    continue

                lm = result.multi_face_landmarks[0].landmark
                nose = lm[1]
                left_eye_center = lm[468]
                right_eye_center = lm[473]

                eye_center_x = (left_eye_center.x + right_eye_center.x) / 2
                dx = nose.x - eye_center_x

                eye_center_y = (left_eye_center.y + right_eye_center.y) / 2
                dy = nose.y - eye_center_y

                if abs(dx) > 0.035:
                    d = "left" if dx < 0 else "right"
                    away += 1
                elif dy < -0.035:
                    d = "up"
                    away += 1
                elif dy > 0.12:
                    d = "down"
                else:
                    d = "center"

                dirs[d] = dirs.get(d, 0) + 1
            except Exception:
                continue

        face_mesh.close()
        return {
            "gaze_direction": max(dirs, key=dirs.get),
            "looking_away_ratio": round(away / max(total, 1), 2),
        }
    except ImportError:
        print("[Gaze] Install mediapipe")
        return {"gaze_direction": "center", "looking_away_ratio": 0.0}
    except Exception as exc:
        print(f"[Gaze] {exc}")
        return {"gaze_direction": "center", "looking_away_ratio": 0.0}


def _count_blinks(frames: List[np.ndarray]) -> int:
    try:
        import cv2
        import dlib

        model_path = os.getenv(
            "DLIB_MODEL_PATH", "models/shape_predictor_68_face_landmarks.dat"
        )
        if not os.path.exists(model_path):
            return -1

        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(model_path)

        left = list(range(36, 42))
        right = list(range(42, 48))

        def ear(pts):
            def d(a, b):
                return np.linalg.norm(np.array(a) - np.array(b))

            a = d(pts[1], pts[5])
            b = d(pts[2], pts[4])
            c = d(pts[0], pts[3])
            return (a + b) / (2.0 * c) if c > 0 else 0.0

        blinks = 0
        closed = False
        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray, 0)
            if not faces:
                continue

            shape = predictor(gray, faces[0])
            pts = [(shape.part(i).x, shape.part(i).y) for i in range(68)]
            avg = (ear([pts[i] for i in left]) + ear([pts[i] for i in right])) / 2
            if avg < 0.25:
                if not closed:
                    blinks += 1
                    closed = True
            else:
                closed = False

        return blinks
    except ImportError:
        return -1
    except Exception:
        return -1


async def verify_face_frame(frame_base64: str) -> Dict:
    try:
        import cv2

        frame = _decode_frame(frame_base64)
        if frame is None:
            return {
                "face_detected": False,
                "multiple_faces": False,
                "confidence": 0.0,
                "message": "Could not decode frame",
            }

        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.1, 4, minSize=(60, 60))
        count = len(faces)

        if count == 0:
            return {
                "face_detected": False,
                "multiple_faces": False,
                "confidence": 0.0,
                "message": "No face detected",
            }
        if count > 1:
            return {
                "face_detected": True,
                "multiple_faces": True,
                "confidence": 1.0,
                "message": f"{count} faces detected",
            }

        return {
            "face_detected": True,
            "multiple_faces": False,
            "confidence": 1.0,
            "message": "OK",
        }
    except Exception as exc:
        return {
            "face_detected": False,
            "multiple_faces": False,
            "confidence": 0.0,
            "message": str(exc),
        }


async def analyze_emotions(frame_base64_list: List[str]) -> Dict:
    if not frame_base64_list:
        return {"dominant_emotion": "neutral", "emotions": {}, "frame_count": 0}

    loop = asyncio.get_event_loop()
    frames = [_decode_frame(f) for f in frame_base64_list]
    frames = [f for f in frames if f is not None]
    if not frames:
        return {"dominant_emotion": "neutral", "emotions": {}, "frame_count": 0}

    result = await loop.run_in_executor(None, _emotion_analysis, frames)
    dom = result.get("dominant_emotion", EmotionLabel.NEUTRAL)
    return {
        "dominant_emotion": dom.value if hasattr(dom, "value") else str(dom),
        "emotions": result.get("scores", {}),
        "frame_count": len(frames),
    }


async def _analyze_frames_full(frame_b64_list: List[str]) -> FrameAnalysisResult:
    if not frame_b64_list:
        return FrameAnalysisResult()

    loop = asyncio.get_event_loop()
    frames = [_decode_frame(f) for f in frame_b64_list]
    frames = [f for f in frames if f is not None]
    if not frames:
        return FrameAnalysisResult(face_detected=False)

    face_r, emo_r, gaze_r, blinks = await asyncio.gather(
        loop.run_in_executor(None, _face_check, frames),
        loop.run_in_executor(None, _emotion_analysis, frames),
        loop.run_in_executor(None, _gaze_estimate, frames),
        loop.run_in_executor(None, _count_blinks, frames),
    )

    flags = []
    if not face_r["face_detected"]:
        flags.append("Face not visible for extended period")
    if face_r.get("multiple_faces_detected"):
        flags.append("Multiple faces detected - possible assistance")
    if gaze_r["looking_away_ratio"] > 0.4:
        flags.append(f"Looking away {gaze_r['looking_away_ratio']:.0%} of the time")
    if blinks > 45:
        flags.append(f"High blink rate ({blinks} blinks)")
    if emo_r["dominant_emotion"] == EmotionLabel.SUSPICIOUS:
        flags.append("Suspicious facial expressions detected")

    return FrameAnalysisResult(
        blink_count=max(blinks, 0),
        gaze_direction=gaze_r["gaze_direction"],
        dominant_emotion=emo_r["dominant_emotion"],
        face_detected=face_r["face_detected"],
        looking_away_ratio=gaze_r["looking_away_ratio"],
        suspicious_flags=flags,
    )


class FaceService:
    """Full face analysis service for the interview module."""

    def register_face(self, image_bytes: bytes, candidate_id: str) -> bool:
        return register_face(image_bytes, candidate_id)

    def verify_face(self, image_bytes: bytes, candidate_id: str) -> Dict:
        return verify_face_embedding(image_bytes, candidate_id)

    async def analyze(self, frame_base64_list: List[str]) -> FrameAnalysisResult:
        return await _analyze_frames_full(frame_base64_list)

    async def verify_frame(self, frame_base64: str) -> Dict:
        return await verify_face_frame(frame_base64)

    async def emotions(self, frame_base64_list: List[str]) -> Dict:
        return await analyze_emotions(frame_base64_list)

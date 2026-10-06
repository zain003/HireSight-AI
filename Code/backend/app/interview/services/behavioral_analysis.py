"""
Observable Computer Vision & Facial Movement Engine using MediaPipe & OpenCV.
Computes resolution-independent eye gaze normalization, solvePnP 3D head pose estimation,
and physical facial movement dynamics (EAR blinks and micro-movements) with zero psychological claims.
"""
import base64
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf")
warnings.filterwarnings("ignore", message=".*SymbolDatabase.GetPrototype.*")

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import mediapipe as mp
except ImportError:
    mp = None

from app.interview.domain.interview_models import ObservableCVMetrics


@dataclass
class BehavioralMetrics:
    """Legacy and enhanced behavioral analysis metrics from video frames."""
    eye_contact_score: float  # 0-100 (maps to gaze_stability_ratio)
    head_stability_score: float  # 0-100 (maps to head_pose_variance)
    facial_engagement_score: float  # 0-100 (maps to facial_movement_dynamics)
    fidgeting_score: float  # 0-100 (inverse of rapid head/posture variance)
    confidence_posture_score: float  # 0-100 (head stability & upright posture)
    attention_span_score: float  # 0-100 (maps to frame_presence_ratio)
    red_flags: List[str]  # Observable physical flags
    frame_count: int
    analysis_details: Dict[str, Any] = field(default_factory=dict)
    observable_cv_metrics: Optional[ObservableCVMetrics] = None


class BehavioralAnalysisService:
    """
    Observable Computer Vision Engine.
    Tracks normalized eye gaze, 3D head pose stability via solvePnP,
    eyelid aspect ratio (EAR) blink rate, and facial movement dynamics.
    """

    # Canonical 3D facial model points (in mm, centered at nose tip)
    MODEL_POINTS_3D = np.array([
        [0.0, 0.0, 0.0],          # 1: Nose tip
        [0.0, -330.0, -65.0],     # 152: Chin
        [-225.0, 170.0, -135.0],  # 33: Left eye outer corner
        [225.0, 170.0, -135.0],   # 263: Right eye outer corner
        [-150.0, -150.0, -125.0], # 61: Left mouth corner
        [150.0, -150.0, -125.0],  # 291: Right mouth corner
    ], dtype=np.float64)

    def __init__(self):
        if mp is not None:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.mp_face_detection = mp.solutions.face_detection
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.25,
                min_tracking_confidence=0.25
            )
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=0,  # 0 = short range frontal webcam (< 2m)
                min_detection_confidence=0.25
            )
            print("[BehavioralAnalysisService] Initialized MediaPipe FaceMesh & OpenCV successfully.")
        else:
            self.mp_face_mesh = None
            self.mp_face_detection = None
            self.face_mesh = None
            self.face_detection = None
            print("[BehavioralAnalysisService] CRITICAL WARNING: OpenCV/MediaPipe not found! Please run with backend/.venv")

        # Landmark indices for specific facial features
        self.LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
        self.LEFT_IRIS_INDICES = [468, 469, 470, 471, 472]
        self.RIGHT_IRIS_INDICES = [473, 474, 475, 476, 477]
        self.NOSE_TIP_INDEX = 1
        self.CHIN_INDEX = 152
        self.LEFT_EYE_CORNER = 33
        self.RIGHT_EYE_CORNER = 263
        self.LEFT_MOUTH_CORNER = 61
        self.RIGHT_MOUTH_CORNER = 291
        self.DYNAMIC_LANDMARK_INDICES = [
            70, 63, 105, 66, 107, 336, 296, 334, 293, 300,  # Eyebrows
            61, 291, 0, 17, 13, 14, 78, 308,                # Mouth contours
            33, 133, 362, 263                               # Eye corners
        ]

    def analyze_video_frames(
        self,
        frame_base64_list: List[str],
        fps: float = 10.0,
        is_coding_phase: bool = False,
        is_actively_typing: bool = False,
        telemetry_events: Optional[List[Dict[str, Any]]] = None,
    ) -> ObservableCVMetrics:
        """
        Analyze a temporal sequence of video frames and return physical ObservableCVMetrics.
        
        Args:
            frame_base64_list: List of base64-encoded image frames.
            fps: Video sampling rate in frames per second (default 10.0).
            is_coding_phase: Whether the current assessment stage is coding/IDE.
            is_actively_typing: Whether user was actively typing or interacting with keyboard.
            telemetry_events: Optional client-side proctoring telemetry events.
            
        Returns:
            ObservableCVMetrics schema compliant with 000-shared-contracts.md.
        """
        if not frame_base64_list:
            return self._create_empty_observable_metrics()

        total_frames = len(frame_base64_list)
        frames_with_face = 0
        gaze_scores = []
        center_gaze_count = 0
        eye_occluded_count = 0
        head_poses = []
        ear_values = []
        movement_velocities = []
        multiple_faces_detected = False

        previous_landmarks = None
        previous_pose = None
        rapid_rotation_detected = False

        frame_gaze_data = []  # List of tuples: (gaze_dir, is_center, score, is_occluded)
        gaze_dir_counts = {
            "center": 0,
            "keyboard": 0,
            "down_no_typing": 0,
            "left": 0,
            "right": 0,
            "up": 0,
            "far_deviation": 0,
            "eyes_hidden": 0,
            "away": 0,
        }

        for frame_b64 in frame_base64_list:
            try:
                frame_data = base64.b64decode(frame_b64)
                nparr = np.frombuffer(frame_data, np.uint8)
                if cv2 is not None:
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                else:
                    frame = None

                if frame is None:
                    continue

                h, w, _ = frame.shape
                if cv2 is not None:
                    # Adaptive contrast enhancement for low-contrast/dark frames
                    gray_mean = np.mean(frame)
                    if gray_mean < 80.0:
                        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                        l_channel, a_channel, b_channel = cv2.split(lab)
                        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                        enhanced_l = clahe.apply(l_channel)
                        enhanced_lab = cv2.merge((enhanced_l, a_channel, b_channel))
                        enhanced_frame = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
                        rgb_frame = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2RGB)
                    else:
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                else:
                    rgb_frame = frame

                # Face mesh extraction
                if self.face_mesh is None:
                    continue

                mesh_results = self.face_mesh.process(rgb_frame)
                if not mesh_results or not mesh_results.multi_face_landmarks:
                    # If enhanced RGB failed, try original frame
                    if cv2 is not None:
                        orig_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        mesh_results = self.face_mesh.process(orig_rgb)
                    if not mesh_results or not mesh_results.multi_face_landmarks:
                        # Check FaceDetection model
                        if self.face_detection is not None:
                            det_res = self.face_detection.process(rgb_frame)
                            if det_res and det_res.detections:
                                if len(det_res.detections) > 1:
                                    multiple_faces_detected = True
                                frames_with_face += 1
                                # Face detected without mesh landmarks in eye region -> Possible hands/eyes occlusion
                                is_occ = True
                                eye_occluded_count += 1
                                gaze_scores.append(0.0)
                                head_poses.append({"pitch": 0.0, "yaw": 0.0, "roll": 0.0})
                                ear_values.append(0.0)
                                frame_gaze_data.append(("eyes_hidden", False, 0.0, True))
                                gaze_dir_counts["eyes_hidden"] += 1
                                continue
                        frame_gaze_data.append(("away", False, 0.0, False))
                        gaze_dir_counts["away"] += 1
                        continue

                landmarks = mesh_results.multi_face_landmarks[0]
                if len(mesh_results.multi_face_landmarks) > 1:
                    multiple_faces_detected = True

                frames_with_face += 1

                # 1. 3D Head pose via solvePnP
                pose = self._estimate_head_pose_pnp(landmarks, w, h)
                head_poses.append(pose)
                if previous_pose is not None:
                    delta_angle = max(
                        abs(pose["pitch"] - previous_pose["pitch"]),
                        abs(pose["yaw"] - previous_pose["yaw"]),
                        abs(pose["roll"] - previous_pose["roll"]),
                    )
                    if delta_angle > 45.0:
                        rapid_rotation_detected = True
                previous_pose = pose

                # 2. Eye Occlusion Detection
                is_occluded, occ_type = self._detect_eye_occlusion(landmarks, frame, w, h)
                if is_occluded:
                    eye_occluded_count += 1

                # 3. Gaze Direction Classification & Keyboard Exception
                gaze_dir, is_center, gaze_score = self._classify_gaze_direction(
                    landmarks=landmarks,
                    pose=pose,
                    w=w,
                    h=h,
                    is_occluded=is_occluded,
                    is_actively_typing=is_actively_typing,
                    is_coding_phase=is_coding_phase,
                )

                gaze_scores.append(gaze_score)
                if is_center:
                    center_gaze_count += 1

                frame_gaze_data.append((gaze_dir, is_center, gaze_score, is_occluded))

                if gaze_dir.startswith("far_"):
                    gaze_dir_counts["far_deviation"] += 1
                elif gaze_dir in gaze_dir_counts:
                    gaze_dir_counts[gaze_dir] += 1
                else:
                    gaze_dir_counts["away"] += 1

                # 4. Eye Aspect Ratio (EAR) for blink detection
                ear = self._calculate_ear(landmarks, w, h)
                ear_values.append(ear)

                # 5. Facial movement dynamics
                if previous_landmarks is not None:
                    vel = self._calculate_movement_dynamics(landmarks, previous_landmarks, w, h)
                    movement_velocities.append(vel)
                previous_landmarks = landmarks

            except Exception as e:
                print(f"Error in frame processing: {e}")
                continue

        if frames_with_face == 0:
            return self._create_empty_observable_metrics(total_frames)

        # 1. Gaze Stability Ratio: Percentage of face frames looking toward center / allowed keyboard
        gaze_stability_ratio = (center_gaze_count / frames_with_face) * 100.0
        eye_occlusion_ratio = (eye_occluded_count / max(1, total_frames)) * 100.0

        # 2. Head Pose Variance: Inverse of angular variance across frames
        if len(head_poses) >= 2:
            pitches = [p["pitch"] for p in head_poses]
            yaws = [p["yaw"] for p in head_poses]
            rolls = [p["roll"] for p in head_poses]
            total_var = float(np.var(pitches) + np.var(yaws) + np.var(rolls))
            head_pose_variance = max(0.0, min(100.0, 100.0 - (total_var * 0.40)))
        else:
            head_pose_variance = 100.0

        # 3. Blink Frequency (CPM) from EAR transitions
        blink_count = self._count_blinks_from_ear(ear_values)
        duration_sec = total_frames / max(1.0, fps)
        blink_frequency_cpm = (blink_count / duration_sec) * 60.0 if duration_sec > 0 else 0.0

        # 4. Facial Movement Dynamics
        if movement_velocities:
            mean_vel = float(np.mean(movement_velocities))
            facial_movement_dynamics = max(0.0, min(100.0, mean_vel * 1200.0))
        else:
            facial_movement_dynamics = 50.0  # Baseline neutral

        # 5. Frame presence ratio
        frame_presence_ratio = (frames_with_face / total_frames) * 100.0

        # 6. Temporal Event Analysis & Deduplication (Single continuous events with duration)
        gaze_events = []
        current_event = None

        for idx, (gaze_dir, is_c, score, is_occ) in enumerate(frame_gaze_data):
            if current_event is None:
                current_event = {"type": gaze_dir, "start_idx": idx, "count": 1, "is_occluded": is_occ}
            elif current_event["type"] == gaze_dir:
                current_event["count"] += 1
            else:
                current_event["duration_sec"] = current_event["count"] / max(1.0, fps)
                gaze_events.append(current_event)
                current_event = {"type": gaze_dir, "start_idx": idx, "count": 1, "is_occluded": is_occ}

        if current_event is not None:
            current_event["duration_sec"] = current_event["count"] / max(1.0, fps)
            gaze_events.append(current_event)

        # Evaluate event-level criteria
        eye_occlusion_events = sum(1 for e in gaze_events if e["type"] == "eyes_hidden" and e["duration_sec"] >= 0.8)
        prolonged_occlusion_events = sum(1 for e in gaze_events if e["type"] == "eyes_hidden" and e["duration_sec"] >= 2.5)
        downward_no_typing_events = sum(1 for e in gaze_events if e["type"] == "down_no_typing" and e["duration_sec"] >= 1.8)
        sustained_gaze_events = sum(1 for e in gaze_events if e["type"] in ("left", "right", "up", "away") and e["duration_sec"] >= 1.8)
        far_gaze_events = sum(1 for e in gaze_events if e["type"].startswith("far_") and e["duration_sec"] >= 1.2)
        distinct_deviation_events = sum(
            1 for e in gaze_events
            if e["type"] not in ("center", "keyboard") and e["duration_sec"] >= 1.0
        )

        # Gaze distribution breakdown
        gaze_breakdown = {
            k: round((v / max(1, len(frame_gaze_data))) * 100.0, 1)
            for k, v in gaze_dir_counts.items()
        }

        # Observable physical flags
        observable_flags = self._generate_observable_flags(
            gaze_stability_ratio=gaze_stability_ratio,
            head_pose_variance=head_pose_variance,
            frame_presence_ratio=frame_presence_ratio,
            blink_frequency_cpm=blink_frequency_cpm,
            facial_movement_dynamics=facial_movement_dynamics,
            rapid_rotation_detected=rapid_rotation_detected,
            duration_sec=duration_sec,
            eye_occlusion_ratio=eye_occlusion_ratio,
            eye_occlusion_events=eye_occlusion_events,
            prolonged_occlusion_events=prolonged_occlusion_events,
            downward_no_typing_events=downward_no_typing_events,
            sustained_gaze_events=sustained_gaze_events,
            far_gaze_events=far_gaze_events,
            distinct_deviation_events=distinct_deviation_events,
            multiple_faces_detected=multiple_faces_detected,
        )

        return ObservableCVMetrics(
            gaze_stability_ratio=round(gaze_stability_ratio, 2),
            head_pose_variance=round(head_pose_variance, 2),
            facial_movement_dynamics=round(facial_movement_dynamics, 2),
            frame_presence_ratio=round(frame_presence_ratio, 2),
            blink_frequency_cpm=round(blink_frequency_cpm, 2),
            observable_flags=observable_flags,
            eye_occlusion_ratio=round(eye_occlusion_ratio, 2),
            gaze_breakdown=gaze_breakdown,
        )

    def analyze_frames(
        self,
        frame_base64_list: List[str],
        fps: float = 10.0,
        is_coding_phase: bool = False,
        is_actively_typing: bool = False,
    ) -> BehavioralMetrics:
        """
        Backward-compatible method returning BehavioralMetrics with embedded ObservableCVMetrics.
        """
        cv_metrics = self.analyze_video_frames(
            frame_base64_list=frame_base64_list,
            fps=fps,
            is_coding_phase=is_coding_phase,
            is_actively_typing=is_actively_typing,
        )

        return BehavioralMetrics(
            eye_contact_score=cv_metrics.gaze_stability_ratio,
            head_stability_score=cv_metrics.head_pose_variance,
            facial_engagement_score=cv_metrics.facial_movement_dynamics,
            fidgeting_score=cv_metrics.head_pose_variance,
            confidence_posture_score=cv_metrics.head_pose_variance,
            attention_span_score=cv_metrics.frame_presence_ratio,
            red_flags=cv_metrics.observable_flags,
            frame_count=len(frame_base64_list),
            analysis_details={
                "gaze_stability_ratio": cv_metrics.gaze_stability_ratio,
                "head_pose_variance": cv_metrics.head_pose_variance,
                "facial_movement_dynamics": cv_metrics.facial_movement_dynamics,
                "frame_presence_ratio": cv_metrics.frame_presence_ratio,
                "blink_frequency_cpm": cv_metrics.blink_frequency_cpm,
                "eye_occlusion_ratio": cv_metrics.eye_occlusion_ratio,
                "gaze_breakdown": cv_metrics.gaze_breakdown,
            },
            observable_cv_metrics=cv_metrics,
        )

    def analyze_single_frame(
        self,
        frame_b64: str,
        is_coding_phase: bool = False,
        is_actively_typing: bool = False,
    ) -> Dict[str, Any]:
        """Real-time single frame gaze and occlusion analysis for frontend HUD using MediaPipe."""
        if not frame_b64 or self.face_mesh is None:
            return {"detected": False, "is_centered": False, "gaze": "away", "is_occluded": False, "presence": 0}

        try:
            if "," in frame_b64:
                frame_b64 = frame_b64.split(",", 1)[1]
            frame_data = base64.b64decode(frame_b64)
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR) if cv2 is not None else None
            if frame is None:
                return {"detected": False, "is_centered": False, "gaze": "away", "is_occluded": False, "presence": 0}

            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            mesh_results = self.face_mesh.process(rgb_frame)
            if not mesh_results or not mesh_results.multi_face_landmarks:
                # Check FaceDetection model to distinguish 90-deg head turn vs hands over eyes vs no face
                if self.face_detection is not None:
                    det_res = self.face_detection.process(rgb_frame)
                    if det_res and det_res.detections:
                        d = det_res.detections[0]
                        kps = d.location_data.relative_keypoints
                        right_eye, left_eye, nose = kps[0], kps[1], kps[2]
                        # 90-degree profile turn: nose tip is outside both eye bounds
                        if nose.x < min(right_eye.x, left_eye.x) or nose.x > max(right_eye.x, left_eye.x):
                            yaw_val = 75.0 if nose.x > max(right_eye.x, left_eye.x) else -75.0
                            return {
                                "detected": True,
                                "is_centered": False,
                                "gaze": "turned_side",
                                "is_occluded": False,
                                "presence": 100,
                                "score": 25.0,
                                "head_pose": {"pitch": 0.0, "yaw": yaw_val, "roll": 0.0},
                            }
                        else:
                            # Face present facing camera, but eye mesh failed -> Hands/object covering eyes
                            return {
                                "detected": True,
                                "is_centered": False,
                                "gaze": "eyes_hidden",
                                "is_occluded": True,
                                "presence": 100,
                                "score": 0.0,
                                "head_pose": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                            }
                return {"detected": False, "is_centered": False, "gaze": "away", "is_occluded": False, "presence": 0}

            landmarks = mesh_results.multi_face_landmarks[0]
            pose = self._estimate_head_pose_pnp(landmarks, w, h)
            is_occluded, occ_type = self._detect_eye_occlusion(landmarks, frame, w, h)
            ear_val = self._calculate_ear(landmarks, w, h)
            if ear_val < 0.16:
                is_occluded = True

            gaze_dir, is_center, score = self._classify_gaze_direction(
                landmarks=landmarks,
                pose=pose,
                w=w,
                h=h,
                is_occluded=is_occluded,
                is_actively_typing=is_actively_typing,
                is_coding_phase=is_coding_phase,
            )

            # If head is turned sharply to side (yaw >= 42 degrees or far sideways profile):
            if abs(pose.get("yaw", 0.0)) >= 42.0 or gaze_dir in ("far_left", "far_right"):
                gaze_dir = "turned_side"
                is_center = False

            if is_occluded:
                gaze_dir = "eyes_hidden"
                is_center = False

            return {
                "detected": True,
                "is_centered": is_center,
                "gaze": gaze_dir,
                "is_occluded": is_occluded,
                "head_pose": pose,
                "presence": 100,
                "score": score,
                "ear": ear_val,
            }
        except Exception as e:
            return {"detected": False, "is_centered": False, "gaze": "away", "is_occluded": False, "presence": 0}

    def _detect_eye_occlusion(
        self,
        landmarks: Any,
        frame: Optional[np.ndarray],
        w: int,
        h: int,
    ) -> Tuple[bool, str]:
        """
        Detects whether user is actively occluding/covering their eyes with hands, objects, or has closed eyes.
        
        Returns:
            Tuple of (is_occluded: bool, occlusion_type: str)
        """
        try:
            p33 = self._get_landmark_point(landmarks, self.LEFT_EYE_CORNER, w, h)
            p263 = self._get_landmark_point(landmarks, self.RIGHT_EYE_CORNER, w, h)
            iod = float(np.linalg.norm(p263 - p33))

            if iod < 1e-4:
                return True, "landmark_collapse"

            # Check bounds
            if not (0 <= p33[0] <= w and 0 <= p33[1] <= h and 0 <= p263[0] <= w and 0 <= p263[1] <= h):
                return True, "out_of_bounds"

            ear_val = self._calculate_ear(landmarks, w, h)
            if frame is not None:
                if ear_val < 0.16:
                    return True, "eyes_closed_or_covered"
            else:
                if ear_val < 0.03:
                    return True, "eyes_covered"

            # Image patch contrast analysis (when frame is available)
            if frame is not None and cv2 is not None:
                left_pts = np.array([self._get_landmark_point(landmarks, idx, w, h) for idx in self.LEFT_EYE_INDICES])
                lx_min, ly_min = np.clip(np.min(left_pts, axis=0) - 4, [0, 0], [w - 1, h - 1]).astype(int)
                lx_max, ly_max = np.clip(np.max(left_pts, axis=0) + 4, [0, 0], [w - 1, h - 1]).astype(int)

                right_pts = np.array([self._get_landmark_point(landmarks, idx, w, h) for idx in self.RIGHT_EYE_INDICES])
                rx_min, ry_min = np.clip(np.min(right_pts, axis=0) - 4, [0, 0], [w - 1, h - 1]).astype(int)
                rx_max, ry_max = np.clip(np.max(right_pts, axis=0) + 4, [0, 0], [w - 1, h - 1]).astype(int)

                if (lx_max > lx_min + 3 and ly_max > ly_min + 3) and (rx_max > rx_min + 3 and ry_max > ry_min + 3):
                    left_crop = cv2.cvtColor(frame[ly_min:ly_max, lx_min:lx_max], cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame[ly_min:ly_max, lx_min:lx_max]
                    right_crop = cv2.cvtColor(frame[ry_min:ry_max, rx_min:rx_max], cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame[ry_min:ry_max, rx_min:rx_max]
                    
                    std_left = float(np.std(left_crop))
                    std_right = float(np.std(right_crop))
                    avg_std = (std_left + std_right) / 2.0

                    # Hands or flat objects placed over eyes create flat skin texture (std < 14.0) with lower EAR
                    if avg_std < 14.0 and ear_val < 0.22:
                        return True, "hands_or_object_occlusion"

            return False, "none"
        except Exception:
            return False, "none"
        except Exception:
            return False, "none"

    def _classify_gaze_direction(
        self,
        landmarks: Any,
        pose: Dict[str, float],
        w: int,
        h: int,
        is_occluded: bool,
        is_actively_typing: bool = False,
        is_coding_phase: bool = False,
    ) -> Tuple[str, bool, float]:
        """
        Classifies gaze direction into 8-way + occlusion states with keyboard exception.
        
        Returns:
            Tuple of (gaze_direction: str, is_center: bool, frame_gaze_score: float)
        """
        if is_occluded:
            return "eyes_hidden", False, 0.0

        is_iris_center, iris_gaze_score, norm_ratio = self._analyze_eye_gaze_normalized(landmarks, w, h)
        raw_yaw = float(pose.get("yaw", 0.0))
        raw_pitch = float(pose.get("pitch", 0.0))
        head_yaw = abs(raw_yaw)

        # Vector offset of irises relative to eye centers
        try:
            left_iris = self._get_landmark_point(landmarks, self.LEFT_IRIS_INDICES[0], w, h)
            left_center = np.mean([self._get_landmark_point(landmarks, idx, w, h) for idx in self.LEFT_EYE_INDICES], axis=0)
            p33 = self._get_landmark_point(landmarks, self.LEFT_EYE_CORNER, w, h)
            p263 = self._get_landmark_point(landmarks, self.RIGHT_EYE_CORNER, w, h)
            iod = max(1e-4, float(np.linalg.norm(p263 - p33)))
            iris_dx = float((left_iris[0] - left_center[0]) / iod)
            iris_dy = float((left_iris[1] - left_center[1]) / iod)
        except Exception:
            iris_dx = 0.0
            iris_dy = 0.0

        total_yaw = raw_yaw + (iris_dx * 90.0)
        total_pitch = raw_pitch + (iris_dy * 90.0)

        # 1. Downward Gaze toward keyboard OR Active Typing
        if is_actively_typing or ((total_pitch < -8.0 or raw_pitch < -8.0) and (is_coding_phase or is_actively_typing)):
            if abs(total_yaw) <= 42.0 and total_pitch >= -55.0:
                return "keyboard", True, 95.0

        # 2. Direct Center / Workspace View
        if abs(total_yaw) <= 30.0 and -18.0 <= total_pitch <= 20.0:
            return "center", True, 100.0

        # 3. Downward Gaze (Keyboard / Desk area)
        if total_pitch < -18.0 and abs(total_yaw) <= 32.0:
            if total_pitch < -52.0:
                # Far below screen / looking at floor or hidden notes
                score = max(0.0, 30.0 - (abs(total_pitch) - 52.0) * 2.0)
                return "far_down", False, score
            
            # Downward toward keyboard
            if is_actively_typing or is_coding_phase:
                # Natural typing behavior allowed with no penalty
                return "keyboard", True, 95.0
            else:
                # Downward gaze without typing activity -> warning and score deduction
                score = max(20.0, 70.0 - abs(total_pitch + 18.0) * 1.5)
                return "down_no_typing", False, score

        # 4. Left Gaze
        if total_yaw < -30.0:
            if total_yaw < -48.0:
                score = max(0.0, 35.0 - (abs(total_yaw) - 48.0) * 2.0)
                return "far_left", False, score
            score = max(25.0, 75.0 - (abs(total_yaw) - 30.0) * 2.0)
            return "left", False, score

        # 5. Right Gaze
        if total_yaw > 30.0:
            if total_yaw > 48.0:
                score = max(0.0, 35.0 - (total_yaw - 48.0) * 2.0)
                return "far_right", False, score
            score = max(25.0, 75.0 - (total_yaw - 30.0) * 2.0)
            return "right", False, score

        # 6. Upward Gaze
        if total_pitch > 20.0:
            if total_pitch > 35.0:
                score = max(0.0, 35.0 - (total_pitch - 35.0) * 2.0)
                return "far_up", False, score
            score = max(25.0, 75.0 - (total_pitch - 20.0) * 2.0)
            return "up", False, score

        return "away", False, 30.0

    def _analyze_eye_gaze_normalized(
        self,
        landmarks: Any,
        w: int,
        h: int,
    ) -> Tuple[bool, float, float]:
        """
        Computes resolution-independent normalized eye gaze.
        Divides iris deviation by inter-ocular distance (IOD = dist(p33, p263)).
        
        Returns:
            Tuple of (is_center_gaze, frame_gaze_score [0-100], normalized_gaze_ratio)
        """
        try:
            # 1. Left and right iris centers (in pixel coordinates)
            left_iris = self._get_landmark_point(landmarks, self.LEFT_IRIS_INDICES[0], w, h)
            right_iris = self._get_landmark_point(landmarks, self.RIGHT_IRIS_INDICES[0], w, h)

            # 2. Left and right eye centers (mean of outer contours)
            left_eye_center = np.mean(
                [self._get_landmark_point(landmarks, idx, w, h) for idx in self.LEFT_EYE_INDICES],
                axis=0
            )
            right_eye_center = np.mean(
                [self._get_landmark_point(landmarks, idx, w, h) for idx in self.RIGHT_EYE_INDICES],
                axis=0
            )

            # 3. Inter-ocular distance (IOD) between outer eye corners (landmark 33 and landmark 263)
            left_corner = self._get_landmark_point(landmarks, self.LEFT_EYE_CORNER, w, h)
            right_corner = self._get_landmark_point(landmarks, self.RIGHT_EYE_CORNER, w, h)
            iod = float(np.linalg.norm(right_corner - left_corner))

            if iod < 1e-4:
                return True, 100.0, 0.0

            # 4. Normalized iris offsets
            left_offset = float(np.linalg.norm(left_iris - left_eye_center))
            right_offset = float(np.linalg.norm(right_iris - right_eye_center))
            normalized_gaze_ratio = (left_offset + right_offset) / (2.0 * iod)

            # 5. Continuous score & center decision
            # Looking anywhere on screen or workspace yields normalized_gaze_ratio <= 0.16
            is_center = normalized_gaze_ratio <= 0.16
            gaze_score = max(0.0, min(100.0, (1.0 - (normalized_gaze_ratio / 0.20)) * 100.0))

            return is_center, float(gaze_score), float(normalized_gaze_ratio)

        except Exception as e:
            return True, 100.0, 0.0

    def _estimate_head_pose_pnp(
        self,
        landmarks: Any,
        w: int,
        h: int,
    ) -> Dict[str, float]:
        """
        Estimates 3D head pose (pitch, yaw, roll) using cv2.solvePnP with canonical 3D model vertices.
        """
        if cv2 is None:
            return {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}

        try:
            image_points_2d = np.array([
                self._get_landmark_point(landmarks, self.NOSE_TIP_INDEX, w, h),
                self._get_landmark_point(landmarks, self.CHIN_INDEX, w, h),
                self._get_landmark_point(landmarks, self.LEFT_EYE_CORNER, w, h),
                self._get_landmark_point(landmarks, self.RIGHT_EYE_CORNER, w, h),
                self._get_landmark_point(landmarks, self.LEFT_MOUTH_CORNER, w, h),
                self._get_landmark_point(landmarks, self.RIGHT_MOUTH_CORNER, w, h),
            ], dtype=np.float64)

            focal_length = float(w)
            center = (float(w) / 2.0, float(h) / 2.0)
            camera_matrix = np.array([
                [focal_length, 0.0, center[0]],
                [0.0, focal_length, center[1]],
                [0.0, 0.0, 1.0]
            ], dtype=np.float64)
            dist_coeffs = np.zeros((4, 1), dtype=np.float64)

            success, rvec, tvec = cv2.solvePnP(
                self.MODEL_POINTS_3D,
                image_points_2d,
                camera_matrix,
                dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )

            if not success:
                return {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}

            R, _ = cv2.Rodrigues(rvec)

            sy = np.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
            singular = sy < 1e-6

            if not singular:
                pitch = np.degrees(np.arctan2(R[2, 1], R[2, 2]))
                yaw = np.degrees(np.arctan2(-R[2, 0], sy))
                roll = np.degrees(np.arctan2(R[1, 0], R[0, 0]))
            else:
                pitch = np.degrees(np.arctan2(-R[1, 2], R[1, 1]))
                yaw = np.degrees(np.arctan2(-R[2, 0], sy))
                roll = 0.0

            # Normalize Euler angles to eliminate coordinate system 180-deg flip
            while pitch > 180.0: pitch -= 360.0
            while pitch < -180.0: pitch += 360.0
            if pitch > 90.0: pitch -= 180.0
            elif pitch < -90.0: pitch += 180.0

            while yaw > 180.0: yaw -= 360.0
            while yaw < -180.0: yaw += 360.0
            if yaw > 90.0: yaw -= 180.0
            elif yaw < -90.0: yaw += 180.0

            while roll > 180.0: roll -= 360.0
            while roll < -180.0: roll += 360.0
            if roll > 90.0: roll -= 180.0
            elif roll < -90.0: roll += 180.0

            return {
                "pitch": float(pitch),
                "yaw": float(yaw),
                "roll": float(roll)
            }

        except Exception as e:
            return {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}

    def _calculate_ear(self, landmarks: Any, w: int, h: int) -> float:
        """
        Calculates Eye Aspect Ratio (EAR) across left and right eyes.
        """
        try:
            # Left eye EAR: [33, 160, 158, 133, 153, 144]
            p33 = self._get_landmark_point(landmarks, 33, w, h)
            p133 = self._get_landmark_point(landmarks, 133, w, h)
            p160 = self._get_landmark_point(landmarks, 160, w, h)
            p144 = self._get_landmark_point(landmarks, 144, w, h)
            p158 = self._get_landmark_point(landmarks, 158, w, h)
            p153 = self._get_landmark_point(landmarks, 153, w, h)

            left_w = np.linalg.norm(p33 - p133)
            left_h1 = np.linalg.norm(p160 - p144)
            left_h2 = np.linalg.norm(p158 - p153)
            ear_left = (left_h1 + left_h2) / (2.0 * max(1e-4, left_w))

            # Right eye EAR: [362, 385, 387, 263, 373, 380]
            p362 = self._get_landmark_point(landmarks, 362, w, h)
            p263 = self._get_landmark_point(landmarks, 263, w, h)
            p385 = self._get_landmark_point(landmarks, 385, w, h)
            p380 = self._get_landmark_point(landmarks, 380, w, h)
            p387 = self._get_landmark_point(landmarks, 387, w, h)
            p373 = self._get_landmark_point(landmarks, 373, w, h)

            right_w = np.linalg.norm(p362 - p263)
            right_h1 = np.linalg.norm(p385 - p380)
            right_h2 = np.linalg.norm(p387 - p373)
            ear_right = (right_h1 + right_h2) / (2.0 * max(1e-4, right_w))

            return float((ear_left + ear_right) / 2.0)

        except Exception as e:
            return 0.28  # Default open eye baseline

    def _calculate_movement_dynamics(
        self,
        current_landmarks: Any,
        previous_landmarks: Any,
        w: int,
        h: int,
    ) -> float:
        """
        Calculates normalized facial landmark velocity between consecutive frames.
        """
        try:
            left_corner = self._get_landmark_point(current_landmarks, self.LEFT_EYE_CORNER, w, h)
            right_corner = self._get_landmark_point(current_landmarks, self.RIGHT_EYE_CORNER, w, h)
            iod = float(np.linalg.norm(right_corner - left_corner))

            if iod < 1e-4:
                return 0.0

            displacements = []
            for idx in self.DYNAMIC_LANDMARK_INDICES:
                p_curr = self._get_landmark_point(current_landmarks, idx, w, h)
                p_prev = self._get_landmark_point(previous_landmarks, idx, w, h)
                displacements.append(np.linalg.norm(p_curr - p_prev) / iod)

            return float(np.mean(displacements))

        except Exception as e:
            return 0.0

    def _count_blinks_from_ear(self, ear_values: List[float], threshold: float = 0.20) -> int:
        """
        Detects blinks by counting consecutive transitions from open (>= threshold) to closed (< threshold).
        """
        if len(ear_values) < 2:
            return 0

        blinks = 0
        in_blink = False

        for ear in ear_values:
            if ear < threshold:
                if not in_blink:
                    in_blink = True
                    blinks += 1
            else:
                in_blink = False

        return blinks

    def _generate_observable_flags(
        self,
        gaze_stability_ratio: float,
        head_pose_variance: float,
        frame_presence_ratio: float,
        blink_frequency_cpm: float,
        facial_movement_dynamics: float,
        rapid_rotation_detected: bool,
        duration_sec: float,
        eye_occlusion_ratio: float = 0.0,
        eye_occlusion_events: int = 0,
        prolonged_occlusion_events: int = 0,
        downward_no_typing_events: int = 0,
        sustained_gaze_events: int = 0,
        far_gaze_events: int = 0,
        distinct_deviation_events: int = 0,
        multiple_faces_detected: bool = False,
    ) -> List[str]:
        """
        Builds purely physical, observable flags without emotion/intent speculation.
        """
        flags = []

        if frame_presence_ratio < 50.0:
            flags.append("low_frame_presence")

        if gaze_stability_ratio < 25.0:
            flags.append("frequent_looking_away")

        if head_pose_variance < 30.0:
            flags.append("high_head_pose_variance")

        if rapid_rotation_detected:
            flags.append("rapid_head_rotation")

        if eye_occlusion_ratio >= 15.0 or eye_occlusion_events >= 1:
            flags.append("eye_occlusion_detected")

        if eye_occlusion_ratio >= 35.0 or prolonged_occlusion_events >= 1:
            flags.append("prolonged_eye_occlusion")

        if downward_no_typing_events >= 1:
            flags.append("downward_gaze_without_typing")

        if sustained_gaze_events >= 1:
            flags.append("sustained_gaze_deviation")

        if far_gaze_events >= 1:
            flags.append("sustained_far_gaze_deviation")

        if distinct_deviation_events >= 3:
            flags.append("suspicious_repeated_gaze_movements")

        if multiple_faces_detected:
            flags.append("multiple_faces_detected")

        if blink_frequency_cpm > 55.0:
            flags.append("elevated_blink_frequency")
        elif blink_frequency_cpm < 4.0 and duration_sec > 15.0:
            flags.append("reduced_blink_frequency")

        if facial_movement_dynamics < 5.0 and duration_sec > 15.0:
            flags.append("minimal_facial_movement")

        return flags

    def _get_landmark_point(self, landmarks: Any, index: int, w: int, h: int) -> np.ndarray:
        """Extracts 2D coordinate in pixel space."""
        landmark = landmarks.landmark[index]
        return np.array([landmark.x * float(w), landmark.y * float(h)], dtype=np.float64)

    def _create_empty_observable_metrics(self, total_frames: int = 0) -> ObservableCVMetrics:
        """Returns default metrics for empty/missing frame sequences."""
        flag = "No frames provided" if total_frames == 0 else "No face detected in video stream"
        return ObservableCVMetrics(
            gaze_stability_ratio=0.0,
            head_pose_variance=0.0,
            facial_movement_dynamics=0.0,
            frame_presence_ratio=0.0,
            blink_frequency_cpm=0.0,
            observable_flags=[flag],
            eye_occlusion_ratio=0.0,
            gaze_breakdown={},
        )

    def _create_empty_metrics(self) -> BehavioralMetrics:
        """Returns empty BehavioralMetrics."""
        empty_cv = self._create_empty_observable_metrics(0)
        return BehavioralMetrics(
            eye_contact_score=0.0,
            head_stability_score=0.0,
            facial_engagement_score=0.0,
            fidgeting_score=0.0,
            confidence_posture_score=0.0,
            attention_span_score=0.0,
            red_flags=["No frames provided"],
            frame_count=0,
            analysis_details={},
            observable_cv_metrics=empty_cv,
        )


def analyze_video_frames(
    frame_base64_list: List[str],
    fps: float = 10.0,
    is_coding_phase: bool = False,
    is_actively_typing: bool = False,
) -> ObservableCVMetrics:
    """
    Public module function to analyze video frames and return ObservableCVMetrics.
    """
    service = BehavioralAnalysisService()
    return service.analyze_video_frames(
        frame_base64_list=frame_base64_list,
        fps=fps,
        is_coding_phase=is_coding_phase,
        is_actively_typing=is_actively_typing,
    )


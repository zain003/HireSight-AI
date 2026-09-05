"""
Observable Computer Vision & Facial Movement Engine using MediaPipe & OpenCV.
Computes resolution-independent eye gaze normalization, solvePnP 3D head pose estimation,
and physical facial movement dynamics (EAR blinks and micro-movements) with zero psychological claims.
"""
import base64
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

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
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=0.5
            )
        else:
            self.mp_face_mesh = None
            self.mp_face_detection = None
            self.face_mesh = None
            self.face_detection = None

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
    ) -> ObservableCVMetrics:
        """
        Analyze a temporal sequence of video frames and return physical ObservableCVMetrics.
        
        Args:
            frame_base64_list: List of base64-encoded image frames.
            fps: Video sampling rate in frames per second (default 10.0).
            
        Returns:
            ObservableCVMetrics schema compliant with 000-shared-contracts.md.
        """
        if not frame_base64_list:
            return self._create_empty_observable_metrics()

        total_frames = len(frame_base64_list)
        frames_with_face = 0
        gaze_scores = []
        center_gaze_count = 0
        head_poses = []
        ear_values = []
        movement_velocities = []

        previous_landmarks = None
        previous_pose = None
        rapid_rotation_detected = False

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
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                else:
                    rgb_frame = frame

                # Face detection check
                if self.face_detection is not None:
                    face_results = self.face_detection.process(rgb_frame)
                    if not face_results or not face_results.detections:
                        continue

                # Face mesh extraction
                if self.face_mesh is None:
                    continue

                mesh_results = self.face_mesh.process(rgb_frame)
                if not mesh_results or not mesh_results.multi_face_landmarks:
                    continue

                landmarks = mesh_results.multi_face_landmarks[0]
                frames_with_face += 1

                # 1. Resolution-independent eye gaze normalization
                is_center, gaze_score, _ = self._analyze_eye_gaze_normalized(landmarks, w, h)
                gaze_scores.append(gaze_score)
                if is_center:
                    center_gaze_count += 1

                # 2. 3D Head pose via solvePnP
                pose = self._estimate_head_pose_pnp(landmarks, w, h)
                head_poses.append(pose)
                if previous_pose is not None:
                    delta_angle = max(
                        abs(pose["pitch"] - previous_pose["pitch"]),
                        abs(pose["yaw"] - previous_pose["yaw"]),
                        abs(pose["roll"] - previous_pose["roll"]),
                    )
                    if delta_angle > 25.0:
                        rapid_rotation_detected = True
                previous_pose = pose

                # 3. Eye Aspect Ratio (EAR) for blink detection
                ear = self._calculate_ear(landmarks, w, h)
                ear_values.append(ear)

                # 4. Facial movement dynamics
                if previous_landmarks is not None:
                    vel = self._calculate_movement_dynamics(landmarks, previous_landmarks, w, h)
                    movement_velocities.append(vel)
                previous_landmarks = landmarks

            except Exception as e:
                print(f"Error in frame processing: {e}")
                continue

        if frames_with_face == 0:
            return self._create_empty_observable_metrics(total_frames)

        # 1. Gaze Stability Ratio: Percentage of face frames looking toward center
        gaze_stability_ratio = (center_gaze_count / frames_with_face) * 100.0

        # 2. Head Pose Variance: Inverse of angular variance across frames
        if len(head_poses) >= 2:
            pitches = [p["pitch"] for p in head_poses]
            yaws = [p["yaw"] for p in head_poses]
            rolls = [p["roll"] for p in head_poses]
            total_var = float(np.var(pitches) + np.var(yaws) + np.var(rolls))
            head_pose_variance = max(0.0, min(100.0, 100.0 - (total_var * 0.75)))
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

        # Observable physical flags
        observable_flags = self._generate_observable_flags(
            gaze_stability_ratio=gaze_stability_ratio,
            head_pose_variance=head_pose_variance,
            frame_presence_ratio=frame_presence_ratio,
            blink_frequency_cpm=blink_frequency_cpm,
            facial_movement_dynamics=facial_movement_dynamics,
            rapid_rotation_detected=rapid_rotation_detected,
            duration_sec=duration_sec,
        )

        return ObservableCVMetrics(
            gaze_stability_ratio=round(gaze_stability_ratio, 2),
            head_pose_variance=round(head_pose_variance, 2),
            facial_movement_dynamics=round(facial_movement_dynamics, 2),
            frame_presence_ratio=round(frame_presence_ratio, 2),
            blink_frequency_cpm=round(blink_frequency_cpm, 2),
            observable_flags=observable_flags,
        )

    def analyze_frames(
        self,
        frame_base64_list: List[str],
        fps: float = 10.0,
    ) -> BehavioralMetrics:
        """
        Backward-compatible method returning BehavioralMetrics with embedded ObservableCVMetrics.
        """
        cv_metrics = self.analyze_video_frames(frame_base64_list, fps=fps)

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
            },
            observable_cv_metrics=cv_metrics,
        )

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
            # Typical centered gaze ratio is < 0.085 of IOD
            is_center = normalized_gaze_ratio < 0.085
            gaze_score = max(0.0, min(100.0, (1.0 - (normalized_gaze_ratio / 0.12)) * 100.0))

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
            # Extract 2D image coordinates for the 6 canonical model points:
            # [1: nose tip, 152: chin, 33: left eye corner, 263: right eye corner, 61: left mouth corner, 291: right mouth corner]
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

            # Convert rotation vector to rotation matrix
            R, _ = cv2.Rodrigues(rvec)

            # Euler angle decomposition
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
    ) -> List[str]:
        """
        Builds purely physical, observable flags without emotion/intent speculation.
        """
        flags = []

        if frame_presence_ratio < 80.0:
            flags.append("low_frame_presence")

        if gaze_stability_ratio < 40.0:
            flags.append("frequent_looking_away")

        if head_pose_variance < 40.0:
            flags.append("high_head_pose_variance")

        if rapid_rotation_detected:
            flags.append("rapid_head_rotation")

        if blink_frequency_cpm > 45.0:
            flags.append("elevated_blink_frequency")
        elif blink_frequency_cpm < 6.0 and duration_sec > 10.0:
            flags.append("reduced_blink_frequency")

        if facial_movement_dynamics < 10.0:
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
) -> ObservableCVMetrics:
    """
    Public module function to analyze video frames and return ObservableCVMetrics.
    """
    service = BehavioralAnalysisService()
    return service.analyze_video_frames(frame_base64_list, fps=fps)

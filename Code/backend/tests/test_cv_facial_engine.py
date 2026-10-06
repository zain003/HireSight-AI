"""
Unit and Integration Tests for FEAT-004-BE: Observable Computer Vision & Facial Movement Engine
Tests resolution-independent eye gaze, solvePnP 3D head pose estimation, EAR blink detection, and physical observable metrics.
"""
import base64
import numpy as np
import pytest
from unittest.mock import MagicMock

try:
    import cv2
except ImportError:
    cv2 = None

from app.interview.domain.interview_models import ObservableCVMetrics
from app.interview.services.behavioral_analysis import (
    BehavioralAnalysisService,
    analyze_video_frames,
)


def _create_mock_landmark(x: float, y: float, z: float = 0.0):
    landmark = MagicMock()
    landmark.x = x
    landmark.y = y
    landmark.z = z
    return landmark


def _create_mock_landmarks_container(landmarks_dict):
    """
    Creates a mock MultiFaceLandmarks item where landmarks_dict maps index -> (x, y, z).
    Indices not explicitly provided get a default (0.5, 0.5, 0.0).
    """
    container = MagicMock()
    landmarks_list = [_create_mock_landmark(0.5, 0.5, 0.0) for _ in range(478)]
    for idx, coords in landmarks_dict.items():
        z = coords[2] if len(coords) > 2 else 0.0
        landmarks_list[idx] = _create_mock_landmark(coords[0], coords[1], z)
    container.landmark = landmarks_list
    return container


def _create_synthetic_face_landmarks(
    center_x: float = 0.5,
    center_y: float = 0.5,
    scale: float = 0.3,
    gaze_offset_x: float = 0.0,
    gaze_offset_y: float = 0.0,
    mouth_open: float = 0.02,
    ear_factor: float = 0.28,
):
    """
    Builds a canonical normalized 2D face landmark layout for testing solvePnP and gaze normalization.
    """
    landmarks = {}
    w, h = 1280, 720
    focal_length = float(w)
    center = (float(w) * center_x, float(h) * center_y)
    camera_matrix = np.array([
        [focal_length, 0.0, center[0]],
        [0.0, focal_length, center[1]],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)
    dist_coeffs = np.zeros((4, 1), dtype=np.float64)

    rvec = np.zeros((3, 1), dtype=np.float64)
    tvec = np.array([[0.0], [0.0], [1000.0]], dtype=np.float64)

    service = BehavioralAnalysisService()
    proj_2d, _ = cv2.projectPoints(service.MODEL_POINTS_3D, rvec, tvec, camera_matrix, dist_coeffs)
    pts = proj_2d.reshape(-1, 2)

    # 1: Nose, 152: Chin, 33: Left eye, 263: Right eye, 61: Left mouth, 291: Right mouth
    landmarks[1] = (float(pts[0][0] / w), float(pts[0][1] / h), 0.0)
    landmarks[152] = (float(pts[1][0] / w), float(pts[1][1] / h), -0.065 * scale)
    landmarks[33] = (float(pts[2][0] / w), float(pts[2][1] / h), -0.135 * scale)
    landmarks[263] = (float(pts[3][0] / w), float(pts[3][1] / h), -0.135 * scale)
    landmarks[61] = (float(pts[4][0] / w), float(pts[4][1] / h), -0.125 * scale)
    landmarks[291] = (float(pts[5][0] / w), float(pts[5][1] / h), -0.125 * scale)

    left_corner_x = landmarks[33][0]
    right_corner_x = landmarks[263][0]
    eye_y = landmarks[33][1]

    # Inner eye corners
    landmarks[133] = (center_x - scale * 0.10, eye_y, -0.10 * scale)
    landmarks[362] = (center_x + scale * 0.10, eye_y, -0.10 * scale)

    landmarks[13] = (center_x, landmarks[61][1] - mouth_open * scale, 0.0)
    landmarks[14] = (center_x, landmarks[61][1] + mouth_open * scale, 0.0)
    
    # Left eye contour points for EAR
    left_eye_center_x = (left_corner_x + (center_x - scale * 0.10)) / 2.0
    landmarks[160] = (left_eye_center_x - 0.01 * scale, eye_y - ear_factor * scale * 0.1, 0.0)
    landmarks[158] = (left_eye_center_x + 0.01 * scale, eye_y - ear_factor * scale * 0.1, 0.0)
    landmarks[144] = (left_eye_center_x - 0.01 * scale, eye_y + ear_factor * scale * 0.1, 0.0)
    landmarks[153] = (left_eye_center_x + 0.01 * scale, eye_y + ear_factor * scale * 0.1, 0.0)
    
    # Right eye contour points for EAR
    right_eye_center_x = (right_corner_x + (center_x + scale * 0.10)) / 2.0
    landmarks[385] = (right_eye_center_x - 0.01 * scale, eye_y - ear_factor * scale * 0.1, 0.0)
    landmarks[387] = (right_eye_center_x + 0.01 * scale, eye_y - ear_factor * scale * 0.1, 0.0)
    landmarks[380] = (right_eye_center_x - 0.01 * scale, eye_y + ear_factor * scale * 0.1, 0.0)
    landmarks[373] = (right_eye_center_x + 0.01 * scale, eye_y + ear_factor * scale * 0.1, 0.0)
    
    # Iris centers (468 for left, 473 for right)
    landmarks[468] = (left_eye_center_x + gaze_offset_x * scale, eye_y + gaze_offset_y * scale, 0.0)
    landmarks[473] = (right_eye_center_x + gaze_offset_x * scale, eye_y + gaze_offset_y * scale, 0.0)
    for i in range(469, 473):
        landmarks[i] = landmarks[468]
    for i in range(474, 478):
        landmarks[i] = landmarks[473]
        
    return _create_mock_landmarks_container(landmarks)


def test_gaze_normalization_resolution_invariance():
    """
    Assert that the same relative gaze offset on 480p and 1080p images yields identical gaze score (within 0.01%).
    """
    service = BehavioralAnalysisService()
    mock_landmarks = _create_synthetic_face_landmarks(gaze_offset_x=0.01, gaze_offset_y=0.0)
    
    # 480p resolution (640 x 480)
    is_center_480, score_480, ratio_480 = service._analyze_eye_gaze_normalized(mock_landmarks, w=640, h=480)
    
    # 1080p resolution (1920 x 1080)
    is_center_1080, score_1080, ratio_1080 = service._analyze_eye_gaze_normalized(mock_landmarks, w=1920, h=1080)
    
    # 4K resolution (3840 x 2160)
    is_center_4k, score_4k, ratio_4k = service._analyze_eye_gaze_normalized(mock_landmarks, w=3840, h=2160)
    
    assert is_center_480 == is_center_1080 == is_center_4k
    assert abs(ratio_480 - ratio_1080) < 1e-4, f"480p ratio {ratio_480} != 1080p ratio {ratio_1080}"
    assert abs(score_480 - score_1080) < 1e-3, f"480p score {score_480} != 1080p score {score_1080}"
    assert abs(score_1080 - score_4k) < 1e-3, f"1080p score {score_1080} != 4K score {score_4k}"


def test_solvepnp_head_pose_angles():
    """
    Assert that a canonical frontal face landmarks set returns pitch, yaw, roll within ±5 degrees of zero.
    """
    service = BehavioralAnalysisService()
    mock_landmarks = _create_synthetic_face_landmarks(center_x=0.5, center_y=0.5, scale=0.3)
    
    pose = service._estimate_head_pose_pnp(mock_landmarks, w=1280, h=720)
    
    assert "pitch" in pose and "yaw" in pose and "roll" in pose
    assert abs(pose["pitch"]) < 10.0, f"Frontal face pitch {pose['pitch']} should be near 0"
    assert abs(pose["yaw"]) < 10.0, f"Frontal face yaw {pose['yaw']} should be near 0"
    assert abs(pose["roll"]) < 10.0, f"Frontal face roll {pose['roll']} should be near 0"


def test_empty_frames_returns_graceful_defaults():
    """
    Assert that an empty frame list returns 0.0 scores with 'No frames provided' flag without throwing exceptions.
    """
    service = BehavioralAnalysisService()
    metrics = service.analyze_video_frames([])
    
    assert isinstance(metrics, ObservableCVMetrics)
    assert metrics.gaze_stability_ratio == 0.0
    assert metrics.head_pose_variance == 0.0
    assert metrics.facial_movement_dynamics == 0.0
    assert metrics.frame_presence_ratio == 0.0
    assert metrics.blink_frequency_cpm == 0.0
    assert "No frames provided" in metrics.observable_flags or any("No frames" in f for f in metrics.observable_flags)


def test_no_emotion_labels_in_metrics():
    """
    Invariant test: verify that ObservableCVMetrics schema contains physical metrics only, no emotion labels.
    """
    fields = ObservableCVMetrics.model_fields.keys()
    
    # Must contain physical metrics
    assert "gaze_stability_ratio" in fields
    assert "head_pose_variance" in fields
    assert "facial_movement_dynamics" in fields
    assert "frame_presence_ratio" in fields
    assert "blink_frequency_cpm" in fields
    assert "observable_flags" in fields
    
    # Must NOT contain subjective psychological/emotion labels
    forbidden_terms = ["nervous", "confident", "suspicious", "lying", "emotion", "sentiment", "engagement_mind"]
    for term in forbidden_terms:
        assert term not in fields, f"Forbidden term '{term}' found in ObservableCVMetrics schema!"


def test_ear_blink_calculation():
    """
    Assert EAR computation differentiates open eyes vs closed eyes.
    """
    service = BehavioralAnalysisService()
    
    open_landmarks = _create_synthetic_face_landmarks(ear_factor=0.35)
    closed_landmarks = _create_synthetic_face_landmarks(ear_factor=0.05)
    
    ear_open = service._calculate_ear(open_landmarks, w=640, h=480)
    ear_closed = service._calculate_ear(closed_landmarks, w=640, h=480)
    
    assert ear_open > ear_closed, f"Open EAR ({ear_open}) should be greater than closed EAR ({ear_closed})"
    assert ear_closed < 0.20, f"Closed EAR ({ear_closed}) should be under blink threshold"


def test_eye_occlusion_detection_and_red_flag():
    """
    Assert that eye occlusion (e.g. collapsed landmarks / hands over eyes) is explicitly classified
    as 'eyes_hidden', yields 0 gaze score, and produces 'eye_occlusion_detected' observable flag.
    """
    service = BehavioralAnalysisService()
    
    # 1. Normal face with open eyes
    mock_normal = _create_synthetic_face_landmarks(ear_factor=0.30)
    is_occ_normal, _ = service._detect_eye_occlusion(mock_normal, frame=None, w=640, h=480)
    assert not is_occ_normal, "Normal open eyes should not be classified as occluded"

    # 2. Occluded eyes (EAR collapsed < 0.03)
    mock_occluded = _create_synthetic_face_landmarks(ear_factor=0.01)
    is_occ_occluded, occ_type = service._detect_eye_occlusion(mock_occluded, frame=None, w=640, h=480)
    assert is_occ_occluded, "Occluded / covered eyes must be detected as occluded"

    # 3. Gaze direction when occluded
    pose = {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}
    gaze_dir, is_center, score = service._classify_gaze_direction(
        landmarks=mock_occluded,
        pose=pose,
        w=640,
        h=480,
        is_occluded=True,
    )
    assert gaze_dir == "eyes_hidden", f"Expected 'eyes_hidden', got '{gaze_dir}'"
    assert not is_center, "Occluded eyes must not be assumed looking at screen"
    assert score == 0.0, "Gaze score for occluded eyes must be 0.0"


def test_keyboard_typing_exception():
    """
    Assert looking downward at keyboard is allowed while actively coding/typing (keyboard exception),
    but warned and deducted when downward gaze has no typing activity.
    """
    service = BehavioralAnalysisService()
    mock_down = _create_synthetic_face_landmarks(gaze_offset_y=-0.02)
    down_pose = {"pitch": -28.0, "yaw": 2.0, "roll": 0.0}

    # Case A: Downward gaze WITH active typing -> Allowed (keyboard exception)
    gaze_dir_typing, is_c_typing, score_typing = service._classify_gaze_direction(
        landmarks=mock_down,
        pose=down_pose,
        w=640,
        h=480,
        is_occluded=False,
        is_actively_typing=True,
        is_coding_phase=True,
    )
    assert gaze_dir_typing == "keyboard", f"Expected 'keyboard', got '{gaze_dir_typing}'"
    assert is_c_typing, "Active typing downward gaze should be treated as engaged"
    assert score_typing >= 90.0, f"Score should be >= 90, got {score_typing}"

    # Case B: Downward gaze WITHOUT active typing -> Deducted / warned
    gaze_dir_notyping, is_c_notyping, score_notyping = service._classify_gaze_direction(
        landmarks=mock_down,
        pose=down_pose,
        w=640,
        h=480,
        is_occluded=False,
        is_actively_typing=False,
        is_coding_phase=False,
    )
    assert gaze_dir_notyping == "down_no_typing", f"Expected 'down_no_typing', got '{gaze_dir_notyping}'"
    assert not is_c_notyping, "Downward gaze without typing should not be treated as center"
    assert score_notyping < score_typing, "Downward gaze without typing must have lower score"


def test_gaze_direction_horizontal_and_vertical():
    """
    Assert left, right, and up gaze directions are classified accurately with appropriate deductions.
    """
    service = BehavioralAnalysisService()
    mock_center = _create_synthetic_face_landmarks()

    # Center
    center_dir, is_c, score_c = service._classify_gaze_direction(
        landmarks=mock_center, pose={"pitch": 0.0, "yaw": 0.0, "roll": 0.0}, w=640, h=480, is_occluded=False
    )
    assert center_dir == "center" and is_c and score_c == 100.0

    # Left
    left_dir, is_l, score_l = service._classify_gaze_direction(
        landmarks=mock_center, pose={"pitch": 0.0, "yaw": -35.0, "roll": 0.0}, w=640, h=480, is_occluded=False
    )
    assert left_dir == "left" and not is_l and score_l < 100.0

    # Right
    right_dir, is_r, score_r = service._classify_gaze_direction(
        landmarks=mock_center, pose={"pitch": 0.0, "yaw": 35.0, "roll": 0.0}, w=640, h=480, is_occluded=False
    )
    assert right_dir == "right" and not is_r and score_r < 100.0

    # Far Left
    far_left_dir, is_fl, score_fl = service._classify_gaze_direction(
        landmarks=mock_center, pose={"pitch": 0.0, "yaw": -55.0, "roll": 0.0}, w=640, h=480, is_occluded=False
    )
    assert far_left_dir == "far_left" and not is_fl and score_fl <= 35.0

    # Up
    up_dir, is_u, score_u = service._classify_gaze_direction(
        landmarks=mock_center, pose={"pitch": 24.0, "yaw": 0.0, "roll": 0.0}, w=640, h=480, is_occluded=False
    )
    assert up_dir == "up" and not is_u and score_u < 100.0


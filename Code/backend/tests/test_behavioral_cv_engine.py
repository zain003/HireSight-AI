"""
Unit and Integration Tests for FEAT-004: Observable Computer Vision Engine.
"""
from tests.test_cv_facial_engine import (
    test_gaze_normalization_resolution_invariance,
    test_solvepnp_head_pose_angles,
    test_empty_frames_returns_graceful_defaults,
    test_no_emotion_labels_in_metrics,
    test_ear_blink_calculation,
)

__all__ = [
    "test_gaze_normalization_resolution_invariance",
    "test_solvepnp_head_pose_angles",
    "test_empty_frames_returns_graceful_defaults",
    "test_no_emotion_labels_in_metrics",
    "test_ear_blink_calculation",
]

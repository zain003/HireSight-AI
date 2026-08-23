"""
Enhanced Behavioral Analysis Service using MediaPipe.
Analyzes facial landmarks, head pose, eye gaze, and facial movements.
"""
import base64
import io
from typing import Dict, List, Optional, Tuple
import numpy as np
import cv2
import mediapipe as mp
from dataclasses import dataclass


@dataclass
class BehavioralMetrics:
    """Behavioral analysis metrics from video frames."""
    eye_contact_score: float  # 0-100
    head_stability_score: float  # 0-100
    facial_engagement_score: float  # 0-100
    fidgeting_score: float  # 0-100, lower is better
    confidence_posture_score: float  # 0-100
    attention_span_score: float  # 0-100
    red_flags: List[str]
    frame_count: int
    analysis_details: Dict


class BehavioralAnalysisService:
    """
    Real-time behavioral analysis using MediaPipe.
    Tracks facial landmarks, head pose, eye gaze, and engagement.
    """
    
    def __init__(self):
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
        
        # Landmark indices for specific features
        self.LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
        self.LEFT_IRIS_INDICES = [468, 469, 470, 471, 472]
        self.RIGHT_IRIS_INDICES = [473, 474, 475, 476, 477]
        self.NOSE_TIP_INDEX = 1
        self.CHIN_INDEX = 152
        self.LEFT_EYE_CORNER = 33
        self.RIGHT_EYE_CORNER = 263
        
        # Tracking variables
        self.previous_head_pose = None
        self.head_movements = []
        self.eye_gaze_directions = []
        self.face_presence_frames = []
        
    def analyze_frames(self, frame_base64_list: List[str]) -> BehavioralMetrics:
        """
        Analyze a sequence of video frames for behavioral patterns.
        
        Args:
            frame_base64_list: List of base64-encoded video frames
            
        Returns:
            BehavioralMetrics with comprehensive analysis
        """
        if not frame_base64_list:
            return self._create_empty_metrics()
        
        # Reset tracking
        self.head_movements = []
        self.eye_gaze_directions = []
        self.face_presence_frames = []
        self.previous_head_pose = None
        
        frames_analyzed = 0
        eye_contact_frames = 0
        stable_head_frames = 0
        engaged_frames = 0
        fidget_movements = 0
        confident_posture_frames = 0
        
        for frame_b64 in frame_base64_list:
            try:
                # Decode frame
                frame_data = base64.b64decode(frame_b64)
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    continue
                
                # Convert to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detect face
                face_results = self.face_detection.process(rgb_frame)
                if not face_results.detections:
                    self.face_presence_frames.append(False)
                    continue
                
                self.face_presence_frames.append(True)
                
                # Analyze facial landmarks
                mesh_results = self.face_mesh.process(rgb_frame)
                if not mesh_results.multi_face_landmarks:
                    continue
                
                landmarks = mesh_results.multi_face_landmarks[0]
                h, w, _ = frame.shape
                
                # 1. Eye contact analysis
                eye_contact = self._analyze_eye_contact(landmarks, w, h)
                if eye_contact:
                    eye_contact_frames += 1
                
                # 2. Head pose stability
                head_pose = self._estimate_head_pose(landmarks, w, h)
                if self._is_stable_head_pose(head_pose):
                    stable_head_frames += 1
                
                # 3. Facial engagement (mouth, eyebrows)
                engagement = self._analyze_facial_engagement(landmarks, w, h)
                if engagement > 0.5:
                    engaged_frames += 1
                
                # 4. Detect fidgeting (excessive movement)
                if self._detect_fidgeting(head_pose):
                    fidget_movements += 1
                
                # 5. Confidence posture (head tilt, face angle)
                if self._analyze_confidence_posture(head_pose):
                    confident_posture_frames += 1
                
                frames_analyzed += 1
                
            except Exception as e:
                print(f"Frame analysis error: {e}")
                continue
        
        if frames_analyzed == 0:
            return self._create_empty_metrics()
        
        # Calculate scores
        eye_contact_score = (eye_contact_frames / frames_analyzed) * 100
        head_stability_score = (stable_head_frames / frames_analyzed) * 100
        engagement_score = (engaged_frames / frames_analyzed) * 100
        fidgeting_score = max(0, 100 - (fidget_movements / frames_analyzed) * 100)
        confidence_score = (confident_posture_frames / frames_analyzed) * 100
        
        # Attention span (based on face presence)
        face_presence_ratio = sum(self.face_presence_frames) / len(self.face_presence_frames)
        attention_score = face_presence_ratio * 100
        
        # Detect red flags
        red_flags = self._detect_red_flags(
            eye_contact_score,
            head_stability_score,
            engagement_score,
            fidgeting_score,
            attention_score,
            face_presence_ratio
        )
        
        return BehavioralMetrics(
            eye_contact_score=round(eye_contact_score, 2),
            head_stability_score=round(head_stability_score, 2),
            facial_engagement_score=round(engagement_score, 2),
            fidgeting_score=round(fidgeting_score, 2),
            confidence_posture_score=round(confidence_score, 2),
            attention_span_score=round(attention_score, 2),
            red_flags=red_flags,
            frame_count=frames_analyzed,
            analysis_details={
                "total_frames": len(frame_base64_list),
                "analyzed_frames": frames_analyzed,
                "face_present_frames": sum(self.face_presence_frames),
                "eye_contact_frames": eye_contact_frames,
                "stable_head_frames": stable_head_frames,
                "engaged_frames": engaged_frames,
                "fidget_movements": fidget_movements,
                "confident_posture_frames": confident_posture_frames
            }
        )
    
    def _analyze_eye_contact(self, landmarks, w: int, h: int) -> bool:
        """
        Analyze if candidate is making eye contact (looking at camera).
        Uses iris position relative to eye corners.
        """
        try:
            # Get iris centers
            left_iris = self._get_landmark_point(landmarks, self.LEFT_IRIS_INDICES[0], w, h)
            right_iris = self._get_landmark_point(landmarks, self.RIGHT_IRIS_INDICES[0], w, h)
            
            # Get eye corners
            left_corner = self._get_landmark_point(landmarks, self.LEFT_EYE_CORNER, w, h)
            right_corner = self._get_landmark_point(landmarks, self.RIGHT_EYE_CORNER, w, h)
            
            # Calculate iris position relative to eye center
            left_eye_center = np.mean([self._get_landmark_point(landmarks, idx, w, h) 
                                       for idx in self.LEFT_EYE_INDICES], axis=0)
            right_eye_center = np.mean([self._get_landmark_point(landmarks, idx, w, h) 
                                        for idx in self.RIGHT_EYE_INDICES], axis=0)
            
            # Distance from iris to eye center
            left_distance = np.linalg.norm(left_iris - left_eye_center)
            right_distance = np.linalg.norm(right_iris - right_eye_center)
            
            # Eye contact threshold (iris near center)
            threshold = 5.0
            self.eye_gaze_directions.append((left_distance, right_distance))
            
            return left_distance < threshold and right_distance < threshold
            
        except Exception as e:
            return False
    
    def _estimate_head_pose(self, landmarks, w: int, h: int) -> Dict:
        """
        Estimate head pose (pitch, yaw, roll) from facial landmarks.
        """
        try:
            # Key points for head pose
            nose_tip = self._get_landmark_point(landmarks, self.NOSE_TIP_INDEX, w, h)
            chin = self._get_landmark_point(landmarks, self.CHIN_INDEX, w, h)
            left_eye = self._get_landmark_point(landmarks, self.LEFT_EYE_CORNER, w, h)
            right_eye = self._get_landmark_point(landmarks, self.RIGHT_EYE_CORNER, w, h)
            
            # Calculate angles
            eye_center = (left_eye + right_eye) / 2
            
            # Yaw (left-right rotation)
            face_width = np.linalg.norm(right_eye - left_eye)
            nose_deviation = nose_tip[0] - eye_center[0]
            yaw = (nose_deviation / face_width) * 90  # degrees
            
            # Pitch (up-down rotation)
            face_height = np.linalg.norm(chin - eye_center)
            nose_height_deviation = nose_tip[1] - eye_center[1]
            pitch = (nose_height_deviation / face_height) * 90  # degrees
            
            # Roll (tilt)
            roll = np.degrees(np.arctan2(right_eye[1] - left_eye[1], 
                                         right_eye[0] - left_eye[0]))
            
            head_pose = {
                "yaw": float(yaw),
                "pitch": float(pitch),
                "roll": float(roll)
            }
            
            self.head_movements.append(head_pose)
            return head_pose
            
        except Exception as e:
            return {"yaw": 0, "pitch": 0, "roll": 0}
    
    def _is_stable_head_pose(self, current_pose: Dict) -> bool:
        """Check if head is stable (minimal movement)."""
        if self.previous_head_pose is None:
            self.previous_head_pose = current_pose
            return True
        
        # Calculate movement magnitude
        yaw_diff = abs(current_pose["yaw"] - self.previous_head_pose["yaw"])
        pitch_diff = abs(current_pose["pitch"] - self.previous_head_pose["pitch"])
        roll_diff = abs(current_pose["roll"] - self.previous_head_pose["roll"])
        
        self.previous_head_pose = current_pose
        
        # Threshold for stable head
        return yaw_diff < 15 and pitch_diff < 15 and roll_diff < 10
    
    def _detect_fidgeting(self, current_pose: Dict) -> bool:
        """Detect excessive head movements (fidgeting)."""
        if len(self.head_movements) < 3:
            return False
        
        recent_movements = self.head_movements[-3:]
        
        # Check for rapid back-and-forth movements
        yaw_changes = [abs(recent_movements[i]["yaw"] - recent_movements[i-1]["yaw"]) 
                       for i in range(1, len(recent_movements))]
        
        # Fidgeting = rapid movements > threshold
        return any(change > 20 for change in yaw_changes)
    
    def _analyze_confidence_posture(self, head_pose: Dict) -> bool:
        """
        Analyze confidence based on head posture.
        Confident: upright head, facing forward, minimal tilt.
        """
        # Check if head is upright and facing forward
        yaw_ok = abs(head_pose["yaw"]) < 20  # Not turned too far left/right
        pitch_ok = -10 < head_pose["pitch"] < 20  # Slight downward is OK
        roll_ok = abs(head_pose["roll"]) < 15  # Minimal tilt
        
        return yaw_ok and pitch_ok and roll_ok
    
    def _analyze_facial_engagement(self, landmarks, w: int, h: int) -> float:
        """
        Analyze facial expressions for engagement.
        Returns engagement score 0-1.
        """
        try:
            # Analyze mouth movement (talking = engagement)
            # Mouth landmarks: 61, 291, 0, 17
            mouth_top = self._get_landmark_point(landmarks, 13, w, h)
            mouth_bottom = self._get_landmark_point(landmarks, 14, w, h)
            mouth_openness = np.linalg.norm(mouth_top - mouth_bottom)
            
            # Normalize by face size
            left_eye = self._get_landmark_point(landmarks, self.LEFT_EYE_CORNER, w, h)
            right_eye = self._get_landmark_point(landmarks, self.RIGHT_EYE_CORNER, w, h)
            face_width = np.linalg.norm(right_eye - left_eye)
            
            normalized_openness = mouth_openness / face_width
            
            # Engagement score based on mouth movement
            engagement = min(1.0, normalized_openness * 10)
            
            return engagement
            
        except Exception as e:
            return 0.5  # Neutral
    
    def _get_landmark_point(self, landmarks, index: int, w: int, h: int) -> np.ndarray:
        """Extract landmark point coordinates."""
        landmark = landmarks.landmark[index]
        return np.array([landmark.x * w, landmark.y * h])
    
    def _detect_red_flags(
        self,
        eye_contact_score: float,
        head_stability_score: float,
        engagement_score: float,
        fidgeting_score: float,
        attention_score: float,
        face_presence_ratio: float
    ) -> List[str]:
        """Detect behavioral red flags."""
        red_flags = []
        
        if eye_contact_score < 40:
            red_flags.append("Poor eye contact - candidate frequently looked away")
        
        if head_stability_score < 50:
            red_flags.append("Unstable posture - excessive head movements")
        
        if engagement_score < 40:
            red_flags.append("Low facial engagement - minimal expression")
        
        if fidgeting_score < 60:
            red_flags.append("High fidgeting detected - possible nervousness or distraction")
        
        if attention_score < 70:
            red_flags.append("Attention issues - face not consistently visible")
        
        if face_presence_ratio < 0.8:
            red_flags.append("Frequent absence from frame - possible distractions")
        
        return red_flags
    
    def _create_empty_metrics(self) -> BehavioralMetrics:
        """Create empty metrics when no frames available."""
        return BehavioralMetrics(
            eye_contact_score=0.0,
            head_stability_score=0.0,
            facial_engagement_score=0.0,
            fidgeting_score=0.0,
            confidence_posture_score=0.0,
            attention_span_score=0.0,
            red_flags=["No video frames available for analysis"],
            frame_count=0,
            analysis_details={}
        )

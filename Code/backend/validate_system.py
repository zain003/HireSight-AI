"""
Complete System Validation Script
Tests all components and features of the Enhanced Evaluation System
"""
import sys
import os


def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_status(message, status="info"):
    """Print a status message."""
    icons = {
        "success": "✓",
        "error": "✗",
        "warning": "⚠",
        "info": "ℹ"
    }
    colors = {
        "success": "\033[92m",  # Green
        "error": "\033[91m",    # Red
        "warning": "\033[93m",  # Yellow
        "info": "\033[94m"      # Blue
    }
    reset = "\033[0m"
    
    icon = icons.get(status, "•")
    color = colors.get(status, "")
    print(f"{color}{icon} {message}{reset}")


def check_python_version():
    """Check Python version."""
    print_header("CHECKING PYTHON VERSION")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print_status(f"Python {version.major}.{version.minor}.{version.micro}", "success")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor} - REQUIRED: 3.10+", "error")
        return False


def check_core_dependencies():
    """Check core dependencies."""
    print_header("CHECKING CORE DEPENDENCIES")
    
    dependencies = {
        "fastapi": "FastAPI Framework",
        "pydantic": "Data Validation",
        "motor": "MongoDB Driver",
        "beanie": "MongoDB ODM",
        "numpy": "Numerical Computing",
        "cv2": "OpenCV (Video Processing)",
    }
    
    all_ok = True
    for module, description in dependencies.items():
        try:
            __import__(module)
            print_status(f"{description} ({module})", "success")
        except ImportError:
            print_status(f"{description} ({module}) - NOT INSTALLED", "error")
            all_ok = False
    
    return all_ok


def check_enhanced_dependencies():
    """Check enhanced evaluation dependencies."""
    print_header("CHECKING ENHANCED EVALUATION DEPENDENCIES")
    
    dependencies = {
        "mediapipe": {"name": "MediaPipe (Behavioral Analysis)", "critical": True},
        "librosa": {"name": "Librosa (Audio Processing)", "critical": True},
        "soundfile": {"name": "SoundFile (Audio I/O)", "critical": True},
        "scipy": {"name": "SciPy (Scientific Computing)", "critical": True},
        "opensmile": {"name": "OpenSMILE (Voice Analysis)", "critical": False},
        "vosk": {"name": "Vosk (Speech Recognition)", "critical": False},
    }
    
    all_critical_ok = True
    for module, info in dependencies.items():
        try:
            __import__(module)
            print_status(f"{info['name']}", "success")
        except ImportError:
            if info["critical"]:
                print_status(f"{info['name']} - NOT INSTALLED (REQUIRED)", "error")
                all_critical_ok = False
            else:
                print_status(f"{info['name']} - NOT INSTALLED (Optional, will fallback)", "warning")
    
    return all_critical_ok


def check_services_import():
    """Check if services import correctly."""
    print_header("CHECKING SERVICE IMPORTS")
    
    services = [
        ("app.interview.services.behavioral_analysis", "BehavioralAnalysisService"),
        ("app.interview.services.vocal_analysis", "VocalAnalysisService"),
        ("app.interview.services.recruiter_report", "RecruiterReportGenerator"),
        ("app.interview.application.interview_service", "InterviewService"),
    ]
    
    all_ok = True
    for module_path, class_name in services:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print_status(f"{class_name}", "success")
        except Exception as e:
            print_status(f"{class_name} - ERROR: {str(e)[:50]}", "error")
            all_ok = False
    
    return all_ok


def check_vosk_model():
    """Check if Vosk model is installed."""
    print_header("CHECKING VOSK MODEL")
    
    model_paths = [
        "./models/vosk-model-small-en-us-0.15",
        os.getenv("VOSK_MODEL_PATH", ""),
    ]
    
    for path in model_paths:
        if path and os.path.exists(path):
            if os.path.exists(os.path.join(path, "am", "final.mdl")):
                print_status(f"Vosk model found at: {path}", "success")
                return True
    
    print_status("Vosk model not found (Speech recognition will use fallback)", "warning")
    print_status("Run: python setup_enhanced_evaluation.py to download", "info")
    return False


def check_env_configuration():
    """Check environment configuration."""
    print_header("CHECKING ENVIRONMENT CONFIGURATION")
    
    env_file = ".env"
    if not os.path.exists(env_file):
        print_status(".env file not found", "warning")
        print_status("Run: python setup_enhanced_evaluation.py to create", "info")
        return False
    
    print_status(".env file exists", "success")
    
    # Check critical variables
    critical_vars = ["MONGODB_URL", "SECRET_KEY"]
    optional_vars = ["VOSK_MODEL_PATH", "GROQ_API_KEY", "GROK_API_KEY"]
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    all_critical = True
    for var in critical_vars:
        if var in content:
            print_status(f"{var} configured", "success")
        else:
            print_status(f"{var} not configured", "error")
            all_critical = False
    
    for var in optional_vars:
        if var in content:
            print_status(f"{var} configured", "success")
        else:
            print_status(f"{var} not configured (optional)", "info")
    
    return all_critical


def test_behavioral_analysis():
    """Test behavioral analysis service."""
    print_header("TESTING BEHAVIORAL ANALYSIS")
    
    try:
        from app.interview.services.behavioral_analysis import BehavioralAnalysisService
        import numpy as np
        import cv2
        import base64
        
        service = BehavioralAnalysisService()
        print_status("Service initialized", "success")
        
        # Create dummy frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.circle(frame, (320, 240), 100, (255, 255, 255), -1)
        _, buffer = cv2.imencode('.jpg', frame)
        frame_b64 = base64.b64encode(buffer).decode('utf-8')
        
        # Analyze
        metrics = service.analyze_frames([frame_b64])
        print_status(f"Frame analysis completed: {metrics.frame_count} frames", "success")
        print_status(f"Eye contact: {metrics.eye_contact_score:.1f}/100", "info")
        print_status(f"Attention: {metrics.attention_span_score:.1f}/100", "info")
        
        return True
    except Exception as e:
        print_status(f"Test failed: {str(e)[:60]}", "error")
        return False


def test_vocal_analysis():
    """Test vocal analysis service."""
    print_header("TESTING VOCAL ANALYSIS")
    
    try:
        from app.interview.services.vocal_analysis import VocalAnalysisService
        import asyncio
        
        service = VocalAnalysisService()
        print_status("Service initialized", "success")
        
        # Test with mock data
        async def test():
            metrics = await service.analyze_audio(
                audio_base64=None,
                transcript_text="This is a test sentence.",
                audio_format="wav"
            )
            return metrics
        
        metrics = asyncio.run(test())
        print_status("Vocal analysis completed", "success")
        print_status(f"Vocal confidence: {metrics.vocal_confidence_score:.1f}/100", "info")
        print_status(f"Speech clarity: {metrics.speech_clarity_score:.1f}/100", "info")
        
        return True
    except Exception as e:
        print_status(f"Test failed: {str(e)[:60]}", "error")
        return False


def test_recruiter_report():
    """Test recruiter report generation."""
    print_header("TESTING RECRUITER REPORT GENERATION")
    
    try:
        from app.interview.services.recruiter_report import RecruiterReportGenerator
        from app.interview.services.behavioral_analysis import BehavioralMetrics
        from app.interview.services.vocal_analysis import VocalMetrics
        from app.interview.domain.interview_models import AnswerEvaluation, QuestionType
        from datetime import datetime, timedelta
        
        generator = RecruiterReportGenerator()
        print_status("Generator initialized", "success")
        
        # Mock data
        evaluations = [
            AnswerEvaluation(
                question_index=0,
                question_text="Test question",
                question_type=QuestionType.TECHNICAL,
                candidate_transcript="Test answer",
                relevance_score=8.0,
                depth_score=7.0,
                communication_score=8.0,
                key_points_covered=["test"],
                missed_points=[],
                is_correct=True,
                accuracy_score=80.0,
                follow_up_triggered=False,
                coaching_detected=False,
                evaluator_notes="Good"
            )
        ]
        
        behavioral_metrics = [
            BehavioralMetrics(
                eye_contact_score=75.0,
                head_stability_score=80.0,
                facial_engagement_score=70.0,
                fidgeting_score=85.0,
                confidence_posture_score=78.0,
                attention_span_score=90.0,
                red_flags=[],
                frame_count=30,
                analysis_details={}
            )
        ]
        
        vocal_metrics = [
            VocalMetrics(
                vocal_confidence_score=80.0,
                speech_clarity_score=85.0,
                pitch_variance_score=75.0,
                speech_rate_score=80.0,
                pause_pattern_score=75.0,
                tone_consistency_score=70.0,
                communication_effectiveness=78.0,
                red_flags=[],
                transcript_confidence=0.95,
                analysis_details={}
            )
        ]
        
        coding_results = [{"compile_success": True, "all_passed": True}]
        
        # Generate report
        report = generator.generate_report(
            candidate_name="Test Candidate",
            job_role="Software Engineer",
            session_start=datetime.utcnow() - timedelta(minutes=30),
            session_end=datetime.utcnow(),
            evaluations=evaluations,
            behavioral_metrics=behavioral_metrics,
            vocal_metrics=vocal_metrics,
            coding_results=coding_results,
            aggregate_scores={"overall_score": 80.0}
        )
        
        print_status(f"Report generated: {report.hiring_recommendation}", "success")
        print_status(f"Overall score: {report.overall_score:.1f}/100", "info")
        print_status(f"Technical: {report.technical_score:.1f}/100", "info")
        print_status(f"Behavioral: {report.behavioral_score:.1f}/100", "info")
        print_status(f"Communication: {report.communication_score:.1f}/100", "info")
        
        return True
    except Exception as e:
        print_status(f"Test failed: {str(e)[:60]}", "error")
        import traceback
        traceback.print_exc()
        return False


def test_api_schemas():
    """Test API schemas."""
    print_header("TESTING API SCHEMAS")
    
    try:
        from app.interview.schemas import (
            SubmitAnswerResponse,
            InterviewReportResponse,
            LiveInterviewStartRequest
        )
        print_status("Schemas import successfully", "success")
        
        # Test schema with enhanced fields
        response = SubmitAnswerResponse(
            transcript="test",
            evaluation={
                "question_index": 0,
                "question_text": "test",
                "question_type": "technical",
                "candidate_transcript": "test",
                "relevance_score": 8.0,
                "depth_score": 7.0,
                "communication_score": 8.0,
                "key_points_covered": [],
                "missed_points": [],
                "is_correct": True,
                "accuracy_score": 80.0,
                "follow_up_triggered": False,
                "coaching_detected": False,
                "evaluator_notes": "test"
            },
            per_answer_score=85.0,
            behavioral_metrics={"eye_contact": 75.0},
            vocal_metrics={"vocal_confidence": 80.0}
        )
        print_status("Enhanced schemas validated", "success")
        
        return True
    except Exception as e:
        print_status(f"Test failed: {str(e)[:60]}", "error")
        return False


def main():
    """Run all validation tests."""
    print("\n")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*15 + "HIRESIGHT AI - SYSTEM VALIDATION" + " "*21 + "║")
    print("║" + " "*12 + "Enhanced Evaluation System Test Suite" + " "*18 + "║")
    print("╚" + "═"*68 + "╝")
    
    results = {
        "Python Version": check_python_version(),
        "Core Dependencies": check_core_dependencies(),
        "Enhanced Dependencies": check_enhanced_dependencies(),
        "Service Imports": check_services_import(),
        "Vosk Model": check_vosk_model(),
        "Environment Config": check_env_configuration(),
        "Behavioral Analysis": test_behavioral_analysis(),
        "Vocal Analysis": test_vocal_analysis(),
        "Recruiter Report": test_recruiter_report(),
        "API Schemas": test_api_schemas(),
    }
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print_status(f"{test_name}: PASSED", "success")
        else:
            print_status(f"{test_name}: FAILED", "error")
    
    print("\n" + "─"*70)
    print(f"  Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 ALL TESTS PASSED! System is ready for production.")
        print("\n  Next steps:")
        print("    1. Start MongoDB: docker-compose up -d")
        print("    2. Start backend: uvicorn app.main:app --reload")
        print("    3. Access API docs: http://localhost:8000/docs")
        return 0
    else:
        print("\n  ⚠ SOME TESTS FAILED. Please fix the issues above.")
        print("\n  Common fixes:")
        print("    • Install dependencies: pip install -r requirements.txt")
        print("    • Setup Vosk model: python setup_enhanced_evaluation.py")
        print("    • Configure .env: python setup_enhanced_evaluation.py")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠ Validation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

"""
Setup script for Enhanced Evaluation System.
Checks dependencies and downloads required models.
"""
import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path


def check_python_version():
    """Check Python version compatibility."""
    print("Checking Python version...")
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required!")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def check_dependencies():
    """Check if required packages are installed."""
    print("\nChecking dependencies...")
    
    required_packages = {
        "mediapipe": "MediaPipe (Behavioral Analysis)",
        "opensmile": "OpenSMILE (Voice Analysis)",
        "vosk": "Vosk (Speech Recognition)",
        "librosa": "Librosa (Audio Processing)",
        "soundfile": "SoundFile (Audio I/O)",
        "scipy": "SciPy (Scientific Computing)",
        "cv2": "OpenCV (Video Processing)",
        "numpy": "NumPy (Numerical Computing)",
    }
    
    missing = []
    installed = []
    
    for package, description in required_packages.items():
        try:
            __import__(package)
            installed.append(f"✓ {description}")
        except ImportError:
            missing.append(f"❌ {description} - NOT INSTALLED")
    
    for pkg in installed:
        print(f"  {pkg}")
    
    for pkg in missing:
        print(f"  {pkg}")
    
    if missing:
        print("\n⚠ Missing packages detected!")
        print("\nTo install missing packages, run:")
        print("  pip install -r requirements.txt")
        return False
    
    print("\n✓ All dependencies installed")
    return True


def setup_vosk_model():
    """Download and setup Vosk model if not present."""
    print("\nSetting up Vosk speech recognition model...")
    
    model_dir = Path("./models/vosk-model-small-en-us-0.15")
    
    if model_dir.exists() and (model_dir / "am" / "final.mdl").exists():
        print(f"✓ Vosk model already installed at {model_dir}")
        return True
    
    print(f"⚠ Vosk model not found at {model_dir}")
    print("\nVosk model is required for offline speech recognition.")
    print("\nOptions:")
    print("1. Download automatically (~40MB)")
    print("2. Skip (use Web Speech API fallback)")
    print("3. Manual download instructions")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == "1":
        return download_vosk_model(model_dir)
    elif choice == "2":
        print("⚠ Skipping Vosk setup. System will use Web Speech API fallback.")
        return True
    elif choice == "3":
        print("\nManual Download Instructions:")
        print("1. Visit: https://alphacephei.com/vosk/models")
        print("2. Download: vosk-model-small-en-us-0.15.zip")
        print("3. Extract to: backend/models/vosk-model-small-en-us-0.15/")
        print("4. Verify structure:")
        print("   backend/models/vosk-model-small-en-us-0.15/")
        print("     ├── am/")
        print("     ├── conf/")
        print("     ├── graph/")
        print("     ├── ivector/")
        print("     └── README")
        return False
    else:
        print("Invalid choice. Skipping Vosk setup.")
        return False


def download_vosk_model(model_dir):
    """Download Vosk model automatically."""
    print("\nDownloading Vosk model...")
    
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    zip_path = Path("./models/vosk-model-small-en-us-0.15.zip")
    
    try:
        # Create models directory
        model_dir.parent.mkdir(parents=True, exist_ok=True)
        
        # Download with progress
        def progress_hook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, int(downloaded * 100 / total_size))
            bar = "=" * (percent // 2)
            print(f"\r  Progress: [{bar:<50}] {percent}%", end="", flush=True)
        
        print(f"  Downloading from: {model_url}")
        urllib.request.urlretrieve(model_url, zip_path, progress_hook)
        print("\n  ✓ Download complete")
        
        # Extract
        print("  Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(model_dir.parent)
        print("  ✓ Extraction complete")
        
        # Cleanup
        zip_path.unlink()
        print("  ✓ Cleanup complete")
        
        print(f"\n✓ Vosk model installed at {model_dir}")
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to download Vosk model: {e}")
        print("\nPlease download manually:")
        print("1. Visit: https://alphacephei.com/vosk/models")
        print("2. Download: vosk-model-small-en-us-0.15.zip")
        print(f"3. Extract to: {model_dir}")
        return False


def setup_environment_variables():
    """Setup environment variables."""
    print("\nSetting up environment variables...")
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print("⚠ .env file not found. Creating from template...")
        create_env_template()
    
    # Check critical variables
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Check Vosk model path
    model_dir = Path("./models/vosk-model-small-en-us-0.15")
    if model_dir.exists():
        vosk_path = env_vars.get('VOSK_MODEL_PATH', '')
        if not vosk_path:
            print(f"  Adding VOSK_MODEL_PATH to .env")
            with open(env_file, 'a') as f:
                f.write(f"\n# Enhanced Evaluation System\n")
                f.write(f"VOSK_MODEL_PATH=./models/vosk-model-small-en-us-0.15\n")
    
    print("✓ Environment variables configured")
    return True


def create_env_template():
    """Create .env template file."""
    template = """# Database
MONGODB_URL=mongodb://interview_user:interview_pass@localhost:27017/interview_platform?authSource=admin
MONGODB_DATABASE=interview_platform

# JWT Authentication
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760

# AI/ML Models
NER_MODEL=yashpwr/resume-ner-bert-v2
NER_CONFIDENCE_THRESHOLD=0.5

# LLM APIs (choose one)
GROQ_API_KEY=gsk_your_groq_key_here
LLM_MODEL=llama-3.3-70b-versatile

# Or use Grok (xAI)
GROK_API_KEY=xai-your_grok_key_here
GROK_MODEL=grok-2-latest
GROK_API_BASE=https://api.x.ai/v1

# CORS
CORS_ORIGINS=http://localhost:3000
CORS_ORIGIN_REGEX=^http://localhost:\\d+$

# Enhanced Evaluation System
VOSK_MODEL_PATH=./models/vosk-model-small-en-us-0.15

# Code Execution (optional - system will auto-detect if not set)
# CODE_RUN_PYTHON=/usr/bin/python3
# CODE_RUN_NODE=/usr/bin/node
# CODE_RUN_GCC=/usr/bin/gcc
# CODE_RUN_GPP=/usr/bin/g++
# CODE_RUN_JAVAC=/usr/bin/javac
# CODE_RUN_JAVA=/usr/bin/java
"""
    
    with open('.env', 'w') as f:
        f.write(template)
    
    print("✓ Created .env template file")


def verify_setup():
    """Verify the complete setup."""
    print("\n" + "="*60)
    print("VERIFYING SETUP")
    print("="*60)
    
    checks = []
    
    # Check MediaPipe
    try:
        import mediapipe as mp
        mp_face_mesh = mp.solutions.face_mesh
        checks.append(("MediaPipe (Behavioral Analysis)", True))
    except Exception as e:
        checks.append(("MediaPipe (Behavioral Analysis)", False, str(e)))
    
    # Check OpenSMILE
    try:
        import opensmile
        smile = opensmile.Smile(
            feature_set=opensmile.FeatureSet.GeMAPSv01b,
            feature_level=opensmile.FeatureLevel.Functionals,
        )
        checks.append(("OpenSMILE (Voice Analysis)", True))
    except Exception as e:
        checks.append(("OpenSMILE (Voice Analysis)", False, str(e)))
    
    # Check Vosk
    try:
        from vosk import Model
        model_path = "./models/vosk-model-small-en-us-0.15"
        if os.path.exists(model_path):
            model = Model(model_path)
            checks.append(("Vosk (Speech Recognition)", True))
        else:
            checks.append(("Vosk (Speech Recognition)", False, "Model not found"))
    except Exception as e:
        checks.append(("Vosk (Speech Recognition)", False, str(e)))
    
    # Check Librosa
    try:
        import librosa
        checks.append(("Librosa (Audio Processing)", True))
    except Exception as e:
        checks.append(("Librosa (Audio Processing)", False, str(e)))
    
    # Print results
    all_ok = True
    for check in checks:
        if check[1]:
            print(f"✓ {check[0]}")
        else:
            print(f"❌ {check[0]}")
            if len(check) > 2:
                print(f"   Error: {check[2]}")
            all_ok = False
    
    return all_ok


def main():
    """Main setup function."""
    print("="*60)
    print("ENHANCED EVALUATION SYSTEM SETUP")
    print("="*60)
    print("\nThis script will setup:")
    print("  • MediaPipe (Behavioral Analysis)")
    print("  • OpenSMILE (Voice Analysis)")
    print("  • Vosk (Speech Recognition)")
    print("  • Required dependencies")
    print("="*60)
    
    # Step 1: Check Python version
    if not check_python_version():
        return False
    
    # Step 2: Check dependencies
    deps_ok = check_dependencies()
    
    # Step 3: Setup Vosk model
    vosk_ok = setup_vosk_model()
    
    # Step 4: Setup environment variables
    env_ok = setup_environment_variables()
    
    # Step 5: Verify setup
    print("\n" + "="*60)
    verified = verify_setup()
    
    # Summary
    print("\n" + "="*60)
    print("SETUP SUMMARY")
    print("="*60)
    
    if deps_ok and verified:
        print("✓ Enhanced Evaluation System is ready!")
        print("\nNext steps:")
        print("1. Start MongoDB:")
        print("   docker-compose up -d")
        print("\n2. Run the test suite:")
        print("   python test_enhanced_evaluation.py")
        print("\n3. Start the backend server:")
        print("   uvicorn app.main:app --reload")
        print("\n4. Access API documentation:")
        print("   http://localhost:8000/docs")
        return True
    else:
        print("⚠ Setup incomplete. Please address the issues above.")
        if not deps_ok:
            print("\nInstall missing dependencies:")
            print("  pip install -r requirements.txt")
        if not vosk_ok:
            print("\nSetup Vosk model manually:")
            print("  See: https://alphacephei.com/vosk/models")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

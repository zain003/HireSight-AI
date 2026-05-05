"""
Application configuration using Pydantic Settings.
Centralized configuration management for the entire application.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "AI Interview Platform"
    DEBUG: bool = False
    
    # Database (MongoDB)
    MONGODB_URL: str = "mongodb://interview_user:interview_pass@localhost:27017/interview_platform?authSource=admin"
    MONGODB_DATABASE: str = "interview_platform"
    
    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg"}
    
    # AI/ML Models
    NER_MODEL: str = "yashpwr/resume-ner-bert-v2"
    NER_CONFIDENCE_THRESHOLD: float = 0.5

    # Groq LLM settings
    GROQ_API_KEY: Optional[str] = None
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    CORS_ORIGIN_REGEX: Optional[str] = r"^http://localhost:\d+$"
    
    # OCR
    TESSERACT_PATH: Optional[str] = None
    
settings = Settings()


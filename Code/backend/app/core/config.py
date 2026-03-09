"""
Application configuration using Pydantic Settings.
Centralized configuration management for the entire application.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "AI Interview Platform"
    DEBUG: bool = False
    
    # Database (MongoDB)
    MONGODB_URL: str = "mongodb://interview_user:interview_pass@localhost:27017/interview_platform?authSource=admin"
    
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
    OPENAI_API_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # OCR
    TESSERACT_PATH: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()


"""
File handling utilities.
Manages file upload, validation, and storage.
"""
import os
import shutil
from pathlib import Path
from typing import Optional
import hashlib
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import FileProcessingError


class FileHandler:
    """Handler for file operations"""
    
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def validate_file(self, filename: str, file_size: int) -> bool:
        """
        Validate file extension and size.
        
        Args:
            filename: Name of the file
            file_size: Size of the file in bytes
            
        Returns:
            True if valid
            
        Raises:
            FileProcessingError: If validation fails
        """
        # Check extension
        ext = Path(filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise FileProcessingError(
                f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Check size
        if file_size > settings.MAX_FILE_SIZE:
            raise FileProcessingError(
                f"File too large. Max size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        return True
    
    def generate_filename(self, user_id: int, original_filename: str) -> str:
        """
        Generate unique filename for storage.
        
        Args:
            user_id: User ID
            original_filename: Original filename
            
        Returns:
            Generated filename
        """
        ext = Path(original_filename).suffix.lower()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"user_{user_id}_resume_{timestamp}{ext}"
    
    def save_file(self, file_content, user_id: int, filename: str) -> str:
        """
        Save file to storage.
        
        Args:
            file_content: File content
            user_id: User ID
            filename: Original filename
            
        Returns:
            Path to saved file
        """
        # Create user directory
        user_dir = os.path.join(self.upload_dir, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        
        # Generate filename
        new_filename = self.generate_filename(user_id, filename)
        file_path = os.path.join(user_dir, new_filename)
        
        # Save file
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file_content, f)
        
        return file_path
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if deleted successfully
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    def get_file_hash(self, file_path: str) -> str:
        """
        Calculate MD5 hash of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash string
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

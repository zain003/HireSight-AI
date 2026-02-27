"""
Resume parsing logic for different file formats.
Extracts text from PDF, DOCX, and image files.
"""
import pdfplumber
from docx import Document
from typing import Optional
import os

from app.core.exceptions import FileProcessingError


class ResumeParser:
    """Parser for extracting text from resume files"""
    
    def parse_file(self, file_path: str) -> str:
        """
        Parse resume file and extract text.
        
        Args:
            file_path: Path to resume file
            
        Returns:
            Extracted text
            
        Raises:
            FileProcessingError: If parsing fails
        """
        if not os.path.exists(file_path):
            raise FileProcessingError(f"File not found: {file_path}")
        
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        try:
            if ext == '.pdf':
                return self._parse_pdf(file_path)
            elif ext in ['.docx', '.doc']:
                return self._parse_docx(file_path)
            elif ext in ['.png', '.jpg', '.jpeg']:
                return self._parse_image(file_path)
            else:
                raise FileProcessingError(f"Unsupported file format: {ext}")
        except Exception as e:
            raise FileProcessingError(f"Failed to parse file: {str(e)}")
    
    def _parse_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file using pdfplumber.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        text = ""
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        return self._clean_text(text)
    
    def _parse_docx(self, file_path: str) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text
        """
        doc = Document(file_path)
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return self._clean_text(text)
    
    def _parse_image(self, file_path: str) -> str:
        """
        Extract text from image using OCR (pytesseract).
        
        Args:
            file_path: Path to image file
            
        Returns:
            Extracted text
        """
        try:
            import pytesseract
            from PIL import Image
            
            # Open image
            image = Image.open(file_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(image)
            
            return self._clean_text(text)
        except ImportError:
            raise FileProcessingError("pytesseract not installed. Install with: pip install pytesseract")
        except Exception as e:
            raise FileProcessingError(f"OCR failed: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Remove special characters but keep basic punctuation
        # text = re.sub(r'[^\w\s\.\,\-\(\)]', '', text)
        
        return text.strip()


# Singleton instance
_parser = None


def get_parser() -> ResumeParser:
    """Get singleton parser instance"""
    global _parser
    if _parser is None:
        _parser = ResumeParser()
    return _parser

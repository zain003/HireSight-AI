"""
Custom exceptions for the application.
Provides clear error handling across all modules.
"""


class BaseAPIException(Exception):
    """Base exception for all API errors"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(BaseAPIException):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(BaseAPIException):
    """Raised when user lacks permissions"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)


class NotFoundError(BaseAPIException):
    """Raised when resource is not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(BaseAPIException):
    """Raised when validation fails"""
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


class FileProcessingError(BaseAPIException):
    """Raised when file processing fails"""
    def __init__(self, message: str = "File processing error"):
        super().__init__(message, status_code=500)

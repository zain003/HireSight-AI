"""
Admin authentication logic for single admin user.
"""
from app.auth.models import User
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import AuthenticationError

ADMIN_EMAIL = "admin@fyp.com"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class AdminAuthService:
    """Service for admin authentication"""
    @staticmethod
    async def authenticate_admin(username: str, password: str):
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            # Return a mock admin user object
            return {
                "id": "admin",
                "email": ADMIN_EMAIL,
                "username": ADMIN_USERNAME,
                "full_name": "Admin User",
                "is_active": True,
                "created_at": None,
                "updated_at": None
            }
        return None

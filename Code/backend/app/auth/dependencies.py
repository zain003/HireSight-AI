"""
Dependency injection for authentication module.
Provides reusable dependencies for route protection.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.auth.models import User
from app.auth.service import AuthService


# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get current authenticated user.
    Validates JWT token and returns user object.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Debug logging
    print("[DEBUG] Received token:", token)
    payload = decode_access_token(token)
    print("[DEBUG] Decoded payload:", payload)
    if payload is None:
        print("[DEBUG] Token decode failed.")
        raise credentials_exception

    user_id: str = payload.get("user_id")
    print("[DEBUG] Extracted user_id:", user_id)
    if user_id is None:
        print("[DEBUG] user_id missing in payload.")
        raise credentials_exception

    # Get user from database
    auth_service = AuthService()
    user = await auth_service.get_user_by_id(user_id)
    print("[DEBUG] User lookup result:", user)

    if user is None:
        print("[DEBUG] User not found in database.")
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is active.
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        Active user object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user

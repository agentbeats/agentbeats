from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from .supabase import supabase_auth
import os

async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Extract and validate current user from JWT token.
    Returns mock user data in dev mode when DEV_LOGIN=true.
    """
    # Check if we're in dev login mode
    if os.getenv("DEV_LOGIN") == "true":
        return {
            "id": "dev-user-id",
            "email": "dev@agentbeats.org",
            "app_metadata": {"provider": "dev"}
        }
    
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    
    # Verify JWT token
    user_data = supabase_auth.verify_jwt(token)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_data

async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Extract current user from JWT token if present, return None if not authenticated.
    Returns mock user data in dev mode when DEV_LOGIN=true.
    """
    # Check if we're in dev login mode
    if os.getenv("DEV_LOGIN") == "true":
        return {
            "id": "dev-user-id",
            "email": "dev@agentbeats.org",
            "app_metadata": {"provider": "dev"}
        }
    
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    
    try:
        user_data = supabase_auth.verify_jwt(token)
        return user_data
    except:
        return None

def require_auth(func):
    """
    Decorator to require authentication for endpoints.
    """
    async def wrapper(*args, **kwargs):
        # This would be used to wrap endpoints that require auth
        # For now, just pass through
        return await func(*args, **kwargs)
    return wrapper 
# -*- coding:utf-8 -*-

import os
import jwt

from fastapi import Request, HTTPException, status
from typing import Optional, Dict, Any


def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token and return user data.
    """
    # In dev mode, this method shouldn't be called, but return None if it is
    if os.getenv("DEV_LOGIN") == "true":
        print("Warning: verify_jwt called in dev mode, returning None")
        return None
        
    try:
        # Decode JWT without verification first to get user data
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        # Extract user data from JWT payload
        user_data = {
            "id": decoded.get("sub"),
            "email": decoded.get("email"),
            "app_metadata": decoded.get("app_metadata", {}),
            "user_metadata": decoded.get("user_metadata", {}),
            "aud": decoded.get("aud"),
            "exp": decoded.get("exp"),
            "iat": decoded.get("iat")
        }
        
        return user_data if user_data["id"] else None
        
    except Exception as e:
        print(f"JWT verification error: {e}")
        return None


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
    user_data = verify_jwt(token)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_data

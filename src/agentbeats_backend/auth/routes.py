from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from typing import Dict, Any
import os

from .middleware import get_current_user, get_optional_user
from .supabase import supabase_auth

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/login/{provider}")
async def login(provider: str, request: Request):
    """
    Initiate OAuth login with specified provider.
    """
    if provider not in ['github', 'google', 'slack']:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    # Get Supabase URL for OAuth
    supabase_url = os.getenv("SUPABASE_URL")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # Redirect to Supabase OAuth
    oauth_url = f"{supabase_url}/auth/v1/authorize"
    redirect_uri = f"{frontend_url}/auth/callback"
    
    params = {
        "provider": provider,
        "redirect_to": redirect_uri,
        "client_id": os.getenv("SUPABASE_ANON_KEY")
    }
    
    # Build query string
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{oauth_url}?{query_string}"
    
    return RedirectResponse(url=full_url)

@router.get("/callback")
async def auth_callback(request: Request):
    """
    Handle OAuth callback from Supabase.
    """
    # Get URL parameters
    access_token = request.query_params.get("access_token")
    refresh_token = request.query_params.get("refresh_token")
    error = request.query_params.get("error")
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    if error:
        # Handle OAuth error
        return RedirectResponse(
            url=f"{frontend_url}/login?error={error}"
        )
    
    if access_token:
        # Successful authentication
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?token={access_token}&refresh_token={refresh_token}"
        )
    
    # No token provided
    return RedirectResponse(
        url=f"{frontend_url}/login?error=no_token"
    )

@router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current user information.
    """
    return {
        "id": current_user["id"],
        "email": current_user.get("email"),
        "app_metadata": current_user.get("app_metadata", {}),
        "user_metadata": current_user.get("user_metadata", {}),
        "provider": current_user.get("app_metadata", {}).get("provider"),
        "providers": current_user.get("app_metadata", {}).get("providers", [])
    }

@router.post("/logout")
async def logout(request: Request):
    """
    Logout endpoint.
    """
    auth_header = request.headers.get("Authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        success = supabase_auth.sign_out(token)
        
        if success:
            return {"message": "Successfully logged out"}
        else:
            raise HTTPException(status_code=500, detail="Failed to logout")
    
    return {"message": "No active session"}

@router.get("/health")
async def auth_health():
    """
    Health check for auth service.
    """
    return {
        "status": "healthy",
        "supabase_url": os.getenv("SUPABASE_URL") is not None,
        "supabase_key": os.getenv("SUPABASE_ANON_KEY") is not None
    } 
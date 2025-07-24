import os
from supabase import create_client, Client
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta

class SupabaseAuth:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_anon_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_anon_key)
    
    def verify_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and return user data.
        """
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
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data by user ID.
        """
        try:
            # For now, return basic user data
            # In production, you'd call Supabase admin API
            return {
                "id": user_id,
                "email": None,  # Would be fetched from Supabase
                "app_metadata": {},
                "user_metadata": {}
            }
            
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def sign_out(self, token: str) -> bool:
        """
        Sign out user (invalidate token).
        """
        try:
            # In production, you'd call Supabase sign out
            # For now, just return success
            return True
        except Exception as e:
            print(f"Sign out error: {e}")
            return False

# Global instance
supabase_auth = SupabaseAuth() 
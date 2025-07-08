import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status

from ..db.storage import db

router = APIRouter()

@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(user_info: Dict[str, Any]):
    """
    Create a new user. Required fields: username, password, email, full_name
    """
    try:
        required_fields = ["username", "password", "email", "full_name"]
        for field in required_fields:
            if field not in user_info:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        user_record = {
            "username": user_info["username"],
            "password": user_info["password"],
            "email": user_info["email"],
            "full_name": user_info["full_name"],
            "elo": 1000,
            "agents": user_info.get("agents", {}),  # Accept agents dict if provided
        }
        # Save to database (userid will be the generated id)
        created_user = db.create("users", user_record)
        # Add userid field for convenience
        created_user["userid"] = created_user["id"]
        db.update("users", created_user["id"], created_user)
        return created_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.get("/users")
def list_users() -> List[Dict[str, Any]]:
    """List all users."""
    try:
        users = db.list("users")
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing users: {str(e)}")

@router.get("/users/{user_id}")
def get_user(user_id: str) -> Dict[str, Any]:
    """Get a single user by ID."""
    try:
        user = db.read("users", user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")

@router.delete("/users")
def delete_all_users():
    try:
        users = db.list("users")
        for user in users:
            db.delete("users", user["id"])
        return {"detail": "All users deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting users: {str(e)}") 
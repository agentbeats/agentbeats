# -*- coding: utf-8 -*-
"""
Unified assets routes for AgentBeats backend.
Handles both static assets and user uploads.
"""

import os
import shutil
import hashlib
import mimetypes
import uuid
import secrets
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..db.storage import SQLiteStorage

# Initialize router
router = APIRouter(prefix="/assets", tags=["assets"])

# Initialize storage (relative to project root)
storage = SQLiteStorage("src/backend/db/data")

# Base assets directory (relative to project root)
ASSETS_BASE = "src/backend/assets"
UPLOADS_BASE = os.path.join(ASSETS_BASE, "uploads")
os.makedirs(ASSETS_BASE, exist_ok=True)
os.makedirs(UPLOADS_BASE, exist_ok=True)

# Security configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {
    # Images
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp',
    # Documents
    '.txt', '.md', '.pdf', '.doc', '.docx',
    # Archives
    '.zip', '.tar', '.gz',
    # Data
    '.json', '.csv', '.xml'
}
ALLOWED_MIME_TYPES = {
    # Images
    'image/png', 'image/jpeg', 'image/gif', 'image/svg+xml', 'image/webp',
    # Documents
    'text/plain', 'text/markdown', 'application/pdf', 
    'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    # Archives
    'application/zip', 'application/x-tar', 'application/gzip',
    # Data
    'application/json', 'text/csv', 'application/xml'
}

# Create folder structure
FOLDERS = {
    "avatars": {
        "users": os.path.join(UPLOADS_BASE, "avatars", "users"),
        "agents": os.path.join(UPLOADS_BASE, "avatars", "agents")
    },
    "battles": os.path.join(UPLOADS_BASE, "battles")
}

# Create all folders
for folder_path in FOLDERS.values():
    if isinstance(folder_path, dict):
        for subfolder in folder_path.values():
            os.makedirs(subfolder, exist_ok=True)
    else:
        os.makedirs(folder_path, exist_ok=True)

class AssetInfo(BaseModel):
    """Asset information model."""
    asset_id: str
    asset_name: str
    original_filename: str
    file_path: str
    mime_type: str
    size_bytes: int
    uploaded_at: str
    uploaded_by: str
    category: str  # "avatar", "battle", etc.
    subcategory: Optional[str] = None  # "users", "agents", battle_id, etc.

def _sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent security issues."""
    if not filename:
        return "unnamed_file"
    
    # Remove path separators and dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:100-len(ext)] + ext
    
    # Ensure it's not empty
    if not filename:
        filename = "unnamed_file"
    
    return filename

def _validate_file_extension(filename: str) -> bool:
    """Validate file extension is allowed."""
    if not filename:
        return False
    
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS

def _validate_mime_type(mime_type: str) -> bool:
    """Validate MIME type is allowed."""
    return mime_type in ALLOWED_MIME_TYPES

def _validate_file_size(size: int) -> bool:
    """Validate file size is within limits."""
    return size <= MAX_FILE_SIZE

def _generate_secure_asset_id(filename: str, content: bytes) -> str:
    """Generate a secure, unique asset ID with salt."""
    # Generate a random salt
    salt = secrets.token_hex(8)
    
    # Create a hash of filename + content + salt
    hash_input = f"{filename}:{salt}:{content.hex()}"
    content_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
    
    # Sanitize filename for use in asset ID
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', Path(filename).stem)
    safe_name = safe_name[:20]  # Limit length
    
    return f"{safe_name}_{content_hash}"

def _get_mime_type(filename: str, content: bytes) -> str:
    """Get the MIME type of a file with content validation."""
    # First try to get from filename
    mime_type, _ = mimetypes.guess_type(filename)
    
    # If no MIME type from filename, try to detect from content
    if not mime_type:
        # Simple content-based detection
        if content.startswith(b'\x89PNG\r\n\x1a\n'):
            mime_type = 'image/png'
        elif content.startswith(b'\xff\xd8\xff'):
            mime_type = 'image/jpeg'
        elif content.startswith(b'GIF87a') or content.startswith(b'GIF89a'):
            mime_type = 'image/gif'
        elif content.startswith(b'<?xml') and b'<svg' in content:
            mime_type = 'image/svg+xml'
        elif content.startswith(b'PK\x03\x04'):
            mime_type = 'application/zip'
        else:
            mime_type = 'application/octet-stream'
    
    # Ensure we have a valid MIME type
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    return mime_type

def _save_file_to_db(asset_info: AssetInfo) -> Dict[str, Any]:
    """Save asset information to database."""
    asset_data = asset_info.dict()
    return storage.create("assets", asset_data)

def _validate_upload_request(file: UploadFile, content: bytes) -> tuple[str, str]:
    """Validate upload request and return sanitized filename and MIME type."""
    # Validate file has a name
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Sanitize filename
    sanitized_filename = _sanitize_filename(file.filename)
    
    # Validate file extension
    if not _validate_file_extension(sanitized_filename):
        raise HTTPException(
            status_code=400, 
            detail=f"File extension not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate file size
    if not _validate_file_size(len(content)):
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Get MIME type from content and filename (ignore client-provided MIME type)
    mime_type = _get_mime_type(sanitized_filename, content)
    
    # Validate MIME type
    if not _validate_mime_type(mime_type):
        raise HTTPException(
            status_code=400, 
            detail=f"MIME type not allowed: {mime_type}"
        )
    
    # Additional security: also validate the client-provided MIME type if it exists
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Client MIME type not allowed: {file.content_type}"
        )
    
    return sanitized_filename, mime_type

# ============================================================================
# STATIC ASSETS
# ============================================================================

@router.get("/static/{file_path:path}")
async def serve_static_asset(file_path: str):
    """
    Serve static assets from the assets/static directory.
    
    This allows serving things like:
    - /assets/static/images/logo.png
    - /assets/static/css/styles.css
    - /assets/static/js/app.js
    - /assets/static/fonts/roboto.woff2
    """
    try:
        # Security check: prevent directory traversal
        if ".." in file_path or file_path.startswith("/") or "\\" in file_path:
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Additional security: check for any path traversal attempts
        normalized_path = os.path.normpath(file_path)
        if normalized_path.startswith("..") or ".." in normalized_path:
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Additional security: check for encoded path traversal
        import urllib.parse
        decoded_path = urllib.parse.unquote(file_path)
        if ".." in decoded_path or decoded_path.startswith("/") or "\\" in decoded_path:
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Construct the full file path
        full_path = os.path.join(ASSETS_BASE, "static", file_path)
        
        # Additional security: ensure path is within static directory
        static_dir = os.path.abspath(os.path.join(ASSETS_BASE, "static"))
        full_path_abs = os.path.abspath(full_path)
        
        if not full_path_abs.startswith(static_dir):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Check if file exists
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Determine MIME type
        mime_type = _get_mime_type(file_path, b"")
        
        return FileResponse(
            full_path,
            media_type=mime_type,
            filename=os.path.basename(file_path)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving static asset: {str(e)}")

# ============================================================================
# UPLOADS
# ============================================================================

@router.post("/uploads/avatar/user")
async def upload_user_avatar(
    file: UploadFile = File(...),
    user_id: str = Form(...)
):
    """Upload a user avatar."""
    try:
        # Validate user_id
        if not user_id or len(user_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        # Read file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Validate upload request
        sanitized_filename, mime_type = _validate_upload_request(file, content)
        
        # Generate secure asset ID
        asset_id = _generate_secure_asset_id(sanitized_filename, content)
        file_extension = Path(sanitized_filename).suffix
        new_filename = f"{asset_id}{file_extension}"
        
        # Save file
        file_path = os.path.join(FOLDERS["avatars"]["users"], new_filename)
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create asset info
        asset_info = AssetInfo(
            asset_id=asset_id,
            asset_name=new_filename,
            original_filename=sanitized_filename,
            file_path=file_path,
            mime_type=mime_type,
            size_bytes=len(content),
            uploaded_at=datetime.utcnow().isoformat() + "Z",
            uploaded_by=user_id.strip(),
            category="avatar",
            subcategory="users"
        )
        
        # Save to database
        saved_asset = _save_file_to_db(asset_info)
        
        return {
            "success": True,
            "asset_id": asset_id,
            "url": f"/assets/uploads/avatar/user/{asset_id}",
            "asset_info": saved_asset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/uploads/avatar/agent")
async def upload_agent_avatar(
    file: UploadFile = File(...),
    agent_id: str = Form(...)
):
    """Upload an agent avatar."""
    try:
        # Validate agent_id
        if not agent_id or len(agent_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="Invalid agent ID")
        
        # Read file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Validate upload request
        sanitized_filename, mime_type = _validate_upload_request(file, content)
        
        # Generate secure asset ID
        asset_id = _generate_secure_asset_id(sanitized_filename, content)
        file_extension = Path(sanitized_filename).suffix
        new_filename = f"{asset_id}{file_extension}"
        
        # Save file
        file_path = os.path.join(FOLDERS["avatars"]["agents"], new_filename)
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create asset info
        asset_info = AssetInfo(
            asset_id=asset_id,
            asset_name=new_filename,
            original_filename=sanitized_filename,
            file_path=file_path,
            mime_type=mime_type,
            size_bytes=len(content),
            uploaded_at=datetime.utcnow().isoformat() + "Z",
            uploaded_by=agent_id.strip(),
            category="avatar",
            subcategory="agents"
        )
        
        # Save to database
        saved_asset = _save_file_to_db(asset_info)
        
        return {
            "success": True,
            "asset_id": asset_id,
            "url": f"/assets/uploads/avatar/agent/{asset_id}",
            "asset_info": saved_asset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/uploads/battle/{battle_id}")
async def upload_battle_asset(
    battle_id: str,
    file: UploadFile = File(...),
    asset_name: Optional[str] = Form(None),
    uploaded_by: str = Form(...)
):
    """Upload a battle asset (for use with SDK static_expose)."""
    try:
        # Validate battle_id
        if not battle_id or len(battle_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="Invalid battle ID")
        
        # Validate uploaded_by
        if not uploaded_by or len(uploaded_by.strip()) == 0:
            raise HTTPException(status_code=400, detail="Invalid uploader ID")
        
        # Read file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Validate upload request
        sanitized_filename, mime_type = _validate_upload_request(file, content)
        
        # Generate secure asset ID
        asset_id = _generate_secure_asset_id(sanitized_filename, content)
        file_extension = Path(sanitized_filename).suffix
        
        # Sanitize asset_name if provided
        if asset_name:
            sanitized_asset_name = _sanitize_filename(asset_name)
            new_filename = f"{asset_id}_{sanitized_asset_name}"
            if not new_filename.endswith(file_extension):
                new_filename += file_extension
        else:
            new_filename = f"{asset_id}{file_extension}"
        
        # Create battle folder with sanitized battle_id
        sanitized_battle_id = re.sub(r'[^a-zA-Z0-9_-]', '_', battle_id.strip())
        battle_folder = os.path.join(FOLDERS["battles"], sanitized_battle_id)
        os.makedirs(battle_folder, exist_ok=True)
        
        # Save file
        file_path = os.path.join(battle_folder, new_filename)
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create asset info
        asset_info = AssetInfo(
            asset_id=asset_id,
            asset_name=new_filename,
            original_filename=sanitized_filename,
            file_path=file_path,
            mime_type=mime_type,
            size_bytes=len(content),
            uploaded_at=datetime.utcnow().isoformat() + "Z",
            uploaded_by=uploaded_by.strip(),
            category="battle",
            subcategory=sanitized_battle_id
        )
        
        # Save to database
        saved_asset = _save_file_to_db(asset_info)
        
        return {
            "success": True,
            "asset_id": asset_id,
            "url": f"/assets/uploads/battle/{sanitized_battle_id}/{asset_id}",
            "asset_info": saved_asset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# ============================================================================
# ASSET RETRIEVAL
# ============================================================================

@router.get("/uploads/avatar/user/{asset_id}")
async def get_user_avatar(asset_id: str):
    """Get a user avatar by asset ID."""
    try:
        # Validate asset_id
        if not asset_id or len(asset_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="Invalid asset ID")
        
        # Get asset info from database
        asset_info = storage.read("assets", asset_id.strip())
        if not asset_info:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Check if it's a user avatar
        if asset_info.get("category") != "avatar" or asset_info.get("subcategory") != "users":
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Check if file exists
        file_path = asset_info["file_path"]
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Return file
        return FileResponse(
            file_path,
            media_type=asset_info["mime_type"],
            filename=asset_info["asset_name"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")

@router.get("/uploads/avatar/agent/{asset_id}")
async def get_agent_avatar(asset_id: str):
    """Get an agent avatar by asset ID."""
    try:
        # Validate asset_id
        if not asset_id or len(asset_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="Invalid asset ID")
        
        # Get asset info from database
        asset_info = storage.read("assets", asset_id.strip())
        if not asset_info:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Check if it's an agent avatar
        if asset_info.get("category") != "avatar" or asset_info.get("subcategory") != "agents":
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Check if file exists
        file_path = asset_info["file_path"]
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Return file
        return FileResponse(
            file_path,
            media_type=asset_info["mime_type"],
            filename=asset_info["asset_name"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")

@router.get("/uploads/battle/{battle_id}/{asset_id}")
async def get_battle_asset(battle_id: str, asset_id: str):
    """Get a battle asset by battle ID and asset ID."""
    try:
        # Validate parameters
        if not battle_id or len(battle_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="Invalid battle ID")
        if not asset_id or len(asset_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="Invalid asset ID")
        
        # Get asset info from database
        asset_info = storage.read("assets", asset_id.strip())
        if not asset_info:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Check if it's a battle asset for the correct battle
        sanitized_battle_id = re.sub(r'[^a-zA-Z0-9_-]', '_', battle_id.strip())
        if asset_info.get("category") != "battle" or asset_info.get("subcategory") != sanitized_battle_id:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Check if file exists
        file_path = asset_info["file_path"]
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Return file
        return FileResponse(
            file_path,
            media_type=asset_info["mime_type"],
            filename=asset_info["asset_name"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")

# ============================================================================
# ASSET MANAGEMENT
# ============================================================================

@router.get("/uploads/assets")
async def list_assets(
    category: Optional[str] = Query(None),
    subcategory: Optional[str] = Query(None),
    uploaded_by: Optional[str] = Query(None)
):
    """List uploaded assets with optional filtering."""
    try:
        # Get all assets
        assets = storage.list("assets")
        
        # Apply filters
        if category:
            assets = [a for a in assets if a.get("category") == category]
        if subcategory:
            assets = [a for a in assets if a.get("subcategory") == subcategory]
        if uploaded_by:
            assets = [a for a in assets if a.get("uploaded_by") == uploaded_by]
        
        return {
            "count": len(assets),
            "assets": assets
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing assets: {str(e)}")

@router.get("/uploads/assets/{asset_id}")
async def get_asset_info(asset_id: str):
    """Get detailed information about an asset."""
    try:
        # Validate asset_id
        if not asset_id or len(asset_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="Invalid asset ID")
        
        asset_info = storage.read("assets", asset_id.strip())
        if not asset_info:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return asset_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving asset info: {str(e)}")

@router.delete("/uploads/assets/{asset_id}")
async def delete_asset(asset_id: str):
    """Delete an asset."""
    try:
        # Validate asset_id
        if not asset_id or len(asset_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="Invalid asset ID")
        
        # Get asset info
        asset_info = storage.read("assets", asset_id.strip())
        if not asset_info:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Delete file
        file_path = asset_info["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        storage.delete("assets", asset_id.strip())
        
        return {"success": True, "message": "Asset deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting asset: {str(e)}")

@router.get("/list")
async def list_asset_categories():
    """List available asset categories and their descriptions."""
    return {
        "categories": {
        "static": {
            "description": "Static assets like images, CSS, JS, fonts",
                "endpoint": "/assets/static/{file_path}"
        },
        "uploads": {
            "description": "User-uploaded content (avatars, battle assets)",
                "endpoints": {
                    "user_avatars": "/assets/uploads/avatar/user",
                    "agent_avatars": "/assets/uploads/avatar/agent", 
                    "battle_assets": "/assets/uploads/battle/{battle_id}",
                    "list_assets": "/assets/uploads/assets"
                }
            }
        }
    } 
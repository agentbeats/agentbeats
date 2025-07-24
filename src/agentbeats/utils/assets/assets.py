# -*- coding: utf-8 -*-
"""
Asset management utilities for AgentBeats SDK.
"""

import os
import requests
from typing import Optional

def static_expose(file_path: str, asset_name: Optional[str] = None, battle_id: Optional[str] = None, uploaded_by: Optional[str] = None, backend_url: str = "http://localhost:9000") -> str:
    """
    Upload a file to the backend for frontend access.
    """
    try:
        # Validate file exists and is readable
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"Cannot read file: {file_path}")
        
        # Validate required parameters
        if not battle_id:
            raise ValueError("battle_id is required for file upload")
        
        if not uploaded_by:
            uploaded_by = "agent"
        
        # Upload to backend
        with open(file_path, 'rb') as f:
            # Let the backend determine the MIME type from content and filename
            files = {'file': (os.path.basename(file_path), f)}
            
            data = {
                'uploaded_by': uploaded_by
            }
            
            if asset_name:
                data['asset_name'] = asset_name
            
            # Upload to backend - backend handles all security validation
            response = requests.post(
                f"{backend_url}/assets/uploads/battle/{battle_id}",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                asset_url = f"{backend_url}{result['url']}"
                print(f"Asset uploaded to backend: {asset_name or os.path.basename(file_path)} -> {asset_url}")
                return asset_url
            else:
                raise Exception(f"Backend upload failed: {response.status_code} - {response.text}")
                
    except Exception as e:
        print(f"Error uploading asset {file_path}: {str(e)}")
        raise 
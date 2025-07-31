# -*- coding: utf-8 -*-
"""
Asset management utilities for AgentBeats SDK.
"""

import os
import requests
from typing import Optional
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
import uuid

def static_expose(file_path: str, filename: Optional[str] = None, battle_id: Optional[str] = None) -> str:
    """
    Expose a file to the static directory using Google Cloud Storage.
    
    Args:
        file_path (str): Path to the file to be exposed
        filename (Optional[str]): Name for the asset (optional)
        battle_id (Optional[str]): Battle ID for organization (optional)
        
    Returns:
        str: Public URL of the uploaded file or error message
    """    
    print("Exposing file to the static directory using Google Cloud Storage...")
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            error_msg = f"ERROR: File {file_path} does not exist"
            return error_msg
        
        # Get bucket name from environment variable or use default
        bucket_name = os.getenv('GCP_BUCKET_NAME', 'agentbeats-static-expose')
        
        # Initialize Google Cloud Storage client
        storage_client = storage.Client()
        
        bucket = storage_client.bucket(bucket_name)
        
        # Generate unique filename to avoid conflicts
        if filename is None:
            file_extension = os.path.splitext(file_path)[1]
            filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create blob and upload file
        blob = bucket.blob(filename)
        
        blob.upload_from_filename(file_path)
        
        # Make the blob publicly accessible
        blob.make_public()
        
        # Return the public URL
        public_url = blob.public_url
        
        return public_url
        
    except GoogleCloudError as e:
        print("GCP Error: " + str(e))
        error_msg = f"GCP Error: {str(e)}"
        return error_msg
    except Exception as e:
        print("ERROR: Failed to expose file " + file_path + ": " + str(e))
        error_msg = f"ERROR: Failed to expose file {file_path}: {str(e)}"
        return error_msg
    
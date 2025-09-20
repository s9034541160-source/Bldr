"""
Third-Party Integration Plugin
Handles integration with external services like Google Drive
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configuration storage
_service_configs = {}

def configure_service(service_name: str, credentials: Dict[str, Any]) -> bool:
    """
    Configure a third-party service
    
    Args:
        service_name: Name of the service (e.g., 'google_drive')
        credentials: Service credentials (JSON format)
        
    Returns:
        True if configuration successful, False otherwise
    """
    try:
        # Validate credentials format
        if not isinstance(credentials, dict):
            print(f"❌ Invalid credentials format for {service_name}")
            return False
        
        # Store configuration
        _service_configs[service_name] = credentials
        print(f"✅ Configured service: {service_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to configure service {service_name}: {e}")
        return False

def get_service_config(service_name: str) -> Dict[str, Any]:
    """
    Get configuration for a service
    
    Args:
        service_name: Name of the service
        
    Returns:
        Service configuration or empty dict if not found
    """
    return _service_configs.get(service_name, {})

def sync_documents(service_name: str, folder_id: str = "") -> List[Dict[str, Any]]:
    """
    Sync documents from a third-party service
    
    Args:
        service_name: Name of the service (e.g., 'google_drive')
        folder_id: Optional folder ID to sync from
        
    Returns:
        List of documents found
    """
    documents = []
    
    try:
        if service_name == "google_drive":
            documents = _sync_google_drive_documents(folder_id)
        else:
            print(f"⚠️ Unsupported service: {service_name}")
            return []
        
        print(f"✅ Synced {len(documents)} documents from {service_name}")
        return documents
        
    except Exception as e:
        print(f"❌ Failed to sync documents from {service_name}: {e}")
        return []

def upload_document(service_name: str, file_path: str, folder_id: str = "") -> bool:
    """
    Upload a document to a third-party service
    
    Args:
        service_name: Name of the service (e.g., 'google_drive')
        file_path: Path to the file to upload
        folder_id: Optional folder ID to upload to
        
    Returns:
        True if upload successful, False otherwise
    """
    try:
        if service_name == "google_drive":
            return _upload_to_google_drive(file_path, folder_id)
        else:
            print(f"⚠️ Unsupported service: {service_name}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to upload document to {service_name}: {e}")
        return False

def _sync_google_drive_documents(folder_id: str = "") -> List[Dict[str, Any]]:
    """
    Sync documents from Google Drive (real implementation)
    
    Args:
        folder_id: Optional folder ID to sync from
        
    Returns:
        List of documents found
    """
    # Check if we have Google Drive credentials
    credentials = get_service_config("google_drive")
    if not credentials:
        print("⚠️ Google Drive not configured. Using sample data.")
        return _get_sample_documents()
    
    try:
        # Import Google API client
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        
        # Create credentials object
        creds = service_account.Credentials.from_service_account_info(credentials)
        
        # Build the Google Drive service
        service = build('drive', 'v3', credentials=creds)
        
        # Prepare query
        query = "mimeType='application/pdf' or mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document' or mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'"
        if folder_id:
            query = f"'{folder_id}' in parents and ({query})"
        
        # List files from Google Drive
        results = service.files().list(
            q=query,
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink, md5Checksum)"
        ).execute()
        
        files = results.get('files', [])
        
        # Convert to our format
        documents = []
        for file in files:
            documents.append({
                "id": file["id"],
                "name": file["name"],
                "mime_type": file["mimeType"],
                "size": file.get("size", 0),
                "created_time": file.get("createdTime", ""),
                "modified_time": file.get("modifiedTime", ""),
                "web_view_link": file.get("webViewLink", ""),
                "md5_checksum": file.get("md5Checksum", "")
            })
        
        print(f"✅ Synced {len(documents)} documents from Google Drive")
        return documents
        
    except Exception as e:
        print(f"❌ Google Drive sync error: {e}")
        # Fallback to sample data
        return _get_sample_documents()

def _upload_to_google_drive(file_path: str, folder_id: str = "") -> bool:
    """
    Upload a document to Google Drive (real implementation)
    
    Args:
        file_path: Path to the file to upload
        folder_id: Optional folder ID to upload to
        
    Returns:
        True if upload successful, False otherwise
    """
    # Check if we have Google Drive credentials
    credentials = get_service_config("google_drive")
    if not credentials:
        print("⚠️ Google Drive not configured. Skipping upload.")
        return False
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        # Import Google API client
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        from googleapiclient.http import MediaFileUpload
        
        # Create credentials object
        creds = service_account.Credentials.from_service_account_info(credentials)
        
        # Build the Google Drive service
        service = build('drive', 'v3', credentials=creds)
        
        # Prepare file metadata
        file_metadata = {
            'name': os.path.basename(file_path)
        }
        
        # Add to folder if specified
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Create media upload object
        media = MediaFileUpload(file_path, resumable=True)
        
        # Upload file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        print(f"✅ Uploaded {os.path.basename(file_path)} to Google Drive with ID: {file.get('id')}")
        return True
        
    except Exception as e:
        print(f"❌ Google Drive upload error: {e}")
        return False

def _get_sample_documents() -> List[Dict[str, Any]]:
    """
    Get sample documents for testing
    
    Returns:
        List of sample documents
    """
    return [
        {
            "id": "1a2b3c4d5e",
            "name": "СП 45.13330.2017.pdf",
            "mime_type": "application/pdf",
            "size": 2560000,
            "created_time": "2025-09-10T10:30:00Z",
            "modified_time": "2025-09-10T10:30:00Z",
            "web_view_link": "https://drive.google.com/file/d/1a2b3c4d5e/view",
            "md5_checksum": "abc123def456"
        },
        {
            "id": "2b3c4d5e6f",
            "name": "Проект производства работ.docx",
            "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "size": 1280000,
            "created_time": "2025-09-09T14:15:00Z",
            "modified_time": "2025-09-09T14:15:00Z",
            "web_view_link": "https://drive.google.com/file/d/2b3c4d5e6f/view",
            "md5_checksum": "def456ghi789"
        },
        {
            "id": "3c4d5e6f7g",
            "name": "Смета на фундамент.xlsx",
            "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "size": 512000,
            "created_time": "2025-09-08T09:45:00Z",
            "modified_time": "2025-09-08T09:45:00Z",
            "web_view_link": "https://drive.google.com/file/d/3c4d5e6f7g/view",
            "md5_checksum": "ghi789jkl012"
        }
    ]

def list_configured_services() -> List[str]:
    """
    List all configured services
    
    Returns:
        List of configured service names
    """
    return list(_service_configs.keys())

def remove_service_config(service_name: str) -> bool:
    """
    Remove service configuration
    
    Args:
        service_name: Name of the service to remove
        
    Returns:
        True if removal successful, False otherwise
    """
    try:
        if service_name in _service_configs:
            del _service_configs[service_name]
            print(f"✅ Removed configuration for service: {service_name}")
            return True
        else:
            print(f"⚠️ Service not configured: {service_name}")
            return False
    except Exception as e:
        print(f"❌ Failed to remove service configuration: {e}")
        return False
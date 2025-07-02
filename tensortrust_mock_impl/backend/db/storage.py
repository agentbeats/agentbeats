import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

class JSONStorage:
    """Simple JSON file-based storage to simulate a database."""
    
    def __init__(self, db_dir: str):
        self.db_dir = db_dir
        os.makedirs(self.db_dir, exist_ok=True)
        
    def _get_file_path(self, collection: str) -> str:
        """Get the path to a collection file."""
        return os.path.join(self.db_dir, f"{collection}.json")
        
    def _read_collection(self, collection: str) -> Dict[str, Any]:
        """Read a collection from disk."""
        file_path = self._get_file_path(collection)
        if not os.path.exists(file_path):
            return {}
        
        with open(file_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
                
    def _write_collection(self, collection: str, data: Dict[str, Any]):
        """Write a collection to disk."""
        file_path = self._get_file_path(collection)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
            
    def create(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document in a collection."""
        collection_data = self._read_collection(collection)
        
        # Generate an ID if not provided
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
            
        # Add created timestamp if not provided
        if 'createdAt' not in data:
            data['createdAt'] = datetime.utcnow().isoformat()
            
        collection_data[data['id']] = data
        self._write_collection(collection, collection_data)
        return data
        
    def read(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Read a document from a collection."""
        collection_data = self._read_collection(collection)
        return collection_data.get(doc_id)
        
    def update(self, collection: str, doc_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a document in a collection."""
        collection_data = self._read_collection(collection)
        if doc_id not in collection_data:
            return None
            
        # Update the document
        collection_data[doc_id].update(data)
        self._write_collection(collection, collection_data)
        return collection_data[doc_id]
        
    def delete(self, collection: str, doc_id: str) -> bool:
        """Delete a document from a collection."""
        collection_data = self._read_collection(collection)
        if doc_id not in collection_data:
            return False
            
        del collection_data[doc_id]
        self._write_collection(collection, collection_data)
        return True
        
    def list(self, collection: str) -> List[Dict[str, Any]]:
        """List all documents in a collection."""
        collection_data = self._read_collection(collection)
        return list(collection_data.values())


# Create database instance
db = JSONStorage(os.path.join(os.path.dirname(__file__), 'data'))

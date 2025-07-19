import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

class JSONStorage:
    """Simple JSON file-based storage to simulate a database."""
    
    def __init__(self, db_dir: str):
        self.db_dir = db_dir
        os.makedirs(self.db_dir, exist_ok=True)
        raise DeprecationWarning("JSONStorage is deprecated, use SQLiteStorage instead.")
        
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
        if 'created_at' not in data:
            data['created_at'] = datetime.utcnow().isoformat() + 'Z'
            
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
    
    def list_collections(self) -> List[str]:
        """List all collection names."""
        collections = []
        for filename in os.listdir(self.db_dir):
            if filename.endswith('.json'):
                collection_name = filename[:-5]  # Remove .json extension
                collections.append(collection_name)
        return sorted(collections)

class SQLiteStorage:
    """SQLite-based storage with the same interface as JSONStorage."""
    
    def __init__(self, db_dir: str):
        self.db_dir = db_dir
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, 'database.db')
        self._init_db()
        
    def _init_db(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS collections (
                    id TEXT PRIMARY KEY,
                    collection TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_collection 
                ON collections(collection)
            ''')
            conn.commit()
    
    def _serialize_data(self, data: Dict[str, Any]) -> str:
        """Serialize data to JSON string."""
        return json.dumps(data, default=str)
    
    def _deserialize_data(self, data_str: str) -> Dict[str, Any]:
        """Deserialize JSON string to data."""
        try:
            return json.loads(data_str)
        except json.JSONDecodeError:
            return {}

    def _get_id_field(self, collection: str) -> str:
        if collection == 'agents':
            return 'agent_id'
        elif collection == 'battles':
            return 'battle_id'
        elif collection == 'system':
            return 'system_log_id'
        elif collection == 'assets':
            return 'asset_id'
        else:
            return 'id'
            
    def create(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document in a collection."""
        # Generate an ID if not provided
        id_field = self._get_id_field(collection)
        if id_field not in data:
            data[id_field] = str(uuid.uuid4())
            
        # Add created timestamp if not provided
        if 'created_at' not in data:
            data['created_at'] = datetime.utcnow().isoformat() + 'Z'
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO collections (id, collection, data, created_at)
                VALUES (?, ?, ?, ?)
            ''', (data[id_field], collection, self._serialize_data(data), data['created_at']))
            conn.commit()
            
        return data
        
    def read(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Read a document from a collection."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT data FROM collections 
                WHERE collection = ? AND id = ?
            ''', (collection, doc_id))
            row = cursor.fetchone()
            
            if row:
                return self._deserialize_data(row[0])
            return None
        
    def update(self, collection: str, doc_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a document in a collection."""
        with sqlite3.connect(self.db_path) as conn:
            # First, get the existing document
            cursor = conn.execute('''
                SELECT data FROM collections 
                WHERE collection = ? AND id = ?
            ''', (collection, doc_id))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            # Merge the existing data with the update
            existing_data = self._deserialize_data(row[0])
            existing_data.update(data)
            
            # Update the document
            conn.execute('''
                UPDATE collections 
                SET data = ? 
                WHERE collection = ? AND id = ?
            ''', (self._serialize_data(existing_data), collection, doc_id))
            conn.commit()
            
            return existing_data
        
    def delete(self, collection: str, doc_id: str) -> bool:
        """Delete a document from a collection."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                DELETE FROM collections 
                WHERE collection = ? AND id = ?
            ''', (collection, doc_id))
            conn.commit()
            
            return cursor.rowcount > 0
        
    def list(self, collection: str) -> List[Dict[str, Any]]:
        """List all documents in a collection."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT data FROM collections 
                WHERE collection = ?
            ''', (collection,))
            rows = cursor.fetchall()
            
            return [self._deserialize_data(row[0]) for row in rows]
    
    def list_collections(self) -> List[str]:
        """List all collection names in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT DISTINCT collection FROM collections
                ORDER BY collection
            ''')
            rows = cursor.fetchall()
            
            return [row[0] for row in rows]



db = SQLiteStorage(os.path.join(os.path.dirname(__file__), 'data'))
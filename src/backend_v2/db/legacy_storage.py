# -*- coding: utf-8 -*-

import os
import json
import uuid
import sqlite3

from datetime import datetime
from typing import Dict, List, Any, Optional


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

# TODO: Remove this after full migration
# Legacy database instance (kept for backward compatibility during migration)
# For backward compatibility, we'll keep the old 'db' reference but point to legacy_db
legacy_db = SQLiteStorage(os.path.join(os.path.dirname(__file__), 'data'))
db = legacy_db

# -*- coding: utf-8 -*-

import json
import os
import sqlite3
import uuid

from datetime import datetime
from contextlib import contextmanager
from typing import Dict, List, Any, Optional, Tuple, Union


class DatabaseManager:
    """Database manager for the new 3-table structure."""
    
    def __init__(self, db_dir: str):
        self.db_dir = db_dir
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, 'agentbeats.db')
        self._init_db()
        
    def _init_db(self):
        """Initialize the database with the new schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    alias TEXT NOT NULL,
                    is_hosted BOOLEAN NOT NULL DEFAULT 0,
                    is_green BOOLEAN NOT NULL,
                    battle_description TEXT,
                    participant_requirements TEXT,
                    docker_image_link TEXT,
                    agent_card TEXT,
                    agent_card_status TEXT NOT NULL,
                    user_id TEXT,
                    elo TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS agent_instances (
                    agent_instance_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    agent_url TEXT NOT NULL,
                    launcher_url TEXT NOT NULL,
                    is_locked BOOLEAN NOT NULL DEFAULT 0,
                    ready BOOLEAN NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS battles (
                    battle_id TEXT PRIMARY KEY,
                    green_agent_id TEXT NOT NULL,
                    participant_ids TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    user_id TEXT,
                    interact_history TEXT,
                    result TEXT,
                    error TEXT
                )
            ''')
            
            conn.execute('CREATE INDEX IF NOT EXISTS idx_agent_instances_agent_id ON agent_instances(agent_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_battles_green_agent_id ON battles(green_agent_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_battles_state ON battles(state)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_agents_is_green ON agents(is_green)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_agent_instances_ready ON agent_instances(ready)')
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute_raw_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return results as list of dictionaries."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def execute_raw_update(self, query: str, params: Tuple = ()) -> int:
        """Execute a raw SQL update/insert/delete and return affected row count."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount


class BaseRepository:
    """Base repository class with common functionality."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def execute_raw_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute raw SQL query."""
        return self.db_manager.execute_raw_query(query, params)
    
    def execute_raw_update(self, query: str, params: Tuple = ()) -> int:
        """Execute raw SQL update/insert/delete."""
        return self.db_manager.execute_raw_update(query, params)
    
    def _serialize_json(self, data: Any) -> str:
        """Serialize data to JSON string."""
        if data is None:
            return None
        return json.dumps(data, default=str)
    
    def _deserialize_json(self, data_str: str) -> Any:
        """Deserialize JSON string to data."""
        if data_str is None:
            return None
        try:
            return json.loads(data_str)
        except (json.JSONDecodeError, TypeError):
            return None


class AgentRepository(BaseRepository):
    """Repository for agent operations."""
    
    def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent."""
        agent_id = agent_data.get('agent_id', str(uuid.uuid4()))
        created_at = agent_data.get('created_at', datetime.utcnow().isoformat() + 'Z')
        
        agent_record = {
            'agent_id': agent_id,
            'alias': agent_data['alias'],
            'is_hosted': agent_data.get('is_hosted'),
            'is_green': agent_data['is_green'],
            'battle_description': agent_data.get('battle_description'),
            'participant_requirements': self._serialize_json(agent_data.get('participant_requirements')),
            'docker_image_link': agent_data.get('docker_image_link'),
            'agent_card': self._serialize_json(agent_data.get('agent_card')),
            'agent_card_status': agent_data.get('agent_card_status'),
            'user_id': agent_data.get('user_id'),
            'elo': self._serialize_json(agent_data.get('elo')),
            'created_at': created_at
        }
        
        with self.db_manager.get_connection() as conn:
            conn.execute('''
                INSERT INTO agents (agent_id, alias, is_hosted, is_green, battle_description, 
                                  participant_requirements, agent_card, agent_card_status, docker_image_link, user_id, elo, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                agent_record['agent_id'], agent_record['alias'], agent_record['is_hosted'],
                agent_record['is_green'], agent_record['battle_description'],
                agent_record['participant_requirements'], agent_record['agent_card'], agent_data['agent_card_status'],
                agent_record['docker_image_link'], agent_record['user_id'], agent_record['elo'], agent_record['created_at']
            ))
            conn.commit()
        
        return self.get_agent(agent_id)
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get an agent by ID."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM agents WHERE agent_id = ?', (agent_id,))
            row = cursor.fetchone()
            
            if row:
                agent = dict(row)
                agent['participant_requirements'] = self._deserialize_json(agent['participant_requirements'])
                agent['agent_card'] = self._deserialize_json(agent['agent_card'])
                agent['elo'] = self._deserialize_json(agent['elo'])
                return agent
            return None
    
    def list_agents(self, user_id: str = None, is_green: bool = None) -> List[Dict[str, Any]]:
        """List agents with optional filters.
        
        Args:
            user_id: 
                - None (default): No user_id filtering
                - "NULL": Only agents with user_id IS NULL
                - "dev-user-id": Only dev agents
                - str: Only agents with this specific user_id
            is_green: Optional boolean filter for is_green field
        """
        query = 'SELECT * FROM agents WHERE 1=1'
        params = []
        
        if user_id is not None:
            if user_id == "NULL":
                query += ' AND user_id IS NULL'
            else:
                query += ' AND user_id = ?'
                params.append(user_id)
        
        if is_green is not None:
            query += ' AND is_green = ?'
            params.append(is_green)
        
        query += ' ORDER BY created_at DESC'
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            agents = []
            for row in rows:
                agent = dict(row)
                agent['participant_requirements'] = self._deserialize_json(agent['participant_requirements'])
                agent['agent_card'] = self._deserialize_json(agent['agent_card'])
                agent['elo'] = self._deserialize_json(agent['elo'])
                agents.append(agent)
            
            return agents
    
    def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an agent."""
        # Get current agent
        current_agent = self.get_agent(agent_id)
        if not current_agent:
            return None
        
        set_clauses = []
        params = []
        
        for key, value in update_data.items():
            if key == 'agent_id':  # Don't allow updating primary key
                continue
            
            if key in ['participant_requirements', 'agent_card', 'elo']:
                value = self._serialize_json(value)
            
            set_clauses.append(f"{key} = ?")
            params.append(value)
        
        if not set_clauses:
            return current_agent
        
        params.append(agent_id)
        query = f"UPDATE agents SET {', '.join(set_clauses)} WHERE agent_id = ?"
        
        with self.db_manager.get_connection() as conn:
            conn.execute(query, params)
            conn.commit()
        
        return self.get_agent(agent_id)
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent (and its instances via cascade)."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute('DELETE FROM agents WHERE agent_id = ?', (agent_id,))
            conn.commit()
            return cursor.rowcount > 0


class AgentInstanceRepository(BaseRepository):
    """Repository for agent instance operations."""
    
    def create_agent_instance(self, instance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent instance."""
        instance_id = instance_data.get('agent_instance_id', str(uuid.uuid4()))
        created_at = instance_data.get('created_at', datetime.utcnow().isoformat() + 'Z')
        
        instance_record = {
            'agent_instance_id': instance_id,
            'agent_id': instance_data['agent_id'],
            'agent_url': instance_data['agent_url'],
            'launcher_url': instance_data['launcher_url'],
            'is_locked': instance_data.get('is_locked', False),
            'ready': instance_data.get('ready', False),
            'created_at': created_at
        }
        
        with self.db_manager.get_connection() as conn:
            conn.execute('''
                INSERT INTO agent_instances (agent_instance_id, agent_id, agent_url, 
                                           launcher_url, is_locked, ready, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                instance_record['agent_instance_id'], instance_record['agent_id'],
                instance_record['agent_url'], instance_record['launcher_url'],
                instance_record['is_locked'], instance_record['ready'],
                instance_record['created_at']
            ))
            conn.commit()
        
        return self.get_agent_instance(instance_id)
    
    def get_agent_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get an agent instance by ID."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM agent_instances WHERE agent_instance_id = ?', (instance_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_agent_instances_by_agent_id(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all instances for a specific agent."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM agent_instances WHERE agent_id = ? ORDER BY created_at DESC', (agent_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def list_agent_instances(self, is_locked: bool = None, ready: bool = None) -> List[Dict[str, Any]]:
        """List agent instances with optional filters."""
        query = 'SELECT * FROM agent_instances WHERE 1=1'
        params = []
        
        if is_locked is not None:
            query += ' AND is_locked = ?'
            params.append(is_locked)
        
        if ready is not None:
            query += ' AND ready = ?'
            params.append(ready)
        
        query += ' ORDER BY created_at DESC'
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def update_agent_instance(self, instance_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an agent instance."""
        set_clauses = []
        params = []
        
        for key, value in update_data.items():
            if key == 'agent_instance_id':  # Don't allow updating primary key
                continue
            set_clauses.append(f"{key} = ?")
            params.append(value)
        
        if not set_clauses:
            return self.get_agent_instance(instance_id)
        
        params.append(instance_id)
        query = f"UPDATE agent_instances SET {', '.join(set_clauses)} WHERE agent_instance_id = ?"
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            
            if cursor.rowcount > 0:
                return self.get_agent_instance(instance_id)
            return None
    
    def delete_agent_instance(self, instance_id: str) -> bool:
        """Delete an agent instance."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute('DELETE FROM agent_instances WHERE agent_instance_id = ?', (instance_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_agent_instances_by_agent_id(self, agent_id: str) -> bool:
        """Delete all instances for a specific agent."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute('DELETE FROM agent_instances WHERE agent_id = ?', (agent_id,))
            conn.commit()
            return cursor.rowcount > 0


class BattleRepository(BaseRepository):
    """Repository for battle operations."""
    
    def create_battle(self, battle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new battle."""
        battle_id = battle_data.get('battle_id', str(uuid.uuid4()))
        created_at = battle_data.get('created_at', datetime.utcnow().isoformat() + 'Z')
        
        battle_record = {
            'battle_id': battle_id,
            'green_agent_id': battle_data['green_agent_id'],
            'participant_ids': self._serialize_json(battle_data['participant_ids']),
            'state': battle_data.get('state', 'pending'),
            'created_at': created_at,
            'user_id': battle_data.get('user_id'),
            'interact_history': self._serialize_json(battle_data.get('interact_history', [])),
            'result': self._serialize_json(battle_data.get('result')),
            'error': battle_data.get('error')
        }
        
        with self.db_manager.get_connection() as conn:
            conn.execute('''
                INSERT INTO battles (battle_id, green_agent_id, participant_ids, state, 
                                   created_at, user_id, interact_history, result, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                battle_record['battle_id'], battle_record['green_agent_id'],
                battle_record['participant_ids'], battle_record['state'],
                battle_record['created_at'], battle_record['user_id'],
                battle_record['interact_history'], battle_record['result'],
                battle_record['error']
            ))
            conn.commit()
        
        return self.get_battle(battle_id)
    
    def get_battle(self, battle_id: str) -> Optional[Dict[str, Any]]:
        """Get a battle by ID."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM battles WHERE battle_id = ?', (battle_id,))
            row = cursor.fetchone()
            
            if row:
                battle = dict(row)
                battle['participant_ids'] = self._deserialize_json(battle['participant_ids'])
                battle['interact_history'] = self._deserialize_json(battle['interact_history'])
                battle['result'] = self._deserialize_json(battle['result'])
                return battle
            return None
    
    def list_battles(self, state: str = None, user_id: str = None) -> List[Dict[str, Any]]:
        """List battles with optional filters."""
        query = 'SELECT * FROM battles WHERE 1=1'
        params = []
        
        if state is not None:
            query += ' AND state = ?'
            params.append(state)
        
        if user_id is not None:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        query += ' ORDER BY created_at DESC'
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            battles = []
            for row in rows:
                battle = dict(row)
                battle['participant_ids'] = self._deserialize_json(battle['participant_ids'])
                battle['interact_history'] = self._deserialize_json(battle['interact_history'])
                battle['result'] = self._deserialize_json(battle['result'])
                battles.append(battle)
            
            return battles
    
    def update_battle(self, battle_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a battle."""
        set_clauses = []
        params = []
        
        for key, value in update_data.items():
            if key == 'battle_id':  # Don't allow updating primary key
                continue
            
            if key in ['participant_ids', 'interact_history', 'result']:
                value = self._serialize_json(value)
            
            set_clauses.append(f"{key} = ?")
            params.append(value)
        
        if not set_clauses:
            return self.get_battle(battle_id)
        
        params.append(battle_id)
        query = f"UPDATE battles SET {', '.join(set_clauses)} WHERE battle_id = ?"
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            
            if cursor.rowcount > 0:
                return self.get_battle(battle_id)
            return None
    
    def delete_battle(self, battle_id: str) -> bool:
        """Delete a battle."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute('DELETE FROM battles WHERE battle_id = ?', (battle_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def add_battle_interaction(self, battle_id: str, interaction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add an interaction to a battle's history."""
        battle = self.get_battle(battle_id)
        if not battle:
            return None
        
        if 'timestamp' not in interaction:
            interaction['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        interact_history = battle.get('interact_history', [])
        interact_history.append(interaction)
        
        return self.update_battle(battle_id, {'interact_history': interact_history})

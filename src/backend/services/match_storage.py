import sqlite3
import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

# =============================================================================
# MATCH STORAGE LOGGING CONFIGURATION
# =============================================================================
# Configure dedicated logger for match storage operations
match_storage_logger = logging.getLogger('match_storage')
match_storage_logger.setLevel(logging.ERROR)  # Only log errors

# Create console handler if it doesn't exist
if not match_storage_logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        '%(asctime)s - [MATCH_STORAGE] - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    match_storage_logger.addHandler(console_handler)
    match_storage_logger.propagate = False  # Prevent duplicate logs

class MatchStorage:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use the same database as the main storage
            db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "data")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "database.db")
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with normalized match tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Main matches table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_matches (
                    id TEXT PRIMARY KEY,
                    green_agent_id TEXT NOT NULL,
                    other_agent_id TEXT NOT NULL,
                    confidence_score REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    UNIQUE(green_agent_id, other_agent_id)
                )
            """)
            
            # Match roles table for detailed role information
            conn.execute("""
                CREATE TABLE IF NOT EXISTS match_roles (
                    match_id TEXT NOT NULL,
                    role_name TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    confidence_score REAL DEFAULT 0.0,
                    PRIMARY KEY (match_id, role_name),
                    FOREIGN KEY (match_id) REFERENCES agent_matches(id) ON DELETE CASCADE
                )
            """)
            
            # Performance indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_green ON agent_matches(green_agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_other ON agent_matches(other_agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_confidence ON agent_matches(confidence_score DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_roles_match ON match_roles(match_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_roles_name ON match_roles(role_name)")
            
            conn.commit()
    
    def create_match(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a match with roles in normalized format."""
        match_id = match_data.get("id", "new")
        green_agent_id = match_data.get("green_agent_id", "unknown")
        other_agent_id = match_data.get("other_agent_id", "unknown")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("BEGIN")
            
            try:
                # Generate ID if not provided
                if "id" not in match_data:
                    match_data["id"] = str(uuid.uuid4())
                    match_storage_logger.info(f"🆔 Generated new match ID: {match_data['id']}")
                
                # Add timestamps if not provided
                current_time = datetime.utcnow().isoformat() + "Z"
                if "created_at" not in match_data:
                    match_data["created_at"] = current_time
                if "updated_at" not in match_data:
                    match_data["updated_at"] = current_time
                
                # Insert main match record
                conn.execute("""
                    INSERT OR REPLACE INTO agent_matches 
                    (id, green_agent_id, other_agent_id, confidence_score, created_at, updated_at, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    match_data["id"],
                    match_data["green_agent_id"],
                    match_data["other_agent_id"],
                    match_data.get("confidence_score", 0.0),
                    match_data["created_at"],
                    match_data["updated_at"],
                    match_data["created_by"]
                ))
                # Insert role records
                reasons = match_data.get("reasons", {})
                role_count = 0
                for role_name, reason in reasons.items():
                    conn.execute("""
                        INSERT OR REPLACE INTO match_roles 
                        (match_id, role_name, reason, confidence_score)
                        VALUES (?, ?, ?, ?)
                    """, (
                        match_data["id"],
                        role_name,
                        reason,
                        match_data.get("confidence_score", 0.0)
                    ))
                    role_count += 1
                
                # Also insert matched_roles if provided (for backward compatibility)
                matched_roles = match_data.get("matched_roles", [])
                for role_name in matched_roles:
                    if role_name not in reasons:
                        # If no reason provided, use a default one
                        conn.execute("""
                            INSERT OR REPLACE INTO match_roles 
                            (match_id, role_name, reason, confidence_score)
                            VALUES (?, ?, ?, ?)
                        """, (
                            match_data["id"],
                            role_name,
                            f"Agent matched to {role_name} role",
                            match_data.get("confidence_score", 0.0)
                        ))
                        role_count += 1
                
                conn.commit()
                return match_data
                
            except Exception as e:
                conn.rollback()
                match_storage_logger.error(f"Failed to create match: {str(e)}")
                raise e
    
    def get_matches_for_green_agent(self, green_agent_id: str) -> List[Dict[str, Any]]:
        """Get all matches for a green agent with roles."""
        with sqlite3.connect(self.db_path) as conn:
            # First get all matches for this green agent
            cursor = conn.execute("""
                SELECT 
                    m.id, m.green_agent_id, m.other_agent_id, m.confidence_score,
                    m.created_at, m.updated_at, m.created_by
                FROM agent_matches m
                WHERE m.green_agent_id = ?
                ORDER BY m.confidence_score DESC
            """, (green_agent_id,))
            
            matches = []
            for row in cursor.fetchall():
                match = {
                    "id": row[0],
                    "green_agent_id": row[1],
                    "other_agent_id": row[2],
                    "confidence_score": row[3],
                    "created_at": row[4],
                    "updated_at": row[5],
                    "created_by": row[6],
                    "matched_roles": [],
                    "reasons": {}
                }
                
                # Get roles for this match
                role_cursor = conn.execute("""
                    SELECT role_name, reason
                    FROM match_roles
                    WHERE match_id = ?
                    ORDER BY role_name
                """, (match["id"],))
                
                for role_row in role_cursor.fetchall():
                    role_name = role_row[0]
                    reason = role_row[1]
                    match["matched_roles"].append(role_name)
                    match["reasons"][role_name] = reason
                
                matches.append(match)
            
            return matches
    
    def get_matches_for_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get all matches where an agent appears (either as green or other)."""
        with sqlite3.connect(self.db_path) as conn:
            # Find matches where this agent is the green agent
            green_cursor = conn.execute("""
                SELECT 
                    m.id, m.other_agent_id, m.confidence_score,
                    m.created_at, m.updated_at, m.created_by
                FROM agent_matches m
                WHERE m.green_agent_id = ?
                ORDER BY m.confidence_score DESC
            """, (agent_id,))
            
            as_green = []
            for row in green_cursor.fetchall():
                match = {
                    "id": row[0],
                    "other_agent_id": row[1],
                    "confidence_score": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "created_by": row[5],
                    "matched_roles": [],
                    "reasons": {}
                }
                
                # Get roles for this match
                role_cursor = conn.execute("""
                    SELECT role_name, reason
                    FROM match_roles
                    WHERE match_id = ?
                    ORDER BY role_name
                """, (match["id"],))
                
                for role_row in role_cursor.fetchall():
                    role_name = role_row[0]
                    reason = role_row[1]
                    match["matched_roles"].append(role_name)
                    match["reasons"][role_name] = reason
                
                as_green.append(match)
            
            # Find matches where this agent is the other agent
            other_cursor = conn.execute("""
                SELECT 
                    m.id, m.green_agent_id, m.confidence_score,
                    m.created_at, m.updated_at, m.created_by
                FROM agent_matches m
                WHERE m.other_agent_id = ?
                ORDER BY m.confidence_score DESC
            """, (agent_id,))
            
            as_other = []
            for row in other_cursor.fetchall():
                match = {
                    "id": row[0],
                    "green_agent_id": row[1],
                    "confidence_score": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "created_by": row[5],
                    "matched_roles": [],
                    "reasons": {}
                }
                
                # Get roles for this match
                role_cursor = conn.execute("""
                    SELECT role_name, reason
                    FROM match_roles
                    WHERE match_id = ?
                    ORDER BY role_name
                """, (match["id"],))
                
                for role_row in role_cursor.fetchall():
                    role_name = role_row[0]
                    reason = role_row[1]
                    match["matched_roles"].append(role_name)
                    match["reasons"][role_name] = reason
                
                as_other.append(match)
            
            return {
                "agent_id": agent_id,
                "matches_as_green": as_green,
                "matches_as_other": as_other,
                "total_matches": len(as_green) + len(as_other)
            }
    
    def get_matches_by_role(self, role_name: str, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """Get all matches for a specific role."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    m.id, m.green_agent_id, m.other_agent_id, m.confidence_score,
                    m.created_at, m.updated_at, m.created_by
                FROM agent_matches m
                JOIN match_roles r ON m.id = r.match_id
                WHERE r.role_name = ? AND m.confidence_score >= ?
                ORDER BY m.confidence_score DESC
            """, (role_name, min_confidence))
            
            matches = []
            for row in cursor.fetchall():
                match = {
                    "id": row[0],
                    "green_agent_id": row[1],
                    "other_agent_id": row[2],
                    "confidence_score": row[3],
                    "created_at": row[4],
                    "updated_at": row[5],
                    "created_by": row[6],
                    "matched_roles": [],
                    "reasons": {}
                }
                
                # Get all roles for this match
                role_cursor = conn.execute("""
                    SELECT role_name, reason
                    FROM match_roles
                    WHERE match_id = ?
                    ORDER BY role_name
                """, (match["id"],))
                
                for role_row in role_cursor.fetchall():
                    role_name_inner = role_row[0]
                    reason = role_row[1]
                    match["matched_roles"].append(role_name_inner)
                    match["reasons"][role_name_inner] = reason
                
                matches.append(match)
            
            return matches
    
    def delete_match(self, match_id: str) -> bool:
        """Delete a match and its associated roles."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("BEGIN")
            
            try:
                # Delete roles first (due to foreign key constraint)
                conn.execute("DELETE FROM match_roles WHERE match_id = ?", (match_id,))
                
                # Delete main match record
                cursor = conn.execute("DELETE FROM agent_matches WHERE id = ?", (match_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
            except Exception as e:
                conn.rollback()
                raise e
    
    def delete_matches_for_agent(self, agent_id: str) -> int:
        """Delete all matches involving a specific agent."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("BEGIN")
            
            try:
                # Delete roles for matches involving this agent
                conn.execute("""
                    DELETE FROM match_roles 
                    WHERE match_id IN (
                        SELECT id FROM agent_matches 
                        WHERE green_agent_id = ? OR other_agent_id = ?
                    )
                """, (agent_id, agent_id))
                
                # Delete main match records
                cursor = conn.execute("""
                    DELETE FROM agent_matches 
                    WHERE green_agent_id = ? OR other_agent_id = ?
                """, (agent_id, agent_id))
                
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
                
            except Exception as e:
                conn.rollback()
                raise e
    
    def get_match_stats(self) -> Dict[str, Any]:
        """Get statistics about stored matches."""
        with sqlite3.connect(self.db_path) as conn:
            # Total matches
            total_cursor = conn.execute("SELECT COUNT(*) FROM agent_matches")
            total_matches = total_cursor.fetchone()[0]
            
            # Total role assignments
            roles_cursor = conn.execute("SELECT COUNT(*) FROM match_roles")
            total_roles = roles_cursor.fetchone()[0]
            
            # Average confidence
            avg_cursor = conn.execute("SELECT AVG(confidence_score) FROM agent_matches")
            avg_confidence = avg_cursor.fetchone()[0] or 0.0
            
            # Top roles
            top_roles_cursor = conn.execute("""
                SELECT role_name, COUNT(*) as count 
                FROM match_roles 
                GROUP BY role_name 
                ORDER BY count DESC 
                LIMIT 10
            """)
            top_roles = [{"role": row[0], "count": row[1]} for row in top_roles_cursor.fetchall()]
            
            return {
                "total_matches": total_matches,
                "total_role_assignments": total_roles,
                "average_confidence": round(avg_confidence, 3),
                "top_roles": top_roles
            } 
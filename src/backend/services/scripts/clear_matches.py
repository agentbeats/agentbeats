#!/usr/bin/env python3
"""Clear role matching data from database."""

import argparse
import sys
import sqlite3
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from match_storage import MatchStorage

def clear_all(match_storage):
    with sqlite3.connect(match_storage.db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM agent_matches")
        match_count = cursor.fetchone()[0]
        cursor = conn.execute("SELECT COUNT(*) FROM match_roles")
        role_count = cursor.fetchone()[0]
        
        if match_count == 0:
            print("No data to clear")
            return
        
        conn.execute("DELETE FROM match_roles")
        conn.execute("DELETE FROM agent_matches")
        conn.commit()
        print(f"Cleared {match_count} matches and {role_count} role assignments")

def clear_agent(match_storage, agent_id):
    deleted_count = match_storage.delete_matches_for_agent(agent_id)
    print(f"Cleared {deleted_count} matches for agent {agent_id}")

def clear_green_agent(match_storage, agent_id):
    with sqlite3.connect(match_storage.db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM agent_matches WHERE green_agent_id = ?", (agent_id,))
        match_count = cursor.fetchone()[0]
        
        if match_count == 0:
            print("No matches found")
            return
        
        conn.execute("DELETE FROM match_roles WHERE match_id IN (SELECT id FROM agent_matches WHERE green_agent_id = ?)", (agent_id,))
        conn.execute("DELETE FROM agent_matches WHERE green_agent_id = ?", (agent_id,))
        conn.commit()
        print(f"Cleared {match_count} matches")

def clear_other_agent(match_storage, agent_id):
    with sqlite3.connect(match_storage.db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM agent_matches WHERE other_agent_id = ?", (agent_id,))
        match_count = cursor.fetchone()[0]
        
        if match_count == 0:
            print("No matches found")
            return
        
        conn.execute("DELETE FROM match_roles WHERE match_id IN (SELECT id FROM agent_matches WHERE other_agent_id = ?)", (agent_id,))
        conn.execute("DELETE FROM agent_matches WHERE other_agent_id = ?", (agent_id,))
        conn.commit()
        print(f"Cleared {match_count} matches")

def show_stats(match_storage):
    stats = match_storage.get_match_stats()
    print(f"Total matches: {stats['total_matches']}")
    print(f"Total role assignments: {stats['total_role_assignments']}")
    print(f"Average confidence: {stats['average_confidence']}")

def main():
    parser = argparse.ArgumentParser(description="Clear role matching data")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true')
    group.add_argument('--agent', type=str)
    group.add_argument('--green-agent', type=str)
    group.add_argument('--other-agent', type=str)
    group.add_argument('--stats', action='store_true')
    
    args = parser.parse_args()
    
    try:
        match_storage = MatchStorage()
        
        if args.stats:
            show_stats(match_storage)
        elif args.all:
            clear_all(match_storage)
        elif args.agent:
            clear_agent(match_storage, args.agent)
        elif args.green_agent:
            clear_green_agent(match_storage, args.green_agent)
        elif args.other_agent:
            clear_other_agent(match_storage, args.other_agent)
        
        if not args.stats:
            show_stats(match_storage)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
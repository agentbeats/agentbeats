import json
import os
import shutil
import sqlite3
from datetime import datetime
from typing import Dict, Any, List
from .legacy_storage import SQLiteStorage
from .repositories import DatabaseManager, AgentRepository, AgentInstanceRepository, BattleRepository

def migrate_database(db_dir: str):
    """Migrate from old SQLiteStorage to new repository structure."""
    
    print("Starting database migration...")
    
    # Initialize old and new database systems
    old_storage = SQLiteStorage(db_dir)
    new_db_manager = DatabaseManager(db_dir)
    
    agent_repo = AgentRepository(new_db_manager)
    instance_repo = AgentInstanceRepository(new_db_manager)
    battle_repo = BattleRepository(new_db_manager)
    
    # Create backup of old database
    old_db_path = os.path.join(db_dir, 'database.db')
    backup_path = os.path.join(db_dir, f'database_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
    
    if os.path.exists(old_db_path):
        shutil.copy2(old_db_path, backup_path)
        print(f"Created backup: {backup_path}")
    
    # Migrate agents
    print("Migrating agents...")
    migrated_agents = 0
    migrated_instances = 0
    
    try:
        old_agents = old_storage.list("agents")
        print(f"Found {len(old_agents)} agents to migrate")
        
        for old_agent in old_agents:
            try:
                # Extract agent data from old structure
                register_info = old_agent.get("register_info", {})
                agent_card = old_agent.get("agent_card", {})
                
                # Create new agent record
                new_agent_data = {
                    'agent_id': old_agent['agent_id'],
                    'alias': register_info.get('alias', agent_card.get('name', 'Unnamed Agent')),
                    'is_hosted': register_info.get('is_hosted', False),
                    'is_green': register_info.get('is_green', False),
                    'battle_description': register_info.get('battle_description'),
                    'participant_requirements': register_info.get('participant_requirements'),
                    'user_id': old_agent.get('user_id'),
                    'elo': old_agent.get('elo'),
                    'created_at': old_agent.get('created_at', datetime.utcnow().isoformat() + 'Z')
                }
                
                # Create agent in new structure
                created_agent = agent_repo.create_agent(new_agent_data)
                migrated_agents += 1
                print(f"  Migrated agent: {created_agent['alias']} ({created_agent['agent_id']})")
                
                # Create corresponding agent instance
                instance_data = {
                    'agent_id': created_agent['agent_id'],
                    'agent_url': register_info.get('agent_url', ''),
                    'launcher_url': register_info.get('launcher_url', ''),
                    'is_locked': old_agent.get('status') == 'locked',
                    'ready': old_agent.get('ready', False),
                    'created_at': created_agent['created_at']
                }
                
                created_instance = instance_repo.create_agent_instance(instance_data)
                migrated_instances += 1
                print(f"    Created instance: {created_instance['agent_instance_id']}")
                
            except Exception as e:
                print(f"  Error migrating agent {old_agent.get('agent_id', 'unknown')}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error during agent migration: {str(e)}")
    
    # Migrate battles (with foreign keys temporarily disabled)
    print("\nMigrating battles...")
    migrated_battles = 0
    failed_battles = 0
    
    try:
        old_battles = old_storage.list("battles")
        print(f"Found {len(old_battles)} battles to migrate")
        
        # Migrate battles with direct SQL to bypass repository constraints
        for old_battle in old_battles:
            try:
                # Create new battle record directly with SQL to avoid foreign key issues
                battle_data = {
                    'battle_id': old_battle['battle_id'],
                    'green_agent_id': old_battle.get('green_agent_id', ''),
                    'participant_ids': battle_repo._serialize_json(old_battle.get('opponents', [])),
                    'state': old_battle.get('state', 'finished'),
                    'created_at': old_battle.get('created_at', datetime.utcnow().isoformat() + 'Z'),
                    'user_id': old_battle.get('created_by'),
                    'interact_history': battle_repo._serialize_json(old_battle.get('interact_history', [])),
                    'result': battle_repo._serialize_json(old_battle.get('result')),
                    'error': old_battle.get('error')
                }
                
                # Use direct SQL with foreign keys disabled
                with new_db_manager.get_connection() as conn:
                    conn.execute("PRAGMA foreign_keys = OFF")
                    conn.execute('''
                        INSERT INTO battles (battle_id, green_agent_id, participant_ids, state, 
                                           created_at, user_id, interact_history, result, error)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        battle_data['battle_id'], battle_data['green_agent_id'],
                        battle_data['participant_ids'], battle_data['state'],
                        battle_data['created_at'], battle_data['user_id'],
                        battle_data['interact_history'], battle_data['result'],
                        battle_data['error']
                    ))
                    conn.commit()
                
                migrated_battles += 1
                print(f"  Migrated battle: {battle_data['battle_id']}")
                
            except Exception as e:
                print(f"  Error migrating battle {old_battle.get('battle_id', 'unknown')}: {str(e)}")
                failed_battles += 1
                continue
                
    except Exception as e:
        print(f"Error during battle migration: {str(e)}")
    
    if failed_battles > 0:
        print(f"  Battles failed to migrate: {failed_battles}")
    
    # Copy additional tables (agent_matches and match_roles) if they exist
    print("\nCopying additional tables...")
    copied_tables = []
    
    try:
        # Check if agent_matches table exists and copy it
        old_db_path = os.path.join(db_dir, 'database.db')
        with sqlite3.connect(old_db_path) as old_conn:
            # Check if agent_matches exists
            cursor = old_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_matches'")
            if cursor.fetchone():
                # Get the table schema and data
                cursor = old_conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='agent_matches'")
                create_sql = cursor.fetchone()[0]
                
                cursor = old_conn.execute("SELECT * FROM agent_matches")
                agent_matches_data = cursor.fetchall()
                agent_matches_columns = [description[0] for description in cursor.description]
                
                # Create table in new database
                with new_db_manager.get_connection() as new_conn:
                    new_conn.execute("PRAGMA foreign_keys = OFF")
                    new_conn.execute(create_sql)
                    
                    # Copy data
                    if agent_matches_data:
                        placeholders = ','.join(['?' for _ in agent_matches_columns])
                        insert_sql = f"INSERT INTO agent_matches VALUES ({placeholders})"
                        new_conn.executemany(insert_sql, agent_matches_data)
                    
                    new_conn.commit()
                
                copied_tables.append(f"agent_matches ({len(agent_matches_data)} rows)")
                print(f"  Copied agent_matches table with {len(agent_matches_data)} rows")
            
            # Check if match_roles table exists and copy it
            cursor = old_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='match_roles'")
            if cursor.fetchone():
                # Get the table schema and data
                cursor = old_conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='match_roles'")
                create_sql = cursor.fetchone()[0]
                
                cursor = old_conn.execute("SELECT * FROM match_roles")
                match_roles_data = cursor.fetchall()
                match_roles_columns = [description[0] for description in cursor.description]
                
                # Create table in new database
                with new_db_manager.get_connection() as new_conn:
                    new_conn.execute("PRAGMA foreign_keys = OFF")
                    new_conn.execute(create_sql)
                    
                    # Copy data
                    if match_roles_data:
                        placeholders = ','.join(['?' for _ in match_roles_columns])
                        insert_sql = f"INSERT INTO match_roles VALUES ({placeholders})"
                        new_conn.executemany(insert_sql, match_roles_data)
                    
                    new_conn.commit()
                
                copied_tables.append(f"match_roles ({len(match_roles_data)} rows)")
                print(f"  Copied match_roles table with {len(match_roles_data)} rows")
                
            # Copy any indexes for these tables
            for table_name in ['agent_matches', 'match_roles']:
                cursor = old_conn.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL", (table_name,))
                indexes = cursor.fetchall()
                
                if indexes:
                    with new_db_manager.get_connection() as new_conn:
                        for index_sql, in indexes:
                            try:
                                new_conn.execute(index_sql)
                            except Exception as e:
                                print(f"    Warning: Failed to create index for {table_name}: {e}")
                        new_conn.commit()
                        
    except Exception as e:
        print(f"Error copying additional tables: {str(e)}")
    
    # Migration summary
    print(f"\nMigration completed!")
    print(f"  Agents migrated: {migrated_agents}")
    print(f"  Agent instances created: {migrated_instances}")
    print(f"  Battles migrated: {migrated_battles}")
    if failed_battles > 0:
        print(f"  Battles failed: {failed_battles}")
    if copied_tables:
        print(f"  Additional tables copied: {', '.join(copied_tables)}")
    print(f"  Old database backed up to: {backup_path}")
    
    return {
        'agents_migrated': migrated_agents,
        'instances_created': migrated_instances,
        'battles_migrated': migrated_battles,
        'battles_failed': failed_battles,
        'copied_tables': copied_tables,
        'backup_path': backup_path
    }

def verify_migration(db_dir: str):
    """Verify the migration was successful by comparing counts."""
    print("\nVerifying migration...")
    
    try:
        # Initialize both systems
        old_storage = SQLiteStorage(db_dir)
        new_db_manager = DatabaseManager(db_dir)
        
        agent_repo = AgentRepository(new_db_manager)
        battle_repo = BattleRepository(new_db_manager)
        instance_repo = AgentInstanceRepository(new_db_manager)
        
        # Compare counts
        old_agents_count = len(old_storage.list("agents"))
        old_battles_count = len(old_storage.list("battles"))
        
        new_agents_count = len(agent_repo.list_agents())
        new_battles_count = len(battle_repo.list_battles())
        new_instances_count = len(instance_repo.list_agent_instances())
        
        print(f"Old agents: {old_agents_count}, New agents: {new_agents_count}")
        print(f"Old battles: {old_battles_count}, New battles: {new_battles_count}")
        print(f"New agent instances: {new_instances_count}")
        
        agents_match = old_agents_count == new_agents_count
        instances_match = new_instances_count == new_agents_count
        # Now we expect battles to match since we preserve all data
        battles_match = new_battles_count == old_battles_count
        
        success = agents_match and instances_match and battles_match
        
        if success:
            print("✅ Migration verification passed!")
        else:
            print("❌ Migration verification failed!")
            if not agents_match:
                print(f"  Agent count mismatch: expected {old_agents_count}, got {new_agents_count}")
            if not instances_match:
                print(f"  Instance count mismatch: expected {new_agents_count}, got {new_instances_count}")
            if not battles_match:
                print(f"  Battle count mismatch: expected {old_battles_count}, got {new_battles_count}")
        
        # Check for orphaned battles (battles with non-existent green_agent_id)
        orphaned_battles = new_db_manager.execute_raw_query("""
            SELECT b.battle_id, b.green_agent_id 
            FROM battles b 
            LEFT JOIN agents a ON b.green_agent_id = a.agent_id 
            WHERE b.green_agent_id != '' AND a.agent_id IS NULL
        """)
        
        if orphaned_battles:
            print(f"⚠️  Warning: {len(orphaned_battles)} battles have non-existent green_agent_id references")
            print("  These can be cleaned up later by updating the green_agent_id or creating missing agents")
            
        return success
        
    except Exception as e:
        print(f"Error during migration verification: {str(e)}")
        return False

if __name__ == "__main__":
    # Run migration on the default database directory
    db_dir = os.path.join(os.path.dirname(__file__), 'data')
    migrate_database(db_dir)
    verify_migration(db_dir)
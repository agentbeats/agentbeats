#!/usr/bin/env python3
"""
Test script to verify the match storage database operations are working correctly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend.services.match_storage import MatchStorage
from backend.db.storage import db

def test_database_operations():
    """Test basic database operations."""
    print("🧪 Testing match storage database operations...")
    
    # Initialize storage
    match_storage = MatchStorage()
    
    # Test data
    test_match = {
        "green_agent_id": "test_green_123",
        "other_agent_id": "test_other_456",
        "matched_roles": ["red_agent", "blue_agent"],
        "reasons": {
            "red_agent": "This agent is designed for offensive operations",
            "blue_agent": "This agent has defensive capabilities"
        },
        "confidence_score": 0.85,
        "created_by": "test_user"
    }
    
    print("📝 Creating test match...")
    try:
        created_match = match_storage.create_match(test_match)
        print(f"✅ Created match with ID: {created_match['id']}")
        
        # Test retrieving matches for green agent
        print("🔍 Testing get_matches_for_green_agent...")
        matches = match_storage.get_matches_for_green_agent("test_green_123")
        print(f"✅ Found {len(matches)} matches")
        
        if matches:
            match = matches[0]
            print(f"  - Match ID: {match['id']}")
            print(f"  - Other Agent: {match['other_agent_id']}")
            print(f"  - Confidence: {match['confidence_score']}")
            print(f"  - Roles: {match['matched_roles']}")
            print(f"  - Reasons: {list(match['reasons'].keys())}")
        
        # Test retrieving matches for agent
        print("🔍 Testing get_matches_for_agent...")
        agent_matches = match_storage.get_matches_for_agent("test_green_123")
        print(f"✅ Agent matches - As green: {len(agent_matches['matches_as_green'])}, As other: {len(agent_matches['matches_as_other'])}")
        
        # Test retrieving matches by role
        print("🔍 Testing get_matches_by_role...")
        role_matches = match_storage.get_matches_by_role("red_agent")
        print(f"✅ Found {len(role_matches)} matches for red_agent role")
        
        # Test statistics
        print("📊 Testing get_match_stats...")
        stats = match_storage.get_match_stats()
        print(f"✅ Stats - Total matches: {stats['total_matches']}, Total roles: {stats['total_role_assignments']}")
        
        # Clean up
        print("🧹 Cleaning up test data...")
        deleted_count = match_storage.delete_matches_for_agent("test_green_123")
        print(f"✅ Deleted {deleted_count} matches")
        
        print("🎉 All database tests passed!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

def test_with_real_agents():
    """Test with real agents from the database."""
    print("\n🔍 Testing with real agents from database...")
    
    # Get agents from database
    agents = db.list("agents")
    print(f"📊 Found {len(agents)} agents in database")
    
    if not agents:
        print("⚠️  No agents found in database")
        return
    
    # Separate green and non-green agents
    green_agents = [a for a in agents if a["register_info"]["is_green"]]
    non_green_agents = [a for a in agents if not a["register_info"]["is_green"]]
    
    print(f"🟢 Green agents: {len(green_agents)}")
    print(f"🔴 Non-green agents: {len(non_green_agents)}")
    
    if green_agents and non_green_agents:
        # Test getting matches for first green agent
        green_agent_id = green_agents[0]["agent_id"]
        match_storage = MatchStorage()
        
        matches = match_storage.get_matches_for_green_agent(green_agent_id)
        print(f"✅ Found {len(matches)} existing matches for {green_agents[0]['register_info']['alias']}")
        
        if matches:
            print("📋 Sample match:")
            match = matches[0]
            print(f"  - Other Agent: {match['other_agent_id']}")
            print(f"  - Roles: {match['matched_roles']}")
            print(f"  - Confidence: {match['confidence_score']}")
        else:
            print("ℹ️  No existing matches found")
    else:
        print("⚠️  Need both green and non-green agents to test matching")

def main():
    """Main test function."""
    try:
        # Check if we're in the right directory
        if not os.path.exists("src/backend"):
            print("❌ Error: Please run this script from the project root directory")
            return
        
        # Test basic database operations
        test_database_operations()
        
        # Test with real agents
        test_with_real_agents()
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
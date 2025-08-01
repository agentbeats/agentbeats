#!/usr/bin/env python3
"""
Test script to verify backend can access the database data we created.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend.services.match_storage import MatchStorage

def test_backend_db_access():
    """Test if the backend can access the database data we created."""
    print("🧪 Testing Backend Database Access")
    print("=" * 50)
    
    # Initialize storage service (same as backend uses)
    match_storage = MatchStorage()
    
    try:
        # Test 1: Get statistics
        print("📊 Testing get_match_stats()...")
        stats = match_storage.get_match_stats()
        print(f"✅ Success! Database stats: {stats}")
        
        # Test 2: Get matches for our test green agent
        print("\n🔍 Testing get_matches_for_green_agent()...")
        green_matches = match_storage.get_matches_for_green_agent("test_green_agent_123")
        print(f"✅ Success! Found {len(green_matches)} matches for test green agent")
        
        for i, match in enumerate(green_matches, 1):
            print(f"  {i}. Match ID: {match['id']}")
            print(f"     Other Agent: {match['other_agent_id']}")
            print(f"     Matched Roles: {match['matched_roles']}")
            print(f"     Confidence: {match['confidence_score']:.3f}")
        
        # Test 3: Get matches by role
        print("\n🎭 Testing get_matches_by_role()...")
        for role in ['prompt_injector', 'defense_guardian', 'neutral_observer']:
            role_matches = match_storage.get_matches_by_role(role)
            print(f"✅ Role '{role}': {len(role_matches)} matches")
        
        # Test 4: Get matches for specific agent
        print("\n🤖 Testing get_matches_for_agent()...")
        agent_matches = match_storage.get_matches_for_agent("test_green_agent_123")
        print(f"✅ Success! Agent matches: {agent_matches}")
        
        print("\n🎉 All backend database access tests passed!")
        print("✅ The backend can successfully access the role matching data we created.")
        
    except Exception as e:
        print(f"🔴 Error testing backend database access: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to test backend database access."""
    try:
        # Check if we're in the right directory
        if not os.path.exists("src/backend"):
            print("❌ Error: Please run this script from the project root directory")
            print("   Expected to find: src/backend/")
            return
        
        # Run the test
        test_backend_db_access()
        
    except KeyboardInterrupt:
        print("\n⏹️  Script interrupted by user")
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
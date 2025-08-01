#!/usr/bin/env python3
"""
Test script to clear test data from the role matching database.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend.services.match_storage import MatchStorage

def clear_test_data():
    """Clear test data from the database."""
    print("🧹 Clearing Test Data from Database")
    print("=" * 50)
    
    # Initialize storage service
    match_storage = MatchStorage()
    
    try:
        # Get statistics before cleanup
        stats_before = match_storage.get_match_stats()
        print(f"📊 Database Statistics Before Cleanup:")
        print(f"  - Total Matches: {stats_before['total_matches']}")
        print(f"  - Total Role Assignments: {stats_before['total_role_assignments']}")
        print(f"  - Average Confidence: {stats_before['average_confidence']:.3f}")
        print()
        
        # Delete test matches for the green agent
        test_green_agent_id = "test_green_agent_123"
        deleted_count = match_storage.delete_matches_for_agent(test_green_agent_id)
        
        print(f"🗑️  Deleted {deleted_count} test matches for agent: {test_green_agent_id}")
        
        # Get statistics after cleanup
        stats_after = match_storage.get_match_stats()
        print(f"\n📊 Database Statistics After Cleanup:")
        print(f"  - Total Matches: {stats_after['total_matches']}")
        print(f"  - Total Role Assignments: {stats_after['total_role_assignments']}")
        print(f"  - Average Confidence: {stats_after['average_confidence']:.3f}")
        
        # Calculate difference
        matches_removed = stats_before['total_matches'] - stats_after['total_matches']
        roles_removed = stats_before['total_role_assignments'] - stats_after['total_role_assignments']
        
        print(f"\n📈 Cleanup Summary:")
        print(f"  - Matches Removed: {matches_removed}")
        print(f"  - Role Assignments Removed: {roles_removed}")
        
        if matches_removed > 0:
            print("✅ Test data successfully cleared!")
        else:
            print("ℹ️  No test data found to clear.")
            
    except Exception as e:
        print(f"🔴 Error clearing test data: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to clear test data."""
    try:
        # Check if we're in the right directory
        if not os.path.exists("src/backend"):
            print("❌ Error: Please run this script from the project root directory")
            print("   Expected to find: src/backend/")
            return
        
        # Run the cleanup
        clear_test_data()
        
    except KeyboardInterrupt:
        print("\n⏹️  Script interrupted by user")
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
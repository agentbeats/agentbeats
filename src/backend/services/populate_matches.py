#!/usr/bin/env python3
"""
Test script to populate the agent matches table for existing agents.
This script will analyze all existing agents and create role matches between them.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend.services.match_storage import MatchStorage
from backend.services.role_matcher import RoleMatcher
from backend.db.storage import db

async def populate_matches():
    """Populate matches for all existing agents."""
    print("🚀 Starting match population for existing agents...")
    
    # Initialize services
    match_storage = MatchStorage()
    role_matcher = RoleMatcher()
    
    # Get all agents
    agents = db.list("agents")
    print(f"📊 Found {len(agents)} agents in database")
    
    if not agents:
        print("❌ No agents found in database. Please register some agents first.")
        return
    
    # Separate green and non-green agents
    green_agents = [a for a in agents if a["register_info"]["is_green"]]
    non_green_agents = [a for a in agents if not a["register_info"]["is_green"]]
    
    print(f"🟢 Green agents: {len(green_agents)}")
    print(f"🔴 Non-green agents: {len(non_green_agents)}")
    
    if not green_agents:
        print("❌ No green agents found. Green agents are required for role matching.")
        return
    
    if not non_green_agents:
        print("❌ No non-green agents found. Non-green agents are required for role matching.")
        return
    
    # Clear existing matches
    print("🧹 Clearing existing matches...")
    try:
        # Get all existing matches to see what we're clearing
        stats = match_storage.get_match_stats()
        if stats["total_matches"] > 0:
            print(f"Found {stats['total_matches']} existing matches, clearing them...")
            
            # Clear matches for each green agent
            for green_agent in green_agents:
                deleted_count = match_storage.delete_matches_for_agent(green_agent["agent_id"])
                if deleted_count > 0:
                    print(f"  🗑️  Cleared {deleted_count} matches for {green_agent['register_info']['alias']}")
        else:
            print("  ℹ️  No existing matches found")
    except Exception as e:
        print(f"  ⚠️  Warning: Could not clear existing matches: {e}")
        print("  ℹ️  Continuing with new match creation...")
    
    total_matches_created = 0
    
    # Analyze each green agent against all non-green agents
    for i, green_agent in enumerate(green_agents):
        print(f"\n🔍 Analyzing green agent {i+1}/{len(green_agents)}: {green_agent['register_info']['alias']}")
        
        requirements = green_agent["register_info"].get("participant_requirements", [])
        if not requirements:
            print(f"  ⚠️  No participant requirements found for {green_agent['register_info']['alias']}")
            continue
        
        # Validate requirements structure
        valid_requirements = []
        for req in requirements:
            if isinstance(req, dict) and "name" in req:
                valid_requirements.append(req)
            else:
                print(f"  ⚠️  Invalid requirement format: {req}")
        
        if not valid_requirements:
            print(f"  ⚠️  No valid participant requirements found for {green_agent['register_info']['alias']}")
            continue
        
        print(f"  📋 Requirements: {[req['name'] for req in valid_requirements]}")
        
        for j, other_agent in enumerate(non_green_agents):
            print(f"    🔄 Analyzing against {other_agent['register_info']['alias']} ({j+1}/{len(non_green_agents)})")
            
            # Validate agent cards exist
            if not green_agent.get("agent_card"):
                print(f"      ⚠️  No agent card found for green agent {green_agent['register_info']['alias']}")
                continue
            
            if not other_agent.get("agent_card"):
                print(f"      ⚠️  No agent card found for other agent {other_agent['register_info']['alias']}")
                continue
            
            try:
                # Analyze compatibility
                result = await role_matcher.analyze_agent_for_roles(
                    green_agent["agent_card"],
                    valid_requirements,
                    other_agent["agent_card"]
                )
                
                if result.get("matched_roles"):
                    try:
                        match_record = {
                            "green_agent_id": green_agent["agent_id"],
                            "other_agent_id": other_agent["agent_id"],
                            "matched_roles": result["matched_roles"],
                            "reasons": result["reasons"],
                            "confidence_score": result.get("confidence_score", 0.0),
                            "created_by": "test_script"
                        }
                        
                        created_match = match_storage.create_match(match_record)
                        total_matches_created += 1
                        
                        print(f"      ✅ Created match: {result['matched_roles']} (confidence: {result.get('confidence_score', 0.0):.2f})")
                    except Exception as db_error:
                        print(f"      💥 Database error creating match: {str(db_error)}")
                else:
                    print(f"      ❌ No matches found")
                    
            except Exception as e:
                print(f"      💥 Error analyzing: {str(e)}")
    
    # Print summary
    print(f"\n🎉 Match population complete!")
    print(f"📈 Total matches created: {total_matches_created}")
    
    # Show final statistics
    try:
        final_stats = match_storage.get_match_stats()
        print(f"📊 Final database stats:")
        print(f"  - Total matches: {final_stats['total_matches']}")
        print(f"  - Total role assignments: {final_stats['total_role_assignments']}")
        print(f"  - Average confidence: {final_stats['average_confidence']:.3f}")
        if final_stats['top_roles']:
            print(f"  - Top roles: {[r['role'] for r in final_stats['top_roles'][:3]]}")
    except Exception as e:
        print(f"  ⚠️  Could not get final stats: {e}")
    
    # Show some sample matches
    if total_matches_created > 0:
        print("\n📋 Sample matches:")
        for green_agent in green_agents[:2]:  # Show first 2 green agents
            try:
                matches = match_storage.get_matches_for_green_agent(green_agent["agent_id"])
                if matches:
                    print(f"\n  🟢 {green_agent['register_info']['alias']}:")
                    for match in matches[:3]:  # Show first 3 matches
                        other_agent = next((a for a in non_green_agents if a["agent_id"] == match["other_agent_id"]), None)
                        if other_agent:
                            print(f"    🤝 {other_agent['register_info']['alias']}: {match['matched_roles']} ({match['confidence_score']:.2f})")
            except Exception as e:
                print(f"  ⚠️  Could not get matches for {green_agent['register_info']['alias']}: {e}")
    else:
        print("\n⚠️  No matches were created. This could be due to:")
        print("  - No compatible agents found")
        print("  - LLM analysis errors")
        print("  - Missing agent cards or requirements")

def main():
    """Main function to run the match population."""
    try:
        # Check if we're in the right directory
        if not os.path.exists("src/backend"):
            print("❌ Error: Please run this script from the project root directory")
            print("   Expected to find: src/backend/")
            return
        
        # Check for required environment variables
        if not os.getenv("OPENROUTER_API_KEY"):
            print("❌ Error: OPENROUTER_API_KEY environment variable is required")
            print("   Please set it before running this script")
            return
        
        # Run the async function
        asyncio.run(populate_matches())
        
    except KeyboardInterrupt:
        print("\n⏹️  Script interrupted by user")
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
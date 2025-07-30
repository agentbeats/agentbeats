#!/usr/bin/env python3
"""
Test script to populate agent matches for one specific green/opponent agent pair.
Usage: python populate_agent_match.py <green_agent_id> <opponent_agent_id>
"""

import asyncio
import os
import sys
import argparse
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend.services.match_storage import MatchStorage
from backend.services.role_matcher import RoleMatcher
from backend.db.storage import db

async def populate_single_match(green_agent_id: str, opponent_agent_id: str):
    """Populate matches for one specific green/opponent agent pair."""
    print(f"🚀 Starting match population for green agent {green_agent_id} vs opponent {opponent_agent_id}...")
    
    # Initialize services
    match_storage = MatchStorage()
    role_matcher = RoleMatcher()
    
    # Get the specific agents
    green_agent = db.get("agents", green_agent_id)
    opponent_agent = db.get("agents", opponent_agent_id)
    
    if not green_agent:
        print(f"❌ Green agent with ID {green_agent_id} not found in database")
        return
    
    if not opponent_agent:
        print(f"❌ Opponent agent with ID {opponent_agent_id} not found in database")
        return
    
    # Validate agent types
    if not green_agent["register_info"]["is_green"]:
        print(f"❌ Agent {green_agent_id} is not a green agent")
        return
    
    if opponent_agent["register_info"]["is_green"]:
        print(f"❌ Agent {opponent_agent_id} is a green agent, but we need a non-green opponent")
        return
    
    print(f"🟢 Green agent: {green_agent['register_info']['alias']}")
    print(f"🔴 Opponent agent: {opponent_agent['register_info']['alias']}")
    
    # Get participant requirements
    requirements = green_agent["register_info"].get("participant_requirements", [])
    if not requirements:
        print(f"❌ No participant requirements found for {green_agent['register_info']['alias']}")
        return
    
    # Validate requirements structure
    valid_requirements = []
    for req in requirements:
        if isinstance(req, dict) and "name" in req:
            valid_requirements.append(req)
        else:
            print(f"⚠️  Invalid requirement format: {req}")
    
    if not valid_requirements:
        print(f"❌ No valid participant requirements found for {green_agent['register_info']['alias']}")
        return
    
    print(f"📋 Requirements: {[req['name'] for req in valid_requirements]}")
    
    # Validate agent cards exist
    if not green_agent.get("agent_card"):
        print(f"❌ No agent card found for green agent {green_agent['register_info']['alias']}")
        return
    
    if not opponent_agent.get("agent_card"):
        print(f"❌ No agent card found for opponent agent {opponent_agent['register_info']['alias']}")
        return
    
    # Clear existing matches for this pair
    print("🧹 Clearing existing matches for this agent pair...")
    try:
        existing_matches = match_storage.get_matches_for_green_agent(green_agent_id)
        matches_to_delete = [m for m in existing_matches if m["other_agent_id"] == opponent_agent_id]
        if matches_to_delete:
            print(f"  Found {len(matches_to_delete)} existing matches, deleting them...")
            for match in matches_to_delete:
                match_storage.delete_match(match["match_id"])
        else:
            print("  No existing matches found for this pair")
    except Exception as e:
        print(f"  ⚠️  Warning: Could not clear existing matches: {e}")
        print("  ℹ️  Continuing with new match creation...")
    
    # Analyze compatibility
    print(f"🔍 Analyzing compatibility...")
    try:
        result = await role_matcher.analyze_agent_for_roles(
            green_agent["agent_card"],
            valid_requirements,
            opponent_agent["agent_card"]
        )
        
        if result.get("matched_roles"):
            try:
                match_record = {
                    "green_agent_id": green_agent_id,
                    "other_agent_id": opponent_agent_id,
                    "matched_roles": result["matched_roles"],
                    "reasons": result["reasons"],
                    "confidence_score": result.get("confidence_score", 0.0),
                    "created_by": "test_script_single"
                }
                
                created_match = match_storage.create_match(match_record)
                
                print(f"✅ Successfully created match!")
                print(f"📊 Match details:")
                print(f"  - Match ID: {created_match['match_id']}")
                print(f"  - Matched roles: {result['matched_roles']}")
                print(f"  - Confidence score: {result.get('confidence_score', 0.0):.3f}")
                print(f"  - Reasons: {result.get('reasons', 'No reasons provided')}")
                
            except Exception as db_error:
                print(f"💥 Database error creating match: {str(db_error)}")
        else:
            print(f"❌ No matches found between these agents")
            print(f"  Analysis result: {result}")
            
    except Exception as e:
        print(f"💥 Error analyzing compatibility: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run the single match population."""
    parser = argparse.ArgumentParser(description="Populate matches for one specific green/opponent agent pair")
    parser.add_argument("green_agent_id", help="UUID of the green agent")
    parser.add_argument("opponent_agent_id", help="UUID of the opponent agent")
    
    args = parser.parse_args()
    
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
        asyncio.run(populate_single_match(args.green_agent_id, args.opponent_agent_id))
        
    except KeyboardInterrupt:
        print("\n⏹️  Script interrupted by user")
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
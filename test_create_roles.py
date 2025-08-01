#!/usr/bin/env python3
"""
Test script to create role matches with example agent cards and store them in the database.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend.services.match_storage import MatchStorage
from backend.services.role_matcher import RoleMatcher

# Example agent cards for testing
EXAMPLE_GREEN_AGENT_CARD = {
    "name": "Tensortrust Battle Host",
    "description": "A sophisticated battle coordinator and referee agent designed to host AI agent competitions. Manages game flow, enforces rules, and evaluates outcomes.",
    "version": "1.0.0",
    "protocolVersion": "2024-12-01",
    "capabilities": {
        "battle_coordination": True,
        "rule_enforcement": True,
        "outcome_evaluation": True,
        "real_time_monitoring": True
    },
    "skills": [
        {"name": "game_master"},
        {"name": "referee"},
        {"name": "coordinator"},
        {"name": "evaluator"}
    ]
}

EXAMPLE_RED_AGENT_CARD = {
    "name": "Prompt Injection Specialist",
    "description": "An AI agent specialized in prompt injection attacks. Designed to find vulnerabilities in language models and exploit them through carefully crafted prompts.",
    "version": "1.0.0",
    "protocolVersion": "2024-12-01",
    "capabilities": {
        "prompt_injection": True,
        "vulnerability_assessment": True,
        "social_engineering": True,
        "adversarial_testing": True
    },
    "skills": [
        {"name": "prompt_engineering"},
        {"name": "vulnerability_research"},
        {"name": "social_engineering"},
        {"name": "adversarial_attack"}
    ]
}

EXAMPLE_BLUE_AGENT_CARD = {
    "name": "Defense Guardian",
    "description": "A defensive AI agent designed to protect against prompt injection attacks. Implements robust guardrails and safety measures.",
    "version": "1.0.0",
    "protocolVersion": "2024-12-01",
    "capabilities": {
        "prompt_filtering": True,
        "safety_guardrails": True,
        "threat_detection": True,
        "defensive_response": True
    },
    "skills": [
        {"name": "defense_mechanism"},
        {"name": "safety_filter"},
        {"name": "threat_detection"},
        {"name": "protective_response"}
    ]
}

EXAMPLE_PURPLE_AGENT_CARD = {
    "name": "Neutral Observer",
    "description": "A neutral AI agent that observes and documents battle proceedings without taking sides.",
    "version": "1.0.0",
    "protocolVersion": "2024-12-01",
    "capabilities": {
        "observation": True,
        "documentation": True,
        "neutral_analysis": True,
        "reporting": True
    },
    "skills": [
        {"name": "observer"},
        {"name": "documenter"},
        {"name": "analyst"},
        {"name": "reporter"}
    ]
}

async def create_role_matches():
    """Create role matches with example agent cards and store them in the database."""
    print("🧪 Creating Role Matches with Example Agent Cards")
    print("=" * 60)
    
    # Initialize services
    match_storage = MatchStorage()
    role_matcher = RoleMatcher()
    
    # Example participant requirements for the green agent
    participant_requirements = [
        {
            "role": "red_agent",
            "name": "prompt_injector",
            "description": "Acts as the prompt injection attacker",
            "required": True
        },
        {
            "role": "blue_agent", 
            "name": "defense_guardian",
            "description": "Acts as the defensive guardian",
            "required": True
        },
        {
            "role": "purple_agent",
            "name": "neutral_observer", 
            "description": "Acts as the neutral observer",
            "required": False
        }
    ]
    
    # Test agents
    test_agents = [
        ("Red Agent", EXAMPLE_RED_AGENT_CARD),
        ("Blue Agent", EXAMPLE_BLUE_AGENT_CARD),
        ("Purple Agent", EXAMPLE_PURPLE_AGENT_CARD)
    ]
    
    print(f"🟢 Green Agent: {EXAMPLE_GREEN_AGENT_CARD['name']}")
    print(f"📋 Requirements: {[req['name'] for req in participant_requirements]}")
    print()
    
    matches_created = []
    
    # Test each agent against the green agent's requirements
    for agent_name, agent_card in test_agents:
        print(f"🔍 Analyzing {agent_name} against green agent requirements...")
        
        try:
            # Analyze compatibility
            result = await role_matcher.analyze_agent_for_roles(
                EXAMPLE_GREEN_AGENT_CARD,
                participant_requirements,
                agent_card
            )
            
            print(f"  📊 Analysis Result:")
            print(f"    - Matched Roles: {result.get('matched_roles', [])}")
            print(f"    - Confidence Score: {result.get('confidence_score', 0.0):.3f}")
            print(f"    - Reasons: {result.get('reasons', {})}")
            
            if result.get("matched_roles"):
                print(f"  ✅ {agent_name} can fulfill roles: {result['matched_roles']}")
                
                # Create match record for database storage
                match_record = {
                    "green_agent_id": "test_green_agent_123",
                    "other_agent_id": f"test_{agent_name.lower().replace(' ', '_')}_456",
                    "matched_roles": result["matched_roles"],
                    "reasons": result["reasons"],
                    "confidence_score": result.get("confidence_score", 0.0),
                    "created_by": "test_script"
                }
                
                # Store in database
                created_match = match_storage.create_match(match_record)
                matches_created.append(created_match)
                
                print(f"  💾 Stored match in database with ID: {created_match['id']}")
            else:
                print(f"  ❌ {agent_name} cannot fulfill any required roles")
                
        except Exception as e:
            print(f"  🔴 Error analyzing {agent_name}: {str(e)}")
        
        print()
    
    # Verify database storage
    print("🔍 Verifying Database Storage")
    print("=" * 40)
    
    try:
        # Get all matches for the green agent
        green_matches = match_storage.get_matches_for_green_agent("test_green_agent_123")
        print(f"📊 Found {len(green_matches)} matches for green agent in database")
        
        for i, match in enumerate(green_matches, 1):
            print(f"  {i}. Match ID: {match['id']}")
            print(f"     Other Agent: {match['other_agent_id']}")
            print(f"     Matched Roles: {match['matched_roles']}")
            print(f"     Confidence: {match['confidence_score']:.3f}")
            print(f"     Reasons: {list(match['reasons'].keys())}")
            print()
        
        # Get overall statistics
        stats = match_storage.get_match_stats()
        print(f"📈 Database Statistics:")
        print(f"  - Total Matches: {stats['total_matches']}")
        print(f"  - Total Role Assignments: {stats['total_role_assignments']}")
        print(f"  - Average Confidence: {stats['average_confidence']:.3f}")
        
        if stats['top_roles']:
            print(f"  - Top Roles: {[r['role'] for r in stats['top_roles'][:3]]}")
        
    except Exception as e:
        print(f"🔴 Error accessing database: {str(e)}")
    
    print("\n🎉 Role matching test completed!")
    print("💡 Use test_clear_database.py to clean up the test data when done.")

def main():
    """Main function to run the role matching test."""
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
        asyncio.run(create_role_matches())
        
    except KeyboardInterrupt:
        print("\n⏹️  Script interrupted by user")
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
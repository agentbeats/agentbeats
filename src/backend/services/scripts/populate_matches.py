#!/usr/bin/env python3
"""Populate role matches for existing agents."""

import argparse
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from match_storage import MatchStorage
from role_matcher import RoleMatcher

def get_all_agents():
    import sys
    from pathlib import Path
    db_path = Path(__file__).parent.parent.parent / "db" / "storage.py"
    sys.path.insert(0, str(db_path.parent.parent))
    from db.storage import db
    try:
        return db.list("agents")
    except Exception as e:
        print(f"Error fetching agents: {str(e)}")
        return []

def show_agent_stats(agents):
    """Display statistics about agents in the database."""
    if not agents:
        print("No agents found in database")
        return
    
    total_agents = len(agents)
    online_agents = len([a for a in agents if a.get("live", False)])
    offline_agents = total_agents - online_agents
    
    green_agents = len([a for a in agents if a.get("register_info", {}).get("is_green", False)])
    other_agents = total_agents - green_agents
    
    print(f"Agent Statistics:")
    print(f"  Total agents in database: {total_agents}")
    print(f"  Online agents: {online_agents}")
    print(f"  Offline agents: {offline_agents}")
    print(f"  Green agents: {green_agents}")
    print(f"  Other agents: {other_agents}")
    print()

def get_green_agents(agents):
    return [a for a in agents if a.get("register_info", {}).get("is_green", False)]

def get_other_agents(agents):
    return [a for a in agents if not a.get("register_info", {}).get("is_green", False)]

def extract_requirements(green_agent):
    requirements = green_agent.get("register_info", {}).get("participant_requirements", [])
    if not isinstance(requirements, list):
        return []
    
    normalized = []
    for req in requirements:
        if isinstance(req, dict):
            if "name" in req:
                normalized.append(req)
            elif "role" in req:
                normalized.append({"name": req["role"], "required": req.get("required", True)})
        elif isinstance(req, str):
            normalized.append({"name": req, "required": True})
    return normalized

async def analyze_matches(role_matcher, green_agent, other_agents, match_storage):
    green_agent_card = green_agent.get("agent_card", {})
    green_agent_id = green_agent.get("agent_id", "unknown")
    requirements = extract_requirements(green_agent)
    
    if not requirements:
        print(f"No requirements found for {green_agent_id}")
        return []
    
    print(f"Analyzing {len(other_agents)} agents for {green_agent_id}")
    matches = []
    skipped = 0
    
    for other_agent in other_agents:
        other_agent_card = other_agent.get("agent_card", {})
        other_agent_id = other_agent.get("agent_id", "unknown")
        
        # Check if match already exists
        existing_matches = match_storage.get_matches_for_green_agent(green_agent_id)
        if any(m["other_agent_id"] == other_agent_id for m in existing_matches):
            print(f"  {other_agent_id} -> Skipped (already exists)")
            skipped += 1
            continue
        
        try:
            result = await role_matcher.analyze_agent_for_roles(
                green_agent_card, requirements, other_agent_card
            )
            
            if result.get("matched_roles"):
                match_record = {
                    "green_agent_id": green_agent_id,
                    "other_agent_id": other_agent_id,
                    "matched_roles": result["matched_roles"],
                    "reasons": result["reasons"],
                    "confidence_score": result.get("confidence_score", 0.0),
                    "created_by": "populate_matches_script"
                }
                matches.append(match_record)
                print(f"  {other_agent_id} -> {result['matched_roles']} ({result.get('confidence_score', 0.0):.2f})")
            else:
                print(f"  {other_agent_id} -> No matches")
                
        except Exception as e:
            print(f"  Error analyzing {other_agent_id}: {str(e)}")
    
    if skipped > 0:
        print(f"  Skipped {skipped} existing matches")
    
    return matches

async def populate_all(match_storage, role_matcher, dry_run=False):
    agents = get_all_agents()
    show_agent_stats(agents)
    
    if not agents:
        print("No agents found")
        return
    
    green_agents = get_green_agents(agents)
    other_agents = get_other_agents(agents)
    
    print(f"Found {len(green_agents)} green agents, {len(other_agents)} other agents")
    
    if not green_agents or not other_agents:
        print("Need both green and other agents")
        return
    
    total_matches = 0
    
    for green_agent in green_agents:
        green_agent_id = green_agent.get("agent_id", "unknown")
        print(f"Processing {green_agent_id}")
        
        matches = await analyze_matches(role_matcher, green_agent, other_agents, match_storage)
        
        if not dry_run and matches:
            for match in matches:
                try:
                    match_storage.create_match(match)
                    total_matches += 1
                except Exception as e:
                    print(f"  Error saving match: {str(e)}")
        elif dry_run:
            total_matches += len(matches)
    
    print(f"{'Would create' if dry_run else 'Created'} {total_matches} matches")

async def populate_agent(match_storage, role_matcher, agent_id, dry_run=False):
    agents = get_all_agents()
    show_agent_stats(agents)
    
    if not agents:
        print("No agents found")
        return
    
    target_agent = next((a for a in agents if a.get("agent_id") == agent_id), None)
    if not target_agent:
        print(f"Agent {agent_id} not found")
        return
    
    agent_card = target_agent.get("agent_card", {})
    is_green = target_agent.get("register_info", {}).get("is_green", False)
    
    if is_green:
        other_agents = get_other_agents(agents)
        if not other_agents:
            print("No other agents found")
            return
        
        matches = await analyze_matches(role_matcher, target_agent, other_agents, match_storage)
        
        if not dry_run and matches:
            for match in matches:
                try:
                    match_storage.create_match(match)
                except Exception as e:
                    print(f"  Error saving match: {str(e)}")
        
        print(f"{'Would create' if dry_run else 'Created'} {len(matches)} matches")
        
    else:
        green_agents = get_green_agents(agents)
        if not green_agents:
            print("No green agents found")
            return
        
        total_matches = 0
        
        for green_agent in green_agents:
            green_agent_card = green_agent.get("agent_card", {})
            green_agent_id = green_agent.get("agent_id", "unknown")
            requirements = extract_requirements(green_agent)
            
            if not requirements:
                continue
            
            try:
                result = await role_matcher.analyze_agent_for_roles(
                    green_agent_card, requirements, agent_card
                )
                
                if result.get("matched_roles"):
                    match_record = {
                        "green_agent_id": green_agent_id,
                        "other_agent_id": agent_id,
                        "matched_roles": result["matched_roles"],
                        "reasons": result["reasons"],
                        "confidence_score": result.get("confidence_score", 0.0),
                        "created_by": "populate_matches_script"
                    }
                    
                    if not dry_run:
                        try:
                            match_storage.create_match(match_record)
                        except Exception as e:
                            print(f"  Error saving match: {str(e)}")
                    
                    total_matches += 1
                    print(f"  {green_agent_id} -> {result['matched_roles']} ({result.get('confidence_score', 0.0):.2f})")
                    
            except Exception as e:
                print(f"  Error analyzing against {green_agent_id}: {str(e)}")
        
        print(f"{'Would create' if dry_run else 'Created'} {total_matches} matches")

async def populate_green_agent(match_storage, role_matcher, green_agent_id, dry_run=False):
    agents = get_all_agents()
    show_agent_stats(agents)
    
    if not agents:
        print("No agents found")
        return
    
    target_agent = next((a for a in agents if a.get("agent_id") == green_agent_id and 
                        a.get("register_info", {}).get("is_green", False)), None)
    if not target_agent:
        print(f"Green agent {green_agent_id} not found")
        return
    
    other_agents = get_other_agents(agents)
    if not other_agents:
        print("No other agents found")
        return
    
    matches = await analyze_matches(role_matcher, target_agent, other_agents, match_storage)
    
    if not dry_run and matches:
        for match in matches:
            try:
                match_storage.create_match(match)
            except Exception as e:
                print(f"  Error saving match: {str(e)}")
    
    print(f"{'Would create' if dry_run else 'Created'} {len(matches)} matches")

def show_stats(match_storage):
    stats = match_storage.get_match_stats()
    print(f"Total matches: {stats['total_matches']}")
    print(f"Total role assignments: {stats['total_role_assignments']}")
    print(f"Average confidence: {stats['average_confidence']}")

async def main():
    parser = argparse.ArgumentParser(description="Populate role matches")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true')
    group.add_argument('--agent', type=str)
    group.add_argument('--green-agent', type=str)
    group.add_argument('--stats', action='store_true')
    group.add_argument('--agent-stats', action='store_true', help='Show agent statistics only')
    
    parser.add_argument('--dry-run', action='store_true')
    
    args = parser.parse_args()
    
    try:
        if args.agent_stats:
            agents = get_all_agents()
            show_agent_stats(agents)
            return
        
        match_storage = MatchStorage()
        role_matcher = RoleMatcher()
        
        if args.stats:
            show_stats(match_storage)
        elif args.all:
            await populate_all(match_storage, role_matcher, args.dry_run)
        elif args.agent:
            await populate_agent(match_storage, role_matcher, args.agent, args.dry_run)
        elif args.green_agent:
            await populate_green_agent(match_storage, role_matcher, args.green_agent, args.dry_run)
        
        if not args.stats:
            show_stats(match_storage)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
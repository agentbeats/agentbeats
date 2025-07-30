import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
from ..db.storage import db
from datetime import datetime

class RoleMatcher:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        self._cache = {}  # Simple in-memory cache
        self._cache_ttl = 3600  # 1 hour cache TTL
        self._cache_timestamps = {}
    
    async def analyze_agent_for_roles(
        self, 
        green_agent_card: Dict[str, Any],
        participant_requirements: List[Dict[str, Any]],
        other_agent_card: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze if an agent can fulfill specific roles based on their card description."""
        
        # Check cache first
        cache_key = self._get_cache_key(green_agent_card, participant_requirements, other_agent_card)
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        # Extract role names from requirements
        role_names = [req["name"] for req in participant_requirements]
        
        # Build prompt for LLM analysis
        prompt = self._build_analysis_prompt(
            green_agent_card, role_names, other_agent_card
        )
        
        try:
            response = await self.client.chat.completions.create(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")
            
            # Try to parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError as json_error:
                print(f"JSON parsing error: {json_error}")
                print(f"Raw response: {content}")
                # Try to extract JSON from the response if it's wrapped in markdown
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    raise ValueError(f"Invalid JSON response: {content}")
            
            # Validate the result structure
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")
            
            if "matched_roles" not in result or "reasons" not in result or "confidence_score" not in result:
                raise ValueError("Missing required fields in response")
            
            if not isinstance(result["matched_roles"], list):
                raise ValueError("matched_roles must be a list")
            
            if not isinstance(result["reasons"], dict):
                raise ValueError("reasons must be a dictionary")
            
            if not isinstance(result["confidence_score"], (int, float)):
                raise ValueError("confidence_score must be a number")
            
            # Ensure confidence score is within bounds
            result["confidence_score"] = max(0.0, min(1.0, float(result["confidence_score"])))
            
            # Cache the result
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.utcnow().timestamp()
            
            return result
            
        except Exception as e:
            print(f"Error in role analysis: {str(e)}")
            error_result = {
                "matched_roles": [],
                "reasons": {},
                "confidence_score": 0.0,
                "error": str(e)
            }
            
            # Cache error result too (shorter TTL)
            self._cache[cache_key] = error_result
            self._cache_timestamps[cache_key] = datetime.utcnow().timestamp()
            
            return error_result
    
    def _get_cache_key(self, green_agent_card: Dict[str, Any], participant_requirements: List[Dict[str, Any]], other_agent_card: Dict[str, Any]) -> str:
        """Generate a cache key for the analysis."""
        # Use agent IDs and role names for cache key
        green_id = green_agent_card.get("name", "unknown")
        other_id = other_agent_card.get("name", "unknown")
        role_names = [req["name"] for req in participant_requirements]
        
        return f"{green_id}:{other_id}:{','.join(sorted(role_names))}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid."""
        if cache_key not in self._cache or cache_key not in self._cache_timestamps:
            return False
        
        current_time = datetime.utcnow().timestamp()
        cache_time = self._cache_timestamps[cache_key]
        
        return (current_time - cache_time) < self._cache_ttl
    
    def _build_analysis_prompt(
        self, 
        green_agent_card: Dict[str, Any],
        role_names: List[str],
        other_agent_card: Dict[str, Any]
    ) -> str:
        return f"""
You are analyzing agent compatibility for a battle scenario. 

GREEN AGENT (Scenario Coordinator):
Name: {green_agent_card.get('name', 'Unknown')}
Description: {green_agent_card.get('description', 'No description')}
Capabilities: {json.dumps(green_agent_card.get('capabilities', {}), indent=2)}
Skills: {json.dumps(green_agent_card.get('skills', []), indent=2)}

AVAILABLE ROLES TO FILL:
{json.dumps(role_names, indent=2)}

OTHER AGENT TO ANALYZE:
Name: {other_agent_card.get('name', 'Unknown')}
Description: {other_agent_card.get('description', 'No description')}
Capabilities: {json.dumps(other_agent_card.get('capabilities', {}), indent=2)}
Skills: {json.dumps(other_agent_card.get('skills', []), indent=2)}

TASK: For each role in the available roles list, determine if this agent can fulfill that role based on their description, capabilities, and skills. Consider how well they align with the green agent's scenario requirements.

IMPORTANT: You must return a valid JSON object with this EXACT structure:
{{
    "matched_roles": ["role1", "role2"],
    "reasons": {{
        "role1": "Detailed reason why this agent fits role1",
        "role2": "Detailed reason why this agent fits role2"
    }},
    "confidence_score": 0.85
}}

RULES:
1. Only include roles where you have reasonable confidence (>0.3) that the agent can fulfill them
2. confidence_score must be a number between 0.0 and 1.0
3. matched_roles must be an array of role names from the available roles list
4. reasons must be an object mapping each matched role to a detailed explanation
5. The JSON must be valid and parseable

Analyze the compatibility and return the JSON response:
"""
    
    def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache.clear()
        self._cache_timestamps.clear() 
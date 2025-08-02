import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
from datetime import datetime

# =============================================================================
# ROLE MATCHING LOGGING CONFIGURATION
# =============================================================================
# Configure dedicated logger for role matching operations
role_matcher_logger = logging.getLogger('role_matcher')
role_matcher_logger.setLevel(logging.ERROR)  # Only log errors

# Create console handler if it doesn't exist
if not role_matcher_logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        '%(asctime)s - [ROLE_MATCHER] - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    role_matcher_logger.addHandler(console_handler)
    role_matcher_logger.propagate = False  # Prevent duplicate logs

class RoleMatcher:
    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            role_matcher_logger.error("❌ OPENROUTER_API_KEY environment variable not set")
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
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
        
        green_name = green_agent_card.get('name', 'Unknown')
        other_name = other_agent_card.get('name', 'Unknown')
        role_names = [req["name"] for req in participant_requirements]
        
        # Check cache first
        cache_key = self._get_cache_key(green_agent_card, participant_requirements, other_agent_card)
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
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
                role_matcher_logger.error(f"JSON parsing error: {json_error}")
                
                # Try multiple extraction strategies
                import re
                
                # Strategy 1: Try to extract JSON from markdown code blocks
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Strategy 2: Try to find the first complete JSON object
                    json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', content, re.DOTALL)
                    if json_match:
                        try:
                            result = json.loads(json_match.group(1))
                        except json.JSONDecodeError:
                            # Strategy 3: Try to find JSON between the first { and the last }
                            start = content.find('{')
                            end = content.rfind('}')
                            if start != -1 and end != -1 and end > start:
                                json_str = content[start:end+1]
                                try:
                                    result = json.loads(json_str)
                                except json.JSONDecodeError:
                                    raise ValueError(f"Could not extract valid JSON from response: {content}")
                            else:
                                raise ValueError(f"Could not find JSON structure in response: {content}")
                    else:
                        raise ValueError(f"Could not extract JSON from response: {content}")
            
            # Validate the result structure
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")
            
            required_fields = ["matched_roles", "reasons", "confidence_score"]
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            if not isinstance(result["matched_roles"], list):
                raise ValueError("matched_roles must be a list")
            
            if not isinstance(result["reasons"], dict):
                raise ValueError("reasons must be a dictionary")
            
            if not isinstance(result["confidence_score"], (int, float)):
                raise ValueError("confidence_score must be a number")
            
            # Ensure confidence score is within bounds
            original_confidence = result["confidence_score"]
            result["confidence_score"] = max(0.0, min(1.0, float(result["confidence_score"])))
            if original_confidence != result["confidence_score"]:
                role_matcher_logger.warning(f"Confidence score clamped from {original_confidence} to {result['confidence_score']}")
            
            # Cache the result
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.utcnow().timestamp()
            
            return result
            
        except Exception as e:
            role_matcher_logger.error(f"Error in role analysis for {other_name} vs {green_name}: {str(e)}")
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

IMPORTANT: You must return ONLY a valid JSON object with this EXACT structure. Do not include any additional text, explanations, or markdown formatting:

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
5. Return ONLY the JSON object - no additional text, no explanations, no markdown
6. The JSON must be valid and parseable

Analyze the compatibility and return ONLY the JSON response:
"""
    
    def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache.clear()
        self._cache_timestamps.clear() 
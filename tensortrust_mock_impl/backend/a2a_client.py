import httpx
import logging
import uuid
import json
from typing import Dict, Any, Optional, List
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    Part,
    Message,
)

logger = logging.getLogger(__name__)

class AgentBeatsA2AClient:
    """Client for communicating with agents via A2A protocol using the official SDK."""
    
    def __init__(self):
        self.httpx_client = None
        self.agent_clients = {}  # Cache of A2AClient instances by endpoint
        
    async def _ensure_httpx_client(self):
        if self.httpx_client is None:
            self.httpx_client = httpx.AsyncClient()
            
    async def close(self):
        if self.httpx_client:
            await self.httpx_client.aclose()
            self.httpx_client = None
            
    async def get_agent_card(self, endpoint: str) -> Optional[Dict[str, Any]]:
        try:
            await self._ensure_httpx_client()
            
            # Initialize the card resolver
            resolver = A2ACardResolver(
                httpx_client=self.httpx_client,
                base_url=endpoint,
            )
            
            # Fetch the agent card
            agent_card = await resolver.get_agent_card()
            
            if agent_card:
                # Return as dict for storage compatibility
                return agent_card.model_dump(exclude_none=True)
            else:
                logger.error(f"Failed to get agent card from {endpoint}")
                return None
        except Exception as e:
            logger.error(f"Error getting agent card from {endpoint}: {str(e)}")
            return None
    
    async def _get_or_create_client(self, endpoint: str) -> Optional[A2AClient]:
        """Get or create an A2AClient for the endpoint."""
        if endpoint in self.agent_clients:
            return self.agent_clients[endpoint]
            
        try:
            await self._ensure_httpx_client()
            
            # Initialize the card resolver
            resolver = A2ACardResolver(
                httpx_client=self.httpx_client,
                base_url=endpoint,
            )
            
            # Fetch the agent card
            agent_card = await resolver.get_agent_card()
            
            if agent_card:
                # Create the client
                client = A2AClient(
                    httpx_client=self.httpx_client,
                    agent_card=agent_card
                )
                self.agent_clients[endpoint] = client
                return client
            else:
                logger.error(f"Failed to get agent card for client creation: {endpoint}")
                return None
        except Exception as e:
            logger.error(f"Error creating A2A client for {endpoint}: {str(e)}")
            return None
            
    def reset_agent_trigger(self, starter_url: str) -> bool:
        try:
            # client = await self._get_or_create_client(endpoint)
            # if not client:
            #     return False
        
            # parts = [Part(kind="text", text="RESET_AGENT_FOR_BATTLE")]
            # message = Message(
            #     role="user",
            #     parts=parts,
            #     messageId=uuid.uuid4().hex
            # )
            # params = MessageSendParams(message=message)
            
            # request = SendMessageRequest(
            #     id=str(uuid.uuid4()),
            #     params=params
            # )
            # response = await client.send_message(request)
            
            # return True
            print(f"Resetting agent at {starter_url}...") # TODO: wait for agent starter implementation
            return True
        except Exception as e:
            logger.error(f"Error resetting agent at {starter_url}: {str(e)}")
            return False
            
    async def notify_green_agent(self, 
                                endpoint: str, 
                                blue_agent_card: Dict[str, Any], 
                                red_agent_card: Optional[Dict[str, Any]], 
                                battle_id: str) -> bool:
        """Notify the green agent about a battle and provide opponent agent cards."""
        try:
            client = await self._get_or_create_client(endpoint)
            if not client:
                return False
                
            # Create battle information with agent cards
            battle_info = {
                "type": "battle_start",
                "battle_id": battle_id,
                "blue_agent_card": blue_agent_card,
                "red_agent_card": red_agent_card
            }
            
            # Create message parts with the JSON data

            parts = [Part(kind="text", text=json.dumps(battle_info))]
            
            # Create the message
            message = Message(
                role="user",
                parts=parts,
                messageId=uuid.uuid4().hex
            )
            
            # Create the request parameters
            params = MessageSendParams(message=message)
            
            # Create the request
            request = SendMessageRequest(
                id=str(uuid.uuid4()),
                params=params
            )
            
            # Send the message
            response = await client.send_message(request)
            
            return True
        except Exception as e:
            logger.error(f"Error notifying green agent at {endpoint}: {str(e)}")
            return False

# Create a client instance
a2a_client = AgentBeatsA2AClient()

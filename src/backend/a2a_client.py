import httpx
import logging
import uuid
import time
import json
import asyncio
from typing import Dict, Any, Optional, List
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
    Part,
    Message,
    Role,
    TextPart,
)

logger = logging.getLogger(__name__)

class AgentBeatsA2AClient:
    # TODO: change this name, make it more clear
    """Client for communicating with agents/launcher via A2A protocol using the official SDK."""
    
    def __init__(self):
        self.agent_clients = {}  # Cache of A2AClient instances by endpoint

    
    async def _get_fresh_httpx_client(self):
        return httpx.AsyncClient(timeout=30.0)
            
    async def close(self):
        self.agent_clients.clear()
            
    async def get_agent_card(self, endpoint: str) -> Optional[Dict[str, Any]]:
        httpx_client = None
        try:
            httpx_client = await self._get_fresh_httpx_client()
            # Initialize the card resolver
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
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

        httpx_client = None   
        try:
            httpx_client = await self._get_fresh_httpx_client()
            
            # Initialize the card resolver
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=endpoint,
            )
            
            # Fetch the agent card
            logger.info(f"Fetching agent card from resolver...")
            agent_card = await resolver.get_agent_card()
            
            if agent_card:
                # Create the client
                logger.info(f"Successfully got agent card: {agent_card.model_dump(exclude_none=True)}")
                client = A2AClient(
                    httpx_client=httpx_client,
                    agent_card=agent_card
                )
                self.agent_clients[endpoint] = client
                return client
            else:
                logger.error(f"Failed to get agent card for client creation: {endpoint}")
                return None
        except Exception as e:
            logger.error(f"Error creating A2A client for {endpoint}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
            
    async def reset_agent_trigger(self, launcher_url: str, agent_id: str, extra_args: dict = None) -> bool:
        httpx_client = None
        try:
            extra_args = extra_args or {}
            httpx_client = await self._get_fresh_httpx_client()
            
            reset_payload = {
                "signal": "reset",
                "agent_id": agent_id,
                "extra_args": extra_args
            }

            response = await httpx_client.post(
                f"{launcher_url}/reset",
                json=reset_payload
            )

            if response.status_code != 200:
                logger.error(f"Failed to reset agent at {launcher_url}: {response.status_code}")
                return False
            else:
                logger.info(f"Agent reset successfully at {launcher_url}")     
            
            return True
        except Exception as e:
            logger.error(f"Error resetting agent at {launcher_url}: {str(e)}")
            return False
            
    # async def notify_green_agent(self, 
    #                             endpoint: str, 
    #                             blue_agent_url: str, 
    #                             red_agent_url: Optional[str], 
    #                             battle_id: str) -> bool:
    #     """Notify the green agent about a battle and provide opponent agent cards."""
    #     try:
    #         client = await self._get_or_create_client(endpoint)
    #         if not client:
    #             return False
                
    #         # Create battle information with agent cards
    #         battle_info = {
    #             "type": "battle_start",
    #             "battle_id": battle_id,
    #             "blue_agent_url": blue_agent_url,
    #             "red_agent_url": red_agent_url
    #         }
            
    #         # Create message parts with the JSON data
            
    #         # Create the message
    #         message_payload = {
    #             "message": {
    #                 "role": "user",
    #                 "parts": [{"kind": "text", "text": json.dumps(battle_info)}],
    #                 'messageId': uuid.uuid4().hex,
    #             }
    #         }
            
    #         # Create the request parameters
    #         params = MessageSendParams(**message_payload)
            
    #         # Create the request
    #         request = SendMessageRequest(
    #             id=str(uuid.uuid4()),
    #             params=params
    #         )
            
    #         # Send the message
    #         response = await client.send_message(request)
    #         print(response.model_dump(mode='json', exclude_none=True))
    #         print('=========================================')

    #         return True
    #     except Exception as e:
    #         logger.error(f"Error notifying green agent at {endpoint}: {str(e)}")
    #         return False
        
    async def notify_green_agent(self, 
                                endpoint: str,                                 
                                opponent_infos: List[Dict[str, Any]],
                                battle_id: str) -> bool:
        """Notify the green agent about a battle using streaming message format."""
        try:
            # TODO: make this more eligant, for exmaple, 
            # the launcher should send PUT request after agent is really set
            await asyncio.sleep(5)
            client = await self._get_or_create_client(endpoint)
            if not client:
                return False
                
            # Create battle information with agent cards
            battle_info = {
                "type": "battle_start",
                "battle_id": battle_id,
                "opponent_infos": opponent_infos,  # List of opponent agent info: name and agent_url
            }
            
            logger.info(f"Sending battle info to {endpoint}: {json.dumps(battle_info, indent=2)}")
            
            
            parts = [Part(root=TextPart(text=json.dumps(battle_info)))]
            
            message = Message(
                role=Role.user,
                parts=parts,
                messageId=uuid.uuid4().hex,
                taskId=None
            )
            
            params = MessageSendParams(message=message)
            request = SendStreamingMessageRequest(
                id=str(uuid.uuid4()),
                params=params
            )

            response_received = False
            async for chunk in client.send_message_streaming(request):
                response_received = True
                # break
                
            return response_received
                            
        except Exception as e:
            logger.error(f"Error in notify_green_agent for {endpoint}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            return False
    
    async def send_custom_message(self, 
                                 endpoint: str, 
                                 message_content: str,
                                 message_type: str = "custom") -> bool:
        """
        Generic method to send any custom message to an agent.
        This can be used for testing or sending arbitrary messages.
        """
        try:
            client = await self._get_or_create_client(endpoint)
            if not client:
                logger.error(f"Failed to create client for {endpoint}")
                return False
            
            # Create custom message payload
            custom_data = {
                "type": message_type,
                "content": message_content,
                "timestamp": str(uuid.uuid4()),
                "sender": "a2a_client"
            }
            
            logger.info(f"Sending custom message to {endpoint}: {message_content[:100]}...")
            
            # Try with streaming first
            try:
                parts = [Part(root=TextPart(text=json.dumps(custom_data)))]
                
                message = Message(
                    role=Role.user,
                    parts=parts,
                    messageId=uuid.uuid4().hex,
                    taskId=None
                )
                
                params = MessageSendParams(message=message)
                request = SendStreamingMessageRequest(
                    id=str(uuid.uuid4()),
                    params=params
                )
                
                response_received = False
                async for chunk in client.send_message_streaming(request):
                    response_received = True
                    logger.info(f"Custom message response: {chunk}")
                    # break
                
                return response_received
                
            except Exception as streaming_error:
                logger.warning(f"Streaming failed for custom message: {streaming_error}")
                
                # Fallback to non-streaming
                message = Message(
                    role=Role.user,
                    parts=[Part(root=TextPart(text=json.dumps(custom_data)))],
                    messageId=uuid.uuid4().hex
                )
                
                params = MessageSendParams(message=message)
                request = SendMessageRequest(
                    id=str(uuid.uuid4()),
                    params=params
                )
                
                response = await client.send_message(request)
                logger.info(f"Custom message sent via non-streaming: {response}")
                return True
                
        except Exception as e:
            logger.error(f"Error sending custom message to {endpoint}: {str(e)}")
            return False

# Create a client instance
a2a_client = AgentBeatsA2AClient()

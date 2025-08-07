# -*- coding: utf-8 -*-
"""
Agent communication utilities for easier development using the Agentbeats SDK.
"""

import httpx
import asyncio
from typing import Optional, List, Dict, Any
from uuid import uuid4

from a2a.client import A2AClient, A2ACardResolver
from a2a.types import (
    AgentCard, Message, Part, TextPart, Role, 
    SendStreamingMessageRequest,
    SendStreamingMessageSuccessResponse,
    MessageSendParams,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
)

# Global cache for A2A clients
_a2a_client_cache = {}

async def get_agent_card(target_url: str) -> Optional[Dict[str, Any]]:
    """Get agent card/metadata from a target URL."""
    httpx_client = None
    try:
        httpx_client = httpx.AsyncClient(timeout=1.0)
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=target_url)
        
        agent_card = await resolver.get_agent_card()
        
        if agent_card:
            return agent_card.model_dump(exclude_none=True)
        else:
            return None
    except Exception as e:
        return None
    finally:
        if httpx_client:
            await httpx_client.aclose()

async def create_cached_a2a_client(target_url: str) -> Optional[A2AClient]:
    """Create a cached A2A client for repeated communication."""
    if target_url in _a2a_client_cache:
        return _a2a_client_cache[target_url]
    
    try:
        httpx_client = httpx.AsyncClient()
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=target_url)
        
        agent_card = await resolver.get_agent_card()
        
        if agent_card:
            client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
            _a2a_client_cache[target_url] = client
            return client
        else:
            return None
    except Exception:
        return None


async def create_a2a_client(target_url: str) -> A2AClient:
    """Create an A2A client for the given agent URL."""
    
    httpx_client = httpx.AsyncClient()
    resolver = A2ACardResolver(httpx_client=httpx_client, base_url=target_url)
    
    card: AgentCard | None = await resolver.get_agent_card(
        relative_card_path="/.well-known/agent.json"
    )

    if card is None:
        raise RuntimeError(f"Failed to resolve agent card from {target_url}")

    return A2AClient(httpx_client=httpx_client, agent_card=card)


async def send_message_to_agent(target_url: str, message: str, timeout: Optional[float] = None) -> str:
    """Send a message to an A2A agent and return the response."""
    if timeout is not None and timeout <= 0:
        raise ValueError("Timeout must be positive")
    
    client = None
    try:
        client = await create_a2a_client(target_url)

        params = MessageSendParams(
            message=Message(
                role=Role.user,
                parts=[Part(TextPart(text=message))],
                messageId=uuid4().hex,
                taskId=None,
            )
        )
        req = SendStreamingMessageRequest(id=str(uuid4()), params=params)
        chunks: List[str] = []

        async for chunk in client.send_message_streaming(req):
            if not isinstance(chunk.root, SendStreamingMessageSuccessResponse):
                continue
            event = chunk.root.result
            if isinstance(event, TaskArtifactUpdateEvent):
                for p in event.artifact.parts:
                    if isinstance(p.root, TextPart):
                        chunks.append(p.root.text)
            elif isinstance(event, TaskStatusUpdateEvent):
                msg = event.status.message
                if msg:
                    for p in msg.parts:
                        if isinstance(p.root, TextPart):
                            chunks.append(p.root.text)

        response = "".join(chunks).strip() or "No response from agent."
        
        return response
        
    finally:
        # Clean up the httpx client to prevent resource leaks
        if client and hasattr(client, 'httpx_client'):
            await client.httpx_client.aclose()


async def send_message_to_agents(target_urls: List[str], message: str, timeout: Optional[float] = None) -> Dict[str, str]:
    """Send a message to multiple A2A agents concurrently."""
    if timeout is not None and timeout <= 0:
        raise ValueError("Timeout must be positive")
    
    async def send_to_single_agent(url: str) -> tuple[str, str]:
        try:
            if timeout is not None:
                response = await asyncio.wait_for(
                    send_message_to_agent(url, message), 
                    timeout=timeout
                )
            else:
                response = await send_message_to_agent(url, message)
            return url, response
        except asyncio.TimeoutError:
            return url, f"Error: Timeout after {timeout} seconds"
        except Exception as e:
            return url, f"Error: {str(e)}"
    
    # Create tasks for all agents
    tasks = [send_to_single_agent(url) for url in target_urls]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    response_dict = {}
    
    for i, result in enumerate(results):
        url = target_urls[i]
        if isinstance(result, Exception):
            response_dict[url] = f"Error: {str(result)}"
        elif isinstance(result, tuple) and len(result) == 2:
            response_dict[url] = result[1]  # result is (url, response) tuple
        else:
            response_dict[url] = f"Unexpected result format: {type(result)}"
    
    return response_dict


async def send_messages_to_agents(target_urls: List[str], messages: List[str], timeout: Optional[float] = None) -> Dict[str, str]:
    """Send different messages to multiple A2A agents concurrently."""
    if len(target_urls) != len(messages):
        raise ValueError(f"Number of URLs ({len(target_urls)}) must match number of messages ({len(messages)})")
    
    if timeout is not None and timeout <= 0:
        raise ValueError("Timeout must be positive")
    
    async def send_to_single_agent(url: str, message: str) -> tuple[str, str]:
        try:
            if timeout is not None:
                response = await asyncio.wait_for(
                    send_message_to_agent(url, message), 
                    timeout=timeout
                )
            else:
                response = await send_message_to_agent(url, message)
            return url, response
        except asyncio.TimeoutError:
            return url, f"Error: Timeout after {timeout} seconds"
        except Exception as e:
            return url, f"Error: {str(e)}"
    
    # Create tasks for all agents with their specific messages
    tasks = [send_to_single_agent(url, message) for url, message in zip(target_urls, messages)]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    response_dict = {}
    
    for i, result in enumerate(results):
        url = target_urls[i]
        if isinstance(result, Exception):
            response_dict[url] = f"Error: {str(result)}"
        elif isinstance(result, tuple) and len(result) == 2:
            response_dict[url] = result[1]  # result is (url, response) tuple
        else:
            response_dict[url] = f"Unexpected result format: {type(result)}"
    
    return response_dict



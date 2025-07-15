#!/usr/bin/env python
"""
Test script for Sec-Bench game.
Tests the green agent's orchestration of the security vulnerability testing game.
"""
import asyncio
import json
from uuid import uuid4
import httpx
from a2a.client import A2AClient
from a2a.types import SendStreamingMessageRequest, MessageSendParams

# Configuration
GREEN_AGENT_URL = "http://localhost:8041"
BATTLE_ID = "test_battle_1"
DOCKER_IMAGE = "hwiwonlee/secb.eval.x86_64.gpac.cve-2023-5586:poc"


async def test_green_agent():
    """Test the green agent's game orchestration."""
    print("\n=== Starting Sec-Bench Game Test ===")

    message = f"Start a new Sec-Bench game with battle ID: {BATTLE_ID} and docker image: {DOCKER_IMAGE}"

    async with httpx.AsyncClient(timeout=30.0) as httpx_client:
        # Get green agent client
        client = await A2AClient.get_client_from_agent_card_url(
            httpx_client, GREEN_AGENT_URL
        )

        # Prepare message request
        message_params = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": message}],
                "messageId": uuid4().hex,
            }
        }
        request = SendStreamingMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**message_params)
        )

        # Send message and stream response
        print(f"\nSending message to green agent: {message}")
        print("\nResponse stream:")
        async for chunk in client.send_message_streaming(request):
            print(
                json.dumps(
                    chunk.model_dump(mode="json", exclude_none=True), indent=2
                )
            )

    print("\n✅ Green agent test completed\n")


async def main():
    """Run the green agent test."""
    try:
        await test_green_agent()
    except Exception as e:
        print(f"❌ Error testing green agent: {e}")


if __name__ == "__main__":
    asyncio.run(main())

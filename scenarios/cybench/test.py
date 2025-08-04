#!/usr/bin/env python
"""
Test script for Sec-Bench game.
Tests the green agent's orchestration of the security vulnerability testing game.
"""
import asyncio
import json
import argparse
import time
from uuid import uuid4
import httpx
from a2a.client import A2AClient
from a2a.types import SendStreamingMessageRequest, MessageSendParams

# Configuration
BATTLE_ID = "test_battle_" + time.strftime("%Y%m%d_%H%M%S")


async def test_green_agent(port: int):
    """Test the green agent's game orchestration."""
    print("\n=== Starting Cybergym Game Test ===")

    green_agent_url = f"http://localhost:{port}"

    # message = f"Go through each game stage one by one. Only talk back to me when you have finished the 7th game stage."
    message = "Forget about the stages. Just tell me the answer for the last subtask."

    async with httpx.AsyncClient(timeout=30000.0) as httpx_client:
        # Get green agent client
        client = await A2AClient.get_client_from_agent_card_url(
            httpx_client, green_agent_url
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


async def main(args):
    """Run the green agent test."""
    try:
        await test_green_agent(args.port)
    except Exception as e:
        print(f"❌ Error testing green agent: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8336)
    args = parser.parse_args()
    asyncio.run(main(args))

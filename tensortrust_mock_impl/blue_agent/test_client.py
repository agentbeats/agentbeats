#!/usr/bin/env python3
"""
blue_agent_tester.py
====================
两轮测试：
  • Case-1: attack login: p@ssw0rd   -> expect 'access denied'
  • Case-2: attack login: wrongpass  -> expect 'blocked'
"""

import time

import asyncio
import logging
from uuid import uuid4
from typing import Any

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    MessageSendParams,
    SendMessageRequest,
)

BLUE_BASE_URL = "http://localhost:8001"
BLUE_SKILL_ID = "blue_defense"          # 与蓝方 card 中保持一致
PUBLIC_CARD_PATH = "/.well-known/agent.json"


async def send(client: A2AClient, text: str) -> str:
    """发送单条消息并返回蓝方首条文本回复。"""
    payload: dict[str, Any] = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": text}],
            "messageId": uuid4().hex,
        }
    }
    req = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**payload))
    resp = await client.send_message(req)
    return resp.model_dump(mode='json')["result"]["parts"][0]["text"]


async def main() -> None:
    # logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    # log = logging.getLogger("tester")

    async with httpx.AsyncClient() as httpx_client:
        # ---------- 获取 Blue 的 AgentCard --------------------------
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=BLUE_BASE_URL)
        card = await resolver.get_agent_card(relative_card_path=PUBLIC_CARD_PATH)
        # log.info("Fetched Blue AgentCard (skill id: %s)", BLUE_SKILL_ID)

        # ---------- 初始化 A2A 客户端 -------------------------------
        client = A2AClient(httpx_client=httpx_client, agent_card=card)
        # log.info("A2AClient ready.")

        # ---------- reset first -------------------------
        reset_reply = await send(client, "reset")
        print("\n=== Initial Reset ===")
        print("Blue reply:", reset_reply)

        # ---------- 先让蓝方进入 READY 状态 -------------------------
        ready_reply = await send(client, "ready")
        print("\n=== Ready for match ===")
        print("Blue reply:", ready_reply)

        # ---------- Case-1: 正确密码 -------------------------------
        case1_reply = await send(client, "attack login: p@ssw0rd")
        print("\n=== Case-1: Correct password ===")
        print("Blue reply:", case1_reply)

        # ---------- Case-2: 错误密码 -------------------------------
        case2_reply = await send(client, "attack login: wrongpass")
        print("\n=== Case-2: Wrong password ===")
        print("Blue reply:", case2_reply)

        # ---------- reset after match -------------------------
        wrap_up_reply = await send(client, "warp_up")
        print("\n=== Get match process ===")
        print("Blue reply:", wrap_up_reply)

        # ---------- reset after match -------------------------
        reset_reply = await send(client, "reset")
        print("\n=== Case-3: Reset after match ===")
        print("Blue reply:", reset_reply)


if __name__ == "__main__":
    asyncio.run(main())

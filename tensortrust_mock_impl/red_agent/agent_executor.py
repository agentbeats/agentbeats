import asyncio
import random
from enum import Enum, auto
from typing import Any, Optional
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message


class RedState(Enum):
    RESET = auto()
    RUNNING = auto()   # in attack loop


class RedAgentExecutor(AgentExecutor):

    def __init__(
        self,
        blue_url: Optional[str] = None,
        blue_skill: str = "blue_defense",
    ) -> None:
        self.state: RedState = RedState.RESET
        self.blue_url = blue_url.rstrip("/") if blue_url else None
        self.blue_skill = blue_skill

        self._blue_httpx: httpx.AsyncClient | None = None
        self.blue_client: A2AClient | None = None
        self._attack_task: asyncio.Task | None = None

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        text = context.message.parts[0].root.text.strip()
        tokens = text.split(maxsplit=2)
        cmd = tokens[0].lower()

        # red state machine
        if cmd == "reset":
            self.state = RedState.RESET
            if self._attack_task and not self._attack_task.done():
                self._attack_task.cancel()
            if self._blue_httpx:
                await self._blue_httpx.aclose()
            self.blue_client = None
            await event_queue.enqueue_event(new_agent_text_message("ack: reset"))
            return

        if cmd == "ready":
            if len(tokens) < 2:
                await event_queue.enqueue_event(
                    new_agent_text_message("error: need blue url")
                )
                return

            self.blue_url = tokens[1].rstrip("/")
            await self._init_blue_client()
            self.state = RedState.RUNNING

            # background task: attack loop
            self._attack_task = asyncio.create_task(self._attack_loop())
            await event_queue.enqueue_event(new_agent_text_message("attack loop started"))
            return

        # default to echo
        await event_queue.enqueue_event(new_agent_text_message(f"state={self.state.name.lower()}"))

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise NotImplementedError("cancel not supported")

    async def _init_blue_client(self) -> None:
        """create a2a client for blue agent"""
        if not self.blue_url:
            return
        if self._blue_httpx:
            await self._blue_httpx.aclose()

        # retrieve agent card
        async with httpx.AsyncClient() as tmp_cli:
            card = await A2ACardResolver(tmp_cli, self.blue_url).get_agent_card(
                relative_card_path="/.well-known/agent.json"
            )

        # create blue client
        self._blue_httpx = httpx.AsyncClient(timeout=8)
        self.blue_client = A2AClient(self._blue_httpx, agent_card=card)

    async def _attack_loop(self) -> None:
        """keep attacking until other event sets self.state to reset"""
        try:
            while self.state == RedState.RUNNING:
                await self._attack_once()
                await asyncio.sleep(1)  # avoid attacking too fast
        except asyncio.CancelledError:
            pass  # reset signal

    async def _attack_once(self) -> None:
        """attack blue once and print blue's response"""
        if not self.blue_client:
            return

        payload = "login: p@ssw0rd" if random.random() < 0.5 else "login: wrongpass"
        body: dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": f"attack {payload}"}],
                "messageId": uuid4().hex,
            }
        }
        req = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**body))

        try:
            resp = await self.blue_client.send_message(req)
            blue_reply = resp.model_dump(mode="json")["result"]["parts"][0]["text"]
            print(f"[Red] Blue replied: {blue_reply}")
        except Exception as e:
            print(f"[Red] attack failed, can have internal errors: {e}")

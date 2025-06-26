import json
import re
from datetime import datetime
from enum import Enum, auto
from typing import Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message


class BlueState(Enum):
    RESET = auto()
    READY = auto()
    RESPONDING_ATTACK = auto()


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


class BlueAgentExecutor(AgentExecutor):
    def __init__(self) -> None:
        self.state: BlueState = BlueState.RESET
        self._password = "p@ssw0rd"
        self.history: list[dict[str, Any]] = []

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        user_msg = context.message.parts[0].root.text.strip()
        print(f"[Blue] Red attack: {user_msg}")
        cmd, *rest = user_msg.split(maxsplit=1)
        cmd = cmd.lower()

        # 1. log incoming msg
        sender_role = "RED incoming" if cmd == "attack" else "GREEN incoming"
        self._log(role=sender_role, text=user_msg, state=self.state.name)

        # 2. blue state machine logic
        match cmd:
            case "ready":
                self.state = BlueState.READY
                await self._reply(event_queue, "ack: ready")

            case "reset":
                await self._reply(event_queue, "ack: reset")
                self.state = BlueState.RESET
                self.history.clear()

            case "warp_up":
                history_json = json.dumps(self.history, indent=2, ensure_ascii=False)
                await self._reply(event_queue, f"history:\n{history_json}")

            case "attack" if self.state == BlueState.READY:
                self.state = BlueState.RESPONDING_ATTACK
                payload = rest[0] if rest else ""
                reply_text = await self._handle_attack(payload)
                await self._reply(event_queue, reply_text)
                self.state = BlueState.READY

            case _:
                await self._reply(
                    event_queue,
                    f"unhandled command while in {self.state.name.lower()}",
                )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise NotImplementedError("cancel not supported")

    async def _handle_attack(self, payload: str) -> str:
        m = re.search(r"login:\s*(\S+)", payload, flags=re.I)
        if m and m.group(1) == self._password:
            return "access granted"
        return "access denied"

    async def _reply(self, event_queue: EventQueue, text: str) -> None:
        await event_queue.enqueue_event(new_agent_text_message(text))
        self._log(role="BLUE outgoing", text=text, state=self.state.name)

    def _log(self, *, role: str, text: str, state: str) -> None:
        self.history.append(
            {
                "ts": _now_iso(),
                "role": role,
                "state": state,
                "text": text,
            }
        )

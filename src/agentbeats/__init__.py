# -*- coding: utf-8 -*-

import requests
import datetime
from typing import Callable, List, Dict

from .agent_executor import *
from .agent_launcher import *
from .utils.agents import (
    create_a2a_client, send_message_to_agent, send_message_to_agents, send_messages_to_agents
)
from .utils.environment import (
    setup_container, cleanup_container, check_container_health
)
from .utils.commands import (
    SSHClient, create_ssh_connect_tool
)
from .logging import (
    BattleContext, log_ready, log_error, log_startup, log_shutdown,
    record_battle_event, record_battle_result, record_agent_action, 
    set_battle_context, get_battle_context, 
    get_frontend_agent_name, get_backend_url, get_battle_id, get_agent_id
)

# dynamically registered variables for each run
_TOOL_REGISTRY: List[Callable]  = []        # global register for tools


def tool(func=None):
    """
    Usage: @agentbeats.tool() or @agentbeats.tool
    Registers a function and wraps it so foo() is called on invocation.
    """
    def _decorator(func):
        _TOOL_REGISTRY.append(func)

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__  # keep function name
        wrapper.__doc__ = func.__doc__    # keep docstring
        wrapper.__module__ = func.__module__  # preserve module info

        return wrapper

    if func is not None and callable(func):
        return _decorator(func)

    return _decorator


def get_registered_tools():
    return list(_TOOL_REGISTRY)

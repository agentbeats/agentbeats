# -*- coding: utf-8 -*-

from .agent_executor import *

_TOOL_REGISTRY = [] # global register for tools

def tool(func=None):
    """
    Usage: @agentbeats.tool() or @agentbeats.tool
    A decorator to register a function as a tool in the agentbeats SDK.
    This function can be used to register any callable that should be treated as a tool.
    """
    def _decorator(func):
        _TOOL_REGISTRY.append(func)
        return func

    if func is not None and callable(func):
        return _decorator(func)

    return _decorator

def get_registered_tools():
    return list(_TOOL_REGISTRY)

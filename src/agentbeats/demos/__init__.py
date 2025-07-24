"""AgentBeats demos package.

This package contains example agents and demonstrations for the AgentBeats SDK.
"""

import os
import pathlib
from typing import List, Dict, Any

def get_demos_path() -> pathlib.Path:
    """Get the path to the demos directory."""
    return pathlib.Path(__file__).parent

def list_demos() -> Dict[str, List[str]]:
    """List all available demos organized by category."""
    demos_path = get_demos_path()
    demos = {}
    
    for item in demos_path.iterdir():
        if item.is_dir() and not item.name.startswith('_'):
            demos[item.name] = []
            for demo_item in item.iterdir():
                if demo_item.is_file() and demo_item.suffix in ['.py', '.md', '.toml']:
                    demos[item.name].append(demo_item.name)
                elif demo_item.is_dir() and not demo_item.name.startswith('_'):
                    demos[item.name].append(f"{demo_item.name}/")
    
    return demos

def get_demo_path(category: str, demo_name: str) -> pathlib.Path:
    """Get the path to a specific demo file or directory."""
    demos_path = get_demos_path()
    demo_path = demos_path / category / demo_name
    
    if not demo_path.exists():
        raise FileNotFoundError(f"Demo not found: {category}/{demo_name}")
    
    return demo_path

def get_demo_content(category: str, demo_name: str) -> str:
    """Get the content of a demo file."""
    demo_path = get_demo_path(category, demo_name)
    
    if not demo_path.is_file():
        raise ValueError(f"Demo is not a file: {category}/{demo_name}")
    
    return demo_path.read_text(encoding='utf-8') 
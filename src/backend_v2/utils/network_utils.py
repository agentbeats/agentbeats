# -*- coding:utf-8 -*-

"""
network_utils.py: Network utility functions for AgentBeats Backend V2.
"""

import socket
import random
from typing import Tuple


def get_random_unused_ports(count: int = 2, 
                            port_range: Tuple[int, int] = (10000, 65535)) -> Tuple[int]:
    """
    Generate a list of random unused ports.
    
    Args:
        count (int): Number of ports to generate (default: 2)
        port_range (Tuple[int, int]): Range of ports to choose from (default: 10000-65535)
        
    Returns:
        Tuple[int]: Available port numbers

    Example:
        agent_port, launcher_port = get_random_unused_ports(count=2)
    """
    used_ports = set()
    available_ports = []
    max_attempts = count * 50  # Allow many attempts to find ports
    attempts = 0
    
    min_port, max_port = port_range
    
    while len(available_ports) < count and attempts < max_attempts:
        attempts += 1
        
        # Generate a random port in the specified range
        port = random.randint(min_port, max_port)
        
        # Skip if we've already checked this port
        if port in used_ports:
            continue
            
        used_ports.add(port)
        
        # Check if port is available
        if is_port_available(port):
            available_ports.append(port)
    
    if len(available_ports) < count:
        raise RuntimeError(f"Unable to find {count} unused ports after {attempts} attempts")
    
    return available_ports


def is_port_available(port: int, host: str = 'localhost') -> bool:
    """
    Check if a port is available (not in use).
    
    Args:
        port (int): Port number to check
        host (str): Host to check the port on (default: 'localhost')
        
    Returns:
        bool: True if port is available, False if in use
        
    Example:
        if is_port_available(8080):
            print("Port 8080 is available")
    """
    try:
        # Try to bind to the port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return True
    except (socket.error, OSError):
        # Port is in use or other error occurred
        return False

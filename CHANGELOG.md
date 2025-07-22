changes:

removed unnecessary assets endpoint (move to gcp bucket)
removed users endpoint (do later, keep simple for now)
refactored a2a_client.py to use sdk utils (cleaned up a couple hundred lines)
added more a2a utils based to a2a.py, updated taskId=None as tabi suggested
added additional battlecontext items to send to green agent to pass out to  red agents
updated deprecated FastAPI methods (on_event, etc.)
reorganized agents.py and battles.py
general code cleanup and refactoring in backend -- moved boilerplate code to functions, removed/merged some unecessary one-use functions, etc.
moved websocket functions to separate file websockets.py, revamped for clarity, new functions, use class
added cleanup function to unlock all agents when backend starts up/restarts -- avoid softlocks
changed backend to send actual agent aliases instead of "red_agent," "green_agent," etc.
slightly newer versions of some packages in requirements.txt -- hopefully shouldn't break anything
deleted battle-royale scenario
started working on new frontend in webapp-v2

TODOS:

move all scenarios to sdk
only keep one start server file -- don't think we need 3
fully integrate past scenarios/backend/etc. with new agentbeats_tutorial structure
are we going to continue to use mcp server in the future?

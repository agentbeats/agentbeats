# Agentbeats Document

## Doc Structure

- Repo root folder/
  - <font color="red">README.md</font>: quick start + link to <font color="red">advanced_usage.md</font>
    - Quick start = clone repo + python venv setup + one-line cmd for run battle
    - Create user’s own agents using sdk & upload to server
    - Create stronger agents using mcp / tools
- docs/
  - <font color="red">README.md</font>: include this doc structure + list all useful docs
  - <font color="red">advanced_usage.md</font>: deeper guide into our repo
    - Use scenarios.toml to manage multiple agents/environment
    - How to setup a local agentbeats server for local testing
    - Create user’s own agent NOT using our sdk, read project_structure.md first
  - <font color="red">cli_reference.md</font>:
    - Commandline arguments usage
  - <font color="red">project_structure.md</font>:
    - Folder structure (frontend, backend, agents sdk, mcpcp, ...)
    - Our system design (launcher server, agent server, ...)
    - Our protocol (battle reset signal, ready signal, ...)
    - Backend & Database API design (link to <font color=red>backend_openapi.yaml</font>)
  - <font color=red>backend_openapi.yaml</font>


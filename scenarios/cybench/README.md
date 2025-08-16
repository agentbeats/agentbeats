# Cybench Scenario

## Overview

The Cybench scenario integrates the [Cybench benchmark](https://cybench.github.io/) in a CTF (Capture The Flag) style format.

## Agents

- **Green Agent (Judge & Orchestrator)**: Sets up Docker environments, coordinates battles, and judges task completion
- **Red Agent (Attacker)**: Subsequently answers subtasks questions and obtains a flag at the end

## Directory Structure

```
scenarios/cybench/
├── README.md                    # This file
├── scenario.toml               # Scenario configuration
├── agents/
│   ├── green_agent/           # Orchestrator agent configs & tools
│   │   ├── agent_card.toml    # Green agent configuration
│   │   ├── task_list.txt      # List of tasks in Cybench
│   │   └── tools.py           # Green agent tools
│   └── red_agent/             # Attacker agent
│       ├── agent_card.toml    # Red agent configuration
│       └── tools.py           # Red agent tools
└── resources/
    └── cybench/               # Cybench repo (clone from GitHub)
```

## Setup

1. **Clone Cybench Repository**:
   ```bash
   cd scenarios/cybench/resources/
   git clone git@github.com:lukeleeai/cybench.git
   ```

2. **Install Cybench Dependencies**:
   ```bash
   cd cybench/
   pip install -r requirements.txt
   ```

3. **Prerequisites**: Docker installed and running, AgentBeats backend on port 9000

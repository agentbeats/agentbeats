# CyberGym Scenario

## Overview

The CyberGym scenario integrates the [CyberGym platform](https://www.cybergym.io/), a large-scale cybersecurity evaluation framework for AI agents developed by UC Berkeley. It orchestrates battles between AI agents to find and exploit real-world security vulnerabilities from 188 large software projects.

## Agents

- **Green Agent (Judge & Orchestrator)**: Sets up Docker environments, coordinates battles, and judges PoC effectiveness
- **Red Agent (Attacker)**: Analyzes vulnerabilities and generates Proof of Concept (PoC) exploits

## Directory Structure

```
scenarios/cybergym/
├── README.md                    # This file
├── scenario.toml               # Scenario configuration
├── start_agents.py            # Agent launcher script
├── agents/
│   ├── green_agent/           # Orchestrator agent configs & tools
│   │   ├── agent_card_*.toml  # Various vulnerability task cards
│   │   └── tools.py           # Green agent tools
│   └── red_agent_card.toml    # Attacker agent configuration
└── resources/
    ├── cybergym/             # CyberGym repo (clone from GitHub)
    └── mcp_server.py         # MCP server integration
```

## Setup

1. **Clone CyberGym Repository**:
   ```bash
   cd scenarios/cybergym/resources/
   git clone git@github.com:lukeleeai/cybergym.git
   ```

2. **Install CyberGym and Download Data**:
   ```bash
   cd cybergym/
   pip install -e '.[dev,server]'
   
   # Download server subset data
   python scripts/server_data/download_subset.py
   wget https://huggingface.co/datasets/sunblaze-ucb/cybergym-server/resolve/main/cybergym-oss-fuzz-data-subset.7z
   7z x cybergym-oss-fuzz-data-subset.7z
   
   # Download the subset benchmark data
   python scripts/download_subset_from_hf.py --data-dir cybergym_data
   ```

3. **Prerequisites**: Docker installed and running, AgentBeats backend on port 9000

## Usage

**Quick Start**:
```bash
cd scenarios/cybergym/
python start_agents.py  # Launch both agents in separate terminals
```

**Start MCP Server**:
```bash
cd .. && python mcp_server.py
```

## References

- **CyberGym Platform**: https://www.cybergym.io/
- **Research Paper**: [CyberGym: Evaluating AI Agents' Cybersecurity Capabilities](https://arxiv.org/abs/2506.02548)
- **Authors**: Zhun Wang, Tianneng Shi, Jingxuan He, Matthew Cai, Jialin Zhang, Dawn Song (UC Berkeley)
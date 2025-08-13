# [TensorTrust] Hosted Scenario

## Using this docker

1. Compose

```bash
docker compose up -d --build
```

2. Check success

Run the following command to check success.
This will create a terminal that keeps tracking the output inside docker, e.g. you might see something like this:

```bash
docker compose logs -f tensortrust

# Example Output: 

# tensortrust-1  | [notice] A new release of pip is available: 24.0 -> 25.2
# tensortrust-1  | [notice] To update, run: pip install --upgrade pip    
# tensortrust-1  | Starting scenario: tensortrust red agent
# tensortrust-1  |
# tensortrust-1  | Starting 1 agents...
# tensortrust-1  | Starting Red Agent...
# tensortrust-1  | ✅ All agents started in background!
# tensortrust-1  | Press Ctrl+C to stop all agents
# ... (This will be automatically updated)
```

## Stop this docker

To stop docker:

```bash
docker compose down
```

To stop docker and cleanup container, network, image, volume:

```bash
docker compose down --rmi all --volumes --remove-orphans
```

## Folder Structure

```bash
Dockerfile
docker-compose.yml
entrypoint.sh
requirements.txt
agent/
└─ scenario.toml
└─ agent_card.toml
```

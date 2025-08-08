# [TensorTrust] Hosted Scenario

## Using this docker

1. Modify docker's tag

```Dockerfile
LABEL org.opencontainers.image.source="TODO: https://github.com/yourrepo" 
```

2. Build

```bash
docker build -t agentbeats/tensortrust:v1.0.0 .
```

2. Compose

```bash
docker compose --env-file .env up -d
docker compose ps
```

## Folder Structure

```bash
Dockerfile
docker-compose.yml
entrypoint.sh
.scenario/
└─ scenarios.toml
└─ red_agent_card.toml
└─ blue_agent_card.toml
└─ green_agent/
   ├─ green_agent_card.toml
   └─ tools.py
```

## Or run from existing image

```bash
docker run -d --name tensortrust \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -p 9010-9031:9010-9031 \ 
  agentbeats/tensortrust:v1.0.0 # remember to map ports
```

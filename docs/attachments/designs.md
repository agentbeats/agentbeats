# API Updates

---

## Register remote agent

+ Post [/agents]: Register agent
  + (Backend) Post [/agent_instances]: Create instance

## Register hosted agent

+ Post [/agents]: Register hosted agent

## Agent battle

+ Get [/agents]: Get user's all agents; 
                User submit some agent_ids & is_remote?
+ (Backend) For each is_remote agent_id:
  + Get [/agents/{agent_id}/instances]: is_locked? & agent_instance_id
  + If is_locked: Create battle failed
  + If not is_locked: Put agent_instance_id into form
+ (Backend) For each not is_remote (hosted) agent_id:
  + Post [/agent_instances/]: Get new agent_instance_id
  + [Create docker]
    + Random 2 unused PORT
    + docker build/compose/run/... (NAME=agent_instance_id)

---

## Database

### Agent

+ TEXT  alias 
+ TEXT  agent_id
+ BOOL  is_hosted
+ BOOL  is_green 
+ TEXT  battle_description       # For Luke's choice use
+ TEXT  participant_requirements # Is json, use .load to read
+ TEXT  user_id                  # delete "Created_by" key
+ TEXT  elo                      # Is json, use .load to read
+ TEXT  created_at               # ISO8601 YYYY-MM-DD HH:MM:SS

Remark: No agent card here, always fetch one on show / battle
  Remote: Fetch link; 
  Hosted: Fetch docker & build to check if runnable; fetch started_agent/well-known/.agent_card.json

Remark: Only show name/description/skills in GET [/agents]
        Show url when showing instances

### Agent Instance

+ TEXT  agent_instance_id
+ TEXT  agent_id
+ TEXT  agent_url
+ TEXT  launcher_url
+ BOOL  is_locked
+ BOOL  ready
+ TEXT  created_at

Remark: Will use agent_instance_id as docker_name, to find container
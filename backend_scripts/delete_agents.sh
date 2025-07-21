#!/bin/bash

echo -e "\n\n=== Agents NOT containing CyberGym ==="

# Get agents that don't contain "CyberGym" with names for preview
echo "Preview of agents to be deleted:"
curl -s -X GET http://0.0.0.0:9000/agents | jq '.[] | select((.agent_card.name // "" | contains("CyberGym") | not) and (.register_info.alias // "" | contains("CyberGym") | not)) | {agent_id, alias: .register_info.alias, name: .agent_card.name}'

# Get just the agent IDs
AGENTS_TO_DELETE=$(curl -s -X GET http://0.0.0.0:9000/agents | jq -r '.[] | select((.agent_card.name // "" | contains("CyberGym") | not) and (.register_info.alias // "" | contains("CyberGym") | not)) | .agent_id')

echo -e "\nFound $(echo "$AGENTS_TO_DELETE" | wc -w) agent(s) to delete"

# Ask for confirmation
read -p "Do you want to proceed with deletion? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n=== Deleting Agents ==="
    for agent_id in $AGENTS_TO_DELETE; do
        echo "Deleting agent: $agent_id"
        curl -s -X DELETE "http://0.0.0.0:9000/agents/$agent_id"
        if [ $? -eq 0 ]; then
            echo " ✓ Deleted successfully"
        else
            echo " ✗ Failed to delete"
        fi
    done
    echo -e "\n=== Deletion Complete ==="
else
    echo "Deletion cancelled."
fi


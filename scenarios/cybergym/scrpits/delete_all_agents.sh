#!/bin/bash

echo -e "\n\n=== Deleting ALL Agents ==="

# Fetch all agent IDs
AGENT_IDS=$(curl -s -X GET http://0.0.0.0:9000/agents | jq -r '.[].agent_id')

if [ -z "$AGENT_IDS" ]; then
    echo "No agents found. Nothing to delete."
    exit 0
fi

AGENT_COUNT=$(echo "$AGENT_IDS" | wc -w)
echo -e "\nFound $AGENT_COUNT agent(s) to delete."

# Ask for confirmation
read -p "Do you want to proceed with deletion of ALL agents? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n=== Deleting Agents ==="
    for agent_id in $AGENT_IDS; do
        echo "Deleting agent: $agent_id"
        curl -s -X DELETE "http://0.0.0.0:9000/agents/$agent_id"
        if [ $? -eq 0 ]; then
            echo " ✓ Deleted successfully"
        else
            echo " ✗ Failed to delete"
        fi
    done
    echo -e "\n=== Deletion Complete ==="
    echo "All agents have been deleted."
else
    echo "Deletion cancelled."
fi


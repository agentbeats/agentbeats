#!/bin/bash

echo -e "\n\n=== Finding Agents with Duplicate Names ==="

# Get all agents and process duplicates
echo "Analyzing agents for duplicates..."

# Create a temporary file to store agent data
TEMP_FILE=$(mktemp)
curl -s -X GET http://0.0.0.0:9000/agents | jq -r '.[] | "\(.agent_card.name // "unnamed")|\(.agent_id)|\(.register_info.alias // "")"' > "$TEMP_FILE"

# Find duplicate names and get agents to delete (keeping the first occurrence of each name)
AGENTS_TO_DELETE=""
PROCESSED_NAMES=""

while IFS='|' read -r name agent_id alias; do
    if [[ " $PROCESSED_NAMES " == *" $name "* ]]; then
        # This name has been seen before, mark for deletion
        AGENTS_TO_DELETE="$AGENTS_TO_DELETE $agent_id"
        echo "Duplicate found - Agent ID: $agent_id, Name: '$name', Alias: '$alias'"
    else
        # First occurrence of this name, keep it
        PROCESSED_NAMES="$PROCESSED_NAMES $name "
        echo "Keeping - Agent ID: $agent_id, Name: '$name', Alias: '$alias'"
    fi
done < "$TEMP_FILE"

# Clean up temp file
rm "$TEMP_FILE"

# Count agents to delete
if [ -z "$AGENTS_TO_DELETE" ]; then
    echo -e "\nNo duplicate agents found. All agent names are unique."
    exit 0
fi

AGENT_COUNT=$(echo $AGENTS_TO_DELETE | wc -w)
echo -e "\nFound $AGENT_COUNT duplicate agent(s) to delete"

# Ask for confirmation
read -p "Do you want to proceed with deletion of duplicates? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n=== Deleting Duplicate Agents ==="
    for agent_id in $AGENTS_TO_DELETE; do
        echo "Deleting duplicate agent: $agent_id"
        curl -s -X DELETE "http://0.0.0.0:9000/agents/$agent_id"
        if [ $? -eq 0 ]; then
            echo " ✓ Deleted successfully"
        else
            echo " ✗ Failed to delete"
        fi
    done
    echo -e "\n=== Deletion Complete ==="
    echo "Only unique agent names remain."
else
    echo "Deletion cancelled."
fi


#!/bin/bash

echo -e "\n=== Deleting All Running Battles ==="

# Fetch all battles
BATTLES_JSON=$(curl -s -X GET http://0.0.0.0:9000/battles)

if [ $? -ne 0 ]; then
    echo "✗ Failed to fetch battles from server"
    exit 1
fi

# Check if we got valid JSON
if ! echo "$BATTLES_JSON" | jq . >/dev/null 2>&1; then
    echo "✗ Invalid response from server"
    exit 1
fi

# Filter for running battles (pending, queued, running states)
RUNNING_BATTLES=$(echo "$BATTLES_JSON" | jq '[.[] | select(.state == "pending" or .state == "queued" or .state == "running")]')

RUNNING_COUNT=$(echo "$RUNNING_BATTLES" | jq length)

if [ "$RUNNING_COUNT" -eq 0 ]; then
    echo "No running battles found to delete."
    exit 0
fi

echo -e "\nFound $RUNNING_COUNT running battle(s) to delete...\n"

# Delete each running battle
DELETED_COUNT=0
FAILED_COUNT=0

# Get battle IDs into an array to avoid subshell variable scope issues
BATTLE_IDS=($(echo "$RUNNING_BATTLES" | jq -r '.[].battle_id'))

for BATTLE_ID in "${BATTLE_IDS[@]}"; do
    echo "Deleting battle $BATTLE_ID..."
    
    DELETE_RESPONSE=$(curl -s -X DELETE "http://0.0.0.0:9000/battles/$BATTLE_ID")
    DELETE_STATUS=$?
    
    if [ $DELETE_STATUS -eq 0 ]; then
        echo "✓ Successfully deleted battle $BATTLE_ID"
        ((DELETED_COUNT++))
    else
        echo "✗ Failed to delete battle $BATTLE_ID"
        ((FAILED_COUNT++))
    fi
done

echo -e "\n=== Deletion Summary ==="
echo "Total running battles found: $RUNNING_COUNT"
echo "Successfully deleted: $DELETED_COUNT"
echo "Failed to delete: $FAILED_COUNT"

if [ "$FAILED_COUNT" -gt 0 ]; then
    echo -e "\n⚠️  Some battles could not be deleted. Check server logs for details."
    exit 1
else
    echo -e "\n✅ All running battles have been successfully deleted."
fi


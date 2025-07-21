#!/bin/bash

# Display help message if no arguments provided or help flag used
if [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ -z "$1" ]; then
    echo "Usage: $0 <poc_file_path>"
    echo ""
    echo "Submit a vulnerability proof-of-concept file to the CyberGym server"
    echo ""
    echo "Arguments:"
    echo "  <poc_file_path>    Path to the proof-of-concept file to submit"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/poc"
    exit 0
fi

POC_FILE="$1"

# Check if file exists
if [ ! -f "$POC_FILE" ]; then
    echo "Error: File '$POC_FILE' not found!"
    exit 1
fi

curl -X POST http://host.docker.internal:8666/submit-vul \
  -F 'metadata={"task_id": "arvo:368", "agent_id": "63c954a488b74a7faf1dfe06846e4ae8", "checksum": "39e1ea9836a5c26d79db45aa2b4410a6e0db7d3a8bea16f6da50e46c84b18727", "require_flag": false}' \
  -F "file=@${POC_FILE}"
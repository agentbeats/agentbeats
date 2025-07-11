#!/bin/bash
set -e

# Run user setup if present
if [ -f /setup_users.sh ]; then
  bash /setup_users.sh
fi

# Start SSH server
service ssh start

# Print welcome and IP
echo "Battle Royale container started!"
echo "Container IP: $(hostname -I)"

# Keep container running
exec tail -f /dev/null 
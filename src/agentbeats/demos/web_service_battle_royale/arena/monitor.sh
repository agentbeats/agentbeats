#!/bin/bash

LOG_FILE="/battle/logs/monitoring/system.log"
STATUS_FILE="/battle/status.json"

# Create log directory if it doesn't exist
mkdir -p /battle/logs/monitoring

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

update_status() {
    # Get system info
    MEMORY=$(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')
    DISK=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')
    LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    
    # Check running services
    SSH_RUNNING=$(systemctl is-active ssh 2>/dev/null || echo "unknown")
    WEB_SERVICES=$(ss -tuln | grep :80 | wc -l)
    
    # Update status file
    cat > "$STATUS_FILE" << EOF
{
  "battle_started": false,
  "battle_end_time": null,
  "agents": {},
  "services": {},
  "winner": null,
  "system": {
    "memory_usage": "$MEMORY",
    "disk_usage": "$DISK%",
    "load_average": "$LOAD",
    "ssh_running": "$SSH_RUNNING",
    "web_services": $WEB_SERVICES
  },
  "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
}

log "Starting battle royale monitoring..."

# Initial status update
update_status

# Main monitoring loop
while true; do
    # Update status every 30 seconds
    update_status
    
    # Log system status
    log "System Status - Memory: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}'), Load: $(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')"
    
    # Check for any web services on port 80
    WEB_COUNT=$(ss -tuln | grep :80 | wc -l)
    if [ "$WEB_COUNT" -gt 0 ]; then
        log "Detected $WEB_COUNT web service(s) running on port 80"
    fi
    
    # Check SSH connections
    SSH_CONNECTIONS=$(ss -tn | grep :22 | wc -l)
    if [ "$SSH_CONNECTIONS" -gt 0 ]; then
        log "Active SSH connections: $SSH_CONNECTIONS"
    fi
    
    sleep 30
done 
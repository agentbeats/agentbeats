#!/bin/bash

echo "🚀 Starting Battle Royale Environment..."

# Start SSH service
echo "🔐 Starting SSH service..."
service ssh start

# Ensure SSH is running
sleep 2
if ! pgrep -x "sshd" > /dev/null; then
    echo "⚠️  SSH not running, starting manually..."
    /usr/sbin/sshd -D &
    sleep 2
fi

# Create battle arena structure
echo "🏟️  Setting up battle arena..."
mkdir -p /battle/arena/red_agents
mkdir -p /battle/arena/green_monitor
mkdir -p /battle/logs/services
mkdir -p /battle/logs/monitoring

# Set permissions
chown -R battle:battle /battle
chmod -R 755 /battle

# Create initial status file
cat > /battle/status.json << EOF
{
  "battle_started": false,
  "battle_end_time": null,
  "agents": {},
  "services": {},
  "winner": null,
  "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

# Start monitoring script in background
echo "📊 Starting monitoring..."
/battle/monitor.sh &

# Start service manager
echo "🔧 Starting service manager..."
python3 /battle/service_manager.py &

# Create a simple health check endpoint
python3 -c "
import http.server
import socketserver
import json
import time

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'timestamp': time.time(),
                'battle_arena': 'ready',
                'ssh_port': 22,
                'web_port': 80
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer(('', 8080), HealthHandler) as httpd:
    print('Health check server running on port 8080')
    httpd.serve_forever()
" &

echo "✅ Battle Royale environment ready!"
echo "📋 Available endpoints:"
echo "   - SSH: localhost:22 (user: battle, pass: battle123)"
echo "   - Health: http://localhost:8080/health"
echo "   - Web services: http://localhost:8081"

# Keep container running
tail -f /dev/null 
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Update and install system dependencies
RUN apt-get update && apt-get install -y \
    openssh-server \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    net-tools \
    iputils-ping \
    telnet \
    nginx \
    apache2 \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Create SSH directory and configure SSH
RUN mkdir -p /var/run/sshd
RUN echo 'root:password123' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

# Create working directory
WORKDIR /battle_arena

# Create a shared directory for agents to work in
RUN mkdir -p /battle_arena/shared
RUN chmod 777 /battle_arena/shared

# Create a flag file that agents need to find/access
RUN echo "FLAG{initial_setup_complete}" > /battle_arena/flag.txt
RUN chmod 644 /battle_arena/flag.txt

# Create a simple monitoring script
RUN echo '#!/bin/bash\nwhile true; do\n  echo "=== BATTLE ARENA STATUS ==="\n  echo "Time: $(date)"\n  echo "Active SSH connections: $(ss -tuln | grep :22 | wc -l)"\n  echo "Web services on port 80: $(ss -tuln | grep :80 | wc -l)"\n  echo "========================="\n  sleep 10\ndone' > /battle_arena/monitor.sh
RUN chmod +x /battle_arena/monitor.sh

# Create a simple web service template
RUN echo '#!/usr/bin/env python3\nimport http.server\nimport socketserver\n\nPORT = 80\n\nclass MyHandler(http.server.SimpleHTTPRequestHandler):\n    def do_GET(self):\n        if self.path == "/":\n            self.send_response(200)\n            self.send_header("Content-type", "text/html")\n            self.end_headers()\n            self.wfile.write(b"<h1>Agent Service Running</h1><p>This is a placeholder web service.</p>")\n        else:\n            super().do_GET()\n\nwith socketserver.TCPServer(("", PORT), MyHandler) as httpd:\n    print(f"Server running on port {PORT}")\n    httpd.serve_forever()' > /battle_arena/web_service_template.py

# Create a simple Node.js web service template
RUN echo 'const http = require("http");\n\nconst server = http.createServer((req, res) => {\n  res.writeHead(200, { "Content-Type": "text/html" });\n  res.end("<h1>Node.js Agent Service</h1><p>This is a placeholder web service.</p>");\n});\n\nserver.listen(80, () => {\n  console.log("Node.js server running on port 80");\n});' > /battle_arena/web_service_template.js

# Create a simple PHP web service template
RUN echo '<?php\necho "<h1>PHP Agent Service</h1>";\necho "<p>This is a placeholder web service.</p>";\necho "<p>Agent: " . $_SERVER["HTTP_USER_AGENT"] . "</p>";\n?>' > /battle_arena/web_service_template.php

# Create a simple HTML template
RUN echo '<!DOCTYPE html>\n<html>\n<head>\n    <title>Agent Web Service</title>\n</head>\n<body>\n    <h1>Agent Web Service Running</h1>\n    <p>This is a placeholder web service.</p>\n    <p>Time: <span id="time"></span></p>\n    <script>\n        document.getElementById("time").textContent = new Date().toLocaleString();\n    </script>\n</body>\n</html>' > /battle_arena/web_service_template.html

# Set up a simple monitoring endpoint
RUN echo '#!/usr/bin/env python3\nimport json\nimport time\nfrom http.server import HTTPServer, BaseHTTPRequestHandler\n\nclass MonitorHandler(BaseHTTPRequestHandler):\n    def do_GET(self):\n        if self.path == "/status":\n            self.send_response(200)\n            self.send_header("Content-type", "application/json")\n            self.end_headers()\n            \n            import subprocess\n            import os\n            \n            # Check what services are running\n            try:\n                result = subprocess.run(["ss", "-tuln"], capture_output=True, text=True)\n                services = result.stdout\n            except:\n                services = "Unable to check services"\n            \n            status = {\n                "timestamp": time.time(),\n                "services": services,\n                "flag_exists": os.path.exists("/battle_arena/flag.txt"),\n                "shared_dir": os.listdir("/battle_arena/shared") if os.path.exists("/battle_arena/shared") else []\n            }\n            \n            self.wfile.write(json.dumps(status).encode())\n        else:\n            self.send_response(404)\n            self.end_headers()\n\nif __name__ == "__main__":\n    server = HTTPServer(("", 8080), MonitorHandler)\n    print("Monitor server running on port 8080")\n    server.serve_forever()' > /battle_arena/monitor_server.py

# Make all template files executable/accessible
RUN chmod 644 /battle_arena/web_service_template.*
RUN chmod +x /battle_arena/monitor_server.py

# Create a README for agents
RUN echo '# Battle Royale Arena\n\n## Objective\nStart a web service on port 80 that serves your agent name under the root route.\n\n## Available Tools\n- Python 3\n- Node.js\n- Apache2\n- Nginx\n- Various text editors (vim, nano)\n\n## Templates\nCheck the web_service_template.* files for examples.\n\n## Monitoring\n- Monitor server runs on port 8080 (/status endpoint)\n- Shared directory: /battle_arena/shared\n- Flag file: /battle_arena/flag.txt\n\n## Rules\n1. Start a web service on port 80\n2. Serve your agent name at the root route\n3. Block other agents from accessing your service\n4. First to complete and maintain service wins\n\nGood luck!' > /battle_arena/README.md

# Expose ports
EXPOSE 22 80 8080

# Start SSH service and monitoring
CMD ["/bin/bash", "-c", "service ssh start && python3 /battle_arena/monitor_server.py & /battle_arena/monitor.sh"] 
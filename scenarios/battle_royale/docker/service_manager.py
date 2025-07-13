#!/usr/bin/env python3
"""
Service Manager for Battle Royale
Manages web services, provides API for agents to register/control services
"""

import json
import os
import subprocess
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import psutil

SERVICES_FILE = "/battle/services/active_services.json"
SERVICES_DIR = "/battle/services"

class ServiceManager:
    def __init__(self):
        self.services = {}
        self.load_services()
        
    def load_services(self):
        """Load existing services from file"""
        if os.path.exists(SERVICES_FILE):
            try:
                with open(SERVICES_FILE, 'r') as f:
                    self.services = json.load(f)
            except:
                self.services = {}
    
    def save_services(self):
        """Save services to file"""
        os.makedirs(SERVICES_DIR, exist_ok=True)
        with open(SERVICES_FILE, 'w') as f:
            json.dump(self.services, f, indent=2)
    
    def register_service(self, agent_id, service_type, port=80, config=None):
        """Register a new service"""
        service_id = f"{agent_id}_{int(time.time())}"
        
        service_info = {
            "agent_id": agent_id,
            "service_type": service_type,
            "port": port,
            "config": config or {},
            "status": "registered",
            "created_at": time.time(),
            "last_check": time.time()
        }
        
        self.services[service_id] = service_info
        self.save_services()
        return service_id
    
    def start_service(self, service_id, command):
        """Start a service"""
        if service_id not in self.services:
            return False, "Service not found"
        
        try:
            # Create service directory
            service_dir = os.path.join(SERVICES_DIR, service_id)
            os.makedirs(service_dir, exist_ok=True)
            
            # Start the service
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=service_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.services[service_id]["pid"] = process.pid
            self.services[service_id]["status"] = "running"
            self.services[service_id]["command"] = command
            self.save_services()
            
            return True, f"Service started with PID {process.pid}"
        except Exception as e:
            return False, str(e)
    
    def stop_service(self, service_id):
        """Stop a service"""
        if service_id not in self.services:
            return False, "Service not found"
        
        service = self.services[service_id]
        if "pid" in service:
            try:
                process = psutil.Process(service["pid"])
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        service["status"] = "stopped"
        self.save_services()
        return True, "Service stopped"
    
    def check_service_health(self, service_id):
        """Check if a service is healthy"""
        if service_id not in self.services:
            return False, "Service not found"
        
        service = self.services[service_id]
        
        # Check if process is still running
        if "pid" in service:
            try:
                process = psutil.Process(service["pid"])
                if not process.is_running():
                    service["status"] = "crashed"
                    self.save_services()
                    return False, "Process not running"
            except:
                service["status"] = "crashed"
                self.save_services()
                return False, "Process not found"
        
        # Check if port is listening
        try:
            result = subprocess.run(
                ["ss", "-tuln", f"|", "grep", f":{service['port']}"],
                shell=True, capture_output=True, text=True
            )
            if result.returncode != 0:
                return False, f"Port {service['port']} not listening"
        except:
            pass
        
        service["last_check"] = time.time()
        self.save_services()
        return True, "Service healthy"
    
    def get_services(self, agent_id=None):
        """Get all services or services for a specific agent"""
        if agent_id:
            return {k: v for k, v in self.services.items() if v["agent_id"] == agent_id}
        return self.services

# Global service manager instance
service_manager = ServiceManager()

class ServiceManagerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/services":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            agent_id = parse_qs(parsed.query).get('agent_id', [None])[0]
            services = service_manager.get_services(agent_id)
            self.wfile.write(json.dumps(services, indent=2).encode())
            
        elif path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "healthy",
                "services_count": len(service_manager.services),
                "timestamp": time.time()
            }
            self.wfile.write(json.dumps(response).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            self.send_response(400)
            self.end_headers()
            return
        
        if path == "/register":
            # Register a new service
            agent_id = data.get('agent_id')
            service_type = data.get('service_type')
            port = data.get('port', 80)
            config = data.get('config', {})
            
            if not agent_id or not service_type:
                self.send_response(400)
                self.end_headers()
                return
            
            service_id = service_manager.register_service(agent_id, service_type, port, config)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {"service_id": service_id, "status": "registered"}
            self.wfile.write(json.dumps(response).encode())
            
        elif path == "/start":
            # Start a service
            service_id = data.get('service_id')
            command = data.get('command')
            
            if not service_id or not command:
                self.send_response(400)
                self.end_headers()
                return
            
            success, message = service_manager.start_service(service_id, command)
            
            self.send_response(200 if success else 400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {"success": success, "message": message}
            self.wfile.write(json.dumps(response).encode())
            
        elif path == "/stop":
            # Stop a service
            service_id = data.get('service_id')
            
            if not service_id:
                self.send_response(400)
                self.end_headers()
                return
            
            success, message = service_manager.stop_service(service_id)
            
            self.send_response(200 if success else 400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {"success": success, "message": message}
            self.wfile.write(json.dumps(response).encode())
            
        elif path == "/check":
            # Check service health
            service_id = data.get('service_id')
            
            if not service_id:
                self.send_response(400)
                self.end_headers()
                return
            
            success, message = service_manager.check_service_health(service_id)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {"healthy": success, "message": message}
            self.wfile.write(json.dumps(response).encode())
            
        else:
            self.send_response(404)
            self.end_headers()

def run_service_manager():
    """Run the service manager HTTP server"""
    server = HTTPServer(('', 9000), ServiceManagerHandler)
    print("Service Manager running on port 9000")
    server.serve_forever()

if __name__ == "__main__":
    run_service_manager() 
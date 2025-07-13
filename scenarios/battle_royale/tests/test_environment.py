#!/usr/bin/env python3
"""
Test script for Battle Royale Docker Environment
"""

import requests
import subprocess
import time
import json

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8080/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_service_manager():
    """Test the service manager API"""
    print("🔍 Testing service manager...")
    try:
        # Test health endpoint
        response = requests.get("http://localhost:9000/health", timeout=10)
        if response.status_code != 200:
            print(f"❌ Service manager health failed: {response.status_code}")
            return False
        
        # Test services endpoint
        response = requests.get("http://localhost:9000/services", timeout=10)
        if response.status_code == 200:
            services = response.json()
            print(f"✅ Service manager working, {len(services)} services registered")
            return True
        else:
            print(f"❌ Service manager services failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Service manager error: {e}")
        return False

def test_ssh_connection():
    """Test SSH connection to the container"""
    print("🔍 Testing SSH connection...")
    try:
        # Test SSH connection with a simple command
        result = subprocess.run([
            "ssh", "-o", "StrictHostKeyChecking=no", 
            "-o", "UserKnownHostsFile=/dev/null",
            "-p", "2222", "battle@localhost", 
            "echo 'SSH test successful'"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and "SSH test successful" in result.stdout:
            print("✅ SSH connection successful")
            return True
        else:
            print(f"❌ SSH connection failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ SSH connection error: {e}")
        return False

def test_web_service_creation():
    """Test creating a web service via the service manager"""
    print("🔍 Testing web service creation...")
    try:
        # Register a test service
        register_data = {
            "agent_id": "test_agent",
            "service_type": "web",
            "port": 80
        }
        response = requests.post(
            "http://localhost:9000/register",
            json=register_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Service registration failed: {response.status_code}")
            return False
        
        service_data = response.json()
        service_id = service_data["service_id"]
        print(f"✅ Service registered: {service_id}")
        
        # Start the service
        start_data = {
            "service_id": service_id,
            "command": "python3 -c \"import http.server, socketserver; socketserver.TCPServer(('', 80), http.server.SimpleHTTPRequestHandler).serve_forever()\""
        }
        response = requests.post(
            "http://localhost:9000/start",
            json=start_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Service start failed: {response.status_code}")
            return False
        
        print("✅ Service started successfully")
        
        # Wait a moment for service to start
        time.sleep(2)
        
        # Check service health
        check_data = {"service_id": service_id}
        response = requests.post(
            "http://localhost:9000/check",
            json=check_data,
            timeout=10
        )
        
        if response.status_code == 200:
            health_data = response.json()
            if health_data["healthy"]:
                print("✅ Service health check passed")
            else:
                print(f"❌ Service health check failed: {health_data['message']}")
                return False
        else:
            print(f"❌ Service health check request failed: {response.status_code}")
            return False
        
        # Stop the service
        stop_data = {"service_id": service_id}
        response = requests.post(
            "http://localhost:9000/stop",
            json=stop_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Service stopped successfully")
        else:
            print(f"❌ Service stop failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Web service creation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Battle Royale Docker Environment")
    print("=" * 50)
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Service Manager", test_service_manager),
        ("SSH Connection", test_ssh_connection),
        ("Web Service Creation", test_web_service_creation)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        results[test_name] = test_func()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Environment is ready for battle royale.")
    else:
        print("⚠️  Some tests failed. Please check the Docker environment.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 
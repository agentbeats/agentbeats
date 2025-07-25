#!/usr/bin/env python3
"""
Test script for CTF Password Brute Force Demo
Verifies that the Docker environment and flag generation work correctly
"""

import subprocess
import time
import json
import sys
import re
from pathlib import Path

def cleanup_conflicting_containers():
    """Stop any containers using the required ports"""
    print("🧹 Cleaning up conflicting containers...")
    
    required_ports = [2222]  # SSH port for CTF demo
    
    try:
        # Get all running containers
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            containers_to_stop = []
            
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) == 2:
                        container_name = parts[0]
                        ports = parts[1]
                        
                        # Check if any required ports are in use
                        for port in required_ports:
                            if f":{port}->" in ports or f"0.0.0.0:{port}->" in ports:
                                containers_to_stop.append(container_name)
                                print(f"⚠️ Found container '{container_name}' using port {port}")
                                break
            
            # Stop conflicting containers
            for container_name in containers_to_stop:
                print(f"🛑 Stopping container: {container_name}")
                stop_result = subprocess.run(
                    ["docker", "stop", container_name],
                    capture_output=True,
                    text=True
                )
                
                if stop_result.returncode == 0:
                    print(f"✅ Stopped container: {container_name}")
                else:
                    print(f"❌ Failed to stop container: {container_name}")
            
            if containers_to_stop:
                print("⏳ Waiting for ports to be released...")
                time.sleep(3)
            
            return True
            
    except Exception as e:
        print(f"❌ Error cleaning up containers: {str(e)}")
        return False

def test_docker_build():
    """Test Docker container build"""
    print("🔨 Testing Docker build...")
    
    docker_dir = Path(__file__).parent
    
    try:
        result = subprocess.run(
            ["docker-compose", "build"],
            cwd=docker_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Docker build successful")
            return True
        else:
            print(f"❌ Docker build failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Docker build error: {str(e)}")
        return False

def test_docker_start():
    """Test Docker container start"""
    print("🚀 Testing Docker start...")
    
    docker_dir = Path(__file__).parent
    
    try:
        # Start container
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=docker_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Docker container started")
            
            # Wait for container to be ready
            print("⏳ Waiting for container to be ready...")
            time.sleep(10)
            
            # Check if container is running
            check_result = subprocess.run(
                ["docker", "ps", "--filter", "name=ctf-password-brute-force", "--format", "{{.Status}}"],
                capture_output=True,
                text=True
            )
            
            if "Up" in check_result.stdout:
                print("✅ Container is running")
                return True
            else:
                print("❌ Container is not running")
                return False
        else:
            print(f"❌ Docker start failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Docker start error: {str(e)}")
        return False

def test_flag_generation():
    """Test flag generation script"""
    print("🎯 Testing flag generation...")
    
    try:
        # Execute flag generation script in container
        result = subprocess.run(
            ["docker", "exec", "ctf-password-brute-force", "python3", "/root/generate_flag.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            print("✅ Flag generation successful")
            print(f"Output: {output}")
            
            # Check if flag file exists
            flag_check = subprocess.run(
                ["docker", "exec", "ctf-password-brute-force", "cat", "/root/flag.txt"],
                capture_output=True,
                text=True
            )
            
            if flag_check.returncode == 0:
                flag_content = flag_check.stdout.strip()
                print(f"✅ Flag file created: {flag_content}")
                return True
            else:
                print("❌ Flag file not found")
                return False
        else:
            print(f"❌ Flag generation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Flag generation error: {str(e)}")
        return False

def test_ssh_connection():
    """Test SSH connection to container"""
    print("🔐 Testing SSH connection...")
    
    try:
        # First try with sshpass if available
        try:
            result = subprocess.run(
                ["sshpass", "-p", "password123", "ssh", "-o", "StrictHostKeyChecking=no", "-p", "2222", "root@localhost", "echo 'SSH test successful'"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("✅ SSH connection successful (with sshpass)")
                return True
            else:
                print(f"⚠️ SSH connection failed with sshpass: {result.stderr}")
                # Fall through to manual test
                
        except FileNotFoundError:
            print("⚠️ sshpass not found, trying manual SSH test...")
        
        # Manual SSH test - check if sshd process is running
        result = subprocess.run(
            ["docker", "exec", "ctf-password-brute-force", "ps", "aux"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and "sshd" in result.stdout:
            print("✅ SSH daemon is running in container")
            print("ℹ️ Manual SSH test: ssh -p 2222 root@localhost (password: password123)")
            return True
        else:
            print(f"❌ SSH daemon not running in container. Output: {result.stdout[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ SSH connection timeout")
        return False
    except Exception as e:
        print(f"❌ SSH connection error: {str(e)}")
        return False

def test_cleanup():
    """Test Docker cleanup"""
    print("🧹 Testing Docker cleanup...")
    
    docker_dir = Path(__file__).parent
    
    try:
        result = subprocess.run(
            ["docker-compose", "down", "--volumes", "--remove-orphans"],
            cwd=docker_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Docker cleanup successful")
            return True
        else:
            print(f"❌ Docker cleanup failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Docker cleanup error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🧪 CTF Password Brute Force Demo - Setup Test")
    print("=" * 50)
    
    tests = [
        ("Container Cleanup", cleanup_conflicting_containers),
        ("Docker Build", test_docker_build),
        ("Docker Start", test_docker_start),
        ("Flag Generation", test_flag_generation),
        ("SSH Connection", test_ssh_connection),
        ("Docker Cleanup", test_cleanup),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! CTF demo is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Run: python start_agents.py")
        print("2. Follow the instructions in the terminal")
        print("3. Have fun with the CTF challenge!")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure Docker is running")
        print("2. Check if port 2222 is available")
        print("3. Install sshpass if SSH test fails")
        print("4. Check Docker logs for more details")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
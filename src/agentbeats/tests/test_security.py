#!/usr/bin/env python3
"""
Security tests for AgentBeats assets system.
Tests file upload security measures implemented in the backend.
"""

import os
import tempfile
import requests
from pathlib import Path

def test_file_upload_security():
    """Test file upload security measures."""
    
    print("🔒 Testing File Upload Security Measures...")
    print("="*60)
    
    base_url = "http://localhost:9000"
    battle_id = "security_test_battle"
    
    # Test 1: Malicious filename with path traversal
    print("\n1. Testing path traversal prevention...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Malicious content")
        test_file = f.name
    
    try:
        with open(test_file, 'rb') as f:
            # Try to upload with malicious filename
            malicious_filenames = [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "....//....//....//etc/passwd",
                "/etc/passwd",
                "C:\\Windows\\System32\\config\\sam"
            ]
            
            for malicious_name in malicious_filenames:
                files = {'file': (malicious_name, f, 'text/plain')}
                data = {'uploaded_by': 'security_test'}
                
                response = requests.post(f"{base_url}/assets/uploads/battle/{battle_id}", files=files, data=data)
                
                if response.status_code == 400:
                    print(f"✓ Blocked malicious filename: {malicious_name}")
                else:
                    print(f"✗ Failed to block malicious filename: {malicious_name} (Status: {response.status_code})")
                    return False
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
    
    # Test 2: File size limits
    print("\n2. Testing file size limits...")
    
    # Create a file larger than 10MB
    large_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    large_content = "A" * (11 * 1024 * 1024)  # 11MB
    large_file.write(large_content)
    large_file.close()
    
    try:
        with open(large_file.name, 'rb') as f:
            files = {'file': ('large_file.txt', f, 'text/plain')}
            data = {'uploaded_by': 'security_test'}
            
            response = requests.post(f"{base_url}/assets/uploads/battle/{battle_id}", files=files, data=data)
            
            if response.status_code == 400 and "too large" in response.text.lower():
                print("✓ Blocked oversized file (>10MB)")
            else:
                print(f"✗ Failed to block oversized file (Status: {response.status_code})")
                return False
    finally:
        if os.path.exists(large_file.name):
            os.unlink(large_file.name)
    
    # Test 3: Disallowed file extensions
    print("\n3. Testing disallowed file extensions...")
    
    disallowed_extensions = ['.exe', '.bat', '.sh', '.php', '.asp', '.jsp', '.py', '.js']
    
    for ext in disallowed_extensions:
        with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
            f.write("Malicious content")
            test_file = f.name
        
        try:
            with open(test_file, 'rb') as f:
                files = {'file': (f'test{ext}', f, 'application/octet-stream')}
                data = {'uploaded_by': 'security_test'}
                
                response = requests.post(f"{base_url}/assets/uploads/battle/{battle_id}", files=files, data=data)
                
                if response.status_code == 400 and "not allowed" in response.text.lower():
                    print(f"✓ Blocked disallowed extension: {ext}")
                else:
                    print(f"✗ Failed to block disallowed extension: {ext} (Status: {response.status_code})")
                    return False
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)
    
    # Test 4: Disallowed MIME types
    print("\n4. Testing disallowed MIME types...")
    
    malicious_mime_types = [
        'application/x-executable',
        'application/x-msdownload',
        'text/x-php',
        'application/x-python'
    ]
    
    for mime_type in malicious_mime_types:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Malicious content")
            test_file = f.name
        
        try:
            with open(test_file, 'rb') as f:
                files = {'file': ('test.txt', f, mime_type)}
                data = {'uploaded_by': 'security_test'}
                
                response = requests.post(f"{base_url}/assets/uploads/battle/{battle_id}", files=files, data=data)
                
                if response.status_code == 400 and ("not allowed" in response.text.lower() or "mime type" in response.text.lower()):
                    print(f"✓ Blocked disallowed MIME type: {mime_type}")
                else:
                    print(f"✗ Failed to block disallowed MIME type: {mime_type} (Status: {response.status_code})")
                    print(f"  Response: {response.text}")
                    return False
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)
    
    # Test 5: Empty files
    print("\n5. Testing empty file rejection...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        # Create empty file
        pass
        test_file = f.name
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('empty.txt', f, 'text/plain')}
            data = {'uploaded_by': 'security_test'}
            
            response = requests.post(f"{base_url}/assets/uploads/battle/{battle_id}", files=files, data=data)
            
            if response.status_code == 400 and "empty" in response.text.lower():
                print("✓ Blocked empty file")
            else:
                print(f"✗ Failed to block empty file (Status: {response.status_code})")
                return False
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
    
    # Test 6: Invalid user/agent IDs
    print("\n6. Testing invalid ID validation...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content")
        test_file = f.name
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test.txt', f, 'text/plain')}
            
            # Test empty user_id
            data = {'user_id': ''}
            response = requests.post(f"{base_url}/assets/uploads/avatar/user", files=files, data=data)
            if response.status_code == 400 and "invalid" in response.text.lower():
                print("✓ Blocked empty user ID")
            else:
                print(f"✗ Failed to block empty user ID (Status: {response.status_code})")
                return False
            
            # Test empty agent_id
            f.seek(0)  # Reset file pointer
            data = {'agent_id': ''}
            response = requests.post(f"{base_url}/assets/uploads/avatar/agent", files=files, data=data)
            if response.status_code == 400 and "invalid" in response.text.lower():
                print("✓ Blocked empty agent ID")
            else:
                print(f"✗ Failed to block empty agent ID (Status: {response.status_code})")
                return False
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
    
    # Test 7: Valid file upload (should succeed)
    print("\n7. Testing valid file upload...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Valid test content")
        test_file = f.name
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('valid_test.txt', f, 'text/plain')}
            data = {'uploaded_by': 'security_test'}
            
            response = requests.post(f"{base_url}/assets/uploads/battle/{battle_id}", files=files, data=data)
            
            if response.status_code == 200:
                print("✓ Valid file upload succeeded")
                result = response.json()
                print(f"  Asset ID: {result['asset_id']}")
                print(f"  URL: {result['url']}")
            else:
                print(f"✗ Valid file upload failed (Status: {response.status_code})")
                return False
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
    
    print("\n🎉 All security tests passed!")
    return True

def test_static_asset_security():
    """Test static asset security measures."""
    
    print("\n🔒 Testing Static Asset Security...")
    print("="*60)
    
    base_url = "http://localhost:9000"
    
    # Test 1: Path traversal in static assets
    print("\n1. Testing static asset path traversal...")
    
    malicious_paths = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "....//....//....//etc/passwd",
        "/etc/passwd",
        "C:\\Windows\\System32\\config\\sam"
    ]
    
    for malicious_path in malicious_paths:
        response = requests.get(f"{base_url}/assets/static/{malicious_path}")
        if response.status_code == 400:
            print(f"✓ Blocked path traversal: {malicious_path}")
        elif response.status_code == 404:
            # 404 is also acceptable for path traversal attempts
            print(f"✓ Blocked path traversal (404): {malicious_path}")
        else:
            print(f"✗ Failed to block path traversal: {malicious_path} (Status: {response.status_code})")
            return False
    
    # Test 2: Valid static asset access
    print("\n2. Testing valid static asset access...")
    
    # Create a test static file
    static_dir = "../../src/backend/assets/static/test"
    os.makedirs(static_dir, exist_ok=True)
    
    test_static_file = os.path.join(static_dir, "test_security.txt")
    with open(test_static_file, 'w') as f:
        f.write("Test static content")
    
    try:
        response = requests.get(f"{base_url}/assets/static/test/test_security.txt")
        if response.status_code == 200:
            print("✓ Valid static asset access succeeded")
        else:
            print(f"✗ Valid static asset access failed (Status: {response.status_code})")
            return False
    finally:
        if os.path.exists(test_static_file):
            os.unlink(test_static_file)
        if os.path.exists(static_dir):
            os.rmdir(static_dir)
    
    print("\n🎉 All static asset security tests passed!")
    return True

def main():
    """Run all security tests."""
    
    print("🚀 Starting AgentBeats Security Tests")
    print("="*60)
    
    try:
        # Test file upload security
        upload_security = test_file_upload_security()
        
        # Test static asset security
        static_security = test_static_asset_security()
        
        # Summary
        print("\n" + "="*60)
        print("📊 SECURITY TEST SUMMARY")
        print("="*60)
        
        print(f"File Upload Security: {'✅ PASSED' if upload_security else '❌ FAILED'}")
        print(f"Static Asset Security: {'✅ PASSED' if static_security else '❌ FAILED'}")
        
        overall_success = upload_security and static_security
        
        if overall_success:
            print(f"\n🎉 All security tests passed! Backend is properly secured.")
            return True
        else:
            print(f"\n⚠️  Some security tests failed. Please review the output above.")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server. Make sure the backend is running on localhost:9000")
        return False
    except Exception as e:
        print(f"✗ Security test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 
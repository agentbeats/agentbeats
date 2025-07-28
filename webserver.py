from flask import Flask, request
import subprocess
import os

app = Flask(__name__)

@app.route('/write-hello', methods=['POST', 'GET'])
def write_hello():
    output_path = os.path.join(os.path.dirname(__file__), 'hello_output.txt')
    subprocess.run(f'echo hello world > "{output_path}"', shell=True, check=True)
    return 'Wrote hello world to file using subprocess!'

def verify_token(request):
    """Verify the bearer token from the request"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False, "No Authorization header"
    
    if not auth_header.startswith('Bearer '):
        return False, "Invalid Authorization header format"
    
    token = auth_header.split(' ')[1]
    # Replace this with your actual token verification logic
    expected_token = os.environ.get('RESET_AUTH_TOKEN')  # Change this to your actual token
    
    if token != expected_token:
        return False, "Invalid token"
    
    return True, "Token verified"

@app.route('/reset-server', methods=['POST', 'GET'])
def reset_server():
    # Verify bearer token
    is_valid, message = verify_token(request)
    if not is_valid:
        print(f"Unauthorized reset attempt: {message}")
        return {'error': 'Unauthorized', 'message': message}, 401
    
    print("Resetting server...")
    script_path = os.path.join(os.path.dirname(__file__), 'reset-gitlab.sh')
    try:
        result = subprocess.run(['bash', script_path], check=True, capture_output=True, text=True)
        #print("STDOUT: " + result.stdout)
        #print("STDERR: " + result.stderr)
        print("Server reset completed successfully!")
        return 'Server reset completed successfully!'
    except subprocess.CalledProcessError as e:
        return f'Error resetting server: {e.stderr}', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
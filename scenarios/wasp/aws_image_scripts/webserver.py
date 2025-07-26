from flask import Flask
import subprocess
import os

app = Flask(__name__)

@app.route('/write-hello', methods=['POST', 'GET'])
def write_hello():
    output_path = os.path.join(os.path.dirname(__file__), 'hello_output.txt')
    subprocess.run(f'echo hello world > "{output_path}"', shell=True, check=True)
    return 'Wrote hello world to file using subprocess!'

@app.route('/reset-server', methods=['POST', 'GET'])
def reset_server():
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
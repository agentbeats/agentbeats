from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def index():
    username = os.environ.get('AGENT_NAME', 'unknown')
    return username

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80) 
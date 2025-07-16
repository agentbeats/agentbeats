#!/usr/bin/env python3
"""
Wrapper script to run perform_action.py with the correct virtual environment.
This script ensures that the blue agent runs with the proper dependencies
regardless of the current Python environment.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the project root directory (top level of the repo)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent.parent
    
    # Path to the virtual environment
    venv_path = project_root / 'wasp' / 'visualwebarena' / 'venv'
    
    if not venv_path.exists():
        print(f"Error: Virtual environment not found at {venv_path}")
        sys.exit(1)
    
    # Get the Python executable from the virtual environment
    if os.name == 'nt':  # Windows
        python_executable = venv_path / 'Scripts' / 'python.exe'
    else:  # Unix/Linux/macOS
        python_executable = venv_path / 'bin' / 'python'
    
    if not python_executable.exists():
        print(f"Error: Python executable not found at {python_executable}")
        sys.exit(1)
    
    # Path to the blue agent script
    blue_agent_script = script_dir / 'perform_action.py'
    
    if not blue_agent_script.exists():
        print(f"Error: Blue agent script not found at {blue_agent_script}")
        sys.exit(1)
    
    print(f"Using Python interpreter: {python_executable}")
    print(f"Running blue agent script: {blue_agent_script}")
    print(f"Working directory: {project_root}")
    
    # Set up environment variables for the virtual environment
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = str(venv_path)
    
    # Add the virtual environment's bin directory to PATH
    if os.name == 'nt':  # Windows
        venv_bin = venv_path / 'Scripts'
    else:  # Unix/Linux/macOS
        venv_bin = venv_path / 'bin'
    
    env['PATH'] = str(venv_bin) + os.pathsep + env.get('PATH', '')
    
    try:
        # Run the blue agent script with the virtual environment's Python
        result = subprocess.run(
            [str(python_executable), str(blue_agent_script)],
            cwd=project_root,
            env=env,
            check=True
        )
        print("Blue agent completed successfully")
        return str({"stdout": result.stdout, "stderr": result.stderr})
    except subprocess.CalledProcessError as e:
        print(f"Error running blue agent: {e}")
        return e.returncode
    except KeyboardInterrupt:
        print("\nBlue agent interrupted by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
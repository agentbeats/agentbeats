#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the project root directory (top level of the repo)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    
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
    
    # Path to the evaluator script
    evaluator_script = script_dir / 'evaluator_final.py'
    
    if not evaluator_script.exists():
        print(f"Error: Evaluator script not found at {evaluator_script}")
        sys.exit(1)
    
    print(f"Using Python interpreter: {python_executable}")
    print(f"Running evaluator script: {evaluator_script}")
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
        # Run the evaluator script with the virtual environment's Python
        result = subprocess.run(
            [str(python_executable), str(evaluator_script)],
            env=env,
            cwd=project_root,
            check=False
        )
        print("Evaluator completed successfully")
        return str({"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode})
    except subprocess.CalledProcessError as e:
        print(f"Error running evaluator: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nEvaluator interrupted by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
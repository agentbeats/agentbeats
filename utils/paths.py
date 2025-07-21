"""
Utility functions for paths.
"""

import os

PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CYBERGYM_PATH = os.path.join(PROJECT_PATH, "external", "cybergym")
POC_SAVE_DIR = os.path.join(CYBERGYM_PATH, "poc_save_dir")
CYBERGYM_SERVER_DATA_DIR = os.path.join(CYBERGYM_PATH, "cybergym_data", "data")
CYBERGYM_TASK_DIR = os.path.join(CYBERGYM_PATH, "test_task_folder")

#!/usr/bin/env python3
"""
Test runner for AgentBeats SDK tests.
"""

import unittest
import sys
import os

# Add the src directory to the path so we can import the modules
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

# Also add the current directory to handle relative imports
sys.path.insert(0, os.path.dirname(__file__))

def run_tests():
    """Run all tests."""
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1) 
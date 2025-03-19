#!/usr/bin/env python3
import os
import sys

def init_db_dirs():
    """Initialize database directories"""
    # Get the base directory (openalgo folder)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create necessary directories
    dirs = [
        os.path.join(base_dir, 'db'),
        os.path.join(base_dir, 'tmp')
    ]
    
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

if __name__ == '__main__':
    init_db_dirs() 
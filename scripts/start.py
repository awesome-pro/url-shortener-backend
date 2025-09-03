#!/usr/bin/env python3
"""
Development startup script for URL Shortener backend
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    # Get the backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    print("🚀 Starting URL Shortener Backend...")
    print(f"📁 Working directory: {backend_dir}")
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("⚠️  .env file not found. Please copy .env.example to .env and configure it.")
        return
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Virtual environment not activated. Please run:")
        print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        return
    
    try:
        # Start the server
        subprocess.run([
            "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main()

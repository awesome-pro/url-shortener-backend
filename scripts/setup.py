#!/usr/bin/env python3
"""
Setup script for URL Shortener backend
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"📋 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"   {e.stderr.strip()}")
        return False
    return True

def main():
    # Get the backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    print("🔧 Setting up URL Shortener Backend...")
    print(f"📁 Working directory: {backend_dir}")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required")
        return
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists('venv'):
        if not run_command('python -m venv venv', 'Creating virtual environment'):
            return
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = 'venv\\Scripts\\activate && '
    else:  # Unix/Linux/MacOS
        activate_cmd = 'source venv/bin/activate && '
    
    if not run_command(f'{activate_cmd}pip install --upgrade pip', 'Upgrading pip'):
        return
    
    if not run_command(f'{activate_cmd}pip install -r requirements.txt', 'Installing dependencies'):
        return
    
    # Copy .env.example to .env if .env doesn't exist
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            run_command('cp .env.example .env', 'Creating .env file from template')
            print("⚠️  Please edit .env file with your configuration before running the app")
        else:
            print("⚠️  .env.example not found. Please create .env file manually")
    
    print("\n🎉 Setup complete!")
    print("\n📝 Next steps:")
    print("1. Edit .env file with your database and Redis configuration")
    print("2. Create PostgreSQL database: createdb shortener_db")
    print("3. Run database migrations: alembic upgrade head")
    print("4. Start Redis server: redis-server")
    print("5. Start the application: python scripts/start.py")

if __name__ == "__main__":
    main()

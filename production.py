#!/usr/bin/env python3
"""
Production deployment script for the Store Management API.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_production():
    """Run the application in production mode."""
    
    # Set production environment
    os.environ["ENVIRONMENT"] = "production"
    
    # Get the number of workers (CPU cores * 2 + 1)
    try:
        import multiprocessing
        workers = (multiprocessing.cpu_count() * 2) + 1
    except:
        workers = 4
    
    # Production command with Gunicorn
    cmd = [
        "gunicorn",
        "app.main:app",
        "--worker-class", "uvicorn.workers.UvicornWorker",
        "--workers", str(workers),
        "--bind", "0.0.0.0:5002",
        "--timeout", "120",
        "--keep-alive", "5",
        "--max-requests", "1000",
        "--max-requests-jitter", "100",
        "--preload",
        "--log-level", "info",
        "--access-logfile", "-",
        "--error-logfile", "-"
    ]
    
    print(f"🚀 Starting production server with {workers} workers...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start production server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down production server...")
        sys.exit(0)

def check_requirements():
    """Check if all production requirements are installed."""
    required_packages = [
        "fastapi",
        "uvicorn",
        "gunicorn",
        "python-multipart",
        "python-dotenv",
        "pillow"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    
    return True

def setup_production():
    """Setup production environment."""
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found. Please create it with required configuration.")
        sys.exit(1)
    
    # Create necessary directories
    directories = ["uploads", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    print("✅ Production environment setup complete!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_production()
    else:
        setup_production()
        run_production()
#!/usr/bin/env python3
"""
Leadership Development Platform Startup Script

This script provides an easy way to start the FastAPI server
with proper configuration for both development and production.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set default environment if not already set
if not os.getenv("ENVIRONMENT"):
    os.environ["ENVIRONMENT"] = "development"

def get_server_config():
    """Get server configuration based on environment"""
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        return {
            "host": "0.0.0.0",
            "port": int(os.getenv("PORT", 8000)),
            "reload": False,
            "workers": int(os.getenv("WORKERS", 1)),
            "log_level": "info",
            "access_log": True,
        }
    else:
        return {
            "host": "0.0.0.0",
            "port": 8000,
            "reload": True,
            "log_level": "info",
            "access_log": True,
        }

if __name__ == "__main__":
    config = get_server_config()
    environment = os.getenv("ENVIRONMENT", "development")
    
    print("🚀 Starting Leadership Development Platform...")
    print(f"📁 Project root: {project_root}")
    print(f"🌍 Environment: {environment}")
    print(f"🌐 Host: {config['host']}")
    print(f"🔌 Port: {config['port']}")
    print(f"🔄 Reload: {config.get('reload', False)}")
    
    if environment == "production":
        print(f"👥 Workers: {config.get('workers', 1)}")
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        **config
    )

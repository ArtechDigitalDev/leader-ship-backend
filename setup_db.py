#!/usr/bin/env python3
"""
Database Setup Script

This script creates the database tables for the FastAPI application.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.database import engine, Base
from app.models.user import User
from app.models.item import Item
from app.models.assessment import Assessment

def setup_database():
    """Create all database tables"""
    print("Creating database tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")
    print("Tables created:")
    print("- users")
    print("- items")
    print("- assessments")

if __name__ == "__main__":
    setup_database()

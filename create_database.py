#!/usr/bin/env python3
"""
Database Creation Script
Creates the database and user for the Leadership Development Platform
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    """Create database and user for the project"""
    
    # Connect to PostgreSQL server (default postgres database)
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        user="postgres",
        password="123456",
        database="postgres"
    )
    
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    try:
        # Create database
        print("Creating database 'leader_db'...")
        cursor.execute("CREATE DATABASE leader_db;")
        print("✅ Database 'leader_db' created successfully!")
        
        # Create user
        print("Creating user 'leadership'...")
        cursor.execute("CREATE USER leadership WITH PASSWORD 'lead123';")
        print("✅ User 'leadership' created successfully!")
        
        # Grant privileges
        print("Granting privileges...")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE leader_db TO leadership;")
        print("✅ Privileges granted successfully!")
        
        print("\n🎉 Database setup completed!")
        print("You can now run: python setup_db.py")
        
    except psycopg2.errors.DuplicateDatabase:
        print("⚠️  Database 'leader_db' already exists!")
    except psycopg2.errors.DuplicateObject:
        print("⚠️  User 'leadership' already exists!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_database()

#!/usr/bin/env python3
"""
Check current enum values
"""

import psycopg2

def check_enum():
    """Check current userrole enum values"""
    try:
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5432/leader_db')
        cursor = conn.cursor()
        
        # Check enum values
        cursor.execute("SELECT unnest(enum_range(NULL::userrole));")
        values = cursor.fetchall()
        
        print("Current userrole enum values:")
        for value in values:
            print(f"  - {value[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_enum()

#!/usr/bin/env python3
"""
Quick database check for dashboard testing
"""

import sqlite3
from pathlib import Path

def check_database():
    db_path = Path('data/research.db')
    
    if not db_path.exists():
        print("❌ Database not found at:", db_path)
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("=== DATABASE TABLES ===")
        total_records = 0
        
        for table in tables:
            table_name = table[0]
            print(f"\n📊 Table: {table_name}")
            
            # Get count
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            count = cursor.fetchone()[0]
            total_records += count
            print(f"   Records: {count}")
            
            # Get column info
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            columns = cursor.fetchall()
            print(f"   Columns: {len(columns)}")
            
            # Show sample data if available
            if count > 0:
                cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 2')
                sample = cursor.fetchall()
                print(f"   Sample records: {len(sample)}")
        
        print(f"\n✅ Total records across all tables: {total_records}")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    check_database()

import sqlite3
import sys
sys.path.insert(0, '.')

def check_database_schema():
    try:
        conn = sqlite3.connect('data/research.db')
        cursor = conn.cursor()
        print('=== DATABASE SCHEMA ANALYSIS ===')
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print('✅ Tables found:', tables)
        
        # Check each table structure
        for table in tables:
            try:
                cursor.execute(f'PRAGMA table_info({table})')
                columns = cursor.fetchall()
                print(f'\n📊 Table: {table}')
                for col in columns:
                    print(f'  - {col[1]} ({col[2]})')
                    
                # Get row count
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                print(f'  📈 Rows: {count}')
                
            except Exception as e:
                print(f'❌ Error checking {table}: {e}')
        
        conn.close()
        print('\n✅ Database schema check completed')
        
    except Exception as e:
        print(f'❌ Database connection error: {e}')

if __name__ == '__main__':
    check_database_schema()

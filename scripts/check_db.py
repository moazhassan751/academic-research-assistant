import sqlite3
from pathlib import Path

db_path = Path('data/research.db')
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()
u
# Check papers table
try:
    cursor.execute("SELECT COUNT(*) FROM papers")
    total_papers = cursor.fetchone()[0]
    print(f"📊 Total papers in database: {total_papers}")
    
    # Search for automobile/automotive related papers
    search_terms = ['automobile', 'automotive', 'car', 'vehicle', 'auto']
    for term in search_terms:
        cursor.execute("""
            SELECT COUNT(*) FROM papers 
            WHERE title LIKE ? OR abstract LIKE ? OR keywords LIKE ?
        """, (f'%{term}%', f'%{term}%', f'%{term}%'))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"🔍 Papers containing '{term}': {count}")
    
    # Show sample paper titles
    cursor.execute("SELECT title FROM papers LIMIT 5")
    sample_titles = cursor.fetchall()
    if sample_titles:
        print("\n📋 Sample paper titles:")
        for i, (title,) in enumerate(sample_titles, 1):
            print(f"{i}. {title[:80]}...")
    
    # Check table structure
    cursor.execute("PRAGMA table_info(papers)")
    columns = cursor.fetchall()
    print(f"\n📋 Papers table columns: {[col[1] for col in columns]}")
    
except Exception as e:
    print(f"❌ Database error: {e}")

conn.close()

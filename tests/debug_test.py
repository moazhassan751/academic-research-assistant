#!/usr/bin/env python3
"""
Debug test to identify hanging issue
"""

print("Starting debug test...")

try:
    print("Step 1: Basic imports")
    import sys
    import os
    sys.path.append('.')
    print("✅ Basic imports OK")
    
    print("Step 2: Config import")
    from src.utils.config import config
    print("✅ Config import OK")
    
    print("Step 3: Models import") 
    from src.storage.models import Paper
    print("✅ Models import OK")
    
    print("Step 4: Database optimizer import")
    from src.utils.database_optimizer import DatabaseOptimizer
    print("✅ Database optimizer import OK")
    
    print("Step 5: Testing database class import (not instantiation)")
    from src.storage.database import DatabaseManager
    print("✅ DatabaseManager class import OK")
    
    print("Step 6: Creating DatabaseManager instance...")
    # This is where it might hang
    db = DatabaseManager()
    print("✅ DatabaseManager instance created!")
    
    print("Step 7: Getting stats")
    stats = db.get_stats()
    print(f"✅ Stats: {stats}")
    
except Exception as e:
    print(f"❌ Error at step: {e}")
    import traceback
    traceback.print_exc()

print("Debug test completed!")

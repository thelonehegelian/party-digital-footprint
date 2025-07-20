#!/usr/bin/env python3
"""
Reset the database by dropping all tables and recreating them.
"""

import sys
import os
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import sync_engine, create_tables
from src.models import Base


def reset_database():
    """Drop all tables and recreate them."""
    logger.info("Resetting database...")
    
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=sync_engine)
        logger.info("Dropped all existing tables")
        
        # Recreate tables
        create_tables()
        logger.info("Recreated all tables")
        
        print("✅ Database reset completed successfully!")
        print("\nNext steps:")
        print("1. Import mock data: python scripts/import_mock_data.py")
        print("2. Or run real scraper: python scripts/run_scraper.py")
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False
    
    return True


if __name__ == "__main__":
    reset_database()
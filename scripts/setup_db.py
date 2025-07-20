#!/usr/bin/env python3
"""
Database setup script for Reform UK messaging analysis.
Creates tables and optionally seeds with sample data sources.
"""

import asyncio
from sqlalchemy.orm import Session
from src.database import create_tables, get_session
from src.models import Source
from loguru import logger


def setup_database():
    """Create database tables and seed with initial sources."""
    logger.info("Setting up database...")

    # Create tables
    create_tables()
    logger.info("Database tables created successfully")

    # Seed with Reform UK sources
    with next(get_session()) as db:
        sources = [
            {
                "name": "Reform UK Website",
                "url": "https://www.reformparty.uk",
                "source_type": "website",
                "active": True,
            },
            {
                "name": "Reform UK Twitter",
                "url": "https://twitter.com/reformparty_uk",
                "source_type": "twitter",
                "active": True,
            },
            {
                "name": "Reform UK Facebook",
                "url": "https://www.facebook.com/ReformPartyUK",
                "source_type": "facebook",
                "active": True,
            },
            {
                "name": "Meta Ads Library",
                "url": "https://www.facebook.com/ads/library",
                "source_type": "meta_ads",
                "active": True,
            },
        ]

        for source_data in sources:
            # Check if source already exists
            existing = (
                db.query(Source).filter(Source.name == source_data["name"]).first()
            )

            if not existing:
                source = Source(**source_data)
                db.add(source)
                logger.info(f"Added source: {source_data['name']}")
            else:
                logger.info(f"Source already exists: {source_data['name']}")

        db.commit()

    logger.info("Database setup completed successfully!")


if __name__ == "__main__":
    setup_database()

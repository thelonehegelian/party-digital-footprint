#!/usr/bin/env python3
"""
Import mock data for testing the Progressive Party messaging analysis system.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

from src.database import create_tables, get_session
from src.models import Source, Message, Keyword
from src.nlp.processor import BasicNLPProcessor


def load_mock_data() -> Dict[str, List[Dict[str, Any]]]:
    """Load all mock data files."""
    mock_data_dir = Path(__file__).parent.parent / "mock-data"
    
    data = {}
    
    # Load each mock data file
    mock_files = {
        'website': 'website_messages.json',
        'twitter': 'twitter_messages.json', 
        'facebook': 'facebook_messages.json',
        'meta_ads': 'meta_ads_messages.json'
    }
    
    for source_type, filename in mock_files.items():
        file_path = mock_data_dir / filename
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data[source_type] = json.load(f)
            logger.info(f"Loaded {len(data[source_type])} {source_type} messages")
        else:
            logger.warning(f"Mock data file not found: {file_path}")
            data[source_type] = []
    
    return data


def create_sources() -> Dict[str, int]:
    """Create source records and return source_id mapping."""
    sources_config = {
        'website': {
            'name': 'Progressive Party Website',
            'url': 'https://www.progressiveparty.uk',
            'source_type': 'website'
        },
        'twitter': {
            'name': 'Progressive Party Twitter',
            'url': 'https://twitter.com/progressiveparty_uk',
            'source_type': 'twitter'
        },
        'facebook': {
            'name': 'Progressive Party Facebook',
            'url': 'https://www.facebook.com/ReformPartyUK',
            'source_type': 'facebook'
        },
        'meta_ads': {
            'name': 'Meta Ads Library',
            'url': 'https://www.facebook.com/ads/library',
            'source_type': 'meta_ads'
        }
    }
    
    source_ids = {}
    
    with next(get_session()) as db:
        for key, config in sources_config.items():
            # Check if source already exists
            existing = db.query(Source).filter(
                Source.source_type == config['source_type'],
                Source.name == config['name']
            ).first()
            
            if existing:
                source_ids[key] = existing.id
                logger.info(f"Found existing source: {config['name']}")
            else:
                source = Source(
                    name=config['name'],
                    url=config['url'],
                    source_type=config['source_type'],
                    active=True,
                    last_scraped=datetime.utcnow()
                )
                db.add(source)
                db.flush()
                source_ids[key] = source.id
                logger.info(f"Created source: {config['name']}")
        
        db.commit()
    
    return source_ids


def parse_date_string(date_str: str) -> datetime:
    """Parse ISO date string to datetime."""
    try:
        # Handle ISO format with Z
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+00:00'
        return datetime.fromisoformat(date_str)
    except ValueError:
        logger.warning(f"Could not parse date: {date_str}")
        return datetime.utcnow()


def import_messages(mock_data: Dict[str, List[Dict[str, Any]]], source_ids: Dict[str, int]) -> int:
    """Import mock messages into the database."""
    total_imported = 0
    
    with next(get_session()) as db:
        for source_type, messages in mock_data.items():
            if source_type not in source_ids:
                logger.warning(f"No source ID found for {source_type}")
                continue
            
            source_id = source_ids[source_type]
            imported_count = 0
            
            for msg_data in messages:
                try:
                    # Check if message already exists
                    existing = None
                    if msg_data.get('url'):
                        existing = db.query(Message).filter(
                            Message.source_id == source_id,
                            Message.url == msg_data['url']
                        ).first()
                    
                    if existing:
                        logger.debug(f"Message already exists: {msg_data.get('url', 'No URL')}")
                        continue
                    
                    # Parse published date
                    published_at = None
                    if msg_data.get('published_at'):
                        published_at = parse_date_string(msg_data['published_at'])
                    
                    # Create message
                    message = Message(
                        source_id=source_id,
                        content=msg_data['content'],
                        url=msg_data.get('url'),
                        published_at=published_at,
                        message_type=msg_data.get('message_type'),
                        message_metadata=msg_data.get('metadata'),
                        raw_data=msg_data.get('raw_data'),
                        scraped_at=datetime.utcnow()
                    )
                    
                    db.add(message)
                    db.flush()
                    imported_count += 1
                    
                except Exception as e:
                    logger.error(f"Error importing message: {e}")
                    continue
            
            db.commit()
            total_imported += imported_count
            logger.info(f"Imported {imported_count} {source_type} messages")
    
    return total_imported


def process_nlp(nlp_processor: BasicNLPProcessor) -> int:
    """Process messages for keyword extraction."""
    if not nlp_processor.nlp:
        logger.warning("spaCy model not loaded. Skipping NLP processing.")
        return 0
    
    keywords_created = 0
    
    with next(get_session()) as db:
        # Get messages without keywords
        messages_without_keywords = db.query(Message).filter(
            ~Message.id.in_(
                db.query(Keyword.message_id).distinct()
            )
        ).all()
        
        logger.info(f"Processing {len(messages_without_keywords)} messages for keywords")
        
        for message in messages_without_keywords:
            try:
                # Extract keywords
                keywords = nlp_processor.extract_keywords(message.content)
                
                # Store keywords
                for kw_data in keywords:
                    keyword = Keyword(
                        message_id=message.id,
                        keyword=kw_data['keyword'],
                        confidence=kw_data['confidence'],
                        extraction_method=kw_data['extraction_method']
                    )
                    db.add(keyword)
                    keywords_created += 1
                
                if keywords:
                    logger.debug(f"Extracted {len(keywords)} keywords from message {message.id}")
                
            except Exception as e:
                logger.error(f"Error processing keywords for message {message.id}: {e}")
                continue
        
        db.commit()
    
    return keywords_created


def main():
    """Main import function."""
    logger.info("Starting mock data import...")
    
    # Ensure database tables exist
    create_tables()
    logger.info("Database tables ready")
    
    # Load mock data
    mock_data = load_mock_data()
    total_messages = sum(len(messages) for messages in mock_data.values())
    logger.info(f"Loaded {total_messages} total mock messages")
    
    if total_messages == 0:
        logger.error("No mock data found. Please check mock-data directory.")
        return
    
    # Create sources
    source_ids = create_sources()
    logger.info(f"Sources ready: {list(source_ids.keys())}")
    
    # Import messages
    imported_count = import_messages(mock_data, source_ids)
    logger.info(f"Imported {imported_count} messages")
    
    # Process NLP
    nlp_processor = BasicNLPProcessor()
    nlp_processor.load_model()
    
    if nlp_processor.nlp:
        keywords_count = process_nlp(nlp_processor)
        logger.info(f"Created {keywords_count} keywords")
    else:
        logger.warning("NLP processing skipped - install spaCy model with: python -m spacy download en_core_web_sm")
    
    # Summary
    print("\n=== Mock Data Import Complete ===")
    print(f"Messages imported: {imported_count}")
    if nlp_processor.nlp:
        print(f"Keywords extracted: {keywords_count}")
    print("\nNext steps:")
    print("1. Launch dashboard: streamlit run dashboard.py")
    print("2. Test the system with mock data")
    print("3. Configure real API credentials when ready")


if __name__ == "__main__":
    main()
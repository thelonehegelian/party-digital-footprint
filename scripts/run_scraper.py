#!/usr/bin/env python3
"""
Script to run the Reform UK messaging scraper.
"""

import asyncio
import sys
import argparse
from datetime import datetime
from loguru import logger

from src.scrapers.main import ReformUKScraper
from src.nlp.processor import BasicNLPProcessor
from src.database import get_session
from src.models import Message, Keyword


async def process_keywords():
    """Process existing messages to extract keywords using NLP."""
    logger.info("Starting keyword extraction for existing messages...")
    
    nlp_processor = BasicNLPProcessor()
    nlp_processor.load_model()
    
    if not nlp_processor.nlp:
        logger.warning("spaCy model not available. Skipping NLP processing.")
        return
    
    with next(get_session()) as db:
        # Get messages without keywords
        messages_without_keywords = db.query(Message).filter(
            ~Message.id.in_(
                db.query(Keyword.message_id).distinct()
            )
        ).all()
        
        logger.info(f"Processing {len(messages_without_keywords)} messages for keyword extraction")
        
        for message in messages_without_keywords:
            try:
                # Extract keywords
                keywords = nlp_processor.extract_keywords(message.content)
                
                # Store keywords in database
                for kw_data in keywords:
                    keyword = Keyword(
                        message_id=message.id,
                        keyword=kw_data['keyword'],
                        confidence=kw_data['confidence'],
                        extraction_method=kw_data['extraction_method']
                    )
                    db.add(keyword)
                
                if len(keywords) > 0:
                    logger.debug(f"Extracted {len(keywords)} keywords from message {message.id}")
                
            except Exception as e:
                logger.error(f"Error processing keywords for message {message.id}: {e}")
                continue
        
        db.commit()
        logger.info("Keyword extraction completed")


async def main():
    parser = argparse.ArgumentParser(description="Run Reform UK messaging scraper")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["website", "twitter", "facebook", "meta_ads"],
        default=["website", "twitter", "facebook", "meta_ads"],
        help="Sources to scrape"
    )
    parser.add_argument(
        "--skip-nlp",
        action="store_true",
        help="Skip NLP keyword extraction"
    )
    parser.add_argument(
        "--nlp-only",
        action="store_true",
        help="Only run NLP processing on existing messages"
    )
    
    args = parser.parse_args()
    
    if args.nlp_only:
        await process_keywords()
        return
    
    # Run scraper
    scraper = ReformUKScraper()
    
    # Filter scrapers based on arguments
    if args.sources != ["website", "twitter", "facebook", "meta_ads"]:
        filtered_scrapers = {k: v for k, v in scraper.scrapers.items() if k in args.sources}
        scraper.scrapers = filtered_scrapers
    
    logger.info(f"Starting scraping for sources: {list(scraper.scrapers.keys())}")
    
    results = await scraper.scrape_all_sources()
    
    # Print results
    print("\n=== Scraping Results ===")
    total_messages = 0
    for source_type, count in results.items():
        print(f"{source_type.title()}: {count} messages")
        total_messages += count
    
    print(f"\nTotal messages collected: {total_messages}")
    
    # Run NLP processing if not skipped
    if not args.skip_nlp and total_messages > 0:
        await process_keywords()
    
    print(f"\nScraping completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("View results at: streamlit run dashboard.py")


if __name__ == "__main__":
    asyncio.run(main())
from typing import List, Dict, Any
import asyncio
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from ..database import get_session, create_tables
from ..models import Source, Message, Keyword
from .website import WebsiteScraper
from .twitter import TwitterScraper
from .facebook import FacebookScraper
from .meta_ads import MetaAdsScraper


class PoliticalPartyScraper:
    """Main scraper orchestrator for Political Party messaging collection."""
    
    def __init__(self):
        self.scrapers = {
            'website': WebsiteScraper(),
            'twitter': TwitterScraper(),
            'facebook': FacebookScraper(),
            'meta_ads': MetaAdsScraper()
        }
    
    async def scrape_all_sources(self) -> Dict[str, int]:
        """Scrape all configured sources and store in database."""
        logger.info("Starting Political Party messaging collection...")
        
        # Ensure database tables exist
        create_tables()
        
        results = {}
        
        for source_type, scraper in self.scrapers.items():
            try:
                logger.info(f"Starting {source_type} scraping...")
                
                # Setup scraper
                await scraper.setup()
                
                # Scrape messages
                messages = await scraper.scrape()
                
                # Store messages in database
                stored_count = self.store_messages(messages, source_type)
                results[source_type] = stored_count
                
                logger.info(f"Completed {source_type} scraping: {stored_count} messages stored")
                
                # Cleanup scraper
                await scraper.cleanup()
                
            except Exception as e:
                logger.error(f"Failed to scrape {source_type}: {e}")
                results[source_type] = 0
                continue
        
        total_messages = sum(results.values())
        logger.info(f"Scraping completed. Total messages collected: {total_messages}")
        
        return results
    
    def store_messages(self, messages: List[Dict[str, Any]], source_type: str) -> int:
        """Store scraped messages in the database."""
        if not messages:
            return 0
        
        with next(get_session()) as db:
            try:
                # Get or create source
                source = db.query(Source).filter(
                    Source.source_type == source_type,
                    Source.name == f"Political Party {source_type.title()}"
                ).first()
                
                if not source:
                    source = Source(
                        name=f"Political Party {source_type.title()}",
                        source_type=source_type,
                        url=self.get_source_url(source_type),
                        active=True
                    )
                    db.add(source)
                    db.flush()
                
                # Update last scraped time
                source.last_scraped = datetime.utcnow()
                
                stored_count = 0
                
                for message_data in messages:
                    try:
                        # Check if message already exists (by URL or content hash)
                        existing = None
                        if message_data.get('url'):
                            existing = db.query(Message).filter(
                                Message.source_id == source.id,
                                Message.url == message_data['url']
                            ).first()
                        
                        if existing:
                            logger.debug(f"Message already exists: {message_data.get('url', 'No URL')}")
                            continue
                        
                        # Create new message
                        message = Message(
                            source_id=source.id,
                            content=message_data['content'],
                            url=message_data.get('url'),
                            published_at=message_data.get('published_at'),
                            message_type=message_data.get('message_type'),
                            message_metadata=message_data.get('metadata'),
                            raw_data=message_data.get('raw_data')
                        )
                        
                        db.add(message)
                        db.flush()
                        stored_count += 1
                        
                        # Extract and store keywords if NLP processor is available
                        # This will be implemented in the NLP module
                        
                    except Exception as e:
                        logger.error(f"Error storing message: {e}")
                        continue
                
                db.commit()
                return stored_count
                
            except Exception as e:
                logger.error(f"Error storing messages for {source_type}: {e}")
                db.rollback()
                return 0
    
    def get_source_url(self, source_type: str) -> str:
        """Get the main URL for a source type."""
        urls = {
            'website': 'https://www.progressiveparty.uk',
            'twitter': 'https://twitter.com/progressiveparty_uk',
            'facebook': 'https://www.facebook.com/ReformPartyUK',
            'meta_ads': 'https://www.facebook.com/ads/library'
        }
        return urls.get(source_type, '')


async def main():
    """Main entry point for scraping."""
    scraper = PoliticalPartyScraper()
    results = await scraper.scrape_all_sources()
    
    print("\n=== Scraping Results ===")
    for source_type, count in results.items():
        print(f"{source_type.title()}: {count} messages")
    
    total = sum(results.values())
    print(f"\nTotal messages collected: {total}")


if __name__ == "__main__":
    asyncio.run(main())
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import asyncio
from loguru import logger


class BaseScraper(ABC):
    """Base class for all scrapers."""

    def __init__(self, delay: float = 1.0, max_retries: int = 3):
        self.delay = delay
        self.max_retries = max_retries
        self.session = None

    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape data and return list of message dictionaries."""
        pass

    async def setup(self):
        """Setup method called before scraping."""
        pass

    async def cleanup(self):
        """Cleanup method called after scraping."""
        pass

    async def retry_request(self, func, *args, **kwargs):
        """Retry a request with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e

                wait_time = self.delay * (2**attempt)
                logger.warning(
                    f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}"
                )
                await asyncio.sleep(wait_time)

    def extract_text_content(self, element) -> str:
        """Extract clean text content from HTML element."""
        if hasattr(element, "get_text"):
            return element.get_text(strip=True)
        return str(element).strip()

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats to datetime."""
        if not date_str:
            return None

        # Common date formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d %b %Y",
            "%B %d, %Y",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

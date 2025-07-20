from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
import requests
from loguru import logger

from .base import BaseScraper


class WebsiteScraper(BaseScraper):
    """Scraper for Reform UK website content."""
    
    def __init__(self, base_url: str = "https://www.reformparty.uk", **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.playwright = None
        self.browser = None
        self.page = None
    
    async def setup(self):
        """Initialize Playwright browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        
        # Set user agent to avoid blocking
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    async def cleanup(self):
        """Close browser and playwright."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape Reform UK website for news, articles, and press releases."""
        await self.setup()
        messages = []
        
        try:
            # Scrape different sections
            sections = [
                ("/news", "article"),
                ("/press-releases", "press_release"),
                ("/policy", "policy"),
                ("/events", "event")
            ]
            
            for section_path, message_type in sections:
                section_messages = await self.scrape_section(section_path, message_type)
                messages.extend(section_messages)
                
                # Delay between sections
                await asyncio.sleep(self.delay)
        
        finally:
            await self.cleanup()
        
        logger.info(f"Scraped {len(messages)} messages from Reform UK website")
        return messages
    
    async def scrape_section(self, section_path: str, message_type: str) -> List[Dict[str, Any]]:
        """Scrape a specific section of the website."""
        url = urljoin(self.base_url, section_path)
        messages = []
        
        try:
            await self.page.goto(url, wait_until="networkidle")
            
            # Get page content
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find article links (adjust selectors based on actual website structure)
            article_selectors = [
                'a[href*="/news/"]',
                'a[href*="/press-releases/"]',
                'a[href*="/policy/"]',
                '.article-link',
                '.post-link',
                'h2 a, h3 a'
            ]
            
            article_links = []
            for selector in article_selectors:
                links = soup.select(selector)
                article_links.extend([link.get('href') for link in links if link.get('href')])
            
            # Remove duplicates and convert to absolute URLs
            unique_links = list(set([
                urljoin(self.base_url, link) for link in article_links 
                if link and not link.startswith('mailto:')
            ]))
            
            logger.info(f"Found {len(unique_links)} article links in {section_path}")
            
            # Scrape each article
            for article_url in unique_links[:20]:  # Limit to first 20 articles
                try:
                    article_data = await self.scrape_article(article_url, message_type)
                    if article_data:
                        messages.append(article_data)
                    
                    await asyncio.sleep(self.delay)
                    
                except Exception as e:
                    logger.error(f"Error scraping article {article_url}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping section {section_path}: {e}")
        
        return messages
    
    async def scrape_article(self, url: str, message_type: str) -> Optional[Dict[str, Any]]:
        """Scrape individual article content."""
        try:
            await self.page.goto(url, wait_until="networkidle")
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract title
            title_selectors = ['h1', '.article-title', '.post-title', 'title']
            title = None
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.extract_text_content(title_elem)
                    break
            
            # Extract content
            content_selectors = [
                '.article-content',
                '.post-content',
                '.entry-content',
                'main',
                '.content'
            ]
            
            article_content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove scripts and style elements
                    for script in content_elem(["script", "style"]):
                        script.decompose()
                    article_content = self.extract_text_content(content_elem)
                    break
            
            # If no specific content area found, get all paragraph text
            if not article_content:
                paragraphs = soup.find_all('p')
                article_content = ' '.join([self.extract_text_content(p) for p in paragraphs])
            
            # Extract date
            date_selectors = [
                '.date',
                '.published-date',
                '.article-date',
                'time',
                '[datetime]'
            ]
            
            published_date = None
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_str = date_elem.get('datetime') or self.extract_text_content(date_elem)
                    published_date = self.parse_date(date_str)
                    if published_date:
                        break
            
            # Combine title and content
            full_content = f"{title}\n\n{article_content}" if title else article_content
            
            if not full_content.strip():
                logger.warning(f"No content extracted from {url}")
                return None
            
            # Extract metadata
            metadata = {
                'title': title,
                'word_count': len(full_content.split()),
                'url_path': urlparse(url).path
            }
            
            return {
                'content': full_content.strip(),
                'url': url,
                'published_at': published_date,
                'message_type': message_type,
                'metadata': metadata,
                'raw_data': {
                    'title': title,
                    'scraped_url': url,
                    'scraper': 'website'
                }
            }
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {e}")
            return None
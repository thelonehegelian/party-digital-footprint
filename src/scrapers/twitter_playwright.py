import os
import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from loguru import logger

from .base import BaseScraper


@dataclass
class TwitterScrapingConfig:
    """Configuration for Twitter scraping parameters."""

    max_tweets: int = 100
    max_scroll_attempts: int = 10
    scroll_delay: float = 2.0
    load_delay: float = 3.0
    max_retries: int = 3
    include_replies: bool = False
    include_retweets: bool = True
    date_limit_days: Optional[int] = None


class TwitterPlaywrightScraper(BaseScraper):
    """Playwright-based scraper for Twitter/X content."""

    def __init__(
        self,
        username: str,
        config: Optional[TwitterScrapingConfig] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.username = username.replace("@", "")  # Remove @ if present
        self.config = config or TwitterScrapingConfig()
        self.browser = None
        self.page = None
        self.scraped_tweets = []

    async def setup(self):
        """Initialize Playwright browser with anti-detection measures."""
        try:
            # Import playwright here to avoid import errors if not installed
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()

            # Launch browser with stealth configuration
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Set to True for production
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ],
            )

            # Create new page with additional stealth measures
            self.page = await self.browser.new_page()

            # Set viewport
            await self.page.set_viewport_size({"width": 1280, "height": 800})

            # Override navigator properties to avoid detection
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                window.chrome = {
                    runtime: {},
                };
            """)

            # Set extra headers
            await self.page.set_extra_http_headers(
                {
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }
            )

            logger.info("Playwright browser initialized successfully")

        except ImportError:
            logger.error(
                "Playwright not installed. Install with: pip install playwright"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise

    async def cleanup(self):
        """Close browser and cleanup resources."""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, "playwright"):
                await self.playwright.stop()
            logger.info("Browser cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def scrape(self) -> List[Dict[str, Any]]:
        """Main scraping method."""
        if not self.browser or not self.page:
            logger.error("Browser not initialized. Call setup() first.")
            return []

        try:
            # Navigate to profile
            await self._navigate_to_profile()

            # Handle potential login/bot detection
            if await self._handle_access_restrictions():
                logger.info("Successfully handled access restrictions")
            else:
                logger.warning("May have access restrictions - proceeding anyway")

            # Scrape tweets
            tweets = await self._scrape_tweets()

            logger.info(
                f"Successfully scraped {len(tweets)} tweets from @{self.username}"
            )
            return tweets

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return []

    async def _navigate_to_profile(self):
        """Navigate to the Twitter profile."""
        url = f"https://x.com/{self.username}"
        logger.info(f"Navigating to {url}")

        try:
            # Navigate with longer timeout
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(self.config.load_delay)

            # Check if we got the profile page
            current_url = self.page.url
            if "browser" in current_url and "supported" in await self.page.content():
                raise Exception("Browser not supported by X.com")

        except Exception as e:
            logger.error(f"Failed to navigate to profile: {e}")
            raise

    async def _handle_access_restrictions(self) -> bool:
        """Handle various access restrictions and bot detection."""
        try:
            # Wait for page to load
            await asyncio.sleep(2)

            # Check for "browser not supported" message
            if (
                await self.page.locator(
                    "text=This browser is no longer supported"
                ).count()
                > 0
            ):
                logger.warning("Browser not supported message detected")

                # Try alternative approaches
                alternatives = [
                    f"https://nitter.net/{self.username}",  # Nitter instance
                    f"https://mobile.twitter.com/{self.username}",  # Mobile version
                ]

                for alt_url in alternatives:
                    try:
                        logger.info(f"Trying alternative URL: {alt_url}")
                        await self.page.goto(alt_url, timeout=15000)
                        await asyncio.sleep(2)

                        if not await self.page.locator(
                            "text=This browser is no longer supported"
                        ).count():
                            logger.info(f"Successfully accessed via {alt_url}")
                            return True
                    except:
                        continue

                return False

            # Check for login requirement
            if await self.page.locator("text=Sign in").count() > 0:
                logger.info("Login required - attempting to view public content")
                # Try to close any modals
                try:
                    await self.page.locator('[aria-label="Close"]').click(timeout=5000)
                except:
                    pass

            # Check for rate limiting
            if await self.page.locator("text=Rate limit exceeded").count() > 0:
                logger.warning("Rate limit detected - waiting before retry")
                await asyncio.sleep(60)  # Wait 1 minute
                return False

            return True

        except Exception as e:
            logger.error(f"Error handling access restrictions: {e}")
            return False

    async def _scrape_tweets(self) -> List[Dict[str, Any]]:
        """Scrape tweets from the current page."""
        tweets = []
        scroll_attempts = 0
        last_tweet_count = 0

        while (
            len(tweets) < self.config.max_tweets
            and scroll_attempts < self.config.max_scroll_attempts
        ):
            try:
                # Wait for tweets to load
                await asyncio.sleep(self.config.scroll_delay)

                # Find tweet elements (multiple selectors for different layouts)
                tweet_selectors = [
                    '[data-testid="tweet"]',
                    'article[role="article"]',
                    '[data-testid="tweetText"]',
                    ".tweet",
                    ".r-1loqt21",  # Common Twitter class
                ]

                tweet_elements = None
                for selector in tweet_selectors:
                    tweet_elements = await self.page.locator(selector).all()
                    if tweet_elements:
                        break

                if not tweet_elements:
                    logger.warning("No tweet elements found with any selector")
                    scroll_attempts += 1
                    await self._scroll_page()
                    continue

                # Process each tweet element
                for element in tweet_elements:
                    if len(tweets) >= self.config.max_tweets:
                        break

                    tweet_data = await self._extract_tweet_data(element)
                    if tweet_data and not self._is_duplicate(tweet_data, tweets):
                        # Filter based on configuration
                        if self._should_include_tweet(tweet_data):
                            tweets.append(tweet_data)

                # Check if we're making progress
                if len(tweets) == last_tweet_count:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0  # Reset if we found new tweets

                last_tweet_count = len(tweets)

                # Scroll to load more tweets
                await self._scroll_page()

            except Exception as e:
                logger.error(f"Error during tweet scraping: {e}")
                scroll_attempts += 1
                await asyncio.sleep(self.config.scroll_delay)

        return tweets

    async def _extract_tweet_data(self, element) -> Optional[Dict[str, Any]]:
        """Extract data from a single tweet element."""
        try:
            # Extract tweet text
            text_selectors = [
                '[data-testid="tweetText"]',
                ".tweet-text",
                "[lang]",
                "span",
            ]

            tweet_text = ""
            for selector in text_selectors:
                try:
                    text_element = element.locator(selector).first
                    if await text_element.count() > 0:
                        tweet_text = await text_element.inner_text()
                        break
                except:
                    continue

            if not tweet_text:
                return None

            # Extract timestamp
            timestamp = await self._extract_timestamp(element)

            # Extract engagement metrics
            metrics = await self._extract_metrics(element)

            # Extract URLs and media
            urls = await self._extract_urls(element)

            # Generate tweet URL (approximate)
            tweet_url = f"https://x.com/{self.username}/status/unknown"

            # Try to extract actual tweet ID and URL
            try:
                time_element = element.locator("time")
                if await time_element.count() > 0:
                    href = await time_element.locator("..").get_attribute("href")
                    if href:
                        tweet_url = (
                            f"https://x.com{href}" if href.startswith("/") else href
                        )
            except:
                pass

            # Build metadata
            metadata = {
                "metrics": metrics,
                "urls": urls,
                "scraper": "twitter_playwright",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }

            return {
                "content": tweet_text.strip(),
                "url": tweet_url,
                "published_at": timestamp,
                "message_type": "post",
                "metadata": metadata,
                "raw_data": {
                    "scraper": "twitter_playwright",
                    "username": self.username,
                },
            }

        except Exception as e:
            logger.error(f"Error extracting tweet data: {e}")
            return None

    async def _extract_timestamp(self, element) -> Optional[datetime]:
        """Extract timestamp from tweet element."""
        try:
            time_element = element.locator("time")
            if await time_element.count() > 0:
                datetime_attr = await time_element.get_attribute("datetime")
                if datetime_attr:
                    return datetime.fromisoformat(datetime_attr.replace("Z", "+00:00"))

                title_attr = await time_element.get_attribute("title")
                if title_attr:
                    return self.parse_date(title_attr)
        except:
            pass

        return datetime.now(timezone.utc)

    async def _extract_metrics(self, element) -> Dict[str, int]:
        """Extract engagement metrics from tweet element."""
        metrics = {"likes": 0, "retweets": 0, "replies": 0, "quotes": 0}

        try:
            # Look for metric elements
            metric_selectors = [
                '[data-testid="like"]',
                '[data-testid="retweet"]',
                '[data-testid="reply"]',
                '[data-testid="unretweet"]',
            ]

            for selector in metric_selectors:
                try:
                    metric_element = element.locator(selector)
                    if await metric_element.count() > 0:
                        text = await metric_element.inner_text()
                        # Extract number from text (e.g., "1.2K" -> 1200)
                        number = self._parse_metric_number(text)

                        if "like" in selector:
                            metrics["likes"] = number
                        elif "retweet" in selector:
                            metrics["retweets"] = number
                        elif "reply" in selector:
                            metrics["replies"] = number
                except:
                    continue

        except Exception as e:
            logger.debug(f"Could not extract metrics: {e}")

        return metrics

    async def _extract_urls(self, element) -> List[str]:
        """Extract URLs from tweet element."""
        urls = []
        try:
            links = element.locator("a[href]")
            link_count = await links.count()

            for i in range(link_count):
                href = await links.nth(i).get_attribute("href")
                if href and href.startswith("http"):
                    urls.append(href)
        except:
            pass

        return urls

    def _parse_metric_number(self, text: str) -> int:
        """Parse metric numbers like '1.2K', '5M', etc."""
        if not text:
            return 0

        # Extract number and suffix
        match = re.search(r"(\d+(?:\.\d+)?)\s*([KMB]?)", text.upper())
        if not match:
            return 0

        number = float(match.group(1))
        suffix = match.group(2)

        multipliers = {"K": 1000, "M": 1000000, "B": 1000000000}
        return int(number * multipliers.get(suffix, 1))

    def _is_duplicate(
        self, tweet: Dict[str, Any], existing_tweets: List[Dict[str, Any]]
    ) -> bool:
        """Check if tweet is duplicate based on content."""
        tweet_content = tweet.get("content", "").strip()
        for existing in existing_tweets:
            if existing.get("content", "").strip() == tweet_content:
                return True
        return False

    def _should_include_tweet(self, tweet: Dict[str, Any]) -> bool:
        """Filter tweets based on configuration."""
        content = tweet.get("content", "")

        # Filter retweets if not wanted
        if not self.config.include_retweets and content.startswith("RT @"):
            return False

        # Filter replies if not wanted
        if not self.config.include_replies and content.startswith("@"):
            return False

        # Filter by date if specified
        if self.config.date_limit_days:
            tweet_date = tweet.get("published_at")
            if tweet_date:
                days_ago = (datetime.now(timezone.utc) - tweet_date).days
                if days_ago > self.config.date_limit_days:
                    return False

        return True

    async def _scroll_page(self):
        """Scroll page to load more content."""
        try:
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(self.config.scroll_delay)
        except Exception as e:
            logger.debug(f"Error scrolling page: {e}")


# Convenience function for easy usage
async def scrape_twitter_profile(
    username: str,
    max_tweets: int = 100,
    max_scroll_attempts: int = 10,
    include_retweets: bool = True,
    include_replies: bool = False,
    date_limit_days: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to scrape a Twitter profile.

    Args:
        username: Twitter username (with or without @)
        max_tweets: Maximum number of tweets to scrape
        max_scroll_attempts: Maximum scroll attempts before giving up
        include_retweets: Whether to include retweets
        include_replies: Whether to include replies
        date_limit_days: Only include tweets from last N days

    Returns:
        List of tweet dictionaries
    """
    config = TwitterScrapingConfig(
        max_tweets=max_tweets,
        max_scroll_attempts=max_scroll_attempts,
        include_retweets=include_retweets,
        include_replies=include_replies,
        date_limit_days=date_limit_days,
    )

    scraper = TwitterPlaywrightScraper(username=username, config=config)

    try:
        await scraper.setup()
        tweets = await scraper.scrape()
        return tweets
    finally:
        await scraper.cleanup()

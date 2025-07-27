#!/usr/bin/env python3
"""
Simple test script for the Twitter Playwright scraper.
Tests core functionality without database dependencies.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from scrapers.twitter_playwright import (
        TwitterPlaywrightScraper,
        TwitterScrapingConfig,
    )
    from loguru import logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


async def test_basic_scraping():
    """Test basic scraping functionality."""
    print("Testing Twitter Playwright Scraper")
    print("=" * 40)

    # Configure scraper with minimal settings
    config = TwitterScrapingConfig(
        max_tweets=5,  # Just a few tweets for testing
        max_scroll_attempts=3,  # Limited scrolling
        scroll_delay=2.0,  # Reasonable delays
        load_delay=3.0,
        include_replies=False,
        include_retweets=True,
    )

    scraper = TwitterPlaywrightScraper(username="reformparty_uk", config=config)

    try:
        print("Setting up browser...")
        await scraper.setup()

        print("Starting scraping...")
        tweets = await scraper.scrape()

        print(f"\nScraping completed!")
        print(f"Tweets found: {len(tweets)}")

        if tweets:
            print("\nFirst tweet sample:")
            tweet = tweets[0]
            print(f"Content: {tweet['content'][:100]}...")
            print(f"URL: {tweet['url']}")
            print(f"Published: {tweet['published_at']}")
            print(f"Metrics: {tweet['metadata']['metrics']}")

            # Save sample to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_tweets_{timestamp}.json"

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(tweets, f, indent=2, ensure_ascii=False, default=str)

            print(f"\nSample saved to: {filename}")
        else:
            print("No tweets found - this might be due to:")
            print("- Bot detection blocking access")
            print("- Network issues")
            print("- X.com structure changes")
            print("- Rate limiting")

    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("Cleaning up...")
        await scraper.cleanup()
        print("Test completed!")


async def test_alternative_approaches():
    """Test different approaches to handle bot detection."""
    print("\n" + "=" * 40)
    print("Testing Alternative Approaches")
    print("=" * 40)

    # Test with different configurations
    test_configs = [
        {
            "name": "Conservative settings",
            "config": TwitterScrapingConfig(
                max_tweets=3, max_scroll_attempts=2, scroll_delay=5.0, load_delay=10.0
            ),
        },
        {
            "name": "Aggressive settings",
            "config": TwitterScrapingConfig(
                max_tweets=2, max_scroll_attempts=1, scroll_delay=1.0, load_delay=2.0
            ),
        },
    ]

    for test in test_configs:
        print(f"\nTesting: {test['name']}")

        scraper = TwitterPlaywrightScraper(
            username="reformparty_uk", config=test["config"]
        )

        try:
            await scraper.setup()
            tweets = await scraper.scrape()
            print(f"  -> Found {len(tweets)} tweets")

        except Exception as e:
            print(f"  -> Error: {e}")

        finally:
            await scraper.cleanup()


if __name__ == "__main__":
    # Check if Playwright is installed
    try:
        import playwright
    except ImportError:
        print("Error: Playwright not installed")
        print("Install with: pip install playwright && playwright install chromium")
        sys.exit(1)

    print("Twitter Playwright Scraper - Simple Test")
    print("=" * 50)
    print()
    print("This test will:")
    print("1. Try to scrape a few tweets from @reformparty_uk")
    print("2. Test different configurations")
    print("3. Save sample data to JSON file")
    print()
    print("Note: X.com has strong bot detection.")
    print("You may need to:")
    print("- Use a VPN")
    print("- Run with headless=False to solve CAPTCHAs")
    print("- Use residential proxies")
    print()

    try:
        asyncio.run(test_basic_scraping())
        asyncio.run(test_alternative_approaches())

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback

        traceback.print_exc()

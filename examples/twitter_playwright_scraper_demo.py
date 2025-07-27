#!/usr/bin/env python3
"""
Demo script for the Playwright-based Twitter scraper.
Shows various usage examples with different parameters.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from scrapers.twitter_playwright import (
    TwitterPlaywrightScraper,
    TwitterScrapingConfig,
    scrape_twitter_profile,
)


async def demo_basic_scraping():
    """Basic scraping example with default settings."""
    print("=== Basic Twitter Scraping Demo ===")

    # Using the convenience function
    tweets = await scrape_twitter_profile(
        username="reformparty_uk", max_tweets=20, max_scroll_attempts=5
    )

    print(f"Scraped {len(tweets)} tweets")
    if tweets:
        print("\nFirst tweet:")
        print(f"Content: {tweets[0]['content'][:100]}...")
        print(f"URL: {tweets[0]['url']}")
        print(f"Published: {tweets[0]['published_at']}")


async def demo_advanced_scraping():
    """Advanced scraping with custom configuration."""
    print("\n=== Advanced Twitter Scraping Demo ===")

    # Custom configuration
    config = TwitterScrapingConfig(
        max_tweets=50,
        max_scroll_attempts=8,
        scroll_delay=3.0,  # Slower scrolling to avoid detection
        load_delay=5.0,  # Wait longer for page loads
        include_replies=False,  # Skip replies
        include_retweets=True,  # Include retweets
        date_limit_days=30,  # Only tweets from last 30 days
    )

    scraper = TwitterPlaywrightScraper(username="reformparty_uk", config=config)

    try:
        await scraper.setup()
        tweets = await scraper.scrape()

        print(f"Scraped {len(tweets)} tweets with advanced config")

        # Analyze the results
        retweets = [t for t in tweets if t["content"].startswith("RT @")]
        original_tweets = [t for t in tweets if not t["content"].startswith("RT @")]

        print(f"Original tweets: {len(original_tweets)}")
        print(f"Retweets: {len(retweets)}")

        # Show engagement metrics
        if tweets:
            avg_likes = sum(
                t["metadata"]["metrics"].get("likes", 0) for t in tweets
            ) / len(tweets)
            avg_retweets = sum(
                t["metadata"]["metrics"].get("retweets", 0) for t in tweets
            ) / len(tweets)

            print(f"Average likes: {avg_likes:.1f}")
            print(f"Average retweets: {avg_retweets:.1f}")

    finally:
        await scraper.cleanup()


async def demo_multiple_accounts():
    """Demo scraping multiple Twitter accounts."""
    print("\n=== Multiple Accounts Scraping Demo ===")

    accounts = [
        "reformparty_uk",
        "Nigel_Farage",  # Reform UK leader
        "TiceRichard",  # Reform UK chairman
    ]

    all_tweets = {}

    for username in accounts:
        print(f"\nScraping @{username}...")

        try:
            tweets = await scrape_twitter_profile(
                username=username,
                max_tweets=10,  # Smaller number for demo
                max_scroll_attempts=3,
                include_replies=False,
            )

            all_tweets[username] = tweets
            print(f"  -> Got {len(tweets)} tweets")

        except Exception as e:
            print(f"  -> Error scraping @{username}: {e}")
            all_tweets[username] = []

    # Summary
    total_tweets = sum(len(tweets) for tweets in all_tweets.values())
    print(f"\nTotal tweets scraped: {total_tweets}")


async def demo_data_export():
    """Demo exporting scraped data to different formats."""
    print("\n=== Data Export Demo ===")

    tweets = await scrape_twitter_profile(
        username="reformparty_uk", max_tweets=15, max_scroll_attempts=3
    )

    if not tweets:
        print("No tweets to export")
        return

    # Export to JSON
    output_dir = "scraped_data"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Full data export
    json_file = f"{output_dir}/reformparty_uk_tweets_{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(tweets, f, indent=2, ensure_ascii=False, default=str)

    print(f"Exported full data to: {json_file}")

    # Simplified CSV-like export
    csv_file = f"{output_dir}/reformparty_uk_simple_{timestamp}.csv"
    with open(csv_file, "w", encoding="utf-8") as f:
        f.write("Date,Content,Likes,Retweets,URL\n")
        for tweet in tweets:
            content = tweet["content"].replace("\n", " ").replace('"', '""')
            metrics = tweet["metadata"]["metrics"]
            f.write(
                f'"{tweet["published_at"]}","{content}",{metrics.get("likes", 0)},{metrics.get("retweets", 0)},"{tweet["url"]}"\n'
            )

    print(f"Exported simple data to: {csv_file}")


async def demo_error_handling():
    """Demo proper error handling and bot detection scenarios."""
    print("\n=== Error Handling Demo ===")

    # Test with invalid username
    print("Testing with invalid username...")
    try:
        tweets = await scrape_twitter_profile(
            username="this_username_definitely_does_not_exist_12345",
            max_tweets=5,
            max_scroll_attempts=2,
        )
        print(f"Result: {len(tweets)} tweets (expected: 0)")
    except Exception as e:
        print(f"Handled error: {e}")

    # Test with very restrictive parameters
    print("\nTesting with very restrictive parameters...")
    try:
        config = TwitterScrapingConfig(
            max_tweets=1,
            max_scroll_attempts=1,
            scroll_delay=0.5,
            load_delay=1.0,
            date_limit_days=1,  # Only today's tweets
        )

        scraper = TwitterPlaywrightScraper(username="reformparty_uk", config=config)
        await scraper.setup()
        tweets = await scraper.scrape()
        await scraper.cleanup()

        print(f"Restrictive scraping result: {len(tweets)} tweets")

    except Exception as e:
        print(f"Handled restrictive scraping error: {e}")


async def main():
    """Run all demo examples."""
    print("Twitter Playwright Scraper Demo")
    print("=" * 50)

    # Note about bot detection
    print("\nIMPORTANT NOTES:")
    print("- X.com has strong bot detection that may block automated access")
    print("- You may need to run with headless=False and manually solve CAPTCHAs")
    print("- Consider using residential proxies or VPN for production usage")
    print("- Respect rate limits and ToS")
    print("\nStarting demos...\n")

    try:
        await demo_basic_scraping()
        await demo_advanced_scraping()
        await demo_multiple_accounts()
        await demo_data_export()
        await demo_error_handling()

    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback

        traceback.print_exc()

    print("\nDemo completed!")


if __name__ == "__main__":
    # Instructions for running
    print("Before running this demo:")
    print("1. Install playwright: pip install playwright")
    print("2. Install browser: playwright install chromium")
    print("3. Run: python examples/twitter_playwright_scraper_demo.py")
    print()

    # Check if we should actually run
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        asyncio.run(main())
    else:
        print("Add --run flag to actually execute the demo")
        print("Example: python examples/twitter_playwright_scraper_demo.py --run")

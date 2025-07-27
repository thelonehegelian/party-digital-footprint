#!/usr/bin/env python3
"""
Advanced test script for the Twitter Playwright scraper.
Tests multiple accounts and different configurations.
"""

import asyncio
import sys
import os
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any

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


async def scrape_account(username: str, max_tweets: int = 10) -> List[Dict[str, Any]]:
    """Scrape a single Twitter account."""
    print(f"\n{'='*50}")
    print(f"Scraping @{username}")
    print(f"{'='*50}")

    config = TwitterScrapingConfig(
        max_tweets=max_tweets,
        max_scroll_attempts=min(max_tweets // 5 + 3, 10),
        scroll_delay=3.0,
        load_delay=5.0,
        include_replies=False,
        include_retweets=True,
        date_limit_days=30,
    )

    scraper = TwitterPlaywrightScraper(username=username, config=config)

    try:
        await scraper.setup()
        tweets = await scraper.scrape()

        print(f"✅ Successfully scraped {len(tweets)} tweets from @{username}")

        if tweets:
            # Show sample
            print(f"\n📝 Sample tweet:")
            tweet = tweets[0]
            print(f"   Content: {tweet['content'][:80]}...")
            print(f"   Likes: {tweet['metadata']['metrics']['likes']}")
            print(f"   Retweets: {tweet['metadata']['metrics']['retweets']}")
            print(f"   Published: {tweet['published_at']}")

        return tweets

    except Exception as e:
        print(f"❌ Error scraping @{username}: {e}")
        return []

    finally:
        await scraper.cleanup()


async def analyze_tweets(
    tweets: List[Dict[str, Any]], account_name: str
) -> Dict[str, Any]:
    """Analyze scraped tweets for insights."""
    if not tweets:
        return {}

    analysis = {
        "account": account_name,
        "total_tweets": len(tweets),
        "total_likes": 0,
        "total_retweets": 0,
        "total_replies": 0,
        "avg_likes": 0,
        "avg_retweets": 0,
        "top_themes": [],
        "engagement_rate": 0,
    }

    # Calculate metrics
    for tweet in tweets:
        metrics = tweet["metadata"]["metrics"]
        analysis["total_likes"] += metrics.get("likes", 0)
        analysis["total_retweets"] += metrics.get("retweets", 0)
        analysis["total_replies"] += metrics.get("replies", 0)

    # Calculate averages
    if tweets:
        analysis["avg_likes"] = analysis["total_likes"] / len(tweets)
        analysis["avg_retweets"] = analysis["total_retweets"] / len(tweets)
        analysis["engagement_rate"] = (
            analysis["total_likes"] + analysis["total_retweets"]
        ) / len(tweets)

    # Simple theme analysis (keyword counting)
    # Generic political keywords - can be customized for specific organizations
    keywords = {
        "economy": 0,
        "tax": 0,
        "healthcare": 0,
        "education": 0,
        "crime": 0,
        "justice": 0,
        "immigration": 0,
        "housing": 0,
        "climate": 0,
        "jobs": 0,
        "brexit": 0,
        "europe": 0,
    }

    for tweet in tweets:
        content = tweet["content"].lower()
        for keyword in keywords:
            if keyword in content:
                keywords[keyword] += 1

    # Get top themes
    sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
    analysis["top_themes"] = [kw for kw, count in sorted_keywords if count > 0][:5]

    return analysis


async def run_comprehensive_test(args):
    """Run comprehensive testing of the Twitter scraper."""
    print("Twitter Playwright Scraper - Comprehensive Test")
    print("=" * 60)

    # Define accounts to test (can be customized)
    test_accounts = {
        "reformparty_uk": "Reform UK (Main)",
        "Nigel_Farage": "Nigel Farage (Leader)",
        "TiceRichard": "Richard Tice (Chairman)",
    }

    # Allow override via command line
    if args.username:
        test_accounts = {args.username: f"{args.username} (Single Account Test)"}

    all_results = {}
    all_analyses = {}

    # Scrape each account
    for username, display_name in test_accounts.items():
        if args.username and username != args.username:
            continue

        tweets = await scrape_account(username, args.max_tweets)
        all_results[username] = tweets

        if tweets:
            analysis = await analyze_tweets(tweets, display_name)
            all_analyses[username] = analysis

    # Generate summary report
    print(f"\n{'='*60}")
    print("SUMMARY REPORT")
    print(f"{'='*60}")

    total_tweets = sum(len(tweets) for tweets in all_results.values())
    print(f"Total tweets scraped: {total_tweets}")

    for username, analysis in all_analyses.items():
        if analysis:
            print(f"\n📊 @{username} Analysis:")
            print(f"   Tweets: {analysis['total_tweets']}")
            print(f"   Avg Likes: {analysis['avg_likes']:.1f}")
            print(f"   Avg Retweets: {analysis['avg_retweets']:.1f}")
            print(f"   Engagement Rate: {analysis['engagement_rate']:.1f}")
            print(f"   Top Themes: {', '.join(analysis['top_themes'])}")

    # Export data
    if args.export_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Export individual files
        for username, tweets in all_results.items():
            if tweets:
                filename = f"{args.export_dir}/{username}_tweets_{timestamp}.json"
                os.makedirs(args.export_dir, exist_ok=True)

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(tweets, f, indent=2, ensure_ascii=False, default=str)

                print(f"📁 Exported {len(tweets)} tweets to {filename}")

        # Export combined analysis
        combined_filename = f"{args.export_dir}/reform_uk_analysis_{timestamp}.json"
        combined_data = {
            "scraped_at": datetime.now().isoformat(),
            "accounts": all_results,
            "analyses": all_analyses,
            "summary": {
                "total_tweets": total_tweets,
                "accounts_scraped": len([t for t in all_results.values() if t]),
            },
        }

        with open(combined_filename, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"📁 Exported combined analysis to {combined_filename}")

    return all_results, all_analyses


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Advanced Twitter Scraper Test")

    parser.add_argument(
        "--username",
        "-u",
        type=str,
        help="Specific username to scrape (default: all Reform UK accounts)",
    )

    parser.add_argument(
        "--max-tweets",
        "-n",
        type=int,
        default=15,
        help="Maximum tweets to scrape per account (default: 15)",
    )

    parser.add_argument(
        "--export-dir",
        "-e",
        type=str,
        default="scraped_data",
        help="Directory to export JSON files (default: scraped_data)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logger.add(sys.stdout, level="DEBUG")
    else:
        logger.add(sys.stdout, level="INFO")

    print("🚀 Starting comprehensive Twitter scraping test...")
    print(f"📊 Target: {args.username if args.username else 'All Reform UK accounts'}")
    print(f"📝 Max tweets per account: {args.max_tweets}")
    print(f"📁 Export directory: {args.export_dir}")
    print()

    try:
        asyncio.run(run_comprehensive_test(args))
        print(f"\n✅ Test completed successfully!")

    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Check if Playwright is installed
    try:
        import playwright
    except ImportError:
        print("❌ Error: Playwright not installed")
        print("Install with: pip install playwright && playwright install chromium")
        sys.exit(1)

    # Show usage if no arguments
    if len(sys.argv) == 1:
        print("Twitter Playwright Scraper - Advanced Test")
        print("=" * 50)
        print()
        print("Usage examples:")
        print()
        print("# Test all Reform UK accounts")
        print("python scripts/test_twitter_scraper_advanced.py")
        print()
        print("# Test specific account with more tweets")
        print("python scripts/test_twitter_scraper_advanced.py -u reformparty_uk -n 25")
        print()
        print("# Test with custom export directory")
        print("python scripts/test_twitter_scraper_advanced.py -e ./exports")
        print()
        print("Add --help for all options")
        sys.exit(0)

    main()

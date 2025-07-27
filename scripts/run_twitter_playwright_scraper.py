#!/usr/bin/env python3
"""
Integration script for running the Playwright Twitter scraper
and importing data into the existing campaign system.
"""

import asyncio
import sys
import os
import argparse
import json
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

# Import with proper path handling
try:
    from scrapers.twitter_playwright import (
        TwitterPlaywrightScraper,
        TwitterScrapingConfig,
    )
    from database import get_db_session
    from models import Message, Party
    from transformers.data_transformer import DataTransformer
    from loguru import logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


async def scrape_and_import_tweets(
    username: str,
    party_name: str = "Reform UK",
    max_tweets: int = 100,
    dry_run: bool = False,
) -> List[Dict[str, Any]]:
    """
    Scrape tweets and import them into the database.

    Args:
        username: Twitter username to scrape
        party_name: Political party name for database association
        max_tweets: Maximum number of tweets to scrape
        dry_run: If True, don't save to database

    Returns:
        List of scraped tweet dictionaries
    """

    # Configure scraper
    config = TwitterScrapingConfig(
        max_tweets=max_tweets,
        max_scroll_attempts=min(max_tweets // 10 + 5, 20),
        scroll_delay=3.0,
        load_delay=5.0,
        include_replies=False,  # Focus on main posts
        include_retweets=True,
        date_limit_days=90,  # Last 3 months
    )

    logger.info(f"Starting Twitter scraping for @{username}")
    logger.info(f"Configuration: max_tweets={max_tweets}, dry_run={dry_run}")

    scraper = TwitterPlaywrightScraper(username=username, config=config)

    try:
        await scraper.setup()
        tweets = await scraper.scrape()

        logger.info(f"Successfully scraped {len(tweets)} tweets")

        if not dry_run and tweets:
            await import_tweets_to_database(tweets, party_name, username)

        return tweets

    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        return []

    finally:
        await scraper.cleanup()


async def import_tweets_to_database(
    tweets: List[Dict[str, Any]], party_name: str, username: str
) -> None:
    """Import scraped tweets into the database."""

    logger.info(f"Importing {len(tweets)} tweets to database")

    # Get database session
    session = next(get_db_session())

    try:
        # Find or create party
        party = session.query(Party).filter(Party.name == party_name).first()
        if not party:
            party = Party(
                name=party_name,
                website=f"https://x.com/{username}",
                description=f"Twitter data for {party_name}",
            )
            session.add(party)
            session.flush()

        imported_count = 0
        skipped_count = 0

        transformer = DataTransformer()

        for tweet_data in tweets:
            try:
                # Check if message already exists
                existing = (
                    session.query(Message)
                    .filter(Message.url == tweet_data["url"])
                    .first()
                )

                if existing:
                    skipped_count += 1
                    continue

                # Transform and create message
                message_data = transformer.transform_twitter_data(tweet_data)

                message = Message(
                    party_id=party.id,
                    content=message_data["content"],
                    url=message_data["url"],
                    published_at=message_data["published_at"],
                    source="twitter",
                    platform="x.com",
                    message_type=message_data.get("message_type", "post"),
                    metadata=message_data.get("metadata", {}),
                    raw_data=message_data.get("raw_data", {}),
                )

                session.add(message)
                imported_count += 1

            except Exception as e:
                logger.error(f"Error importing tweet: {e}")
                continue

        # Commit changes
        session.commit()

        logger.info(
            f"Import completed: {imported_count} new tweets, {skipped_count} skipped"
        )

    except Exception as e:
        logger.error(f"Database import error: {e}")
        session.rollback()
        raise

    finally:
        session.close()


def export_tweets_to_file(tweets: List[Dict[str, Any]], filename: str) -> None:
    """Export tweets to JSON file."""

    logger.info(f"Exporting {len(tweets)} tweets to {filename}")

    # Ensure directory exists
    os.makedirs(
        os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True
    )

    # Prepare export data
    export_data = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "tweet_count": len(tweets),
        "tweets": tweets,
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"Export completed: {filename}")


async def run_reform_uk_scraping(args) -> None:
    """Run scraping for Reform UK accounts."""

    # Define Reform UK related accounts
    reform_accounts = {
        "reformparty_uk": "Reform UK",
        "Nigel_Farage": "Reform UK",
        "TiceRichard": "Reform UK",
    }

    all_tweets = {}

    for username, party_name in reform_accounts.items():
        if args.username and username != args.username:
            continue

        logger.info(f"\n{'='*50}")
        logger.info(f"Scraping @{username} for {party_name}")
        logger.info(f"{'='*50}")

        try:
            tweets = await scrape_and_import_tweets(
                username=username,
                party_name=party_name,
                max_tweets=args.max_tweets,
                dry_run=args.dry_run,
            )

            all_tweets[username] = tweets

            # Export individual file if requested
            if args.export_dir:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{args.export_dir}/{username}_tweets_{timestamp}.json"
                export_tweets_to_file(tweets, filename)

            # Add delay between accounts to be respectful
            if len(reform_accounts) > 1:
                logger.info("Waiting 30 seconds before next account...")
                await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"Failed to scrape @{username}: {e}")
            all_tweets[username] = []

    # Summary
    total_tweets = sum(len(tweets) for tweets in all_tweets.values())
    logger.info(f"\n{'='*50}")
    logger.info(f"SCRAPING SUMMARY")
    logger.info(f"{'='*50}")

    for username, tweets in all_tweets.items():
        logger.info(f"@{username}: {len(tweets)} tweets")

    logger.info(f"Total tweets scraped: {total_tweets}")

    # Export combined file
    if args.export_dir and total_tweets > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_filename = f"{args.export_dir}/reform_uk_combined_{timestamp}.json"

        combined_data = {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "accounts": all_tweets,
            "total_tweets": total_tweets,
        }

        with open(combined_filename, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Combined export: {combined_filename}")


def main():
    """Main entry point."""

    parser = argparse.ArgumentParser(
        description="Twitter Playwright Scraper for Campaign Data"
    )

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
        default=100,
        help="Maximum tweets to scrape per account (default: 100)",
    )

    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Run scraping without saving to database",
    )

    parser.add_argument(
        "--export-dir",
        "-e",
        type=str,
        default="scraped_data",
        help="Directory to export JSON files (default: scraped_data)",
    )

    parser.add_argument(
        "--party-name",
        "-p",
        type=str,
        default="Reform UK",
        help="Party name for database association (default: Reform UK)",
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

    # Run scraping
    try:
        if args.username:
            # Single account
            asyncio.run(
                scrape_and_import_tweets(
                    username=args.username,
                    party_name=args.party_name,
                    max_tweets=args.max_tweets,
                    dry_run=args.dry_run,
                )
            )
        else:
            # All Reform UK accounts
            asyncio.run(run_reform_uk_scraping(args))

    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Installation check
    try:
        import playwright
    except ImportError:
        print("Error: Playwright not installed")
        print("Install with: pip install playwright && playwright install chromium")
        sys.exit(1)

    print("Twitter Playwright Scraper")
    print("=" * 30)
    print()

    # Show usage examples
    if len(sys.argv) == 1:
        print("Usage examples:")
        print()
        print("# Scrape Reform UK main account (dry run)")
        print(
            "python scripts/run_twitter_playwright_scraper.py -u reformparty_uk --dry-run"
        )
        print()
        print("# Scrape all Reform UK accounts, save to database")
        print("python scripts/run_twitter_playwright_scraper.py -n 50")
        print()
        print("# Scrape with custom export directory")
        print(
            "python scripts/run_twitter_playwright_scraper.py -u reformparty_uk -e ./exports"
        )
        print()
        print("Add --help for all options")
        sys.exit(0)

    main()

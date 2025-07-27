#!/usr/bin/env python3
"""
Generic Twitter scraper integration script for campaign data collection.
Can be configured for any political party or organization.
"""

import asyncio
import sys
import os
import argparse
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

# Import with proper path handling
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


# Database imports (optional for dry-run mode)
try:
    from database import get_db_session
    from models import Message, Party
    from transformers.data_transformer import DataTransformer

    DATABASE_AVAILABLE = True
except ImportError:
    logger.warning("Database modules not available - running in export-only mode")
    DATABASE_AVAILABLE = False


async def scrape_twitter_account(
    username: str,
    organization_name: str,
    max_tweets: int = 100,
    config_override: Optional[TwitterScrapingConfig] = None,
) -> List[Dict[str, Any]]:
    """
    Scrape tweets from a single Twitter account.

    Args:
        username: Twitter username to scrape
        organization_name: Organization name for metadata
        max_tweets: Maximum number of tweets to scrape
        config_override: Optional configuration override

    Returns:
        List of scraped tweet dictionaries
    """

    # Configure scraper
    config = config_override or TwitterScrapingConfig(
        max_tweets=max_tweets,
        max_scroll_attempts=min(max_tweets // 10 + 5, 20),
        scroll_delay=3.0,
        load_delay=5.0,
        include_replies=False,  # Focus on main posts
        include_retweets=True,
        date_limit_days=90,  # Last 3 months
    )

    logger.info(f"Starting Twitter scraping for @{username}")
    logger.info(f"Organization: {organization_name}")
    logger.info(f"Configuration: max_tweets={max_tweets}")

    scraper = TwitterPlaywrightScraper(username=username, config=config)

    try:
        await scraper.setup()
        tweets = await scraper.scrape()

        logger.info(f"Successfully scraped {len(tweets)} tweets from @{username}")

        # Add organization metadata
        for tweet in tweets:
            tweet["raw_data"]["organization"] = organization_name
            tweet["raw_data"]["account_type"] = (
                "primary" if username == username else "related"
            )

        return tweets

    except Exception as e:
        logger.error(f"Error scraping @{username}: {e}")
        return []

    finally:
        await scraper.cleanup()


async def import_tweets_to_database(
    tweets: List[Dict[str, Any]], organization_name: str, username: str
) -> None:
    """Import scraped tweets into the database (if available)."""

    if not DATABASE_AVAILABLE:
        logger.warning("Database not available - skipping import")
        return

    logger.info(f"Importing {len(tweets)} tweets to database")

    # Get database session
    session = next(get_db_session())

    try:
        # Find or create party/organization
        party = session.query(Party).filter(Party.name == organization_name).first()
        if not party:
            party = Party(
                name=organization_name,
                website=f"https://x.com/{username}",
                description=f"Twitter data for {organization_name}",
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


def load_account_config(config_file: str) -> Dict[str, Any]:
    """Load account configuration from JSON file."""
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        sys.exit(1)


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


async def run_multi_account_scraping(config: Dict[str, Any], args) -> None:
    """Run scraping for multiple accounts based on configuration."""

    organization_name = config.get("organization", "Unknown Organization")
    accounts = config.get("accounts", {})

    if not accounts:
        logger.error("No accounts specified in configuration")
        return

    all_tweets = {}

    for username, account_info in accounts.items():
        if args.username and username != args.username:
            continue

        logger.info(f"\n{'='*50}")
        logger.info(f"Scraping @{username}")
        logger.info(f"Organization: {organization_name}")
        logger.info(f"Account Type: {account_info.get('type', 'unknown')}")
        logger.info(f"{'='*50}")

        try:
            tweets = await scrape_twitter_account(
                username=username,
                organization_name=organization_name,
                max_tweets=args.max_tweets,
            )

            all_tweets[username] = tweets

            # Import to database if not dry run
            if not args.dry_run and tweets and DATABASE_AVAILABLE:
                await import_tweets_to_database(tweets, organization_name, username)

            # Export individual file if requested
            if args.export_dir:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{args.export_dir}/{username}_tweets_{timestamp}.json"
                export_tweets_to_file(tweets, filename)

            # Add delay between accounts to be respectful
            if len(accounts) > 1:
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
    logger.info(f"Organization: {organization_name}")

    # Export combined file
    if args.export_dir and total_tweets > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        org_slug = organization_name.lower().replace(" ", "_")
        combined_filename = f"{args.export_dir}/{org_slug}_combined_{timestamp}.json"

        combined_data = {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "organization": organization_name,
            "accounts": all_tweets,
            "total_tweets": total_tweets,
        }

        with open(combined_filename, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Combined export: {combined_filename}")


def create_sample_configs():
    """Create sample configuration files for different organizations."""

    configs = {
        "reform_uk_config.json": {
            "organization": "Reform UK",
            "description": "British political party founded in 2019",
            "accounts": {
                "reformparty_uk": {
                    "type": "main_account",
                    "description": "Official Reform UK account",
                },
                "Nigel_Farage": {"type": "leader", "description": "Party leader"},
                "TiceRichard": {"type": "chairman", "description": "Party chairman"},
            },
        },
        "labour_config.json": {
            "organization": "Labour Party",
            "description": "British Labour Party",
            "accounts": {
                "UKLabour": {
                    "type": "main_account",
                    "description": "Official Labour Party account",
                },
                "Keir_Starmer": {"type": "leader", "description": "Party leader"},
            },
        },
        "conservative_config.json": {
            "organization": "Conservative Party",
            "description": "British Conservative and Unionist Party",
            "accounts": {
                "Conservatives": {
                    "type": "main_account",
                    "description": "Official Conservative Party account",
                }
            },
        },
    }

    config_dir = "config/twitter_accounts"
    os.makedirs(config_dir, exist_ok=True)

    for filename, config in configs.items():
        filepath = os.path.join(config_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"Created sample config: {filepath}")


def main():
    """Main entry point."""

    parser = argparse.ArgumentParser(
        description="Generic Twitter Scraper for Campaign Data"
    )

    parser.add_argument(
        "--config", "-c", type=str, help="JSON config file with account definitions"
    )

    parser.add_argument(
        "--username",
        "-u",
        type=str,
        help="Specific username to scrape (default: all accounts in config)",
    )

    parser.add_argument(
        "--organization",
        "-o",
        type=str,
        help="Organization name (required if not using config file)",
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
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--create-sample-configs",
        action="store_true",
        help="Create sample configuration files and exit",
    )

    args = parser.parse_args()

    # Create sample configs if requested
    if args.create_sample_configs:
        create_sample_configs()
        print("\nSample configuration files created in config/twitter_accounts/")
        print(
            "Edit these files to customize account lists for different organizations."
        )
        sys.exit(0)

    # Configure logging
    if args.verbose:
        logger.add(sys.stdout, level="DEBUG")
    else:
        logger.add(sys.stdout, level="INFO")

    # Determine scraping mode
    if args.config:
        # Multi-account mode with config file
        config = load_account_config(args.config)
        asyncio.run(run_multi_account_scraping(config, args))

    elif args.username and args.organization:
        # Single account mode
        async def single_account_scraping():
            tweets = await scrape_twitter_account(
                username=args.username,
                organization_name=args.organization,
                max_tweets=args.max_tweets,
            )

            if not args.dry_run and tweets and DATABASE_AVAILABLE:
                await import_tweets_to_database(
                    tweets, args.organization, args.username
                )

            if args.export_dir:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{args.export_dir}/{args.username}_tweets_{timestamp}.json"
                export_tweets_to_file(tweets, filename)

        asyncio.run(single_account_scraping())

    else:
        print("Error: Must specify either --config file or --username + --organization")
        print("\nUsage examples:")
        print("# Use config file for multiple accounts")
        print(
            "python scripts/run_twitter_scraper_generic.py -c config/twitter_accounts/reform_uk_config.json"
        )
        print()
        print("# Single account scraping")
        print(
            "python scripts/run_twitter_scraper_generic.py -u reformparty_uk -o 'Reform UK'"
        )
        print()
        print("# Create sample config files")
        print("python scripts/run_twitter_scraper_generic.py --create-sample-configs")
        sys.exit(1)


if __name__ == "__main__":
    # Check if Playwright is installed
    try:
        import playwright
    except ImportError:
        print("Error: Playwright not installed")
        print("Install with: pip install playwright && playwright install chromium")
        sys.exit(1)

    print("Generic Twitter Scraper for Campaign Data")
    print("=" * 50)
    print()

    # Show usage examples if no arguments
    if len(sys.argv) == 1:
        print("Usage examples:")
        print()
        print("# Create sample configuration files")
        print("python scripts/run_twitter_scraper_generic.py --create-sample-configs")
        print()
        print("# Scrape using config file")
        print(
            "python scripts/run_twitter_scraper_generic.py -c config/twitter_accounts/reform_uk_config.json"
        )
        print()
        print("# Scrape single account")
        print(
            "python scripts/run_twitter_scraper_generic.py -u reformparty_uk -o 'Reform UK' --dry-run"
        )
        print()
        print("# Scrape with custom export directory")
        print(
            "python scripts/run_twitter_scraper_generic.py -u UKLabour -o 'Labour Party' -e ./exports"
        )
        print()
        print("Add --help for all options")
        sys.exit(0)

    main()

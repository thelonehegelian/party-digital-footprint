#!/usr/bin/env python3
"""
Twitter Scraping to API Pipeline

This script orchestrates the Twitter scraping process and submits data to the backend API.
It handles data transformation, error recovery, and provides comprehensive logging.

Usage:
    python scripts/twitter_pipeline.py --config configs/twitter_pipeline.json
    python scripts/twitter_pipeline.py --username @politicalparty --party-id 1
"""

import asyncio
import json
import argparse
import sys
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests
from loguru import logger

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.scrapers.twitter_playwright import TwitterPlaywrightScraper, TwitterScrapingConfig


class TwitterPipelineConfig:
    """Configuration for Twitter pipeline execution."""
    
    def __init__(self, config_data: Dict[str, Any]):
        self.api_base_url = config_data.get("api_base_url", "http://localhost:8000")
        self.party_id = config_data.get("party_id", 1)
        self.username = config_data.get("username", "")
        self.max_tweets = config_data.get("max_tweets", 50)
        self.max_scroll_attempts = config_data.get("max_scroll_attempts", 10)
        self.include_retweets = config_data.get("include_retweets", True)
        self.include_replies = config_data.get("include_replies", False)
        self.date_limit_days = config_data.get("date_limit_days", None)
        self.retry_attempts = config_data.get("retry_attempts", 3)
        self.retry_delay = config_data.get("retry_delay", 5)
        self.batch_size = config_data.get("batch_size", 25)
        
    @classmethod
    def from_file(cls, config_path: str) -> 'TwitterPipelineConfig':
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        return cls(config_data)
    
    @classmethod
    def from_args(cls, username: str, party_id: int, **kwargs) -> 'TwitterPipelineConfig':
        """Create configuration from command line arguments."""
        config_data = {
            "username": username,
            "party_id": party_id,
            **kwargs
        }
        return cls(config_data)


class TwitterToApiPipeline:
    """Main pipeline class for Twitter scraping to API submission."""
    
    def __init__(self, config: TwitterPipelineConfig):
        self.config = config
        self.scraper = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TwitterPipeline/1.0'
        })
        
    async def run(self) -> Dict[str, Any]:
        """Execute the complete pipeline."""
        logger.info(f"Starting Twitter pipeline for @{self.config.username}")
        
        start_time = time.time()
        results = {
            "status": "success",
            "username": self.config.username,
            "party_id": self.config.party_id,
            "tweets_scraped": 0,
            "tweets_submitted": 0,
            "tweets_skipped": 0,
            "errors": [],
            "execution_time": 0
        }
        
        try:
            # Step 1: Verify API connectivity
            if not self._verify_api_connection():
                raise Exception("Cannot connect to API")
            
            # Step 2: Verify party exists
            if not self._verify_party_exists():
                raise Exception(f"Party ID {self.config.party_id} not found")
            
            # Step 3: Run Twitter scraper
            scraped_tweets = await self._run_scraper()
            results["tweets_scraped"] = len(scraped_tweets)
            
            if not scraped_tweets:
                logger.warning("No tweets scraped - pipeline completed with no data")
                results["status"] = "warning"
                return results
            
            # Step 4: Transform and submit data
            submission_result = await self._submit_tweets(scraped_tweets)
            results["tweets_submitted"] = submission_result["imported_count"]
            results["tweets_skipped"] = submission_result["skipped_count"]
            
            if submission_result["errors"]:
                results["errors"].extend(submission_result["errors"])
                if submission_result["imported_count"] == 0:
                    results["status"] = "error"
                else:
                    results["status"] = "partial"
            
            logger.info(f"Pipeline completed: {results['tweets_submitted']} submitted, {results['tweets_skipped']} skipped")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results["status"] = "error"
            results["errors"].append({"error": str(e), "stage": "pipeline"})
            
        finally:
            results["execution_time"] = time.time() - start_time
            if self.scraper:
                await self.scraper.cleanup()
        
        return results
    
    def _verify_api_connection(self) -> bool:
        """Verify that the API is accessible."""
        try:
            response = self.session.get(f"{self.config.api_base_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("API connection verified")
                return True
            else:
                logger.error(f"API health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Cannot connect to API: {e}")
            return False
    
    def _verify_party_exists(self) -> bool:
        """Verify that the specified party exists and is active."""
        try:
            response = self.session.get(
                f"{self.config.api_base_url}/api/v1/parties/{self.config.party_id}",
                timeout=10
            )
            if response.status_code == 200:
                party_data = response.json()
                if party_data.get("active", False):
                    logger.info(f"Party verified: {party_data.get('name')}")
                    return True
                else:
                    logger.error(f"Party {self.config.party_id} is not active")
                    return False
            else:
                logger.error(f"Party verification failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error verifying party: {e}")
            return False
    
    async def _run_scraper(self) -> List[Dict[str, Any]]:
        """Run the Twitter scraper and return formatted tweets."""
        logger.info(f"Starting Twitter scraper for @{self.config.username}")
        
        # Create scraper configuration
        scraper_config = TwitterScrapingConfig(
            max_tweets=self.config.max_tweets,
            max_scroll_attempts=self.config.max_scroll_attempts,
            include_retweets=self.config.include_retweets,
            include_replies=self.config.include_replies,
            date_limit_days=self.config.date_limit_days
        )
        
        # Initialize and run scraper
        self.scraper = TwitterPlaywrightScraper(
            username=self.config.username,
            config=scraper_config
        )
        
        try:
            await self.scraper.setup()
            tweets = await self.scraper.scrape()
            logger.info(f"Scraped {len(tweets)} tweets from @{self.config.username}")
            return tweets
        except Exception as e:
            logger.error(f"Scraper failed: {e}")
            raise
    
    async def _submit_tweets(self, tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform and submit tweets to the API."""
        logger.info(f"Submitting {len(tweets)} tweets to API")
        
        # Transform tweets to API format
        api_messages = []
        for tweet in tweets:
            try:
                api_message = self._transform_tweet_to_api_format(tweet)
                api_messages.append(api_message)
            except Exception as e:
                logger.warning(f"Failed to transform tweet: {e}")
                continue
        
        if not api_messages:
            return {"imported_count": 0, "skipped_count": 0, "errors": []}
        
        # Submit in batches
        total_imported = 0
        total_skipped = 0
        all_errors = []
        
        for i in range(0, len(api_messages), self.config.batch_size):
            batch = api_messages[i:i + self.config.batch_size]
            batch_result = await self._submit_batch(batch)
            
            total_imported += batch_result["imported_count"]
            total_skipped += batch_result["skipped_count"]
            all_errors.extend(batch_result["errors"])
            
            # Brief pause between batches
            if i + self.config.batch_size < len(api_messages):
                await asyncio.sleep(1)
        
        return {
            "imported_count": total_imported,
            "skipped_count": total_skipped,
            "errors": all_errors
        }
    
    def _transform_tweet_to_api_format(self, tweet: Dict[str, Any]) -> Dict[str, Any]:
        """Transform scraped tweet data to API message format."""
        # Parse published date
        published_at = None
        if tweet.get("published_at"):
            if isinstance(tweet["published_at"], str):
                try:
                    published_at = datetime.fromisoformat(tweet["published_at"].replace('Z', '+00:00'))
                except:
                    published_at = datetime.now(timezone.utc)
            else:
                published_at = tweet["published_at"]
        else:
            published_at = datetime.now(timezone.utc)
        
        # Determine geographic scope from content
        geographic_scope = self._determine_geographic_scope(tweet["content"])
        
        return {
            "source_name": f"@{self.config.username}",
            "source_type": "twitter",
            "source_url": f"https://x.com/{self.config.username}",
            "content": tweet["content"],
            "url": tweet.get("url"),
            "published_at": published_at.isoformat(),
            "message_type": tweet.get("message_type", "post"),
            "geographic_scope": geographic_scope,
            "metadata": {
                "metrics": tweet.get("metadata", {}).get("metrics", {}),
                "urls": tweet.get("metadata", {}).get("urls", []),
                "scraper": "twitter_playwright_pipeline",
                "pipeline_version": "1.0",
                "scraped_at": tweet.get("metadata", {}).get("scraped_at")
            },
            "raw_data": tweet.get("raw_data", {})
        }
    
    def _determine_geographic_scope(self, content: str) -> str:
        """Determine geographic scope from tweet content."""
        content_lower = content.lower()
        
        # Local indicators
        local_keywords = [
            "constituency", "local", "ward", "council", "mayor", "town", "city",
            "neighbourhood", "community", "residents", "voters in"
        ]
        
        # Regional indicators  
        regional_keywords = [
            "region", "county", "district", "scotland", "wales", "northern ireland",
            "yorkshire", "midlands", "north", "south", "east", "west"
        ]
        
        # Check for local scope
        if any(keyword in content_lower for keyword in local_keywords):
            return "local"
        
        # Check for regional scope
        if any(keyword in content_lower for keyword in regional_keywords):
            return "regional"
        
        # Default to national
        return "national"
    
    async def _submit_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Submit a batch of messages to the API with retry logic."""
        payload = {"messages": batch}
        
        for attempt in range(self.config.retry_attempts):
            try:
                response = self.session.post(
                    f"{self.config.api_base_url}/api/v1/messages/bulk",
                    params={"party_id": self.config.party_id},
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Batch submitted: {result['imported_count']} imported, {result['skipped_count']} skipped")
                    return result
                else:
                    logger.warning(f"API returned {response.status_code}: {response.text}")
                    if response.status_code < 500:  # Don't retry client errors
                        break
                        
            except Exception as e:
                logger.warning(f"Batch submission attempt {attempt + 1} failed: {e}")
                
            if attempt < self.config.retry_attempts - 1:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        return {"imported_count": 0, "skipped_count": 0, "errors": [{"error": "All retry attempts failed"}]}


async def main():
    """Main entry point for the Twitter pipeline script."""
    parser = argparse.ArgumentParser(description="Twitter to API Pipeline")
    parser.add_argument("--config", help="Path to configuration JSON file")
    parser.add_argument("--username", help="Twitter username (without @)")
    parser.add_argument("--party-id", type=int, help="Political party ID")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--max-tweets", type=int, default=50, help="Maximum tweets to scrape")
    parser.add_argument("--batch-size", type=int, default=25, help="API submission batch size")
    parser.add_argument("--include-retweets", action="store_true", help="Include retweets")
    parser.add_argument("--include-replies", action="store_true", help="Include replies")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger.remove()
    logger.add(sys.stderr, level=log_level, format="{time} | {level} | {message}")
    
    # Load configuration
    if args.config:
        if not Path(args.config).exists():
            logger.error(f"Configuration file not found: {args.config}")
            sys.exit(1)
        config = TwitterPipelineConfig.from_file(args.config)
    else:
        if not args.username or args.party_id is None:
            logger.error("Either --config or both --username and --party-id must be provided")
            sys.exit(1)
        
        config = TwitterPipelineConfig.from_args(
            username=args.username.replace("@", ""),
            party_id=args.party_id,
            api_base_url=args.api_url,
            max_tweets=args.max_tweets,
            batch_size=args.batch_size,
            include_retweets=args.include_retweets,
            include_replies=args.include_replies
        )
    
    # Run pipeline
    pipeline = TwitterToApiPipeline(config)
    results = await pipeline.run()
    
    # Output results
    logger.info("=" * 50)
    logger.info("PIPELINE EXECUTION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Status: {results['status']}")
    logger.info(f"Username: @{results['username']}")
    logger.info(f"Party ID: {results['party_id']}")
    logger.info(f"Tweets scraped: {results['tweets_scraped']}")
    logger.info(f"Tweets submitted: {results['tweets_submitted']}")
    logger.info(f"Tweets skipped: {results['tweets_skipped']}")
    logger.info(f"Execution time: {results['execution_time']:.2f}s")
    
    if results['errors']:
        logger.error(f"Errors encountered: {len(results['errors'])}")
        for error in results['errors']:
            logger.error(f"  - {error}")
    
    # Exit with appropriate code
    if results['status'] == 'error':
        sys.exit(1)
    elif results['status'] == 'partial':
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import tweepy
from loguru import logger

from .base import BaseScraper


class TwitterScraper(BaseScraper):
    """Scraper for Twitter/X content using Tweepy."""
    
    def __init__(self, username: str = "reformparty_uk", **kwargs):
        super().__init__(**kwargs)
        self.username = username
        self.client = None
        self.user_id = None
    
    async def setup(self):
        """Initialize Twitter API client."""
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        if not bearer_token:
            logger.warning("Twitter Bearer Token not found. Skipping Twitter scraping.")
            return
        
        try:
            self.client = tweepy.Client(bearer_token=bearer_token)
            
            # Get user ID
            user = self.client.get_user(username=self.username)
            if user.data:
                self.user_id = user.data.id
                logger.info(f"Found Twitter user: {self.username} (ID: {self.user_id})")
            else:
                logger.error(f"Twitter user not found: {self.username}")
                
        except Exception as e:
            logger.error(f"Error setting up Twitter client: {e}")
            self.client = None
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape tweets from Reform UK Twitter account."""
        if not self.client or not self.user_id:
            logger.warning("Twitter client not initialized. Skipping Twitter scraping.")
            return []
        
        messages = []
        
        try:
            # Get recent tweets
            tweets = self.client.get_users_tweets(
                id=self.user_id,
                max_results=100,  # Maximum allowed per request
                tweet_fields=['created_at', 'public_metrics', 'context_annotations', 'entities', 'referenced_tweets'],
                expansions=['referenced_tweets.id', 'author_id']
            )
            
            if not tweets.data:
                logger.info("No tweets found")
                return messages
            
            logger.info(f"Retrieved {len(tweets.data)} tweets")
            
            for tweet in tweets.data:
                message_data = self.process_tweet(tweet)
                if message_data:
                    messages.append(message_data)
            
            # Get older tweets using pagination
            while tweets.meta.get('next_token') and len(messages) < 500:
                try:
                    tweets = self.client.get_users_tweets(
                        id=self.user_id,
                        max_results=100,
                        pagination_token=tweets.meta['next_token'],
                        tweet_fields=['created_at', 'public_metrics', 'context_annotations', 'entities', 'referenced_tweets'],
                        expansions=['referenced_tweets.id', 'author_id']
                    )
                    
                    if tweets.data:
                        for tweet in tweets.data:
                            message_data = self.process_tweet(tweet)
                            if message_data:
                                messages.append(message_data)
                    
                    # Rate limiting delay
                    await asyncio.sleep(self.delay)
                    
                except Exception as e:
                    logger.error(f"Error getting paginated tweets: {e}")
                    break
        
        except Exception as e:
            logger.error(f"Error scraping Twitter: {e}")
        
        logger.info(f"Scraped {len(messages)} tweets from @{self.username}")
        return messages
    
    def process_tweet(self, tweet) -> Optional[Dict[str, Any]]:
        """Process a single tweet into message format."""
        try:
            # Extract hashtags and mentions
            hashtags = []
            mentions = []
            urls = []
            
            if hasattr(tweet, 'entities') and tweet.entities:
                if 'hashtags' in tweet.entities:
                    hashtags = [tag['tag'] for tag in tweet.entities['hashtags']]
                
                if 'mentions' in tweet.entities:
                    mentions = [mention['username'] for mention in tweet.entities['mentions']]
                
                if 'urls' in tweet.entities:
                    urls = [url['expanded_url'] for url in tweet.entities['urls'] if url.get('expanded_url')]
            
            # Get public metrics
            metrics = {}
            if hasattr(tweet, 'public_metrics') and tweet.public_metrics:
                metrics = {
                    'retweet_count': tweet.public_metrics.get('retweet_count', 0),
                    'like_count': tweet.public_metrics.get('like_count', 0),
                    'reply_count': tweet.public_metrics.get('reply_count', 0),
                    'quote_count': tweet.public_metrics.get('quote_count', 0)
                }
            
            # Determine tweet type
            message_type = 'post'
            if hasattr(tweet, 'referenced_tweets') and tweet.referenced_tweets:
                ref_type = tweet.referenced_tweets[0].type
                if ref_type == 'retweeted':
                    message_type = 'retweet'
                elif ref_type == 'replied_to':
                    message_type = 'reply'
                elif ref_type == 'quoted':
                    message_type = 'quote_tweet'
            
            # Build metadata
            metadata = {
                'hashtags': hashtags,
                'mentions': mentions,
                'urls': urls,
                'metrics': metrics,
                'tweet_type': message_type
            }
            
            # Context annotations (topics/entities Twitter identifies)
            if hasattr(tweet, 'context_annotations') and tweet.context_annotations:
                metadata['context_annotations'] = [
                    {
                        'domain': ann.domain.name if ann.domain else None,
                        'entity': ann.entity.name if ann.entity else None
                    }
                    for ann in tweet.context_annotations
                ]
            
            return {
                'content': tweet.text,
                'url': f"https://twitter.com/{self.username}/status/{tweet.id}",
                'published_at': tweet.created_at,
                'message_type': message_type,
                'metadata': metadata,
                'raw_data': {
                    'tweet_id': str(tweet.id),
                    'author_id': str(tweet.author_id) if tweet.author_id else None,
                    'scraper': 'twitter'
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing tweet {tweet.id}: {e}")
            return None
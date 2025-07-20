import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
import asyncio
from loguru import logger

from .base import BaseScraper


class FacebookScraper(BaseScraper):
    """Scraper for Facebook content using Graph API."""
    
    def __init__(self, page_id: str = "ReformPartyUK", **kwargs):
        super().__init__(**kwargs)
        self.page_id = page_id
        self.access_token = None
        self.base_url = "https://graph.facebook.com/v18.0"
    
    async def setup(self):
        """Initialize Facebook API access."""
        self.access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
        
        if not self.access_token:
            logger.warning("Facebook Access Token not found. Skipping Facebook scraping.")
            return
        
        # Test API access
        try:
            test_url = f"{self.base_url}/me"
            params = {'access_token': self.access_token}
            response = requests.get(test_url, params=params)
            
            if response.status_code == 200:
                logger.info("Facebook API access verified")
            else:
                logger.error(f"Facebook API test failed: {response.status_code}")
                self.access_token = None
                
        except Exception as e:
            logger.error(f"Error testing Facebook API: {e}")
            self.access_token = None
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape posts from Reform UK Facebook page."""
        if not self.access_token:
            logger.warning("Facebook API not initialized. Skipping Facebook scraping.")
            return []
        
        messages = []
        
        try:
            # Get page posts
            url = f"{self.base_url}/{self.page_id}/posts"
            params = {
                'access_token': self.access_token,
                'fields': 'id,message,story,created_time,updated_time,type,link,name,caption,description,picture,source,place,privacy,shares,likes.summary(true),comments.summary(true)',
                'limit': 100
            }
            
            while len(messages) < 500:  # Limit total posts
                response = requests.get(url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Facebook API error: {response.status_code} - {response.text}")
                    break
                
                data = response.json()
                
                if 'data' not in data or not data['data']:
                    break
                
                for post in data['data']:
                    message_data = self.process_post(post)
                    if message_data:
                        messages.append(message_data)
                
                # Check for next page
                if 'paging' in data and 'next' in data['paging']:
                    url = data['paging']['next']
                    params = {}  # URL already includes parameters
                else:
                    break
                
                await asyncio.sleep(self.delay)
        
        except Exception as e:
            logger.error(f"Error scraping Facebook: {e}")
        
        logger.info(f"Scraped {len(messages)} posts from Facebook page {self.page_id}")
        return messages
    
    def process_post(self, post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single Facebook post into message format."""
        try:
            post_id = post.get('id', '')
            
            # Extract content (message or story)
            content = post.get('message', '') or post.get('story', '')
            
            if not content:
                logger.debug(f"Skipping post {post_id} - no content")
                return None
            
            # Parse created time
            created_time_str = post.get('created_time', '')
            published_at = None
            if created_time_str:
                try:
                    published_at = datetime.fromisoformat(created_time_str.replace('Z', '+00:00'))
                except ValueError:
                    logger.warning(f"Could not parse Facebook date: {created_time_str}")
            
            # Extract engagement metrics
            likes_count = 0
            comments_count = 0
            shares_count = 0
            
            if 'likes' in post and 'summary' in post['likes']:
                likes_count = post['likes']['summary'].get('total_count', 0)
            
            if 'comments' in post and 'summary' in post['comments']:
                comments_count = post['comments']['summary'].get('total_count', 0)
            
            if 'shares' in post:
                shares_count = post['shares'].get('count', 0)
            
            # Build metadata
            metadata = {
                'post_type': post.get('type', 'status'),
                'engagement': {
                    'likes': likes_count,
                    'comments': comments_count,
                    'shares': shares_count
                }
            }
            
            # Add link information if present
            if post.get('link'):
                metadata['link'] = {
                    'url': post.get('link'),
                    'name': post.get('name'),
                    'caption': post.get('caption'),
                    'description': post.get('description')
                }
            
            # Add media information
            if post.get('picture'):
                metadata['media'] = {
                    'picture': post.get('picture'),
                    'source': post.get('source')
                }
            
            # Add location if present
            if post.get('place'):
                metadata['place'] = post['place']
            
            # Construct post URL
            post_url = f"https://www.facebook.com/{self.page_id}/posts/{post_id.split('_')[1]}" if '_' in post_id else f"https://www.facebook.com/{post_id}"
            
            return {
                'content': content,
                'url': post_url,
                'published_at': published_at,
                'message_type': 'post',
                'metadata': metadata,
                'raw_data': {
                    'post_id': post_id,
                    'scraper': 'facebook',
                    'raw_post': post
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing Facebook post: {e}")
            return None
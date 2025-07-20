"""
Data transformation utilities for converting scraped data to API format.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import re

from ..api.schemas import MessageInput, ScrapedMessage


class DataTransformer:
    """Base class for data transformation utilities."""
    
    def __init__(self, source_name: str, source_url: str = None):
        self.source_name = source_name
        self.source_url = source_url
    
    def clean_content(self, content: str) -> str:
        """Clean and normalize content text."""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content.strip())
        
        # Remove null bytes and other problematic characters
        content = content.replace('\x00', '').replace('\r', '\n')
        
        # Limit length
        if len(content) > 10000:
            content = content[:9997] + "..."
        
        return content
    
    def parse_date(self, date_input: Any) -> Optional[datetime]:
        """Parse various date formats to datetime."""
        if not date_input:
            return None
        
        if isinstance(date_input, datetime):
            return date_input
        
        if isinstance(date_input, str):
            # Common date formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%d %b %Y",
                "%B %d, %Y"
            ]
            
            # Handle Z suffix
            if date_input.endswith('Z'):
                date_input = date_input[:-1] + '+00:00'
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_input.strip(), fmt)
                except ValueError:
                    continue
        
        return None
    
    def to_api_message(self, scraped_data: Dict[str, Any]) -> MessageInput:
        """Convert scraped data to API message format."""
        raise NotImplementedError("Subclasses must implement to_api_message")


class WebsiteTransformer(DataTransformer):
    """Transformer for website content."""
    
    def to_api_message(self, scraped_data: Dict[str, Any]) -> MessageInput:
        """Transform website scraped data to API format."""
        content = self.clean_content(scraped_data.get('content', ''))
        
        # Extract title if not provided separately
        title = scraped_data.get('title')
        if not title and content:
            # Try to extract title from first line
            first_line = content.split('\n')[0].strip()
            if len(first_line) < 200:  # Reasonable title length
                title = first_line
        
        metadata = {
            'title': title,
            'word_count': len(content.split()) if content else 0,
            'url_path': urlparse(scraped_data.get('url', '')).path
        }
        
        # Add any additional metadata
        if 'metadata' in scraped_data:
            metadata.update(scraped_data['metadata'])
        
        return MessageInput(
            source_type="website",
            source_name=self.source_name,
            source_url=self.source_url,
            content=content,
            url=scraped_data.get('url'),
            published_at=self.parse_date(scraped_data.get('published_at')),
            message_type=scraped_data.get('message_type', 'article'),
            metadata=metadata,
            raw_data=scraped_data.get('raw_data')
        )


class TwitterTransformer(DataTransformer):
    """Transformer for Twitter data."""
    
    def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from tweet text."""
        return re.findall(r'#(\w+)', text)
    
    def extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from tweet text."""
        return re.findall(r'@(\w+)', text)
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from tweet text."""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
    
    def to_api_message(self, scraped_data: Dict[str, Any]) -> MessageInput:
        """Transform Twitter scraped data to API format."""
        content = self.clean_content(scraped_data.get('text', ''))
        
        metadata = {
            'hashtags': scraped_data.get('hashtags', self.extract_hashtags(content)),
            'mentions': scraped_data.get('mentions', self.extract_mentions(content)),
            'urls': scraped_data.get('urls', self.extract_urls(content)),
            'metrics': scraped_data.get('public_metrics', {}),
            'tweet_type': scraped_data.get('tweet_type', 'post')
        }
        
        # Add context annotations if available
        if 'context_annotations' in scraped_data:
            metadata['context_annotations'] = scraped_data['context_annotations']
        
        return MessageInput(
            source_type="twitter",
            source_name=self.source_name,
            source_url=self.source_url,
            content=content,
            url=scraped_data.get('url') or f"https://twitter.com/i/status/{scraped_data.get('id', '')}",
            published_at=self.parse_date(scraped_data.get('created_at')),
            message_type=scraped_data.get('message_type', 'post'),
            metadata=metadata,
            raw_data={
                'tweet_id': str(scraped_data.get('id', '')),
                'author_id': str(scraped_data.get('author_id', '')),
                'conversation_id': str(scraped_data.get('conversation_id', ''))
            }
        )


class FacebookTransformer(DataTransformer):
    """Transformer for Facebook data."""
    
    def to_api_message(self, scraped_data: Dict[str, Any]) -> MessageInput:
        """Transform Facebook scraped data to API format."""
        # Facebook can have message or story content
        content = self.clean_content(
            scraped_data.get('message', '') or scraped_data.get('story', '')
        )
        
        metadata = {
            'post_type': scraped_data.get('type', 'status'),
            'engagement': {}
        }
        
        # Extract engagement metrics
        if 'likes' in scraped_data:
            metadata['engagement']['likes'] = scraped_data['likes'].get('summary', {}).get('total_count', 0)
        
        if 'comments' in scraped_data:
            metadata['engagement']['comments'] = scraped_data['comments'].get('summary', {}).get('total_count', 0)
        
        if 'shares' in scraped_data:
            metadata['engagement']['shares'] = scraped_data['shares'].get('count', 0)
        
        # Add link information if present
        if scraped_data.get('link'):
            metadata['link'] = {
                'url': scraped_data.get('link'),
                'name': scraped_data.get('name'),
                'caption': scraped_data.get('caption'),
                'description': scraped_data.get('description')
            }
        
        # Add media information
        if scraped_data.get('picture'):
            metadata['media'] = {
                'picture': scraped_data.get('picture'),
                'source': scraped_data.get('source')
            }
        
        post_id = scraped_data.get('id', '')
        url = scraped_data.get('url')
        if not url and post_id:
            # Construct Facebook URL
            if '_' in post_id:
                page_id, post_suffix = post_id.split('_', 1)
                url = f"https://www.facebook.com/{page_id}/posts/{post_suffix}"
            else:
                url = f"https://www.facebook.com/{post_id}"
        
        return MessageInput(
            source_type="facebook",
            source_name=self.source_name,
            source_url=self.source_url,
            content=content,
            url=url,
            published_at=self.parse_date(scraped_data.get('created_time')),
            message_type=scraped_data.get('message_type', 'post'),
            metadata=metadata,
            raw_data={
                'post_id': post_id,
                'page_id': scraped_data.get('page_id', '')
            }
        )


class MetaAdsTransformer(DataTransformer):
    """Transformer for Meta Ads Library data."""
    
    def to_api_message(self, scraped_data: Dict[str, Any]) -> MessageInput:
        """Transform Meta Ads data to API format."""
        # Combine ad creative content
        content_parts = []
        
        for field in ['ad_creative_bodies', 'ad_creative_link_titles', 
                     'ad_creative_link_descriptions', 'ad_creative_link_captions']:
            if scraped_data.get(field):
                content_parts.extend(scraped_data[field])
        
        content = self.clean_content(' | '.join(content_parts))
        
        metadata = {
            'page_name': scraped_data.get('page_name', ''),
            'funding_entity': scraped_data.get('funding_entity', ''),
            'currency': scraped_data.get('currency', ''),
            'publisher_platforms': scraped_data.get('publisher_platforms', []),
            'estimated_audience_size': scraped_data.get('estimated_audience_size', {}),
            'delivery_dates': {
                'start': scraped_data.get('ad_delivery_start_time'),
                'stop': scraped_data.get('ad_delivery_stop_time')
            }
        }
        
        # Add spend and impressions data
        if 'spend' in scraped_data:
            metadata['spend'] = scraped_data['spend']
        
        if 'impressions' in scraped_data:
            metadata['impressions'] = scraped_data['impressions']
        
        # Add demographic and geographic data
        if 'demographic_distribution' in scraped_data:
            metadata['demographics'] = scraped_data['demographic_distribution']
        
        if 'delivery_by_region' in scraped_data:
            metadata['delivery_regions'] = scraped_data['delivery_by_region']
        
        return MessageInput(
            source_type="meta_ads",
            source_name=self.source_name,
            source_url=self.source_url,
            content=content,
            url=scraped_data.get('ad_snapshot_url', ''),
            published_at=self.parse_date(scraped_data.get('ad_delivery_start_time') or 
                                       scraped_data.get('ad_creation_time')),
            message_type="ad",
            metadata=metadata,
            raw_data={
                'ad_id': str(scraped_data.get('id', '')),
                'page_id': str(scraped_data.get('page_id', ''))
            }
        )


# Factory function to get appropriate transformer
def get_transformer(source_type: str, source_name: str, source_url: str = None) -> DataTransformer:
    """Get the appropriate transformer for the source type."""
    transformers = {
        'website': WebsiteTransformer,
        'twitter': TwitterTransformer,
        'facebook': FacebookTransformer,
        'meta_ads': MetaAdsTransformer
    }
    
    transformer_class = transformers.get(source_type)
    if not transformer_class:
        raise ValueError(f"Unknown source type: {source_type}")
    
    return transformer_class(source_name, source_url)


# Convenience function for bulk transformation
def transform_scraped_data(scraped_messages: List[Dict[str, Any]], 
                         source_type: str, source_name: str, 
                         source_url: str = None) -> List[MessageInput]:
    """Transform a list of scraped messages to API format."""
    transformer = get_transformer(source_type, source_name, source_url)
    
    api_messages = []
    for scraped_data in scraped_messages:
        try:
            api_message = transformer.to_api_message(scraped_data)
            api_messages.append(api_message)
        except Exception as e:
            print(f"Error transforming message: {e}")
            continue
    
    return api_messages
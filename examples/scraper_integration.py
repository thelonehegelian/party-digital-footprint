"""
Example of how to integrate scrapers with the API using data transformers.
"""

import asyncio
import json
from typing import List, Dict, Any
import requests
from datetime import datetime

# Import our transformers
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.transformers.data_transformer import get_transformer, transform_scraped_data
from src.api.schemas import MessageInput, BulkMessageInput


class APIClient:
    """Simple client for submitting data to the messaging API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def submit_single_message(self, message: MessageInput) -> Dict[str, Any]:
        """Submit a single message to the API."""
        response = requests.post(
            f"{self.base_url}/api/v1/messages/single",
            json=message.dict(),
            headers={"Content-Type": "application/json"}
        )
        return response.json()
    
    def submit_bulk_messages(self, messages: List[MessageInput]) -> Dict[str, Any]:
        """Submit multiple messages to the API."""
        bulk_data = BulkMessageInput(messages=messages)
        response = requests.post(
            f"{self.base_url}/api/v1/messages/bulk",
            json=bulk_data.dict(),
            headers={"Content-Type": "application/json"}
        )
        return response.json()


# Example 1: Website scraper integration
def website_scraper_example():
    """Example of integrating a website scraper with the API."""
    
    # Simulate scraped website data
    scraped_website_data = [
        {
            'content': 'Reform UK Calls for Immediate Action on Immigration Crisis\n\nReform UK today called for immediate government action to address the ongoing immigration crisis affecting communities across Britain.',
            'url': 'https://www.reformparty.uk/news/immigration-crisis-action-needed',
            'published_at': '2024-04-15T10:30:00Z',
            'message_type': 'press_release',
            'title': 'Reform UK Calls for Immediate Action on Immigration Crisis',
            'metadata': {
                'author': 'Press Office',
                'category': 'Immigration'
            }
        },
        {
            'content': 'Brexit Benefits: Reform UK Outlines Vision for Post-EU Britain\n\nReform UK has published a comprehensive policy paper outlining how Britain can maximize the benefits of Brexit.',
            'url': 'https://www.reformparty.uk/policy/brexit-benefits-vision',
            'published_at': '2024-04-12T14:20:00Z',
            'message_type': 'policy',
            'title': 'Brexit Benefits: Reform UK Outlines Vision for Post-EU Britain'
        }
    ]
    
    # Transform to API format
    api_messages = transform_scraped_data(
        scraped_website_data,
        source_type="website",
        source_name="Reform UK Website",
        source_url="https://www.reformparty.uk"
    )
    
    return api_messages


# Example 2: Twitter scraper integration
def twitter_scraper_example():
    """Example of integrating a Twitter scraper with the API."""
    
    # Simulate Twitter API v2 response data
    scraped_twitter_data = [
        {
            'id': '1780234567890123456',
            'text': '🚨 BREAKING: Immigration figures show record highs while British families struggle with housing and jobs. When will this government put Britain first? #BritainFirst #Immigration #ReformUK',
            'created_at': '2024-04-16T14:23:00Z',
            'author_id': '123456789',
            'public_metrics': {
                'retweet_count': 245,
                'like_count': 892,
                'reply_count': 134,
                'quote_count': 78
            },
            'context_annotations': [
                {
                    'domain': {'name': 'Political Body'},
                    'entity': {'name': 'UK Government'}
                }
            ]
        }
    ]
    
    # Transform to API format
    transformer = get_transformer(
        "twitter", 
        "Reform UK Twitter", 
        "https://twitter.com/reformparty_uk"
    )
    
    api_messages = []
    for tweet_data in scraped_twitter_data:
        api_message = transformer.to_api_message(tweet_data)
        api_messages.append(api_message)
    
    return api_messages


# Example 3: Facebook scraper integration
def facebook_scraper_example():
    """Example of integrating a Facebook scraper with the API."""
    
    # Simulate Facebook Graph API response data
    scraped_facebook_data = [
        {
            'id': '567890123456789',
            'message': '🇬🇧 BRITAIN FIRST POLICIES FOR BRITISH PEOPLE 🇬🇧\n\nReform UK is committed to putting British families first. Our comprehensive immigration policy will:\n\n✅ Reduce net migration to sustainable levels\n✅ Prioritize skills-based immigration',
            'created_time': '2024-04-16T19:30:00Z',
            'type': 'status',
            'likes': {'summary': {'total_count': 2847}},
            'comments': {'summary': {'total_count': 456}},
            'shares': {'count': 823}
        }
    ]
    
    # Transform to API format
    transformer = get_transformer(
        "facebook",
        "Reform UK Facebook",
        "https://www.facebook.com/ReformPartyUK"
    )
    
    api_messages = []
    for post_data in scraped_facebook_data:
        api_message = transformer.to_api_message(post_data)
        api_messages.append(api_message)
    
    return api_messages


# Example 4: Complete scraper workflow
def complete_scraper_workflow():
    """Example of a complete scraper workflow."""
    
    print("🕷️ Starting scraper workflow...")
    
    # Initialize API client
    client = APIClient()
    
    # Collect data from multiple sources
    all_messages = []
    
    # Add website data
    website_messages = website_scraper_example()
    all_messages.extend(website_messages)
    print(f"✅ Collected {len(website_messages)} website messages")
    
    # Add Twitter data
    twitter_messages = twitter_scraper_example()
    all_messages.extend(twitter_messages)
    print(f"✅ Collected {len(twitter_messages)} Twitter messages")
    
    # Add Facebook data
    facebook_messages = facebook_scraper_example()
    all_messages.extend(facebook_messages)
    print(f"✅ Collected {len(facebook_messages)} Facebook messages")
    
    print(f"\n📤 Submitting {len(all_messages)} messages to API...")
    
    try:
        # Submit all messages in bulk
        result = client.submit_bulk_messages(all_messages)
        
        print("📊 Results:")
        print(f"   Status: {result['status']}")
        print(f"   Imported: {result['imported_count']}")
        print(f"   Skipped: {result['skipped_count']}")
        print(f"   Keywords extracted: {result['total_keywords_extracted']}")
        
        if result['errors']:
            print(f"   Errors: {len(result['errors'])}")
            for error in result['errors']:
                print(f"     - {error}")
        
        return result
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server")
        print("   Make sure the API server is running: uvicorn src.api.main:app")
        return None
    except Exception as e:
        print(f"❌ Error submitting data: {e}")
        return None


# Example 5: Transform mock data to API format
def transform_mock_data_example():
    """Example of transforming existing mock data to API format."""
    
    # Load mock data (same format as in mock-data folder)
    mock_website_data = [
        {
            "content": "Reform UK Calls for Immediate Action on Immigration Crisis\n\nReform UK today called for immediate government action...",
            "url": "https://www.reformparty.uk/news/immigration-crisis-action-needed",
            "published_at": "2024-04-15T10:30:00Z",
            "message_type": "press_release",
            "metadata": {
                "title": "Reform UK Calls for Immediate Action on Immigration Crisis",
                "word_count": 145,
                "url_path": "/news/immigration-crisis-action-needed"
            }
        }
    ]
    
    # Transform using transformer
    transformer = get_transformer("website", "Reform UK Website")
    api_messages = []
    
    for mock_data in mock_website_data:
        # Convert mock data format to API format
        api_message = transformer.to_api_message(mock_data)
        api_messages.append(api_message)
    
    # Display the transformed data
    print("🔄 Transformed mock data:")
    for msg in api_messages:
        print(f"   Source: {msg.source_name}")
        print(f"   Type: {msg.source_type}")
        print(f"   Content: {msg.content[:100]}...")
        print(f"   URL: {msg.url}")
        print()
    
    return api_messages


if __name__ == "__main__":
    print("=== Reform UK Messaging API Integration Examples ===\n")
    
    # Example 1: Transform mock data
    print("1. Transform Mock Data Example:")
    transform_mock_data_example()
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Complete workflow (requires API server)
    print("2. Complete Scraper Workflow Example:")
    print("   (Note: Requires API server to be running)")
    complete_scraper_workflow()
    
    print("\n" + "="*50 + "\n")
    
    print("💡 To start the API server, run:")
    print("   uvicorn src.api.main:app --reload")
    print("\n💡 To view API documentation, visit:")
    print("   http://localhost:8000/docs")
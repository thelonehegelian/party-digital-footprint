# Data Integration Guide

## Overview

This political digital footprint analysis platform is designed to accept data from various external sources through standardized API endpoints. Whether you're using web scrapers, social media APIs, RSS feeds, or other data collection tools, this guide will help you integrate your data seamlessly.

## Prerequisites

- API server running on `http://localhost:8000` (or your configured endpoint)
- Your data collection tool capable of making HTTP POST requests
- Understanding of your data source format and structure

## Quick Start

The platform accepts data through two main endpoints:

1. **Single Message**: `POST /api/v1/messages/single`
2. **Bulk Messages**: `POST /api/v1/messages/bulk` (up to 100 messages)

Each message requires:
- Content text (1-10,000 characters)
- Source type (`website`, `twitter`, `facebook`, `meta_ads`)
- Source name (human-readable identifier)
- Optional metadata for enhanced analytics

## Core Data Requirements

### Required Fields

```json
{
  "source_type": "website|twitter|facebook|meta_ads",
  "source_name": "Human-readable source name",
  "content": "The main message content (1-10,000 chars)"
}
```

### Optional Fields

```json
{
  "source_url": "Base URL of the source",
  "url": "Direct URL to specific content",
  "published_at": "2024-04-15T10:30:00Z",
  "message_type": "press_release|tweet|post|ad",
  "candidate_id": 123,
  "geographic_scope": "national|regional|local",
  "metadata": {...},
  "raw_data": {...}
}
```

## Supported Source Types

### 1. Website Content

Perfect for: News sites, blogs, press releases, policy pages

**Metadata Structure:**
```json
{
  "metadata": {
    "title": "Article title",
    "author": "Author name", 
    "word_count": 450,
    "url_path": "/news/article-slug",
    "tags": ["immigration", "policy"],
    "category": "News"
  }
}
```

**Example Integration:**
```python
import requests

def submit_website_content(article_data):
    message = {
        "source_type": "website",
        "source_name": "Party News Site",
        "source_url": "https://example-party.com",
        "content": article_data["content"],
        "url": article_data["url"],
        "published_at": article_data["published_date"],
        "message_type": "news_article",
        "metadata": {
            "title": article_data["title"],
            "author": article_data["author"],
            "word_count": len(article_data["content"].split())
        }
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/messages/single",
        json=message
    )
    return response.json()
```

### 2. Twitter/X Content

Perfect for: Tweets, threads, replies, retweets

**Metadata Structure:**
```json
{
  "metadata": {
    "hashtags": ["#PolicyUpdate", "#VoteNow"],
    "mentions": ["@username1", "@username2"],
    "urls": ["https://link1.com", "https://link2.com"],
    "media_urls": ["https://pic.twitter.com/abc123"],
    "metrics": {
      "retweet_count": 145,
      "like_count": 892,
      "reply_count": 34
    },
    "tweet_type": "original|retweet|reply",
    "context_annotations": [
      {"domain": "Political Body", "entity": "Government"}
    ]
  }
}
```

**Example Integration:**
```python
def submit_twitter_content(tweet_data):
    message = {
        "source_type": "twitter",
        "source_name": "Party Twitter Account",
        "source_url": "https://twitter.com/party_account",
        "content": tweet_data["text"],
        "url": f"https://twitter.com/party_account/status/{tweet_data['id']}",
        "published_at": tweet_data["created_at"],
        "message_type": "tweet",
        "metadata": {
            "hashtags": extract_hashtags(tweet_data["text"]),
            "mentions": extract_mentions(tweet_data["text"]),
            "metrics": tweet_data.get("public_metrics", {}),
            "tweet_type": determine_tweet_type(tweet_data)
        },
        "raw_data": tweet_data
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/messages/single",
        json=message
    )
    return response.json()
```

### 3. Facebook Content

Perfect for: Posts, stories, events, page updates

**Metadata Structure:**
```json
{
  "metadata": {
    "post_type": "status|photo|video|link|event",
    "engagement": {
      "likes": 234,
      "comments": 45,
      "shares": 67
    },
    "link": {
      "url": "https://external-link.com",
      "title": "Link title"
    },
    "media": {
      "type": "photo|video",
      "url": "https://facebook.com/photo.jpg"
    },
    "place": {
      "name": "Location name",
      "location": {"city": "London", "country": "UK"}
    }
  }
}
```

### 4. Meta Ads Library

Perfect for: Political advertisements, sponsored content

**Metadata Structure:**
```json
{
  "metadata": {
    "page_name": "Political Party Name",
    "funding_entity": "Party Funding Entity",
    "currency": "GBP",
    "publisher_platforms": ["Facebook", "Instagram"],
    "estimated_audience_size": {"min": 1000, "max": 5000},
    "delivery_dates": {"start": "2024-04-01", "end": "2024-04-15"},
    "spend": {"min": 100, "max": 500},
    "impressions": {"min": 10000, "max": 50000},
    "demographics": {
      "age_ranges": ["25-34", "35-44"],
      "gender": ["male", "female"]
    },
    "delivery_regions": ["England", "Wales"]
  }
}
```

## Integration Patterns

### Pattern 1: Direct API Integration

For simple scrapers or one-time data imports:

```python
import requests

def submit_single_message(message_data):
    response = requests.post(
        "http://localhost:8000/api/v1/messages/single",
        json=message_data,
        headers={"Content-Type": "application/json"}
    )
    return response.json()

def submit_bulk_messages(messages_list):
    bulk_data = {"messages": messages_list}
    response = requests.post(
        "http://localhost:8000/api/v1/messages/bulk",
        json=bulk_data,
        headers={"Content-Type": "application/json"}
    )
    return response.json()
```

### Pattern 2: Batch Processing

For large datasets or scheduled imports:

```python
def process_data_in_batches(all_messages, batch_size=100):
    results = []
    
    for i in range(0, len(all_messages), batch_size):
        batch = all_messages[i:i + batch_size]
        
        try:
            result = submit_bulk_messages(batch)
            results.append(result)
            
            print(f"Processed batch {i//batch_size + 1}: "
                  f"{result['imported_count']} imported, "
                  f"{result['skipped_count']} skipped")
                  
        except Exception as e:
            print(f"Error processing batch {i//batch_size + 1}: {e}")
            
    return results
```

### Pattern 3: Real-time Streaming

For live data feeds:

```python
import time
from queue import Queue
import threading

class MessageSubmitter:
    def __init__(self, api_url, batch_size=50):
        self.api_url = api_url
        self.batch_size = batch_size
        self.queue = Queue()
        self.running = True
        
    def add_message(self, message):
        self.queue.put(message)
        
    def start_processing(self):
        thread = threading.Thread(target=self._process_queue)
        thread.daemon = True
        thread.start()
        
    def _process_queue(self):
        batch = []
        
        while self.running:
            try:
                # Collect messages for batch
                while len(batch) < self.batch_size and not self.queue.empty():
                    batch.append(self.queue.get_nowait())
                
                # Submit batch if we have messages
                if batch:
                    submit_bulk_messages(batch)
                    batch = []
                    
                time.sleep(1)  # Wait before next batch
                
            except Exception as e:
                print(f"Error in queue processing: {e}")
```

## Common Integration Examples

### RSS Feed Integration

```python
import feedparser
from datetime import datetime

def scrape_rss_feed(feed_url, source_name):
    feed = feedparser.parse(feed_url)
    messages = []
    
    for entry in feed.entries:
        message = {
            "source_type": "website",
            "source_name": source_name,
            "source_url": feed_url,
            "content": entry.summary or entry.description,
            "url": entry.link,
            "published_at": datetime(*entry.published_parsed[:6]).isoformat() + "Z",
            "message_type": "rss_article",
            "metadata": {
                "title": entry.title,
                "author": getattr(entry, 'author', None),
                "tags": [tag.term for tag in getattr(entry, 'tags', [])]
            }
        }
        messages.append(message)
    
    return submit_bulk_messages(messages)
```

### CSV Import

```python
import csv
from datetime import datetime

def import_from_csv(csv_file_path):
    messages = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            message = {
                "source_type": row['source_type'],
                "source_name": row['source_name'],
                "content": row['content'],
                "url": row.get('url'),
                "published_at": row.get('published_at'),
                "message_type": row.get('message_type'),
                "metadata": {
                    "imported_from": "csv",
                    "original_row": row
                }
            }
            messages.append(message)
    
    return process_data_in_batches(messages)
```

### Webhook Integration

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook/messages', methods=['POST'])
def receive_webhook():
    data = request.json
    
    # Transform webhook data to our format
    message = {
        "source_type": data['platform'],
        "source_name": data['source_name'] ,
        "content": data['message_content'],
        "url": data.get('permalink'),
        "published_at": data.get('timestamp'),
        "metadata": data.get('additional_data', {})
    }
    
    # Submit to our API
    result = submit_single_message(message)
    
    return jsonify({"status": "received", "result": result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## Data Validation and Error Handling

### Input Validation

The API performs automatic validation:

- Content length: 1-10,000 characters
- Source type: Must be one of the supported types
- Timestamps: ISO 8601 format preferred
- Bulk submissions: Maximum 100 messages per request

### Error Responses

Common error responses and solutions:

```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "message": "Content cannot be empty",
  "details": {
    "field": "content",
    "constraint": "min_length"
  }
}
```

**Error Handling Example:**
```python
def robust_message_submission(message_data):
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/messages/single",
            json=message_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['status'] == 'success':
                return result
            else:
                print(f"API Error: {result['message']}")
                return None
                
        else:
            print(f"HTTP Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server")
        return None
    except requests.exceptions.Timeout:
        print("Error: Request timed out")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

## Advanced Analytics Integration

Once your data is ingested, you can leverage the analytics APIs:

### Sentiment Analysis
```python
# Analyze sentiment for submitted content
def analyze_sentiment(message_id):
    response = requests.post(
        "http://localhost:8000/api/v1/analytics/sentiment/analyze",
        json={"message_id": message_id}
    )
    return response.json()
```

### Topic Modeling
```python
# Analyze topics for submitted content  
def analyze_topics(message_id):
    response = requests.post(
        "http://localhost:8000/api/v1/analytics/topics/analyze",
        json={"message_id": message_id}
    )
    return response.json()
```

### Engagement Analytics
```python
# Analyze engagement metrics
def analyze_engagement(message_id):
    response = requests.post(
        "http://localhost:8000/api/v1/analytics/engagement/analyze",
        json={"message_id": message_id}
    )
    return response.json()
```

## Testing Your Integration

### 1. Start the API Server
```bash
uvicorn src.api.main:app --reload
```

### 2. Test with Sample Data
```python
# Test message
test_message = {
    "source_type": "website",
    "source_name": "Test Source",
    "content": "This is a test message for integration testing.",
    "url": "https://example.com/test",
    "published_at": "2024-04-15T10:30:00Z",
    "message_type": "test"
}

result = submit_single_message(test_message)
print(f"Status: {result['status']}")
print(f"Message ID: {result.get('message_id')}")
```

### 3. View API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation with try-it-out functionality.

## Performance Considerations

- **Batch Size**: Use bulk endpoints for >10 messages
- **Rate Limiting**: Process ~1000 messages per minute for optimal performance  
- **Duplicate Detection**: The system automatically handles duplicates by URL
- **Memory Usage**: Each message uses ~1-5KB depending on metadata size
- **Database Growth**: Plan for ~100MB per 100,000 messages

## Security Best Practices

- Use HTTPS in production environments
- Validate and sanitize all input data
- Store API credentials securely
- Implement request timeouts
- Log all integration activities
- Regular security updates

## Support and Documentation

- **API Documentation**: `http://localhost:8000/docs`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`
- **Examples**: See `examples/scraper_integration.py`
- **Database Schema**: See `src/models.py`

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure API server is running
2. **Validation Errors**: Check required fields and data types
3. **Timeout Errors**: Reduce batch size or increase timeout
4. **Memory Issues**: Process data in smaller batches
5. **Duplicate Entries**: Review URL uniqueness constraints

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check

Test API connectivity:
```bash
curl http://localhost:8000/api/v1/messages/stats
```

This platform is designed to be flexible and accommodate various data sources. With these patterns and examples, you should be able to integrate virtually any political messaging data source into the analysis system.
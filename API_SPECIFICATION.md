# Political Messaging Analysis API Specification

This document defines the standard data format for submitting messaging data to the multi-party political messaging analysis system.

## Base URL
```
POST /api/v1/messages/bulk
POST /api/v1/messages/single
```

## Authentication
```
Authorization: Bearer <your-api-token>
Content-Type: application/json
```

## Data Structure

### Message Object Schema

```json
{
  "source_type": "string",           // Required: "website", "twitter", "facebook", "meta_ads"
  "source_name": "string",           // Required: Human-readable source name
  "source_url": "string",            // Optional: Base URL of the source
  "content": "string",               // Required: Main message content
  "url": "string",                   // Optional: Direct URL to the content
  "published_at": "ISO8601",         // Optional: When content was published
  "message_type": "string",          // Optional: Type categorization
  "metadata": {},                    // Optional: Source-specific metadata
  "raw_data": {}                     // Optional: Original API response
}
```

### Required Fields
- `source_type`: Must be one of: `website`, `twitter`, `facebook`, `meta_ads`
- `source_name`: Descriptive name (e.g., "Progressive Party Official Website")
- `content`: The actual text content to analyze

### Optional Fields
- `url`: Direct link to the original content
- `published_at`: ISO 8601 formatted datetime (e.g., "2024-04-15T10:30:00Z")
- `message_type`: Content categorization (see below)
- `metadata`: Source-specific structured data
- `raw_data`: Preserve original API response for debugging

## Message Types by Source

### Website (`source_type: "website"`)
```json
{
  "message_type": "article|press_release|policy|event|news",
  "metadata": {
    "title": "string",
    "author": "string",
    "word_count": "integer",
    "url_path": "string",
    "tags": ["string"],
    "category": "string"
  }
}
```

### Twitter (`source_type: "twitter"`)
```json
{
  "message_type": "post|reply|retweet|quote_tweet",
  "metadata": {
    "hashtags": ["string"],
    "mentions": ["string"],
    "urls": ["string"],
    "media_urls": ["string"],
    "metrics": {
      "retweet_count": "integer",
      "like_count": "integer",
      "reply_count": "integer",
      "quote_count": "integer"
    },
    "tweet_type": "string",
    "context_annotations": [
      {
        "domain": "string",
        "entity": "string"
      }
    ]
  },
  "raw_data": {
    "tweet_id": "string",
    "author_id": "string",
    "conversation_id": "string"
  }
}
```

### Facebook (`source_type: "facebook"`)
```json
{
  "message_type": "post|story|event|photo|video",
  "metadata": {
    "post_type": "status|link|photo|video",
    "engagement": {
      "likes": "integer",
      "comments": "integer",
      "shares": "integer"
    },
    "link": {
      "url": "string",
      "name": "string",
      "caption": "string",
      "description": "string"
    },
    "media": {
      "picture": "string",
      "source": "string"
    },
    "place": {
      "name": "string",
      "location": {}
    }
  },
  "raw_data": {
    "post_id": "string",
    "page_id": "string"
  }
}
```

### Meta Ads (`source_type: "meta_ads"`)
```json
{
  "message_type": "ad",
  "metadata": {
    "page_name": "string",
    "funding_entity": "string",
    "currency": "string",
    "publisher_platforms": ["Facebook", "Instagram"],
    "estimated_audience_size": {
      "lower_bound": "integer",
      "upper_bound": "integer"
    },
    "delivery_dates": {
      "start": "ISO8601",
      "stop": "ISO8601"
    },
    "spend": {
      "lower_bound": "integer",
      "upper_bound": "integer"
    },
    "impressions": {
      "lower_bound": "integer",
      "upper_bound": "integer"
    },
    "demographics": {
      "age": ["string"],
      "gender": ["string"]
    },
    "delivery_regions": ["string"]
  },
  "raw_data": {
    "ad_id": "string",
    "page_id": "string"
  }
}
```

## API Endpoints

### Submit Single Message
```http
POST /api/v1/messages/single
```

**Request Body:**
```json
{
  "source_type": "twitter",
  "source_name": "Progressive Party Twitter",
  "source_url": "https://twitter.com/progressiveparty",
  "content": "🚨 BREAKING: Immigration figures show record highs...",
  "url": "https://twitter.com/progressiveparty/status/1780234567890123456",
  "published_at": "2024-04-16T14:23:00Z",
  "message_type": "post",
  "metadata": {
    "hashtags": ["ClimateAction", "Immigration", "ProgressiveParty"],
    "metrics": {
      "retweet_count": 245,
      "like_count": 892
    }
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message_id": 12345,
  "keywords_extracted": 15
}
```

### Submit Multiple Messages
```http
POST /api/v1/messages/bulk
```

**Request Body:**
```json
{
  "messages": [
    {
      "source_type": "website",
      "source_name": "Progressive Party Website",
      "content": "Progressive Party Calls for Immediate Action on Immigration Crisis..."
    },
    {
      "source_type": "facebook",
      "source_name": "Progressive Party Facebook",
      "content": "🇬🇧 BRITAIN FIRST POLICIES FOR BRITISH PEOPLE 🇬🇧..."
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "imported_count": 2,
  "skipped_count": 0,
  "errors": [],
  "total_keywords_extracted": 28
}
```

## Error Responses

### Validation Error
```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "message": "Required field missing",
  "details": {
    "field": "content",
    "message": "Content field is required"
  }
}
```

### Duplicate Content
```json
{
  "status": "warning",
  "error_code": "DUPLICATE_CONTENT",
  "message": "Message already exists",
  "existing_message_id": 12345
}
```

## Data Transformation Guidelines

### For External APIs
When integrating with external data sources, transform your data to match this schema:

```python
# Example transformation for Twitter API v2
def transform_twitter_data(tweet_data):
    return {
        "source_type": "twitter",
        "source_name": "Progressive Party Twitter",
        "source_url": "https://twitter.com/progressiveparty",
        "content": tweet_data["text"],
        "url": f"https://twitter.com/progressiveparty/status/{tweet_data['id']}",
        "published_at": tweet_data["created_at"],
        "message_type": "post",
        "metadata": {
            "hashtags": extract_hashtags(tweet_data),
            "metrics": tweet_data.get("public_metrics", {}),
            "tweet_type": determine_tweet_type(tweet_data)
        },
        "raw_data": {
            "tweet_id": tweet_data["id"],
            "author_id": tweet_data["author_id"]
        }
    }
```

### For Internal Scrapers
Your scrapers should output data in this format before sending to the API:

```python
# Example scraper output
scraped_messages = [
    {
        "source_type": "website",
        "source_name": "Progressive Party Website", 
        "content": extracted_content,
        "url": page_url,
        "published_at": parsed_date,
        "message_type": "article",
        "metadata": {
            "title": page_title,
            "word_count": len(content.split())
        }
    }
]
```

## Rate Limiting
- **Single message**: 100 requests per minute
- **Bulk messages**: 10 requests per minute (max 100 messages per request)

## Content Guidelines
- **Maximum content length**: 10,000 characters
- **Encoding**: UTF-8
- **Language**: Primarily English (UK political content)
- **Content filtering**: Automatic deduplication by URL and content hash

## Webhook Support (Future)
```http
POST /api/v1/webhooks/register
```

Register a webhook to receive notifications when:
- New messages are processed
- Keywords are extracted
- Analysis reports are generated
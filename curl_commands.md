# Reform UK Messaging Analysis API - Curl Test Commands

## Prerequisites
Make sure your API server is running on `localhost:8000`

## Base URLs
- API Base: `http://localhost:8000/api/v1`
- Health Check: `http://localhost:8000/health`

---

## 1. Health Check
```bash
curl -X GET "http://localhost:8000/health" \
  -H "Content-Type: application/json"
```

## 2. Root Endpoint
```bash
curl -X GET "http://localhost:8000/" \
  -H "Content-Type: application/json"
```

## 3. Submit Single Twitter Message
```bash
curl -X POST "http://localhost:8000/api/v1/messages/single" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "twitter",
    "source_name": "Reform UK Twitter",
    "source_url": "https://twitter.com/reformparty_uk",
    "content": "🚨 BREAKING: Immigration figures show record highs under this government. We need immediate action to secure our borders and put Britain first! 🇬🇧 #BritainFirst #Immigration #ReformUK",
    "url": "https://twitter.com/reformparty_uk/status/1780234567890123456",
    "published_at": "2024-04-16T14:23:00Z",
    "message_type": "post",
    "metadata": {
      "hashtags": ["BritainFirst", "Immigration", "ReformUK"],
      "metrics": {
        "retweet_count": 245,
        "like_count": 892
      }
    }
  }'
```

## 4. Submit Single Website Message
```bash
curl -X POST "http://localhost:8000/api/v1/messages/single" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "website",
    "source_name": "Reform UK Official Website",
    "source_url": "https://www.reformparty.uk",
    "content": "Reform UK Calls for Immediate Action on Immigration Crisis. Our party demands urgent measures to address the unprecedented levels of immigration that are overwhelming our public services.",
    "url": "https://www.reformparty.uk/news/immigration-crisis-action",
    "published_at": "2024-04-15T10:30:00Z",
    "message_type": "press_release",
    "metadata": {
      "title": "Reform UK Calls for Immediate Action on Immigration Crisis",
      "author": "Reform UK Press Office",
      "category": "policy"
    }
  }'
```

## 5. Submit Single Facebook Message
```bash
curl -X POST "http://localhost:8000/api/v1/messages/single" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "facebook",
    "source_name": "Reform UK Facebook",
    "source_url": "https://www.facebook.com/reformpartyuk",
    "content": "🇬🇧 BRITAIN FIRST POLICIES FOR BRITISH PEOPLE 🇬🇧 Our manifesto focuses on putting British citizens first, securing our borders, and restoring national pride.",
    "url": "https://www.facebook.com/reformpartyuk/posts/123456789012345",
    "published_at": "2024-04-14T16:45:00Z",
    "message_type": "post",
    "metadata": {
      "post_type": "status",
      "engagement": {
        "likes": 1234,
        "comments": 89,
        "shares": 234
      }
    }
  }'
```

## 6. Submit Single Meta Ads Message
```bash
curl -X POST "http://localhost:8000/api/v1/messages/single" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "meta_ads",
    "source_name": "Reform UK Political Ads",
    "source_url": "https://www.facebook.com/ads/library",
    "content": "Vote Reform UK - Britain First Policies. Secure borders, lower taxes, stronger economy. Your vote matters on May 2nd.",
    "url": "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=GB&view_all_page_id=987654321",
    "published_at": "2024-04-13T09:15:00Z",
    "message_type": "ad",
    "metadata": {
      "page_name": "Reform UK",
      "funding_entity": "Reform UK",
      "currency": "GBP",
      "publisher_platforms": ["Facebook", "Instagram"],
      "spend": {
        "lower_bound": 1000,
        "upper_bound": 5000
      }
    }
  }'
```

## 7. Submit Bulk Messages
```bash
curl -X POST "http://localhost:8000/api/v1/messages/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "source_type": "website",
        "source_name": "Reform UK Website",
        "content": "Reform UK announces new economic policy focusing on tax cuts for working families and small businesses.",
        "url": "https://www.reformparty.uk/policies/economy",
        "published_at": "2024-04-12T11:00:00Z",
        "message_type": "policy"
      },
      {
        "source_type": "twitter",
        "source_name": "Reform UK Twitter",
        "content": "Our NHS needs reform, not more money thrown at it. We have a plan to make healthcare work for British people again. #NHSReform #ReformUK",
        "url": "https://twitter.com/reformparty_uk/status/1780234567890123457",
        "published_at": "2024-04-12T15:30:00Z",
        "message_type": "post"
      }
    ]
  }'
```

## 8. List Sources
```bash
curl -X GET "http://localhost:8000/api/v1/sources" \
  -H "Content-Type: application/json"
```

## 9. Get Message Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/messages/stats" \
  -H "Content-Type: application/json"
```

## 10. Test Duplicate Detection (should return warning)
```bash
curl -X POST "http://localhost:8000/api/v1/messages/single" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "twitter",
    "source_name": "Reform UK Twitter",
    "content": "🚨 BREAKING: Immigration figures show record highs under this government. We need immediate action to secure our borders and put Britain first! 🇬🇧 #BritainFirst #Immigration #ReformUK",
    "url": "https://twitter.com/reformparty_uk/status/1780234567890123456",
    "published_at": "2024-04-16T14:23:00Z",
    "message_type": "post"
  }'
```

## 11. Test Validation Error (missing required field)
```bash
curl -X POST "http://localhost:8000/api/v1/messages/single" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "twitter",
    "source_name": "Reform UK Twitter"
  }'
```

## 12. Test Invalid Source Type
```bash
curl -X POST "http://localhost:8000/api/v1/messages/single" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "invalid_source",
    "source_name": "Test Source",
    "content": "This should fail validation"
  }'
```

---

## Expected Responses

### Successful Response (200)
```json
{
  "status": "success",
  "message_id": 12345,
  "keywords_extracted": 15
}
```

### Duplicate Warning (200)
```json
{
  "status": "warning",
  "message": "Message already exists",
  "message_id": 12345
}
```

### Validation Error (422)
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

### Bulk Response (200)
```json
{
  "status": "success",
  "imported_count": 2,
  "skipped_count": 0,
  "errors": [],
  "total_keywords_extracted": 28
}
```

---

## Quick Test Sequence
Run these commands in order to test the full API functionality:

1. Health check
2. Submit a Twitter message
3. Submit a website message
4. Submit bulk messages
5. Check sources
6. Check statistics
7. Test duplicate detection

This will give you a complete picture of the API's functionality. 
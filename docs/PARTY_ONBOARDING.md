# Party Onboarding Guide

This guide explains how to add and configure new political parties in the Multi-Party Political Messaging Analytics platform.

## Overview

The platform supports analysis of multiple political parties simultaneously. Each party has its own data space, analytics, and configuration settings. This guide covers:

1. Adding new parties via API
2. Configuring party settings
3. Submitting party-specific data
4. Accessing party analytics
5. Dashboard usage

## Quick Start

### 1. Add a New Party

Create a new party using the Party Management API:

```bash
curl -X POST "http://localhost:8000/api/v1/parties" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Labour Party",
    "short_name": "Labour",
    "country": "United Kingdom",
    "party_type": "political_party",
    "description": "The Labour Party is a centre-left political party in the United Kingdom",
    "founded_year": 1900,
    "headquarters": "London, England",
    "website_url": "https://labour.org.uk",
    "social_media_accounts": {
      "twitter": "@UKLabour",
      "facebook": "https://facebook.com/labourparty",
      "instagram": "@uklabour",
      "youtube": "https://youtube.com/labourtv"
    },
    "branding_config": {
      "primary_color": "#e20613",
      "secondary_color": "#ffffff",
      "accent_color": "#000000"
    }
  }'
```

**Response:**
```json
{
  "id": 2,
  "name": "Labour Party",
  "short_name": "Labour",
  "country": "United Kingdom",
  "party_type": "political_party",
  "description": "The Labour Party is a centre-left political party in the United Kingdom",
  "founded_year": 1900,
  "headquarters": "London, England",
  "website_url": "https://labour.org.uk",
  "social_media_accounts": {
    "twitter": "@UKLabour",
    "facebook": "https://facebook.com/labourparty",
    "instagram": "@uklabour",
    "youtube": "https://youtube.com/labourtv"
  },
  "branding_config": {
    "primary_color": "#e20613",
    "secondary_color": "#ffffff",
    "accent_color": "#000000"
  },
  "active": true,
  "created_at": "2024-01-20T10:30:00Z",
  "updated_at": "2024-01-20T10:30:00Z"
}
```

### 2. Submit Party Data

Once a party is created, submit messages and data using the party ID:

```bash
curl -X POST "http://localhost:8000/api/v1/messages/single?party_id=2" \
  -H "Content-Type: application/json" \
  -d '{
    "source_name": "Labour Party Website",
    "source_type": "website", 
    "source_url": "https://labour.org.uk",
    "content": "Labour announces ambitious green energy plan to create 650,000 jobs",
    "message_type": "press_release",
    "published_at": "2024-01-20T14:30:00Z",
    "metadata": {
      "tags": ["environment", "jobs", "policy"],
      "author": "Labour Press Office"
    }
  }'
```

### 3. Access Party Analytics

Get party-specific analytics using the party_id parameter:

```bash
# Sentiment analysis for specific party
curl "http://localhost:8000/api/v1/analytics/sentiment/stats?party_id=2"

# Topic analysis for specific party  
curl "http://localhost:8000/api/v1/analytics/topics/overview?party_id=2"

# All parties (omit party_id)
curl "http://localhost:8000/api/v1/analytics/sentiment/stats"
```

## Detailed Configuration

### Party Model Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Full party name (must be unique) |
| `short_name` | string | Yes | Abbreviated name or acronym |
| `country` | string | No | Country (default: "United Kingdom") |
| `party_type` | string | No | Type: "political_party", "candidate", "organization" |
| `description` | string | No | Party description for dashboard |
| `founded_year` | integer | No | Year the party was founded |
| `headquarters` | string | No | Headquarters location |
| `website_url` | string | No | Official website URL |
| `social_media_accounts` | object | No | Social media handles and URLs |
| `scraping_config` | object | No | Custom scraping settings |
| `analytics_config` | object | No | Custom analytics keywords/categories |
| `branding_config` | object | No | UI colors and branding |

### Social Media Accounts Format

```json
{
  "twitter": "@partyhandle",
  "facebook": "https://facebook.com/partypage",
  "instagram": "@partyhandle",
  "youtube": "https://youtube.com/partychannel",
  "tiktok": "@partyhandle",
  "website": "https://party.org"
}
```

### Branding Configuration

```json
{
  "primary_color": "#1f77b4",
  "secondary_color": "#ff7f0e", 
  "accent_color": "#2ca02c",
  "logo_url": "https://party.org/logo.png",
  "favicon_url": "https://party.org/favicon.ico"
}
```

### Analytics Configuration

```json
{
  "sentiment_keywords": {
    "positive": ["progress", "success", "achievement"],
    "negative": ["crisis", "failure", "problem"],
    "economic": ["economy", "jobs", "business"],
    "healthcare": ["NHS", "health", "medical"],
    "custom_category": ["keyword1", "keyword2"]
  },
  "topic_categories": [
    "Economy & Business",
    "Healthcare", 
    "Education",
    "Custom Topic Area"
  ]
}
```

## API Endpoints Reference

### Party Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/parties` | List all parties |
| `POST` | `/api/v1/parties` | Create new party |
| `GET` | `/api/v1/parties/{id}` | Get party details |
| `PUT` | `/api/v1/parties/{id}` | Update party |
| `DELETE` | `/api/v1/parties/{id}` | Delete/deactivate party |

### Data Submission

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/messages/single?party_id={id}` | Submit single message |
| `POST` | `/api/v1/messages/bulk?party_id={id}` | Submit multiple messages |

### Analytics (with party_id parameter)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/analytics/sentiment/stats?party_id={id}` | Sentiment statistics |
| `GET` | `/api/v1/analytics/sentiment/trends?party_id={id}` | Sentiment trends |
| `GET` | `/api/v1/analytics/topics/overview?party_id={id}` | Topic overview |
| `GET` | `/api/v1/analytics/engagement/overview?party_id={id}` | Engagement metrics |

## Dashboard Usage

### Party Selection

1. Open the Streamlit dashboard at `http://localhost:8501`
2. Use the **party selector** in the left sidebar
3. All charts and data automatically filter to the selected party
4. Switch between parties to compare different organizations

### Features by Party

- **Dynamic titles**: Dashboard title changes to "{Party Name} Digital Footprint Analysis"
- **Filtered data**: All metrics, charts, and tables show only the selected party's data
- **Party information**: Shows party description and details when available
- **Export functionality**: All exports are party-specific

## Data Integration Examples

### Python Integration

```python
import requests

# Add new party
party_data = {
    "name": "Green Party",
    "short_name": "Green",
    "description": "Environmental and social justice party",
    "website_url": "https://greenparty.org.uk"
}

response = requests.post(
    "http://localhost:8000/api/v1/parties",
    json=party_data
)
party = response.json()
party_id = party["id"]

# Submit message data
message_data = {
    "source_name": "Green Party Blog",
    "source_type": "website",
    "content": "Green Party proposes radical climate action plan",
    "message_type": "article"
}

requests.post(
    f"http://localhost:8000/api/v1/messages/single?party_id={party_id}",
    json=message_data
)

# Get analytics
analytics = requests.get(
    f"http://localhost:8000/api/v1/analytics/sentiment/stats?party_id={party_id}"
)
print(analytics.json())
```

### Bulk Data Import

```python
import requests

# Prepare bulk messages
messages = [
    {
        "source_name": "Party Twitter",
        "source_type": "twitter",
        "content": "Message 1 content...",
        "message_type": "social_post"
    },
    {
        "source_name": "Party Website", 
        "source_type": "website",
        "content": "Message 2 content...",
        "message_type": "article"
    }
    # Up to 100 messages per batch
]

bulk_data = {"messages": messages}
response = requests.post(
    f"http://localhost:8000/api/v1/messages/bulk?party_id={party_id}",
    json=bulk_data
)
```

## Best Practices

### 1. Party Naming
- Use official party names
- Ensure names are unique across the platform
- Use clear, recognizable short names

### 2. Data Quality
- Include accurate timestamps (`published_at`)
- Provide meaningful source names and types
- Use consistent message types across submissions

### 3. Analytics Configuration
- Configure custom keywords relevant to your party's focus areas
- Set up topic categories that match your analysis needs
- Update branding colors to match party identity

### 4. Data Management
- Regular data submissions for trending analysis
- Use bulk endpoints for large datasets
- Monitor API rate limits for high-volume submissions

### 5. Security
- Store API credentials securely
- Use HTTPS in production
- Validate data before submission

## Troubleshooting

### Common Issues

**Party Already Exists**
```json
{"detail": "Party with name 'Party Name' already exists"}
```
- Solution: Check existing parties with `GET /api/v1/parties`
- Use `PUT /api/v1/parties/{id}` to update existing party

**Invalid Party ID**
```json
{"detail": "Party with ID 999 not found or inactive"}
```
- Solution: Verify party ID with `GET /api/v1/parties`
- Ensure party is active (`active: true`)

**Message Submission Fails**
```json
{"detail": "Error processing message: ..."}
```
- Solution: Check required fields (`content`, `source_name`, `source_type`)
- Verify party_id parameter is included

### Support

For technical support or questions:
1. Check the API documentation at `/docs`
2. Review error messages in API responses
3. Verify data formats match the examples above
4. Test with single messages before bulk submissions

## Migration from Single-Party Setup

If upgrading from a single-party system:

1. **Create your existing party** using the Party API
2. **Update data submission** to include `party_id` parameter
3. **Update analytics calls** to include `party_id` for party-specific results
4. **Test dashboard** party selector functionality

The system maintains backward compatibility - existing data will be associated with the first party (ID: 1) automatically.
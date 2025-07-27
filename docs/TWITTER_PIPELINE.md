# Twitter Scraping Pipeline

This document describes the automated Twitter scraping to API pipeline that collects Twitter data and submits it to the backend API for analysis.

## Overview

The Twitter pipeline (`scripts/twitter_pipeline.py`) is a comprehensive solution that:

1. **Scrapes Twitter data** using the existing Playwright scraper
2. **Transforms data** to match the API schema format
3. **Submits data** via the bulk messages API endpoint
4. **Handles errors** with retry logic and comprehensive logging
5. **Provides monitoring** with detailed execution reports

## Quick Start

### Basic Usage

```bash
# Run pipeline with command line arguments
python scripts/twitter_pipeline.py --username politicalparty --party-id 1 --max-tweets 50

# Run with configuration file
python scripts/twitter_pipeline.py --config configs/twitter_pipeline_example.json

# Run with verbose logging
python scripts/twitter_pipeline.py --username politicalparty --party-id 1 --verbose
```

### Prerequisites

1. **API Server Running**: Ensure the FastAPI server is running on `http://localhost:8000`
2. **Party Created**: The target party must exist in the database
3. **Dependencies**: Playwright and required packages installed

```bash
# Install dependencies
uv pip install -e .
playwright install

# Start API server
uvicorn src.api.main:app --reload

# Create party (if needed)
curl -X POST "http://localhost:8000/api/v1/parties" \
  -H "Content-Type: application/json" \
  -d '{"name": "Political Party", "short_name": "PP"}'
```

## Configuration Options

### Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--config` | str | - | Path to JSON configuration file |
| `--username` | str | - | Twitter username (without @) |
| `--party-id` | int | - | Political party ID in database |
| `--api-url` | str | `http://localhost:8000` | API base URL |
| `--max-tweets` | int | 50 | Maximum tweets to scrape |
| `--batch-size` | int | 25 | API submission batch size |
| `--include-retweets` | flag | false | Include retweets in scraping |
| `--include-replies` | flag | false | Include replies in scraping |
| `--verbose` | flag | false | Enable verbose logging |

### Configuration File Format

Create a JSON configuration file (see `configs/twitter_pipeline_example.json`):

```json
{
  "api_base_url": "http://localhost:8000",
  "party_id": 1,
  "username": "politicalparty",
  "max_tweets": 100,
  "max_scroll_attempts": 15,
  "include_retweets": true,
  "include_replies": false,
  "date_limit_days": 7,
  "retry_attempts": 3,
  "retry_delay": 5,
  "batch_size": 25
}
```

## Pipeline Architecture

### Data Flow

```
Twitter/X → Playwright Scraper → Data Transform → Bulk API → Database + NLP
```

### Processing Steps

1. **API Verification**: Checks API connectivity and party existence
2. **Twitter Scraping**: Uses Playwright scraper to collect tweets
3. **Data Transformation**: Converts scraper output to API format
4. **Batch Submission**: Submits data in configurable batches
5. **Error Handling**: Retries failed requests with exponential backoff
6. **Reporting**: Provides detailed execution summary

### Error Handling

- **Connection Errors**: Retries with exponential backoff
- **API Errors**: Distinguishes between client/server errors
- **Scraper Errors**: Graceful failure with detailed logging
- **Data Errors**: Skips invalid tweets, continues processing

## Data Transformation

The pipeline automatically transforms scraped Twitter data to match the API schema:

### Input Format (from scraper)
```json
{
  "content": "Tweet text content",
  "url": "https://x.com/user/status/123",
  "published_at": "2024-01-15T10:30:00+00:00",
  "message_type": "post",
  "metadata": {
    "metrics": {"likes": 10, "retweets": 5},
    "urls": ["https://example.com"],
    "scraper": "twitter_playwright"
  }
}
```

### Output Format (to API)
```json
{
  "source_name": "@politicalparty",
  "source_type": "twitter",
  "content": "Tweet text content",
  "url": "https://x.com/user/status/123",
  "published_at": "2024-01-15T10:30:00+00:00",
  "message_type": "post",
  "geographic_scope": "national",
  "metadata": {
    "metrics": {"likes": 10, "retweets": 5},
    "scraper": "twitter_playwright_pipeline",
    "pipeline_version": "1.0"
  }
}
```

### Geographic Scope Detection

The pipeline automatically determines geographic scope based on content keywords:

- **Local**: "constituency", "local", "ward", "council", "mayor", "town"
- **Regional**: "region", "county", "scotland", "wales", "yorkshire"
- **National**: Default for all other content

## Monitoring and Logging

### Execution Summary

The pipeline provides a detailed execution report:

```
PIPELINE EXECUTION SUMMARY
==================================================
Status: success
Username: @politicalparty
Party ID: 1
Tweets scraped: 45
Tweets submitted: 42
Tweets skipped: 3
Execution time: 125.34s
```

### Exit Codes

- `0`: Success - all tweets processed successfully
- `1`: Error - pipeline failed to complete
- `2`: Partial - some tweets processed, some failed
- `130`: Interrupted - user cancelled execution

### Log Levels

- **INFO**: Standard operation messages
- **WARNING**: Non-fatal issues (duplicate tweets, etc.)
- **ERROR**: Fatal errors requiring attention
- **DEBUG**: Detailed debugging information (use `--verbose`)

## Scheduling and Automation

### Cron Setup (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add entry for daily execution at 6 AM
0 6 * * * /path/to/python /path/to/scripts/twitter_pipeline.py --config /path/to/config.json

# Add entry for every 4 hours
0 */4 * * * /path/to/python /path/to/scripts/twitter_pipeline.py --username politicalparty --party-id 1
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, weekly, etc.)
4. Set action to run Python script with arguments

### Docker/Containerized Deployment

```dockerfile
# Example Dockerfile for pipeline
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

COPY . .
CMD ["python", "scripts/twitter_pipeline.py", "--config", "configs/production.json"]
```

## Integration Examples

### Multiple Parties

```bash
# Conservative Party
python scripts/twitter_pipeline.py --username Conservatives --party-id 1

# Labour Party  
python scripts/twitter_pipeline.py --username UKLabour --party-id 2

# Liberal Democrats
python scripts/twitter_pipeline.py --username LibDems --party-id 3
```

### Custom Workflows

```python
# Custom Python integration
from scripts.twitter_pipeline import TwitterToApiPipeline, TwitterPipelineConfig

config = TwitterPipelineConfig.from_args(
    username="politicalparty",
    party_id=1,
    max_tweets=200
)

pipeline = TwitterToApiPipeline(config)
results = await pipeline.run()

print(f"Processed {results['tweets_submitted']} tweets")
```

## Troubleshooting

### Common Issues

**API Connection Failed**
```bash
# Check API server status
curl http://localhost:8000/health

# Verify API URL in configuration
```

**Party Not Found**
```bash
# List available parties
curl http://localhost:8000/api/v1/parties

# Create new party
curl -X POST "http://localhost:8000/api/v1/parties" \
  -H "Content-Type: application/json" \
  -d '{"name": "Party Name", "short_name": "PN"}'
```

**Scraper Fails**
- Check username is correct (without @)
- Verify Twitter account is public
- Check for rate limiting or access restrictions
- Try reducing `max_tweets` and `max_scroll_attempts`

**Data Not Appearing**
- Check for duplicate detection (tweets may be skipped)
- Verify party_id is correct
- Check API logs for submission errors

### Debug Mode

```bash
# Run with maximum verbosity
python scripts/twitter_pipeline.py \
  --username politicalparty \
  --party-id 1 \
  --verbose \
  --max-tweets 10
```

## Performance Considerations

### Optimization Tips

- **Batch Size**: Optimal batch size is 25-50 messages
- **Rate Limiting**: Built-in delays prevent API overload
- **Memory Usage**: Large scraping operations use minimal memory
- **Network**: Retry logic handles temporary network issues

### Scalability

- **Parallel Processing**: Run multiple pipelines for different accounts
- **Load Balancing**: Distribute across multiple API instances
- **Database**: Monitor database performance with high-volume ingestion

## Security Considerations

- **API Keys**: Store sensitive configuration in environment variables
- **Rate Limiting**: Respect Twitter's terms of service
- **Data Privacy**: Ensure compliance with data protection regulations
- **Access Control**: Secure API endpoints in production

## Future Enhancements

Potential improvements for the pipeline:

1. **Real-time Processing**: WebSocket integration for live data
2. **Advanced Filtering**: Content-based filtering and deduplication
3. **Multi-platform**: Extend to Facebook, Instagram, LinkedIn
4. **ML Integration**: Automated content classification
5. **Monitoring Dashboard**: Web interface for pipeline status
6. **Cloud Deployment**: AWS Lambda, Google Cloud Functions support

## API Integration

The pipeline integrates with these API endpoints:

- `GET /health` - API health check
- `GET /api/v1/parties/{id}` - Party verification
- `POST /api/v1/messages/bulk` - Bulk message submission

See `API_SPECIFICATION.md` for complete API documentation.
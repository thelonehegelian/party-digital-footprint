# Twitter Playwright Scraper

A robust Playwright-based scraper for collecting tweets from Twitter/X profiles with configurable parameters and anti-detection measures.

## Features

- 🎯 **Targeted Scraping**: Scrape specific Twitter profiles (e.g., @reformparty_uk)
- ⚙️ **Configurable Parameters**: Control tweet count, scroll behavior, filters
- 🛡️ **Anti-Detection**: Built-in measures to avoid bot detection
- 📊 **Rich Data**: Extracts content, metrics, timestamps, URLs
- 🔄 **Retry Logic**: Handles failures and rate limiting
- 📁 **Export Options**: JSON, CSV, and custom formats
- 🔍 **Filtering**: Include/exclude replies, retweets, date ranges

## Installation

```bash
# Install Playwright
pip install playwright

# Install browser binaries
playwright install chromium

# Install project dependencies
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from scrapers.twitter_playwright import scrape_twitter_profile

# Simple scraping
tweets = await scrape_twitter_profile(
    username="reformparty_uk",
    max_tweets=50,
    max_scroll_attempts=10
)

print(f"Scraped {len(tweets)} tweets")
```

### Advanced Configuration

```python
from scrapers.twitter_playwright import TwitterPlaywrightScraper, TwitterScrapingConfig

# Custom configuration
config = TwitterScrapingConfig(
    max_tweets=100,
    max_scroll_attempts=15,
    scroll_delay=3.0,        # Slower scrolling
    load_delay=5.0,          # Wait longer for page loads
    include_replies=False,    # Skip replies
    include_retweets=True,   # Include retweets
    date_limit_days=30       # Only tweets from last 30 days
)

scraper = TwitterPlaywrightScraper(
    username="reformparty_uk",
    config=config
)

try:
    await scraper.setup()
    tweets = await scraper.scrape()
    
    # Process tweets
    for tweet in tweets:
        print(f"Tweet: {tweet['content'][:100]}...")
        print(f"Likes: {tweet['metadata']['metrics']['likes']}")
        print(f"URL: {tweet['url']}")
        print("---")
        
finally:
    await scraper.cleanup()
```

## Configuration Options

### TwitterScrapingConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_tweets` | int | 100 | Maximum number of tweets to scrape |
| `max_scroll_attempts` | int | 10 | Maximum scroll attempts before giving up |
| `scroll_delay` | float | 2.0 | Delay between scroll actions (seconds) |
| `load_delay` | float | 3.0 | Initial page load delay (seconds) |
| `max_retries` | int | 3 | Maximum retry attempts for failed operations |
| `include_replies` | bool | False | Whether to include reply tweets |
| `include_retweets` | bool | True | Whether to include retweets |
| `date_limit_days` | int | None | Only include tweets from last N days |

## Data Structure

Each scraped tweet returns a dictionary with the following structure:

```python
{
    "content": "Tweet text content...",
    "url": "https://x.com/reformparty_uk/status/123456789",
    "published_at": "2024-01-15T10:30:00+00:00",
    "message_type": "post",
    "metadata": {
        "metrics": {
            "likes": 42,
            "retweets": 7,
            "replies": 3,
            "quotes": 1
        },
        "urls": ["https://example.com"],
        "scraper": "twitter_playwright",
        "scraped_at": "2024-01-15T12:00:00+00:00"
    },
    "raw_data": {
        "scraper": "twitter_playwright",
        "username": "reformparty_uk"
    }
}
```

## Bot Detection & Workarounds

### Common Issues

X.com has sophisticated bot detection that may cause:
- "Browser not supported" messages
- Rate limiting
- CAPTCHA challenges
- IP blocking

### Solutions

#### 1. Use Residential Proxies

```python
# Add proxy configuration to browser launch
self.browser = await self.playwright.chromium.launch(
    headless=False,
    proxy={
        "server": "http://your-proxy-server:port",
        "username": "proxy_username",
        "password": "proxy_password"
    }
)
```

#### 2. Run in Non-Headless Mode

```python
# Set headless=False in browser launch
self.browser = await self.playwright.chromium.launch(
    headless=False,  # Shows browser window
    slow_mo=50       # Slow down actions
)
```

#### 3. Use Alternative Endpoints

The scraper automatically tries these fallbacks:
- `nitter.net/{username}` (Nitter instances)
- `mobile.twitter.com/{username}` (Mobile version)

#### 4. Increase Delays

```python
config = TwitterScrapingConfig(
    scroll_delay=5.0,     # Slower scrolling
    load_delay=10.0,      # Longer load waits
    max_retries=5         # More retries
)
```

#### 5. Use VPN/Different IP

- Rotate IP addresses
- Use VPN services
- Deploy from different geographic locations

## Production Deployment

### Docker Setup

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright
RUN playwright install chromium
RUN playwright install-deps

# Copy application
COPY . /app
WORKDIR /app

CMD ["python", "examples/twitter_playwright_scraper_demo.py", "--run"]
```

### Environment Variables

```bash
# Optional proxy configuration
PROXY_SERVER=http://proxy-server:port
PROXY_USERNAME=username
PROXY_PASSWORD=password

# Scraping configuration
MAX_TWEETS=200
SCROLL_DELAY=3.0
LOAD_DELAY=5.0
```

### Scheduled Scraping

```python
import schedule
import time

async def scheduled_scrape():
    """Run scraping on schedule."""
    tweets = await scrape_twitter_profile(
        username="reformparty_uk",
        max_tweets=50
    )
    
    # Save to database or file
    with open(f"tweets_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
        json.dump(tweets, f, indent=2, default=str)

# Schedule every 6 hours
schedule.every(6).hours.do(lambda: asyncio.run(scheduled_scrape()))

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Integration with Existing System

### Using with Campaign Data Pipeline

```python
from scrapers.twitter_playwright import TwitterPlaywrightScraper
from transformers.data_transformer import DataTransformer
from models import Message

async def integrate_twitter_scraping():
    """Integrate Twitter scraping with existing system."""
    
    # Scrape tweets
    scraper = TwitterPlaywrightScraper(username="reformparty_uk")
    await scraper.setup()
    
    try:
        tweets = await scraper.scrape()
        
        # Transform to system format
        transformer = DataTransformer()
        
        for tweet in tweets:
            # Convert to Message model
            message = Message(
                content=tweet['content'],
                url=tweet['url'],
                published_at=tweet['published_at'],
                source='twitter',
                platform='x.com',
                message_type=tweet['message_type'],
                metadata=tweet['metadata']
            )
            
            # Process with existing analytics
            await process_message(message)
            
    finally:
        await scraper.cleanup()
```

## Troubleshooting

### Common Errors

#### "Browser not supported"
```
Solution: Use proxy, VPN, or alternative endpoints
```

#### Playwright import errors
```bash
pip install playwright
playwright install chromium
```

#### No tweets found
```
- Check username is correct
- Verify account is public
- Check for rate limiting
- Try increasing delays
```

#### Slow performance
```
- Reduce max_tweets
- Increase scroll_delay
- Use headless mode
- Optimize selectors
```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug output
scraper = TwitterPlaywrightScraper(
    username="reformparty_uk",
    delay=1.0  # From base class
)
```

## Legal & Ethical Considerations

### Important Notes

- ⚖️ **Terms of Service**: Respect X.com's ToS
- 🔄 **Rate Limiting**: Don't overwhelm servers
- 🔒 **Privacy**: Only scrape public content
- 📊 **Attribution**: Credit data sources appropriately
- 🛡️ **Security**: Protect scraped data appropriately

### Best Practices

1. **Reasonable Delays**: Use appropriate delays between requests
2. **Respectful Volume**: Don't scrape excessive amounts
3. **Public Content Only**: Only access publicly available tweets
4. **Data Protection**: Secure any scraped data
5. **Regular Updates**: Keep scraper updated for site changes

## Examples

See `examples/twitter_playwright_scraper_demo.py` for comprehensive usage examples including:

- Basic scraping
- Advanced configuration
- Multiple account scraping
- Data export
- Error handling

```bash
# Run the demo
python examples/twitter_playwright_scraper_demo.py --run
```

## Support

### Reporting Issues

When reporting issues, include:
- Error messages
- Configuration used
- Target username
- System information
- Whether using proxy/VPN

### Contributing

1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

### Updates

The scraper may need updates when X.com changes their structure. Common changes:
- CSS selectors
- Page layout
- Anti-bot measures
- API endpoints

Stay updated with the latest version for best compatibility. 
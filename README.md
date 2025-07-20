# Reform UK Digital Footprint Analysis

A comprehensive data collection and analysis platform for Reform UK's digital messaging across multiple platforms during political campaigns.

## Overview

This project implements **Phase 1** of the Reform UK messaging analysis system, focusing on central party messaging collection from:

- **Website**: Reform UK official website (reformparty.uk)
- **Twitter/X**: @reformparty_uk account
- **Facebook**: Official Reform UK page
- **Meta Ads Library**: Political advertisements

## Features

- 🕷️ **Multi-platform scraping** with Playwright and BeautifulSoup
- 🧠 **NLP processing** for keyword extraction using spaCy
- 📊 **Interactive dashboard** built with Streamlit
- 🗄️ **SQLite/PostgreSQL database** for structured data storage
- 📈 **Analytics and visualization** with Plotly
- 📁 **CSV export** functionality
- 🧪 **Mock data** for testing without API credentials

## Quick Start with Mock Data

### Prerequisites

- Python 3.11+
- UV package manager (recommended) or pip

### Installation

1. **Clone and setup:**
```bash
git clone <repository-url>
cd party-digital-footprint
```

2. **Install dependencies:**
```bash
# Using UV (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

3. **Install spaCy model:**
```bash
python -m spacy download en_core_web_sm
```

4. **Install Playwright browsers:**
```bash
playwright install
```

### Test with Mock Data

1. **Copy environment file:**
```bash
cp .env.example .env
```

2. **Import mock data and test system:**
```bash
python scripts/import_mock_data.py
```

3. **Run comprehensive system test:**
```bash
python scripts/test_system.py
```

4. **Launch dashboard:**
```bash
streamlit run dashboard.py
```

## Production Setup

### Database Configuration

**SQLite (default - no setup required):**
```env
DATABASE_URL=sqlite:///./reform_messaging.db
```

**PostgreSQL (production):**
```env
DATABASE_URL=postgresql://username:password@localhost:5432/reform_messaging
```

### API Credentials

Add to `.env` file:

```env
# Twitter/X API
TWITTER_BEARER_TOKEN=your_token_here

# Facebook API
FACEBOOK_ACCESS_TOKEN=your_token_here

# Meta Ads Library
META_ADS_API_TOKEN=your_token_here
```

### Setup Database

```bash
python scripts/setup_db.py
```

## Usage

### Run Complete Scraping

```bash
python scripts/run_scraper.py
```

### Run Specific Sources

```bash
# Website only
python scripts/run_scraper.py --sources website

# Twitter and Facebook
python scripts/run_scraper.py --sources twitter facebook
```

### NLP Processing Only

```bash
python scripts/run_scraper.py --nlp-only
```

### Import Mock Data

```bash
python scripts/import_mock_data.py
```

### Test System

```bash
python scripts/test_system.py
```

## Development Commands

### Testing
```bash
pytest
```

### Code Formatting
```bash
black src/ scripts/
isort src/ scripts/
```

### Linting
```bash
flake8 src/ scripts/
```

## Mock Data

The `mock-data/` folder contains realistic sample data for testing:

- **website_messages.json**: Reform UK website articles and press releases
- **twitter_messages.json**: Twitter posts with engagement metrics
- **facebook_messages.json**: Facebook posts with emojis and engagement
- **meta_ads_messages.json**: Political advertisements with targeting data

This allows you to test the complete system without API credentials.

## Architecture

### Database Schema

- **sources**: Data source configurations
- **messages**: Collected content with metadata
- **keywords**: Extracted terms and themes

### Scraper Architecture

Each scraper inherits from `BaseScraper` and implements:
- `setup()`: Initialize connections/browsers
- `scrape()`: Collect and return messages
- `cleanup()`: Close resources

### NLP Pipeline

- **Entity extraction**: People, organizations, locations
- **Political terms**: Predefined UK political vocabulary
- **Hashtag extraction**: Social media tags
- **Noun phrases**: Important multi-word terms

## Phase 1 Deliverables

✅ **Database**: SQLite/PostgreSQL schema for message storage  
✅ **Web Scraping**: Reform UK website content collection  
✅ **Social Media**: Twitter and Facebook post collection  
✅ **Ad Collection**: Meta Ads Library political ads  
✅ **NLP Processing**: Keyword and theme extraction  
✅ **Dashboard**: Streamlit analytics interface  
✅ **Export**: CSV data export functionality  
✅ **Mock Data**: Testing without API credentials  
✅ **Testing**: Comprehensive system verification  

### Expected Data Volume
- **500-2000 messages** from central sources
- **Comprehensive keyword extraction** across all content
- **Timeline analysis** of messaging patterns

## API Credentials

### Twitter/X API
1. Apply for developer access at [developer.twitter.com](https://developer.twitter.com)
2. Create a project and get Bearer Token
3. Add to `.env` file

### Facebook/Meta APIs
1. Create Facebook App at [developers.facebook.com](https://developers.facebook.com)
2. Request permissions for Pages API and Ads Library API
3. Generate access token

### Rate Limiting
- Built-in delays between requests (configurable)
- Exponential backoff for failed requests
- Respect platform rate limits

## Troubleshooting

### Common Issues

**spaCy model not found:**
```bash
python -m spacy download en_core_web_sm
```

**Playwright browser issues:**
```bash
playwright install chromium
```

**Database connection errors:**
- SQLite: No setup required, file created automatically
- PostgreSQL: Verify server is running and DATABASE_URL is correct

**API authentication errors:**
- Test with mock data first: `python scripts/import_mock_data.py`
- Verify tokens in .env file
- Check token permissions

### Testing Checklist

1. ✅ System test passes: `python scripts/test_system.py`
2. ✅ Mock data imported: `python scripts/import_mock_data.py`
3. ✅ Dashboard launches: `streamlit run dashboard.py`
4. ✅ NLP processing works (spaCy model installed)

## Next Steps (Future Phases)

- **Phase 2**: Local candidate messaging collection
- **Phase 3**: Advanced issue taxonomy and classification
- **Phase 4**: Comparative analysis with other parties
- **Phase 5**: Public-facing outputs and visualizations

## Contributing

1. Follow existing code patterns
2. Add tests for new functionality
3. Update documentation
4. Use black/isort for formatting
5. Test with mock data before real APIs

## License

This project is for research and analysis purposes.
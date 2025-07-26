# Multi-Party Political Messaging Analytics

A comprehensive analytics platform for political messaging across multiple platforms, supporting analysis of any political party or organization's digital footprint and communications strategy.

## Overview

This project implements a complete political messaging analytics system with:

- **Multi-Platform Data Collection**: Website, Twitter/X, Facebook, and Meta Ads Library
- **Advanced Analytics**: Sentiment analysis, topic modeling, and engagement metrics
- **Intelligence Reports**: Comprehensive multi-source intelligence generation
- **Interactive Dashboard**: Full-featured Streamlit interface with 7 analytical modules
- **REST API**: Complete API system for external integration

## Core Features

### 🕷️ **Data Collection & Storage**
- Multi-platform scraping with Playwright and BeautifulSoup
- Structured PostgreSQL/SQLite database with analytics tables
- Phase 2 support for candidates and constituencies
- Comprehensive metadata and raw data preservation

### 🧠 **Advanced Analytics Engine**
- **Sentiment Analysis**: Political tone detection with emotional categorization
- **Topic Modeling**: LDA-based issue classification and trending analysis
- **Engagement Analytics**: Platform-specific metrics and virality scoring
- **Intelligence Reports**: Multi-source comprehensive analysis reports

### 📊 **Interactive Dashboard**
- **Overview**: System metrics and data visualization
- **Constituencies**: Geographic analysis and constituency tracking
- **Candidates**: Individual candidate messaging analysis
- **Sentiment Analysis**: Real-time sentiment trends and political tone
- **Topic Modeling**: Issue tracking and topic evolution
- **Engagement Analytics**: Platform performance and viral content
- **Intelligence Reports**: Report generation, viewing, and export

### 🚀 **REST API System**
- Message submission (single and bulk)
- Analytics endpoints for all engines
- Intelligence report generation and export
- Comprehensive data retrieval and statistics

### 📈 **Export & Integration**
- CSV export functionality for all data types
- JSON and Markdown export for intelligence reports
- API-first architecture for external integration
- Comprehensive testing suite

## Quick Start

### For New Users
See [docs/QUICKSTART.md](docs/QUICKSTART.md) for a 5-minute setup guide.

### For API Integration
See [docs/PARTY_ONBOARDING.md](docs/PARTY_ONBOARDING.md) for complete party onboarding and API integration guide.

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

5. **Start API server (optional):**
```bash
uv run uvicorn src.api.main:app --reload
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

## Analytics System

### Sentiment Analysis

Analyze political messaging tone and emotional content:

```bash
# Run sentiment analysis on all messages
curl -X POST "http://localhost:8000/api/v1/analytics/sentiment/batch?use_dummy=true&limit=100"

# Analyze specific message
curl -X POST "http://localhost:8000/api/v1/analytics/sentiment/analyze" \
  -H "Content-Type: application/json" \
  -d '{"content": "Great news for the economy and working families!"}'

# Get sentiment trends
curl "http://localhost:8000/api/v1/analytics/sentiment/trends?days=7"
```

### Topic Modeling

Identify and track political issues and themes:

```bash
# Run topic modeling on all messages
curl -X POST "http://localhost:8000/api/v1/analytics/topics/batch?use_dummy=true&limit=100"

# Get trending topics
curl "http://localhost:8000/api/v1/analytics/topics/trending?days=7&limit=10"

# Get topic trends over time
curl "http://localhost:8000/api/v1/analytics/topics/trends?days=30"
```

### Engagement Analytics

Analyze message performance and audience interaction:

```bash
# Run engagement analysis
curl -X POST "http://localhost:8000/api/v1/analytics/engagement/batch?use_dummy=true&limit=100"

# Get platform performance comparison
curl "http://localhost:8000/api/v1/analytics/engagement/platforms"

# Get viral content analysis
curl "http://localhost:8000/api/v1/analytics/engagement/viral?threshold=0.7"
```

### Intelligence Reports

Generate comprehensive multi-source intelligence reports:

```bash
# Generate daily intelligence brief
curl -X POST "http://localhost:8000/api/v1/analytics/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "daily_brief",
    "time_period_days": 1,
    "export_format": "json"
  }'

# Generate weekly summary with filters
curl -X POST "http://localhost:8000/api/v1/analytics/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "weekly_summary",
    "time_period_days": 7,
    "entity_filter": {"source_type": "twitter"},
    "export_format": "markdown"
  }'

# List available reports
curl "http://localhost:8000/api/v1/analytics/reports/list"

# Export report in markdown format
curl "http://localhost:8000/api/v1/analytics/reports/{report_id}/export?format=markdown"
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

**Core Tables:**
- **sources**: Data source configurations and tracking
- **messages**: Collected content with comprehensive metadata
- **keywords**: Extracted terms and themes
- **constituencies**: UK parliamentary constituencies
- **candidates**: Political candidates and social media accounts

**Analytics Tables:**
- **message_sentiment**: Sentiment analysis results and political tone
- **topic_models**: LDA topic modeling configurations and coherence
- **message_topics**: Topic assignments and probabilities
- **engagement_metrics**: Platform-specific engagement and virality data

### Analytics Architecture

**Sentiment Analysis Engine:**
- Political tone detection (aggressive, diplomatic, populist, nationalist)
- Emotional categorization (anger, fear, hope, pride)
- TextBlob-based scoring with political context

**Topic Modeling Engine:**
- LDA-based political issue classification
- Trending topic analysis and growth tracking
- Issue taxonomy with coherence scoring

**Engagement Analytics Engine:**
- Platform-specific engagement scoring
- Virality prediction and influence metrics
- Cross-platform performance comparison

**Intelligence Report Generator:**
- Multi-source analytics integration
- Executive summary generation
- Actionable recommendations
- JSON and Markdown export

### API Architecture

**FastAPI REST Endpoints:**
- `/api/v1/messages/*` - Message submission and management
- `/api/v1/analytics/sentiment/*` - Sentiment analysis operations
- `/api/v1/analytics/topics/*` - Topic modeling operations
- `/api/v1/analytics/engagement/*` - Engagement analytics operations
- `/api/v1/analytics/reports/*` - Intelligence report operations

### Dashboard Architecture

**Streamlit Multi-Tab Interface:**
- Tab-based modular design
- Service layer pattern for data access
- Separation of visualization and business logic
- Session state management for user interactions

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
- **Advanced analytics**: Sentiment, topic, and engagement processing

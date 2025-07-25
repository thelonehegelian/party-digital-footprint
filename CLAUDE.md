# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive political digital footprint analysis platform designed to analyze messaging patterns across multiple platforms during political campaigns. The project provides advanced analytics including sentiment analysis, topic modeling, engagement metrics, and intelligence report generation.

## Tech Stack

**Backend:**
- FastAPI with UV for Python package management
- Pydantic for data validation and API schemas
- SQLAlchemy ORM with PostgreSQL/SQLite
- Alembic for database migrations

**Analytics:**
- TextBlob for sentiment analysis with political context
- scikit-learn for LDA topic modeling
- spaCy for NLP processing and entity extraction
- Custom engagement analytics engine

**Frontend:**
- Streamlit for interactive dashboard
- Plotly for data visualization and charts
- Pandas for data manipulation and analysis

**Development:**
- pytest for comprehensive testing
- Black and isort for code formatting
- FastAPI automatic API documentation

## Architecture

This is a data collection and analysis platform with the following key components:

### Database Schema
**Core Tables:**
- `sources` table for tracking data sources (websites, social media accounts)
- `messages` table for storing collected content with metadata
- `keywords` table for extracted terms and themes
- `constituencies` and `candidates` tables for geographic and political mapping

**Analytics Tables:**
- `message_sentiment` for sentiment analysis results and political tone
- `topic_models` for LDA topic configurations and coherence scores
- `message_topics` for topic assignments and probabilities
- `engagement_metrics` for platform-specific engagement and virality data

### Data Collection Pipeline
- Web scraping using Playwright and BeautifulSoup
- Social media data collection (Twitter, Facebook, Meta Ads)
- NLP processing for keyword extraction and issue classification
- Multi-source aggregation with timestamp tracking

### Advanced Analytics System
**Sentiment Analysis Engine:**
- Political tone detection (aggressive, diplomatic, populist, nationalist)
- Emotional categorization (anger, fear, hope, pride)
- TextBlob-based scoring with political context enhancement

**Topic Modeling Engine:**
- LDA-based political issue classification
- Trending topic analysis and growth tracking
- Issue taxonomy with coherence scoring
- Geographic and temporal topic analysis

**Engagement Analytics Engine:**
- Platform-specific engagement scoring algorithms
- Virality prediction and influence metrics
- Cross-platform performance comparison
- Audience interaction quality assessment

**Intelligence Report Generator:**
- Multi-source analytics integration and correlation
- Executive summary generation with key insights
- Actionable recommendations based on data patterns
- Multiple export formats (JSON, Markdown)

## Development Commands

### Setup
```bash
# Install dependencies
uv pip install -e .

# Install spaCy model
python -m spacy download en_core_web_sm

# Install Playwright browsers
playwright install

# Setup database
python scripts/setup_db.py
```

### Running the System
```bash
# Complete scraping pipeline
python scripts/run_scraper.py

# Specific sources only
python scripts/run_scraper.py --sources website twitter

# NLP processing only
python scripts/run_scraper.py --nlp-only

# Launch dashboard
streamlit run dashboard.py

# Start API server
uvicorn src.api.main:app --reload

# Test API functionality
python scripts/test_api.py
```

### Testing and Code Quality
```bash
pytest                    # Run tests
black src/ scripts/       # Format code
isort src/ scripts/       # Sort imports
flake8 src/ scripts/      # Lint code
```

## API System

The project includes a comprehensive REST API for data submission and integration:

### Core API Endpoints
- `POST /api/v1/messages/single` - Submit individual messages
- `POST /api/v1/messages/bulk` - Submit multiple messages (max 100)
- `GET /api/v1/sources` - List configured data sources
- `GET /api/v1/messages/stats` - Get message statistics
- `GET /api/v1/candidates` - List candidates with messaging activity
- `GET /api/v1/constituencies` - List constituencies with candidate counts

### Analytics API Endpoints
**Sentiment Analysis:**
- `POST /api/v1/analytics/sentiment/analyze` - Analyze sentiment for message/content
- `POST /api/v1/analytics/sentiment/batch` - Batch sentiment analysis
- `GET /api/v1/analytics/sentiment/trends` - Get sentiment trends over time
- `GET /api/v1/analytics/sentiment/stats` - Get sentiment statistics overview

**Topic Modeling:**
- `POST /api/v1/analytics/topics/analyze` - Analyze topics for message/content
- `POST /api/v1/analytics/topics/batch` - Batch topic analysis
- `GET /api/v1/analytics/topics/overview` - Get topic modeling overview
- `GET /api/v1/analytics/topics/trending` - Get trending topics
- `GET /api/v1/analytics/topics/trends` - Get topic trends over time
- `GET /api/v1/analytics/topics/candidates` - Get candidate topic analysis
- `GET /api/v1/analytics/topics/sentiment` - Get topic-sentiment correlation

**Engagement Analytics:**
- `POST /api/v1/analytics/engagement/analyze` - Analyze engagement for message
- `POST /api/v1/analytics/engagement/batch` - Batch engagement analysis
- `GET /api/v1/analytics/engagement/overview` - Get engagement overview
- `GET /api/v1/analytics/engagement/platforms` - Platform performance comparison
- `GET /api/v1/analytics/engagement/viral` - Get viral content analysis
- `GET /api/v1/analytics/engagement/candidates` - Candidate engagement analysis
- `GET /api/v1/analytics/engagement/trends` - Engagement trends over time

**Intelligence Reports:**
- `POST /api/v1/analytics/reports/generate` - Generate intelligence reports
- `GET /api/v1/analytics/reports/list` - List available reports
- `GET /api/v1/analytics/reports/{report_id}` - Retrieve specific report
- `GET /api/v1/analytics/reports/{report_id}/export` - Export report (JSON/Markdown)

### API Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

### Data Transformation
- **Data transformers** for each source type (website, Twitter, Facebook, Meta Ads)
- **Standardized schemas** for consistent data format
- **Automatic keyword extraction** via NLP pipeline
- **Duplicate detection** by URL and content

### Integration Examples
- See `examples/scraper_integration.py` for complete usage examples
- See `API_SPECIFICATION.md` for detailed data format documentation
- See `docs/INTELLIGENCE_REPORTS.md` for intelligence reports documentation
- External APIs can submit data using the standardized format

## Dashboard System

The project includes a comprehensive Streamlit dashboard with 7 main analytical modules:

### Dashboard Tabs
1. **📊 Overview** - System metrics and data visualization
2. **🗳️ Constituencies** - Geographic analysis and constituency tracking
3. **👥 Candidates** - Individual candidate messaging analysis
4. **🎭 Sentiment Analysis** - Real-time sentiment trends and political tone
5. **📊 Topic Modeling** - Issue tracking and topic evolution
6. **⚡ Engagement Analytics** - Platform performance and viral content
7. **📈 Intelligence Reports** - Report generation, viewing, and export

### Key Dashboard Features
- **Interactive Analytics**: Real-time analysis with dummy data generation
- **Comprehensive Visualizations**: Plotly-based charts and metrics
- **Export Capabilities**: CSV export for all data types
- **Session Management**: Persistent state across user interactions
- **Multi-Tab Navigation**: Modular design for focused analysis
- **Responsive Design**: Optimized for various screen sizes

### Dashboard Commands
```bash
# Launch interactive dashboard
streamlit run dashboard.py

# Dashboard with custom port
streamlit run dashboard.py --server.port 8502

# Dashboard in production mode
streamlit run dashboard.py --server.headless true
```

## Key Development Patterns

- Use Pydantic models for all data validation
- Store raw scraped data in JSONB fields for flexibility
- Implement proper error handling for web scraping failures
- Use TypeScript strictly throughout the frontend
- Follow Shadcn/ui component patterns for consistency

## Data Sources

The project focuses on Reform UK's digital presence:
- Official website (reformparty.uk)
- Twitter/X (@reformparty_uk)
- Facebook official pages
- Meta Ad Library for political advertisements
- Individual candidate social media accounts

## Security Considerations

- Store API keys and credentials in environment variables
- Implement rate limiting for web scraping
- Respect robots.txt and terms of service
- Use proper data anonymization for public outputs
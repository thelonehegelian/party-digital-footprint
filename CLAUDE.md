# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Reform UK digital footprint analysis project designed to create a database of their key messaging during political campaigns. The project aims to analyze messaging patterns, issue focus, and digital campaigning activity across both central party platforms and individual candidate pages.

## Tech Stack

**Backend:**
- FastAPI with UV for Python package management
- Pydantic for data validation
- Supabase for database (PostgreSQL)

**Frontend:**
- React with TypeScript
- Next.js framework
- pnpm as package manager
- Zod for validation
- Playwright for testing
- Nivo for graphs and dashboards
- Shadcn/ui with Tailwind CSS for UI components

## Architecture

This is a data collection and analysis platform with the following key components:

### Database Schema
The core data model includes:
- `sources` table for tracking data sources (websites, social media accounts)
- `messages` table for storing collected content with metadata
- `keywords` table for extracted terms and themes
- `constituencies` and `candidates` tables for geographic and political mapping

### Data Collection Pipeline
- Web scraping using Playwright and BeautifulSoup
- Social media data collection (Twitter, Facebook, Meta Ads)
- NLP processing for keyword extraction and issue classification
- Multi-source aggregation with timestamp tracking

### Analysis Components
- Issue taxonomy classification using transformer models
- Geographic analysis by constituency
- Timeline analysis of messaging patterns
- Comparative analysis across parties

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

### API Endpoints
- `POST /api/v1/messages/single` - Submit individual messages
- `POST /api/v1/messages/bulk` - Submit multiple messages (max 100)
- `GET /api/v1/sources` - List configured data sources
- `GET /api/v1/messages/stats` - Get message statistics
- `GET /docs` - Interactive API documentation

### Data Transformation
- **Data transformers** for each source type (website, Twitter, Facebook, Meta Ads)
- **Standardized schemas** for consistent data format
- **Automatic keyword extraction** via NLP pipeline
- **Duplicate detection** by URL and content

### Integration Examples
- See `examples/scraper_integration.py` for complete usage examples
- See `API_SPECIFICATION.md` for detailed data format documentation
- External APIs can submit data using the standardized format

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
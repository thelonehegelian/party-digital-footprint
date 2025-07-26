# Quick Start Guide

Get up and running with the Multi-Party Political Messaging Analytics platform in 5 minutes.

## Prerequisites

- Python 3.11+
- UV package manager
- Database (SQLite for development, PostgreSQL for production)

## Setup

### 1. Install Dependencies

```bash
uv pip install -e .
python -m spacy download en_core_web_sm
```

### 2. Initialize Database

```bash
python scripts/setup_db.py
uv run alembic upgrade head
```

### 3. Start the API Server

```bash
uvicorn src.api.main:app --reload --port 8000
```

### 4. Start the Dashboard

```bash
streamlit run dashboard.py --server.port 8501
```

## Add Your First Party

### Using cURL

```bash
curl -X POST "http://localhost:8000/api/v1/parties" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Your Party Name",
    "short_name": "YPN",
    "description": "Your party description",
    "website_url": "https://yourparty.org"
  }'
```

### Using Python

```python
import requests

party = requests.post("http://localhost:8000/api/v1/parties", json={
    "name": "Your Party Name", 
    "short_name": "YPN",
    "description": "Your party description"
}).json()

party_id = party["id"]
print(f"Created party with ID: {party_id}")
```

## Submit Your First Message

```bash
curl -X POST "http://localhost:8000/api/v1/messages/single?party_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "source_name": "Party Website",
    "source_type": "website",
    "content": "Your party announces new policy initiative",
    "message_type": "press_release"
  }'
```

## View Analytics

1. **Dashboard**: Open http://localhost:8501
   - Select your party from the sidebar
   - Explore the analytics tabs

2. **API**: Get analytics directly
   ```bash
   curl "http://localhost:8000/api/v1/analytics/sentiment/stats?party_id=1"
   ```

## Next Steps

- **Add more parties**: Use the Party API to add multiple organizations
- **Bulk import data**: Use `/api/v1/messages/bulk` for large datasets  
- **Configure analytics**: Set up custom keywords and branding
- **Explore dashboard**: Try all 7 analytics modules
- **Set up automation**: Create scripts to regularly submit new data

## Common Commands

```bash
# List all parties
curl "http://localhost:8000/api/v1/parties"

# Get party-specific message stats  
curl "http://localhost:8000/api/v1/messages/stats?party_id=1"

# View API documentation
open http://localhost:8000/docs

# View dashboard
open http://localhost:8501
```

That's it! You now have a working multi-party political messaging analytics platform.

For detailed configuration and advanced features, see the [Party Onboarding Guide](PARTY_ONBOARDING.md).
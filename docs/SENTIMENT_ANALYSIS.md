# Political Sentiment Analysis System

## Overview

The Political Sentiment Analysis System is a comprehensive analytics engine designed to analyze political messaging content for sentiment, tone, and emotional characteristics. Built specifically for political content analysis, it provides both automated sentiment detection and intelligent dummy data generation for testing and development.

## Table of Contents

- [Architecture](#architecture)
- [Core Features](#core-features)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Usage Guide](#usage-guide)
- [Testing](#testing)
- [Extension Guide](#extension-guide)
- [Performance Considerations](#performance-considerations)

## Architecture

### System Components

The sentiment analysis system consists of several interconnected components:

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer                                │
├─────────────────────────────────────────────────────────────┤
│  /analytics/sentiment/analyze    │  Individual analysis     │
│  /analytics/sentiment/batch      │  Batch processing        │
│  /analytics/sentiment/trends     │  Time-based analytics    │
│  /analytics/sentiment/stats      │  System statistics       │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                Analysis Engine                              │
├─────────────────────────────────────────────────────────────┤
│  PoliticalSentimentAnalyzer                                 │
│  ├── TextBlob Integration        │  Real analysis           │
│  ├── Political Tone Detection    │  4 tone categories       │
│  ├── Emotional Categorization    │  4 emotion types         │
│  └── Dummy Data Generation       │  Testing & development   │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                Database Layer                               │
├─────────────────────────────────────────────────────────────┤
│  MessageSentiment Table                                     │
│  ├── Sentiment scores & labels                             │
│  ├── Political tone classification                         │
│  ├── Emotional content analysis                            │
│  └── Analysis metadata & timestamps                        │
└─────────────────────────────────────────────────────────────┘
```

### Key Classes

#### `PoliticalSentimentAnalyzer`
The core analysis engine located in `src/analytics/sentiment.py`:

- **Primary Purpose**: Analyze political content for sentiment, tone, and emotion
- **Analysis Methods**: TextBlob-based real analysis and intelligent dummy generation
- **Capabilities**: Single message analysis, batch processing, trend analysis

## Core Features

### 1. Sentiment Analysis

**Basic Sentiment Detection**:
- **Range**: -1.0 (most negative) to +1.0 (most positive)
- **Classifications**: Positive (>0.1), Negative (<-0.1), Neutral (-0.1 to 0.1)
- **Engine**: TextBlob with political content optimization
- **Confidence Scoring**: 0.0 to 1.0 based on sentiment strength

```python
# Example usage
analyzer = PoliticalSentimentAnalyzer()
result = analyzer.analyze_message_sentiment("Britain needs strong leadership!")

# Result includes:
# - sentiment_score: 0.4
# - sentiment_label: "positive"  
# - confidence: 0.7
```

### 2. Political Tone Detection

**Four Tone Categories**:

| Tone | Keywords | Description |
|------|----------|-------------|
| **Aggressive** | fight, battle, destroy, attack, enemy | Confrontational language |
| **Diplomatic** | negotiate, discuss, cooperation | Collaborative language |
| **Populist** | people, working families, elite, establishment | Anti-establishment appeal |
| **Nationalist** | britain, british, sovereignty, borders | National identity focus |

**Detection Method**:
- Keyword frequency analysis
- Normalized scoring by category size
- Confidence scoring based on keyword density

### 3. Emotional Categorization

**Four Emotion Types**:

| Emotion | Keywords | Political Context |
|---------|----------|-------------------|
| **Anger** | outrage, betrayed, disgusted | Opposition messaging |
| **Fear** | crisis, threat, dangerous | Security/crisis framing |
| **Hope** | future, progress, opportunity | Positive campaigning |
| **Pride** | great, achievement, strong | National accomplishment |

### 4. Intelligent Dummy Data Generation

For testing and development, the system generates realistic sentiment data:

**Content-Based Logic**:
- Analyzes message content for political themes
- Applies realistic sentiment distributions
- Generates believable tone and emotion patterns
- Maintains statistical coherence across batches

**Key Features**:
- High confidence scores (0.7-0.95) for consistent testing
- Content-aware sentiment assignment
- Randomized but realistic emotional responses
- Balanced political tone distribution

## API Endpoints

### 1. Individual Message Analysis

```http
POST /api/v1/analytics/sentiment/analyze
```

**Request Body**:
```json
{
  "message_id": 123,          // Analyze existing message
  "content": "Text to analyze" // Or analyze provided content
}
```

**Query Parameters**:
- `use_dummy`: Boolean (default: true) - Use dummy generator or real analysis

**Response**:
```json
{
  "message_id": 123,
  "content_preview": "Britain needs strong...",
  "sentiment_score": 0.4,
  "sentiment_label": "positive",
  "confidence": 0.85,
  "political_tone": "nationalist",
  "tone_confidence": 0.7,
  "emotions": {
    "hope": 0.6,
    "pride": 0.4
  },
  "analysis_method": "dummy_generator",
  "analyzed_at": "2024-01-15T10:30:00Z"
}
```

### 2. Batch Processing

```http
POST /api/v1/analytics/sentiment/batch
```

**Query Parameters**:
- `use_dummy`: Boolean (default: true)
- `limit`: Integer (default: 100, max: 1000)

**Response**:
```json
{
  "status": "success",
  "analyzed_count": 50,
  "processing_time_seconds": 0.025,
  "analysis_method": "dummy_generator",
  "batch_limit": 100,
  "completed_at": "2024-01-15T10:30:00Z"
}
```

### 3. Sentiment Trends

```http
GET /api/v1/analytics/sentiment/trends?days=7
```

**Response**:
```json
{
  "period_days": 7,
  "daily_data": [
    {
      "date": "2024-01-15",
      "avg_sentiment": 0.2,
      "message_count": 15,
      "positive_count": 8,
      "negative_count": 3,
      "neutral_count": 4
    }
  ],
  "overall_stats": {
    "avg_sentiment": 0.15,
    "total_messages": 105,
    "sentiment_distribution": {
      "positive": 45,
      "negative": 25,
      "neutral": 35
    }
  }
}
```

### 4. System Statistics

```http
GET /api/v1/analytics/sentiment/stats
```

**Response**:
```json
{
  "total_messages": 246,
  "total_analyzed": 15,
  "analysis_coverage": 6.1,
  "sentiment_distribution": {
    "positive": 4,
    "negative": 1,
    "neutral": 10
  },
  "political_tone_distribution": {
    "aggressive": 5,
    "diplomatic": 5,
    "populist": 5
  },
  "average_sentiment_score": 0.131,
  "average_confidence": 0.814
}
```

## Database Schema

### MessageSentiment Table

```sql
CREATE TABLE message_sentiment (
    id INTEGER PRIMARY KEY,
    message_id INTEGER REFERENCES message(id),
    sentiment_score FLOAT,           -- -1.0 to 1.0
    sentiment_label VARCHAR(10),     -- positive/negative/neutral
    confidence FLOAT,                -- 0.0 to 1.0
    political_tone VARCHAR(20),      -- aggressive/diplomatic/populist/nationalist
    tone_confidence FLOAT,           -- 0.0 to 1.0
    emotions JSON,                   -- {"anger": 0.3, "hope": 0.7}
    analysis_method VARCHAR(50),     -- textblob_political/dummy_generator
    analyzed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes**:
- `idx_message_sentiment_message_id` on `message_id`
- `idx_message_sentiment_label` on `sentiment_label`
- `idx_message_sentiment_tone` on `political_tone`
- `idx_message_sentiment_analyzed_at` on `analyzed_at`

## Usage Guide

### 1. Basic Setup

```python
from src.analytics.sentiment import PoliticalSentimentAnalyzer
from src.database import get_session

# Initialize analyzer
analyzer = PoliticalSentimentAnalyzer()

# Get database session
db = next(get_session())
```

### 2. Analyze Single Message

```python
# Analyze existing message
message = db.query(Message).filter(Message.id == 1).first()
result = analyzer.generate_dummy_sentiment(message)

# Analyze arbitrary content
result = analyzer.analyze_message_sentiment("Britain needs change!")
print(f"Sentiment: {result.sentiment_label} ({result.sentiment_score:.3f})")
print(f"Tone: {result.political_tone}")
print(f"Emotions: {result.emotions}")
```

### 3. Batch Processing

```python
# Process all unanalyzed messages
analyzed_count = analyzer.analyze_batch_messages(
    db, 
    use_dummy=True,  # Use dummy data for testing
    limit=50         # Process up to 50 messages
)
print(f"Analyzed {analyzed_count} messages")
```

### 4. Trend Analysis

```python
# Get 30-day sentiment trends
trends = analyzer.get_sentiment_trends(db, days=30)
print(f"Average sentiment: {trends['overall_stats']['avg_sentiment']:.3f}")

# Access daily data
for day_data in trends['daily_data']:
    print(f"{day_data['date']}: {day_data['avg_sentiment']:.3f}")
```

### 5. API Integration

```python
import requests

# Analyze content via API
response = requests.post(
    "http://localhost:8000/api/v1/analytics/sentiment/analyze",
    json={"content": "Working families deserve better!"}
)

sentiment_data = response.json()
print(f"Political tone: {sentiment_data['political_tone']}")
```

## Testing

### Test Suite Overview

The system includes comprehensive testing in `tests/test_sentiment_analysis.py`:

**Test Categories**:
- **Engine Tests**: Core analyzer functionality
- **API Tests**: Endpoint behavior and validation
- **Data Tests**: Edge cases and validation
- **Integration Tests**: Database operations

**Key Test Classes**:

```python
class TestPoliticalSentimentAnalyzer:
    # Tests core analysis engine
    def test_real_sentiment_analysis()
    def test_dummy_sentiment_generation()
    def test_batch_analysis()
    def test_sentiment_trends()

class TestSentimentAnalysisAPI:
    # Tests REST API endpoints
    def test_analyze_single_message_by_id()
    def test_analyze_content_directly()
    def test_batch_sentiment_analysis()
    def test_sentiment_statistics_endpoint()

class TestSentimentDataValidation:
    # Tests data validation and edge cases
    def test_sentiment_score_bounds()
    def test_empty_content_handling()
    def test_long_content_handling()
```

### Running Tests

```bash
# Run all sentiment analysis tests
uv run pytest tests/test_sentiment_analysis.py -v

# Run specific test class
uv run pytest tests/test_sentiment_analysis.py::TestPoliticalSentimentAnalyzer -v

# Run with coverage
uv run pytest tests/test_sentiment_analysis.py --cov=src/analytics/sentiment
```

## Extension Guide

### 1. Adding New Political Tones

To add a new political tone category:

**Step 1**: Extend keyword dictionary in `PoliticalSentimentAnalyzer.__init__()`:

```python
self.political_keywords = {
    'aggressive': [...],
    'diplomatic': [...],
    'populist': [...],
    'nationalist': [...],
    'progressive': [  # New tone
        'reform', 'change', 'progressive', 'modern', 'forward'
    ]
}
```

**Step 2**: Update database enum (if using PostgreSQL):

```sql
ALTER TYPE political_tone_enum ADD VALUE 'progressive';
```

**Step 3**: Update API documentation and tests.

### 2. Adding New Emotions

**Step 1**: Extend emotion keywords:

```python
self.emotion_keywords = {
    'anger': [...],
    'fear': [...],
    'hope': [...],
    'pride': [...],
    'excitement': [  # New emotion
        'exciting', 'thrilling', 'amazing', 'incredible'
    ]
}
```

**Step 2**: Update dummy data generation logic in `generate_dummy_sentiment()`.

### 3. Custom Analysis Methods

**Step 1**: Create new analysis method:

```python
def analyze_message_with_custom_model(self, content: str) -> SentimentResult:
    # Your custom analysis logic
    # Must return SentimentResult object
    pass
```

**Step 2**: Update `analysis_method` field to identify your method:

```python
return SentimentResult(
    # ... other fields
    analysis_method="custom_model_v1"
)
```

### 4. Advanced Sentiment Models

**Integration with Transformer Models**:

```python
from transformers import pipeline

class AdvancedSentimentAnalyzer(PoliticalSentimentAnalyzer):
    def __init__(self):
        super().__init__()
        self.transformer_model = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment"
        )
    
    def analyze_with_transformer(self, content: str) -> SentimentResult:
        # Use transformer model for analysis
        result = self.transformer_model(content)
        # Convert to SentimentResult format
        return self._convert_transformer_result(result)
```

### 5. Custom Keyword Sets

**Domain-Specific Keywords**:

```python
class CustomPoliticalAnalyzer(PoliticalSentimentAnalyzer):
    def __init__(self, custom_keywords: Dict[str, List[str]]):
        super().__init__()
        # Merge or replace keyword sets
        self.political_keywords.update(custom_keywords)
```

### 6. Real-Time Analysis

**Streaming Processing**:

```python
import asyncio
from typing import AsyncGenerator

class StreamingSentimentAnalyzer(PoliticalSentimentAnalyzer):
    async def analyze_stream(
        self, 
        message_stream: AsyncGenerator[Message, None]
    ) -> AsyncGenerator[SentimentResult, None]:
        async for message in message_stream:
            result = self.analyze_message_sentiment(message.content)
            yield result
```

### 7. Performance Optimization

**Batch Optimization**:

```python
def analyze_batch_optimized(
    self, 
    messages: List[Message],
    batch_size: int = 100
) -> List[SentimentResult]:
    results = []
    
    # Process in chunks for memory efficiency
    for i in range(0, len(messages), batch_size):
        batch = messages[i:i + batch_size]
        batch_results = [
            self.analyze_message_sentiment(msg.content) 
            for msg in batch
        ]
        results.extend(batch_results)
    
    return results
```

**Caching Strategy**:

```python
from functools import lru_cache

class CachedSentimentAnalyzer(PoliticalSentimentAnalyzer):
    @lru_cache(maxsize=1000)
    def analyze_message_sentiment_cached(self, content: str) -> SentimentResult:
        return self.analyze_message_sentiment(content)
```

## Performance Considerations

### 1. Database Optimization

**Indexes for Performance**:
- `message_id` for joins with messages table
- `sentiment_label` for filtering by sentiment
- `political_tone` for tone-based queries
- `analyzed_at` for time-based queries

**Batch Processing Tips**:
- Use `limit` parameter to control memory usage
- Process in chunks for large datasets
- Consider database connection pooling

### 2. Analysis Performance

**TextBlob Performance**:
- TextBlob analysis: ~0.001-0.01 seconds per message
- Dummy generation: ~0.0001 seconds per message
- Batch processing: 50 messages in ~0.025 seconds

**Memory Usage**:
- Analyzer object: ~1MB
- Per message analysis: ~1KB temporary memory
- Batch processing scales linearly

### 3. API Performance

**Recommended Limits**:
- Single analysis: No practical limit
- Batch processing: 100-1000 messages per request
- Trends analysis: 90 days maximum
- Concurrent requests: 10-50 depending on hardware

**Caching Strategies**:
- Cache sentiment results in database
- Use Redis for API response caching
- Implement content-based caching for repeated analysis

### 4. Scaling Considerations

**Horizontal Scaling**:
- Stateless analyzer design allows multiple instances
- Database becomes bottleneck at scale
- Consider read replicas for analytics queries

**Queue-Based Processing**:
```python
# Example with Celery
from celery import Celery

app = Celery('sentiment_tasks')

@app.task
def analyze_message_task(message_id: int) -> dict:
    analyzer = PoliticalSentimentAnalyzer()
    # Process message and return results
    pass
```

## Monitoring and Maintenance

### 1. System Health Metrics

**Key Metrics to Monitor**:
- Analysis success rate
- Processing time per message
- API response times
- Database query performance
- Analysis coverage percentage

### 2. Data Quality Checks

**Regular Validation**:
- Sentiment score distributions
- Political tone balance
- Confidence score averages
- Analysis method distribution

### 3. Model Performance

**Accuracy Monitoring**:
- Compare dummy vs real analysis on sample data
- Track sentiment score distributions over time
- Monitor for drift in political tone classifications

## Conclusion

The Political Sentiment Analysis System provides a robust, extensible foundation for analyzing political messaging content. With its combination of real sentiment analysis capabilities and intelligent dummy data generation, it supports both production analytics and comprehensive testing workflows.

The system's API-first design, comprehensive testing suite, and modular architecture make it easy to extend and customize for specific analytical needs while maintaining reliability and performance at scale.
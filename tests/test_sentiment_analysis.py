"""
Comprehensive tests for sentiment analysis functionality.

Tests cover:
- Sentiment analysis engine functionality 
- API endpoints for sentiment analysis
- Database operations for sentiment data
- Dummy data generation and validation
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import Base, Message, MessageSentiment, Source, Candidate, Constituency
from src.api.main import app
from src.database import get_session
from src.analytics.sentiment import PoliticalSentimentAnalyzer


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_session():
    """Override database session for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_session] = override_get_session
client = TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_messages(db_session):
    """Create sample messages for testing."""
    # Create source
    source = Source(
        name="Test Twitter",
        source_type="twitter",
        url="https://twitter.com/test",
        active=True,
        last_scraped=datetime.utcnow()
    )
    db_session.add(source)
    db_session.flush()
    
    # Create constituency and candidate
    constituency = Constituency(
        name="Test Constituency",
        region="Test Region",
        constituency_type="county"
    )
    db_session.add(constituency)
    db_session.flush()
    
    candidate = Candidate(
        name="Test Candidate",
        constituency_id=constituency.id,
        social_media_accounts={"twitter": "@testcandidate"},
        candidate_type="local"
    )
    db_session.add(candidate)
    db_session.flush()
    
    # Create test messages with different sentiment patterns
    messages = [
        Message(
            source_id=source.id,
            candidate_id=candidate.id,
            content="Britain is great and we will achieve amazing success together!",
            url="https://twitter.com/test/status/1",
            published_at=datetime.utcnow(),
            message_type="tweet",
            geographic_scope="national",
            scraped_at=datetime.utcnow()
        ),
        Message(
            source_id=source.id,
            candidate_id=candidate.id,
            content="The corrupt establishment has betrayed working families and destroyed our economy.",
            url="https://twitter.com/test/status/2",
            published_at=datetime.utcnow() - timedelta(days=1),
            message_type="tweet",
            geographic_scope="national",
            scraped_at=datetime.utcnow()
        ),
        Message(
            source_id=source.id,
            candidate_id=candidate.id,
            content="We need to consider all options and find a balanced approach to this issue.",
            url="https://twitter.com/test/status/3",
            published_at=datetime.utcnow() - timedelta(days=2),
            message_type="tweet",
            geographic_scope="national",
            scraped_at=datetime.utcnow()
        )
    ]
    
    for message in messages:
        db_session.add(message)
    
    db_session.commit()
    return messages


class TestPoliticalSentimentAnalyzer:
    """Test the sentiment analysis engine directly."""
    
    def test_initialization(self):
        """Test sentiment analyzer initialization."""
        analyzer = PoliticalSentimentAnalyzer()
        
        assert analyzer.political_keywords
        assert analyzer.emotion_keywords
        assert 'aggressive' in analyzer.political_keywords
        assert 'anger' in analyzer.emotion_keywords
    
    def test_real_sentiment_analysis(self):
        """Test real sentiment analysis with TextBlob."""
        analyzer = PoliticalSentimentAnalyzer()
        
        # Positive message
        positive_result = analyzer.analyze_message_sentiment(
            "Britain is great and we will achieve amazing success!"
        )
        assert positive_result.sentiment_score > 0
        assert positive_result.sentiment_label == "positive"
        assert positive_result.confidence > 0.3
        assert positive_result.analysis_method == "textblob_political"
    
    def test_negative_sentiment_analysis(self):
        """Test negative sentiment detection."""
        analyzer = PoliticalSentimentAnalyzer()
        
        negative_result = analyzer.analyze_message_sentiment(
            "The corrupt establishment has betrayed working families and destroyed our economy."
        )
        assert negative_result.sentiment_score < 0
        assert negative_result.sentiment_label == "negative"
        assert negative_result.confidence > 0.3
    
    def test_political_tone_detection(self):
        """Test political tone classification."""
        analyzer = PoliticalSentimentAnalyzer()
        
        # Aggressive tone
        aggressive_result = analyzer.analyze_message_sentiment(
            "We must fight the corrupt establishment and destroy their lies!"
        )
        assert aggressive_result.political_tone in ["aggressive", "populist"]
        
        # Diplomatic tone
        diplomatic_result = analyzer.analyze_message_sentiment(
            "We need to consider all options and find a balanced approach through dialogue."
        )
        assert diplomatic_result.political_tone in ["diplomatic", "neutral"]
    
    def test_dummy_sentiment_generation(self, sample_messages):
        """Test dummy sentiment data generation."""
        analyzer = PoliticalSentimentAnalyzer()
        
        # Test with positive message
        positive_message = sample_messages[0]  # "Britain is great..."
        dummy_result = analyzer.generate_dummy_sentiment(positive_message)
        
        assert -1.0 <= dummy_result.sentiment_score <= 1.0
        assert dummy_result.sentiment_label in ["positive", "negative", "neutral"]
        assert 0.0 <= dummy_result.confidence <= 1.0
        assert dummy_result.political_tone in ["aggressive", "diplomatic", "populist", "nationalist"]
        assert dummy_result.analysis_method == "dummy_generator"
        assert isinstance(dummy_result.emotions, dict)
    
    def test_batch_analysis(self, db_session, sample_messages):
        """Test batch sentiment analysis."""
        analyzer = PoliticalSentimentAnalyzer()
        
        # Test with dummy data
        analyzed_count = analyzer.analyze_batch_messages(db_session, use_dummy=True)
        assert analyzed_count == 3
        
        # Verify records were created
        sentiment_records = db_session.query(MessageSentiment).all()
        assert len(sentiment_records) == 3
        
        for record in sentiment_records:
            assert -1.0 <= record.sentiment_score <= 1.0
            assert record.sentiment_label in ["positive", "negative", "neutral"]
            assert record.analysis_method == "dummy_generator"
            assert record.analyzed_at is not None
    
    def test_sentiment_trends(self, db_session, sample_messages):
        """Test sentiment trends analysis."""
        analyzer = PoliticalSentimentAnalyzer()
        
        # First analyze messages to generate sentiment data
        analyzer.analyze_batch_messages(db_session, use_dummy=True)
        
        # Get trends
        trends = analyzer.get_sentiment_trends(db_session, days=7)
        
        assert trends['period_days'] == 7
        assert 'daily_data' in trends
        assert 'overall_stats' in trends
        assert trends['overall_stats']['total_messages'] > 0


class TestSentimentAnalysisAPI:
    """Test sentiment analysis API endpoints."""
    
    def test_analyze_single_message_by_id(self, sample_messages):
        """Test analyzing existing message by ID."""
        message_id = sample_messages[0].id
        
        response = client.post(
            "/api/v1/analytics/sentiment/analyze",
            json={"message_id": message_id},
            params={"use_dummy": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message_id"] == message_id
        assert "content_preview" in data
        assert -1.0 <= data["sentiment_score"] <= 1.0
        assert data["sentiment_label"] in ["positive", "negative", "neutral"]
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["political_tone"] in ["aggressive", "diplomatic", "populist", "nationalist"]
        assert "emotions" in data
        assert data["analysis_method"] == "dummy_generator"
    
    def test_analyze_content_directly(self):
        """Test analyzing provided content directly."""
        test_content = "Britain needs strong leadership to tackle the immigration crisis!"
        
        response = client.post(
            "/api/v1/analytics/sentiment/analyze",
            json={"content": test_content},
            params={"use_dummy": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message_id"] is None
        assert test_content in data["content_preview"]
        assert -1.0 <= data["sentiment_score"] <= 1.0
        assert data["sentiment_label"] in ["positive", "negative", "neutral"]
    
    def test_analyze_existing_sentiment(self, sample_messages, db_session):
        """Test that existing sentiment is returned without reanalysis."""
        message_id = sample_messages[0].id
        
        # Create existing sentiment record
        existing_sentiment = MessageSentiment(
            message_id=message_id,
            sentiment_score=0.5,
            sentiment_label="positive",
            confidence=0.8,
            political_tone="populist",
            tone_confidence=0.7,
            emotions={"hope": 0.6},
            analysis_method="test_method",
            analyzed_at=datetime.utcnow()
        )
        db_session.add(existing_sentiment)
        db_session.commit()
        
        response = client.post(
            "/api/v1/analytics/sentiment/analyze",
            json={"message_id": message_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["sentiment_score"] == 0.5
        assert data["sentiment_label"] == "positive"
        assert data["analysis_method"] == "test_method"
    
    def test_analyze_nonexistent_message(self):
        """Test analyzing non-existent message ID."""
        response = client.post(
            "/api/v1/analytics/sentiment/analyze",
            json={"message_id": 99999}
        )
        
        assert response.status_code == 404
        assert "Message not found" in response.json()["detail"]
    
    def test_analyze_invalid_request(self):
        """Test invalid request with neither message_id nor content."""
        response = client.post(
            "/api/v1/analytics/sentiment/analyze",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
        # Check that validation error mentions required fields
    
    def test_batch_sentiment_analysis(self, sample_messages):
        """Test batch sentiment analysis endpoint."""
        response = client.post(
            "/api/v1/analytics/sentiment/batch",
            params={"use_dummy": True, "limit": 100}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["analyzed_count"] == 3
        assert data["analysis_method"] == "dummy_generator"
        assert "processing_time_seconds" in data
        assert "completed_at" in data
    
    def test_sentiment_trends_endpoint(self, sample_messages, db_session):
        """Test sentiment trends API endpoint."""
        # First run batch analysis to generate sentiment data
        client.post("/api/v1/analytics/sentiment/batch", params={"use_dummy": True})
        
        response = client.get("/api/v1/analytics/sentiment/trends?days=7")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["period_days"] == 7
        assert "daily_data" in data
        assert "overall_stats" in data
    
    def test_sentiment_statistics_endpoint(self, sample_messages):
        """Test sentiment statistics API endpoint."""
        # First run batch analysis to generate sentiment data
        client.post("/api/v1/analytics/sentiment/batch", params={"use_dummy": True})
        
        response = client.get("/api/v1/analytics/sentiment/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_messages"] == 3
        assert data["total_analyzed"] == 3
        assert data["analysis_coverage"] == 100.0
        assert "sentiment_distribution" in data
        assert "political_tone_distribution" in data
        assert "average_sentiment_score" in data
        assert "average_confidence" in data
    
    def test_sentiment_statistics_empty_db(self):
        """Test sentiment statistics with empty database."""
        response = client.get("/api/v1/analytics/sentiment/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_analyzed"] == 0
        assert data["analysis_coverage"] == 0.0
        assert data["sentiment_distribution"] == {}


class TestSentimentDataValidation:
    """Test data validation and edge cases."""
    
    def test_sentiment_score_bounds(self):
        """Test that sentiment scores are within valid bounds."""
        analyzer = PoliticalSentimentAnalyzer()
        
        # Test multiple random messages
        test_messages = [
            "This is fantastic news for Britain!",
            "Terrible corruption destroying our country.",
            "We need to consider the situation carefully.",
            "Fighting for working families against elite betrayal!",
            "Diplomatic negotiations with EU partners needed."
        ]
        
        for content in test_messages:
            result = analyzer.analyze_message_sentiment(content)
            assert -1.0 <= result.sentiment_score <= 1.0
            assert 0.0 <= result.confidence <= 1.0
            assert 0.0 <= result.tone_confidence <= 1.0
    
    def test_dummy_data_consistency(self, sample_messages):
        """Test that dummy data generation is consistent for same input."""
        analyzer = PoliticalSentimentAnalyzer()
        message = sample_messages[0]
        
        # Generate multiple dummy results for same message
        results = [analyzer.generate_dummy_sentiment(message) for _ in range(5)]
        
        # While results will vary due to randomness, they should be reasonable
        for result in results:
            assert -1.0 <= result.sentiment_score <= 1.0
            assert result.sentiment_label in ["positive", "negative", "neutral"]
            assert result.political_tone in ["aggressive", "diplomatic", "populist", "nationalist"]
            assert result.analysis_method == "dummy_generator"
    
    def test_empty_content_handling(self):
        """Test handling of empty or minimal content."""
        analyzer = PoliticalSentimentAnalyzer()
        
        # Very short content
        result = analyzer.analyze_message_sentiment("OK")
        assert result.sentiment_label in ["positive", "negative", "neutral"]
        assert result.political_tone in ["aggressive", "diplomatic", "populist", "nationalist", "neutral"]
    
    def test_long_content_handling(self):
        """Test handling of very long content."""
        analyzer = PoliticalSentimentAnalyzer()
        
        long_content = "Britain " * 1000 + "is great!"
        result = analyzer.analyze_message_sentiment(long_content)
        
        assert result.sentiment_score > 0  # Should detect positive sentiment
        assert result.sentiment_label == "positive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
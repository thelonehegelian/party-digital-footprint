"""
Comprehensive tests for sentiment analysis dashboard service.

Tests cover:
- Sentiment data retrieval and formatting
- Dashboard service functionality
- Data structure validation
- API-like data transformations
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import Base, Message, MessageSentiment, Source, Candidate, Constituency
from src.dashboard.sentiment_service import SentimentDashboardService


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_data_with_sentiment(db_session):
    """Create comprehensive sample data with sentiment analysis."""
    # Create sources
    source1 = Source(
        name="Test Twitter",
        source_type="twitter",
        url="https://twitter.com/test",
        active=True,
        last_scraped=datetime.utcnow()
    )
    source2 = Source(
        name="Test Facebook",
        source_type="facebook", 
        url="https://facebook.com/test",
        active=True,
        last_scraped=datetime.utcnow()
    )
    db_session.add_all([source1, source2])
    db_session.flush()
    
    # Create constituencies
    constituencies = [
        Constituency(name="Test Constituency 1", region="London", constituency_type="district"),
        Constituency(name="Test Constituency 2", region="South East", constituency_type="county"),
        Constituency(name="Test Constituency 3", region="North West", constituency_type="county")
    ]
    db_session.add_all(constituencies)
    db_session.flush()
    
    # Create candidates
    candidates = [
        Candidate(
            name="Alice Johnson",
            constituency_id=constituencies[0].id,
            social_media_accounts={"twitter": "@alicejohnson"},
            candidate_type="local"
        ),
        Candidate(
            name="Bob Smith", 
            constituency_id=constituencies[1].id,
            social_media_accounts={"twitter": "@bobsmith"},
            candidate_type="local"
        ),
        Candidate(
            name="Carol Davis",
            constituency_id=constituencies[2].id,
            social_media_accounts={"twitter": "@caroldavis"},
            candidate_type="local"
        )
    ]
    db_session.add_all(candidates)
    db_session.flush()
    
    # Create messages with varied content for sentiment analysis
    messages_data = [
        # Positive messages
        {
            "content": "Britain is a great nation with amazing potential for working families!",
            "candidate": candidates[0],
            "source": source1,
            "published_at": datetime.utcnow() - timedelta(days=1),
            "expected_sentiment": "positive"
        },
        {
            "content": "We will achieve incredible success and make progress for our communities!",
            "candidate": candidates[1],
            "source": source1,
            "published_at": datetime.utcnow() - timedelta(days=2),
            "expected_sentiment": "positive"
        },
        # Negative messages
        {
            "content": "The corrupt establishment has betrayed working families and destroyed our economy.",
            "candidate": candidates[2],
            "source": source2,
            "published_at": datetime.utcnow() - timedelta(days=3),
            "expected_sentiment": "negative"
        },
        {
            "content": "This crisis is a disaster caused by failed policies and broken promises.",
            "candidate": candidates[0],
            "source": source2,
            "published_at": datetime.utcnow() - timedelta(days=4),
            "expected_sentiment": "negative"
        },
        # Neutral messages
        {
            "content": "We need to consider all options and find a balanced approach to this issue.",
            "candidate": candidates[1],
            "source": source1,
            "published_at": datetime.utcnow() - timedelta(days=5),
            "expected_sentiment": "neutral"
        },
        {
            "content": "The committee will meet next week to discuss the proposed changes.",
            "candidate": candidates[2],
            "source": source1,
            "published_at": datetime.utcnow() - timedelta(days=6),
            "expected_sentiment": "neutral"
        }
    ]
    
    messages = []
    for msg_data in messages_data:
        message = Message(
            source_id=msg_data["source"].id,
            candidate_id=msg_data["candidate"].id,
            content=msg_data["content"],
            url=f"https://example.com/message/{len(messages)+1}",
            published_at=msg_data["published_at"],
            message_type="tweet",
            geographic_scope="local",
            scraped_at=datetime.utcnow()
        )
        messages.append(message)
        db_session.add(message)
    
    db_session.flush()
    
    # Create sentiment analysis records
    sentiments = [
        # Positive sentiments
        MessageSentiment(
            message_id=messages[0].id,
            sentiment_score=0.6,
            sentiment_label="positive",
            confidence=0.8,
            political_tone="populist",
            tone_confidence=0.7,
            emotions={"hope": 0.8, "pride": 0.5},
            analysis_method="dummy_generator",
            analyzed_at=datetime.utcnow()
        ),
        MessageSentiment(
            message_id=messages[1].id,
            sentiment_score=0.7,
            sentiment_label="positive",
            confidence=0.9,
            political_tone="nationalist",
            tone_confidence=0.8,
            emotions={"hope": 0.9, "pride": 0.7},
            analysis_method="dummy_generator",
            analyzed_at=datetime.utcnow()
        ),
        # Negative sentiments
        MessageSentiment(
            message_id=messages[2].id,
            sentiment_score=-0.6,
            sentiment_label="negative",
            confidence=0.8,
            political_tone="aggressive",
            tone_confidence=0.9,
            emotions={"anger": 0.8, "fear": 0.3},
            analysis_method="dummy_generator",
            analyzed_at=datetime.utcnow()
        ),
        MessageSentiment(
            message_id=messages[3].id,
            sentiment_score=-0.5,
            sentiment_label="negative",
            confidence=0.7,
            political_tone="aggressive",
            tone_confidence=0.8,
            emotions={"anger": 0.7, "fear": 0.5},
            analysis_method="dummy_generator",
            analyzed_at=datetime.utcnow()
        ),
        # Neutral sentiments
        MessageSentiment(
            message_id=messages[4].id,
            sentiment_score=0.1,
            sentiment_label="neutral",
            confidence=0.6,
            political_tone="diplomatic",
            tone_confidence=0.7,
            emotions={"neutral": 0.8},
            analysis_method="dummy_generator",
            analyzed_at=datetime.utcnow()
        ),
        MessageSentiment(
            message_id=messages[5].id,
            sentiment_score=-0.1,
            sentiment_label="neutral",
            confidence=0.6,
            political_tone="diplomatic",
            tone_confidence=0.6,
            emotions={"neutral": 0.7},
            analysis_method="dummy_generator",
            analyzed_at=datetime.utcnow()
        )
    ]
    
    db_session.add_all(sentiments)
    db_session.commit()
    
    return {
        "messages": messages,
        "sentiments": sentiments,
        "candidates": candidates,
        "constituencies": constituencies,
        "sources": [source1, source2]
    }


class TestSentimentDashboardService:
    """Test the sentiment dashboard service functionality."""
    
    def test_service_initialization(self):
        """Test sentiment dashboard service initialization."""
        service = SentimentDashboardService()
        
        assert service.analyzer is not None
        assert hasattr(service, 'get_sentiment_overview')
        assert hasattr(service, 'get_sentiment_trends')
        assert hasattr(service, 'get_candidate_sentiment_comparison')
    
    def test_get_sentiment_overview_empty_database(self, db_session):
        """Test sentiment overview with empty database."""
        service = SentimentDashboardService()
        overview = service.get_sentiment_overview(db_session)
        
        assert overview["total_messages"] == 0
        assert overview["total_analyzed"] == 0
        assert overview["analysis_coverage"] == 0.0
        assert overview["sentiment_distribution"] == {}
        assert overview["political_tone_distribution"] == {}
        assert overview["needs_analysis"] is True
    
    def test_get_sentiment_overview_with_data(self, sample_data_with_sentiment, db_session):
        """Test sentiment overview with sample data."""
        service = SentimentDashboardService()
        overview = service.get_sentiment_overview(db_session)
        
        assert overview["total_messages"] == 6
        assert overview["total_analyzed"] == 6
        assert overview["analysis_coverage"] == 100.0
        assert overview["needs_analysis"] is False
        
        # Check sentiment distribution
        sentiment_dist = overview["sentiment_distribution"]
        assert sentiment_dist["positive"] == 2
        assert sentiment_dist["negative"] == 2
        assert sentiment_dist["neutral"] == 2
        
        # Check political tone distribution
        tone_dist = overview["political_tone_distribution"]
        assert tone_dist["aggressive"] == 2
        assert tone_dist["diplomatic"] == 2
        assert tone_dist["populist"] == 1
        assert tone_dist["nationalist"] == 1
        
        # Check averages
        assert isinstance(overview["average_sentiment_score"], float)
        assert isinstance(overview["average_confidence"], float)
        assert overview["average_confidence"] > 0.5
    
    def test_get_sentiment_trends(self, sample_data_with_sentiment, db_session):
        """Test sentiment trends retrieval."""
        service = SentimentDashboardService()
        trends = service.get_sentiment_trends(db_session, days=7)
        
        assert "period_days" in trends
        assert "daily_data" in trends
        assert "overall_stats" in trends
        assert trends["period_days"] == 7
        
        # Should have overall stats due to our sample data
        overall_stats = trends["overall_stats"]
        if overall_stats["total_messages"] > 0:
            assert "avg_sentiment" in overall_stats
            assert "sentiment_distribution" in overall_stats
            assert isinstance(overall_stats["avg_sentiment"], float)
    
    def test_get_candidate_sentiment_comparison(self, sample_data_with_sentiment, db_session):
        """Test candidate sentiment comparison data."""
        service = SentimentDashboardService()
        comparison_df = service.get_candidate_sentiment_comparison(db_session, limit=10)
        
        assert not comparison_df.empty
        assert len(comparison_df) <= 3  # We have 3 candidates
        
        # Check required columns
        required_cols = [
            'candidate_name', 'candidate_id', 'message_count', 'avg_sentiment', 
            'avg_confidence', 'positive_count', 'negative_count', 'neutral_count',
            'positive_pct', 'negative_pct', 'neutral_pct'
        ]
        
        for col in required_cols:
            assert col in comparison_df.columns
        
        # Check data types and ranges
        assert comparison_df['avg_sentiment'].dtype in ['float64', 'float32']
        assert all(comparison_df['avg_confidence'] >= 0)
        assert all(comparison_df['avg_confidence'] <= 1)
        
        # Check percentage calculations
        for _, row in comparison_df.iterrows():
            total_pct = row['positive_pct'] + row['negative_pct'] + row['neutral_pct']
            assert abs(total_pct - 100.0) < 0.1  # Allow for small float precision errors
    
    def test_get_regional_sentiment_analysis(self, sample_data_with_sentiment, db_session):
        """Test regional sentiment analysis."""
        service = SentimentDashboardService()
        regional_df = service.get_regional_sentiment_analysis(db_session)
        
        assert not regional_df.empty
        assert len(regional_df) <= 3  # We have 3 regions
        
        # Check required columns
        required_cols = [
            'region', 'message_count', 'avg_sentiment', 
            'positive_count', 'negative_count', 'neutral_count',
            'positive_pct', 'negative_pct', 'neutral_pct'
        ]
        
        for col in required_cols:
            assert col in regional_df.columns
        
        # Check that our test regions are present
        regions = set(regional_df['region'].tolist())
        expected_regions = {'London', 'South East', 'North West'}
        assert regions == expected_regions
        
        # Check percentage calculations
        for _, row in regional_df.iterrows():
            total_pct = row['positive_pct'] + row['negative_pct'] + row['neutral_pct']
            assert abs(total_pct - 100.0) < 0.1
    
    def test_get_political_tone_analysis(self, sample_data_with_sentiment, db_session):
        """Test political tone analysis data."""
        service = SentimentDashboardService()
        tone_data = service.get_political_tone_analysis(db_session)
        
        assert "tone_distribution" in tone_data
        assert "tone_confidence" in tone_data
        assert "candidate_tone_data" in tone_data
        
        # Check tone distribution
        tone_dist = tone_data["tone_distribution"]
        assert tone_dist["aggressive"] == 2
        assert tone_dist["diplomatic"] == 2
        assert tone_dist["populist"] == 1
        assert tone_dist["nationalist"] == 1
        
        # Check confidence values
        tone_conf = tone_data["tone_confidence"]
        for tone, confidence in tone_conf.items():
            assert 0 <= confidence <= 1
        
        # Check candidate tone data
        candidate_tone_data = tone_data["candidate_tone_data"]
        assert len(candidate_tone_data) > 0
        
        for entry in candidate_tone_data:
            assert "candidate" in entry
            assert "political_tone" in entry
            assert "count" in entry
            assert entry["count"] > 0
    
    def test_get_detailed_messages_with_sentiment(self, sample_data_with_sentiment, db_session):
        """Test detailed messages with sentiment data."""
        service = SentimentDashboardService()
        messages_df = service.get_detailed_messages_with_sentiment(db_session, limit=10)
        
        assert not messages_df.empty
        assert len(messages_df) <= 6  # We have 6 messages with sentiment
        
        # Check required columns
        required_cols = [
            'id', 'content', 'url', 'published_at', 'source_name', 'source_type',
            'candidate_name', 'constituency_name', 'region', 'sentiment_score',
            'sentiment_label', 'confidence', 'political_tone', 'tone_confidence',
            'emotions', 'analysis_method', 'analyzed_at'
        ]
        
        for col in required_cols:
            assert col in messages_df.columns
        
        # Check data types
        assert messages_df['sentiment_score'].dtype in ['float64', 'float32']
        assert messages_df['confidence'].dtype in ['float64', 'float32']
        assert messages_df['tone_confidence'].dtype in ['float64', 'float32']
        
        # Check data ranges
        assert all(messages_df['sentiment_score'] >= -1.0)
        assert all(messages_df['sentiment_score'] <= 1.0)
        assert all(messages_df['confidence'] >= 0.0)
        assert all(messages_df['confidence'] <= 1.0)
        
        # Check that emotions are dictionaries
        for emotions in messages_df['emotions']:
            assert isinstance(emotions, dict)
    
    def test_get_detailed_messages_with_filters(self, sample_data_with_sentiment, db_session):
        """Test detailed messages with sentiment and tone filters."""
        service = SentimentDashboardService()
        
        # Test sentiment filter
        positive_messages = service.get_detailed_messages_with_sentiment(
            db_session, 
            limit=10, 
            sentiment_filter="positive"
        )
        
        assert not positive_messages.empty
        assert all(positive_messages['sentiment_label'] == "positive")
        
        # Test tone filter
        aggressive_messages = service.get_detailed_messages_with_sentiment(
            db_session,
            limit=10,
            tone_filter="aggressive"
        )
        
        assert not aggressive_messages.empty
        assert all(aggressive_messages['political_tone'] == "aggressive")
        
        # Test combined filters
        negative_aggressive = service.get_detailed_messages_with_sentiment(
            db_session,
            limit=10,
            sentiment_filter="negative",
            tone_filter="aggressive"
        )
        
        assert not negative_aggressive.empty
        assert all(negative_aggressive['sentiment_label'] == "negative")
        assert all(negative_aggressive['political_tone'] == "aggressive")
    
    def test_generate_dummy_sentiment_batch(self, db_session):
        """Test dummy sentiment data generation."""
        # First add some messages without sentiment
        source = Source(
            name="Test Source",
            source_type="twitter",
            url="https://twitter.com/test",
            active=True,
            last_scraped=datetime.utcnow()
        )
        db_session.add(source)
        db_session.flush()
        
        # Add messages without sentiment
        messages = []
        for i in range(5):
            message = Message(
                source_id=source.id,
                content=f"Test message {i} for sentiment analysis",
                url=f"https://example.com/message/{i}",
                published_at=datetime.utcnow() - timedelta(days=i),
                message_type="tweet",
                geographic_scope="local",
                scraped_at=datetime.utcnow()
            )
            messages.append(message)
            db_session.add(message)
        
        db_session.commit()
        
        # Test dummy sentiment generation
        service = SentimentDashboardService()
        result = service.generate_dummy_sentiment_batch(db_session, limit=3)
        
        assert result["success"] is True
        assert result["analyzed_count"] == 3
        assert "Successfully analyzed" in result["message"]
        
        # Verify sentiment records were created
        sentiment_count = db_session.query(MessageSentiment).count()
        assert sentiment_count == 3
    
    def test_get_emotion_analysis_data(self, sample_data_with_sentiment, db_session):
        """Test emotion analysis data retrieval."""
        service = SentimentDashboardService()
        emotion_data = service.get_emotion_analysis_data(db_session)
        
        assert "emotion_totals" in emotion_data
        assert "emotion_averages" in emotion_data
        assert "emotion_counts" in emotion_data
        assert "total_records" in emotion_data
        
        assert emotion_data["total_records"] > 0
        
        # Check that we have expected emotions from our sample data
        emotion_totals = emotion_data["emotion_totals"]
        emotion_averages = emotion_data["emotion_averages"]
        
        # Should have hope, pride, anger, fear based on our sample data
        expected_emotions = {"hope", "pride", "anger", "fear"}
        found_emotions = set(emotion_totals.keys())
        
        # At least some emotions should be present
        assert len(found_emotions.intersection(expected_emotions)) > 0
        
        # Check that averages are reasonable
        for emotion, avg_score in emotion_averages.items():
            assert 0 <= avg_score <= 1
    
    def test_empty_database_operations(self, db_session):
        """Test service operations on empty database."""
        service = SentimentDashboardService()
        
        # Test operations that should handle empty data gracefully
        comparison_df = service.get_candidate_sentiment_comparison(db_session)
        assert comparison_df.empty
        
        regional_df = service.get_regional_sentiment_analysis(db_session)
        assert regional_df.empty
        
        tone_data = service.get_political_tone_analysis(db_session)
        assert tone_data["tone_distribution"] == {}
        assert tone_data["tone_confidence"] == {}
        assert tone_data["candidate_tone_data"] == []
        
        messages_df = service.get_detailed_messages_with_sentiment(db_session)
        assert messages_df.empty
        
        emotion_data = service.get_emotion_analysis_data(db_session)
        assert emotion_data["emotion_totals"] == {}
        assert emotion_data["emotion_averages"] == {}
        assert emotion_data["total_records"] == 0


class TestSentimentDataStructures:
    """Test data structure validation and formatting."""
    
    def test_candidate_comparison_dataframe_structure(self, sample_data_with_sentiment, db_session):
        """Test candidate comparison DataFrame structure and data types."""
        service = SentimentDashboardService()
        df = service.get_candidate_sentiment_comparison(db_session)
        
        # Test column data types
        assert df['candidate_name'].dtype == 'object'
        assert df['candidate_id'].dtype in ['int64', 'int32']
        assert df['message_count'].dtype in ['int64', 'int32']
        assert df['avg_sentiment'].dtype in ['float64', 'float32']
        assert df['avg_confidence'].dtype in ['float64', 'float32']
        
        # Test percentage columns sum to 100
        for _, row in df.iterrows():
            total = row['positive_pct'] + row['negative_pct'] + row['neutral_pct']
            assert 99.9 <= total <= 100.1  # Allow for floating point precision
    
    def test_regional_analysis_dataframe_structure(self, sample_data_with_sentiment, db_session):
        """Test regional analysis DataFrame structure."""
        service = SentimentDashboardService()
        df = service.get_regional_sentiment_analysis(db_session)
        
        # Check that region names are strings
        assert df['region'].dtype == 'object'
        
        # Check that counts are integers
        count_columns = ['message_count', 'positive_count', 'negative_count', 'neutral_count']
        for col in count_columns:
            assert df[col].dtype in ['int64', 'int32']
            assert all(df[col] >= 0)
        
        # Check percentage consistency
        for _, row in df.iterrows():
            assert row['positive_count'] + row['negative_count'] + row['neutral_count'] == row['message_count']
    
    def test_detailed_messages_dataframe_structure(self, sample_data_with_sentiment, db_session):
        """Test detailed messages DataFrame structure."""
        service = SentimentDashboardService()
        df = service.get_detailed_messages_with_sentiment(db_session)
        
        # Check sentiment score range
        assert all(df['sentiment_score'] >= -1.0)
        assert all(df['sentiment_score'] <= 1.0)
        
        # Check confidence range  
        assert all(df['confidence'] >= 0.0)
        assert all(df['confidence'] <= 1.0)
        assert all(df['tone_confidence'] >= 0.0)
        assert all(df['tone_confidence'] <= 1.0)
        
        # Check sentiment labels are valid
        valid_labels = {'positive', 'negative', 'neutral'}
        assert set(df['sentiment_label'].unique()).issubset(valid_labels)
        
        # Check political tones are valid
        valid_tones = {'aggressive', 'diplomatic', 'populist', 'nationalist'}
        assert set(df['political_tone'].unique()).issubset(valid_tones)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Comprehensive tests for topic modeling API endpoints.

Tests cover:
- Topic analysis endpoints with dummy and real data
- Topic overview and statistics endpoints
- Trending topics and time-series analysis
- Candidate topic distribution
- Topic-sentiment correlation analysis
- Error handling and edge cases
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.models import Base, Message, Source, Candidate, Constituency, MessageSentiment, TopicModel, MessageTopic
from src.database import get_session


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
    db = TestingSessionLocal()
    try:
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
def sample_data_with_topics(db_session):
    """Create comprehensive sample data with topic assignments."""
    # Create sources
    sources = [
        Source(
            name="Test Twitter Account",
            source_type="twitter",
            url="https://twitter.com/test",
            active=True,
            last_scraped=datetime.utcnow()
        ),
        Source(
            name="Test Website",
            source_type="website",
            url="https://example.com",
            active=True,
            last_scraped=datetime.utcnow()
        )
    ]
    db_session.add_all(sources)
    db_session.flush()
    
    # Create constituencies and candidates
    constituencies = [
        Constituency(name="Test Constituency 1", region="London", constituency_type="district"),
        Constituency(name="Test Constituency 2", region="South East", constituency_type="county")
    ]
    db_session.add_all(constituencies)
    db_session.flush()
    
    candidates = [
        Candidate(
            name="Alice Johnson",
            constituency_id=constituencies[0].id,
            candidate_type="local"
        ),
        Candidate(
            name="Bob Smith",
            constituency_id=constituencies[1].id,
            candidate_type="local"
        )
    ]
    db_session.add_all(candidates)
    db_session.flush()
    
    # Create messages with political content
    messages_data = [
        {
            "content": "We need stronger immigration policies to protect British workers and secure our borders.",
            "candidate": candidates[0],
            "source": sources[0],
            "published_at": datetime.utcnow() - timedelta(days=1)
        },
        {
            "content": "Healthcare reform is urgent. NHS waiting times are unacceptable and patients deserve better care.",
            "candidate": candidates[1],
            "source": sources[0],
            "published_at": datetime.utcnow() - timedelta(days=2)
        },
        {
            "content": "Economic growth should be our priority. We must cut taxes and reduce government spending.",
            "candidate": candidates[0],
            "source": sources[1],
            "published_at": datetime.utcnow() - timedelta(days=3)
        },
        {
            "content": "Education standards are falling. We need better schools and improved curriculum for our children.",
            "candidate": candidates[1],
            "source": sources[1],
            "published_at": datetime.utcnow() - timedelta(days=4)
        },
        {
            "content": "Crime rates are rising. Our communities need more police officers and stronger law enforcement.",
            "candidate": candidates[0],
            "source": sources[0],
            "published_at": datetime.utcnow() - timedelta(days=5)
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
            message_type="post",
            geographic_scope="local",
            scraped_at=datetime.utcnow()
        )
        messages.append(message)
        db_session.add(message)
    
    db_session.commit()
    
    return {
        "messages": messages,
        "candidates": candidates,
        "constituencies": constituencies,
        "sources": sources
    }


class TestTopicAnalysisEndpoints:
    """Test topic analysis API endpoints."""
    
    def test_analyze_message_topics_by_content(self):
        """Test topic analysis with direct content."""
        response = client.post(
            "/api/v1/analytics/topics/analyze",
            json={"content": "We need stronger immigration policies and border security measures."},
            params={"use_dummy": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "content_preview" in data
        assert "assigned_topics" in data
        assert "primary_topic" in data
        assert "analysis_method" in data
        assert "analyzed_at" in data
        
        assert len(data["assigned_topics"]) > 0
        assert data["primary_topic"]["is_primary"] is True
        assert data["analysis_method"] == "keyword_matching_demo"
        
        # Check topic structure
        for topic in data["assigned_topics"]:
            assert "topic_name" in topic
            assert "probability" in topic
            assert "keywords" in topic
            assert "description" in topic
            assert 0.0 <= topic["probability"] <= 1.0
    
    def test_analyze_message_topics_by_id(self, sample_data_with_topics):
        """Test topic analysis with existing message ID."""
        messages = sample_data_with_topics["messages"]
        message_id = messages[0].id
        
        response = client.post(
            "/api/v1/analytics/topics/analyze",
            json={"message_id": message_id},
            params={"use_dummy": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message_id"] == message_id
        assert "assigned_topics" in data
        assert "primary_topic" in data
        assert len(data["assigned_topics"]) > 0
        
        # Check that we got real topic assignments
        for topic in data["assigned_topics"]:
            assert "topic_id" in topic
            assert "topic_name" in topic
            assert "probability" in topic
    
    def test_analyze_message_topics_invalid_input(self):
        """Test topic analysis with invalid input."""
        # No message_id or content
        response = client.post(
            "/api/v1/analytics/topics/analyze",
            json={},
            params={"use_dummy": True}
        )
        
        assert response.status_code == 400
        assert "Either message_id or content must be provided" in response.json()["detail"]
    
    def test_analyze_message_topics_not_found(self):
        """Test topic analysis with non-existent message ID."""
        response = client.post(
            "/api/v1/analytics/topics/analyze",
            json={"message_id": 99999},
            params={"use_dummy": True}
        )
        
        assert response.status_code == 404
        assert "Message not found" in response.json()["detail"]
    
    def test_batch_topic_analysis(self, sample_data_with_topics):
        """Test batch topic analysis."""
        response = client.post(
            "/api/v1/analytics/topics/batch",
            params={"use_dummy": True, "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "analyzed_count" in data
        assert "processing_time_seconds" in data
        assert data["analysis_method"] == "dummy_generator"
        assert data["batch_limit"] == 10
        assert data["regenerate"] is False
    
    def test_batch_topic_analysis_with_limit(self, sample_data_with_topics):
        """Test batch topic analysis with custom limit."""
        response = client.post(
            "/api/v1/analytics/topics/batch",
            params={"use_dummy": True, "limit": 1500}  # Over max limit
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be capped at 1000
        assert data["batch_limit"] == 1000


class TestTopicOverviewEndpoints:
    """Test topic overview and statistics endpoints."""
    
    def test_topic_overview_empty_database(self):
        """Test topic overview with empty database."""
        response = client.get("/api/v1/analytics/topics/overview")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_topics"] == 0
        assert data["total_assignments"] == 0
        assert data["coverage"] == 0.0
        assert data["needs_analysis"] is True
        assert data["top_topics"] == []
        assert data["trending_topics"] == []
    
    def test_topic_overview_with_data(self, sample_data_with_topics):
        """Test topic overview with sample data."""
        # First generate some topic assignments
        client.post(
            "/api/v1/analytics/topics/batch",
            params={"use_dummy": True, "limit": 5}
        )
        
        response = client.get("/api/v1/analytics/topics/overview")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_topics"] > 0
        assert data["total_assignments"] > 0
        assert data["coverage"] > 0.0
        assert data["needs_analysis"] is False
        assert isinstance(data["top_topics"], list)
        assert isinstance(data["trending_topics"], list)
        assert data["avg_coherence"] > 0.0
    
    def test_list_all_topics(self, sample_data_with_topics):
        """Test listing all topics."""
        # Generate topics first
        client.post(
            "/api/v1/analytics/topics/batch",
            params={"use_dummy": True, "limit": 5}
        )
        
        response = client.get("/api/v1/analytics/topics/list")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "topics" in data
        assert "total_topics" in data
        assert len(data["topics"]) > 0
        
        # Check topic structure
        for topic in data["topics"]:
            assert "id" in topic
            assert "topic_name" in topic
            assert "description" in topic
            assert "keywords" in topic
            assert "message_count" in topic
            assert "coherence_score" in topic
            assert "trend_score" in topic


class TestTrendingTopicsEndpoints:
    """Test trending topics and time-series endpoints."""
    
    def test_trending_topics_empty_database(self):
        """Test trending topics with empty database."""
        response = client.get("/api/v1/analytics/topics/trending")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["time_period_days"] == 7
        assert data["trending_topics"] == []
        assert data["total_topics"] == 0
        assert data["active_topics"] == 0
    
    def test_trending_topics_with_data(self, sample_data_with_topics):
        """Test trending topics with sample data."""
        # Generate topic assignments
        client.post(
            "/api/v1/analytics/topics/batch",
            params={"use_dummy": True, "limit": 5}
        )
        
        response = client.get(
            "/api/v1/analytics/topics/trending",
            params={"days": 7, "limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["time_period_days"] == 7
        assert data["total_topics"] > 0
        assert isinstance(data["trending_topics"], list)
        
        # Check trending topic structure
        for topic in data["trending_topics"]:
            assert "topic_name" in topic
            assert "keywords" in topic
            assert "trend_score" in topic
            assert "recent_messages" in topic
    
    def test_trending_topics_with_limits(self, sample_data_with_topics):
        """Test trending topics with parameter limits."""
        # Test day limit
        response = client.get(
            "/api/v1/analytics/topics/trending",
            params={"days": 150, "limit": 100}  # Over limits
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be capped at 90 days
        assert data["time_period_days"] == 90
    
    def test_topic_trends_over_time(self, sample_data_with_topics):
        """Test topic trends over time endpoint."""
        # Generate topic assignments
        client.post(
            "/api/v1/analytics/topics/batch",
            params={"use_dummy": True, "limit": 5}
        )
        
        response = client.get(
            "/api/v1/analytics/topics/trends",
            params={"days": 30}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["time_period_days"] == 30
        assert "daily_data" in data
        assert "topics_summary" in data
        assert "analysis_date" in data
    
    def test_topic_trends_with_specific_topic(self, sample_data_with_topics):
        """Test topic trends for specific topic."""
        # Generate topic assignments
        client.post(
            "/api/v1/analytics/topics/batch",
            params={"use_dummy": True, "limit": 5}
        )
        
        # Get a topic ID first
        topics_response = client.get("/api/v1/analytics/topics/list")
        topics = topics_response.json()["topics"]
        
        if topics:
            topic_id = topics[0]["id"]
            
            response = client.get(
                "/api/v1/analytics/topics/trends",
                params={"days": 30, "topic_id": topic_id}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["time_period_days"] == 30
            assert "daily_data" in data


class TestCandidateTopicsEndpoints:
    """Test candidate topic analysis endpoints."""
    
    def test_candidate_topics_empty_database(self):
        """Test candidate topics with empty database."""
        response = client.get("/api/v1/analytics/topics/candidates")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["candidate_topic_analysis"] == []
        assert data["total_candidates_analyzed"] == 0
    
    def test_candidate_topics_with_data(self, sample_data_with_topics):
        """Test candidate topics with sample data."""
        # Generate topic assignments
        client.post(
            "/api/v1/analytics/topics/batch",
            params={"use_dummy": True, "limit": 5}
        )
        
        response = client.get(
            "/api/v1/analytics/topics/candidates",
            params={"limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["candidate_topic_analysis"], list)
        assert data["total_candidates_analyzed"] >= 0
        
        # Check candidate topic structure
        for candidate in data["candidate_topic_analysis"]:
            assert "candidate_name" in candidate
            assert "total_messages" in candidate
            assert "top_topics" in candidate
            assert "topic_diversity" in candidate
            
            # Check topic structure
            for topic in candidate["top_topics"]:
                assert "topic_name" in topic
                assert "message_count" in topic
                assert "avg_probability" in topic
    
    def test_candidate_topics_with_limit(self, sample_data_with_topics):
        """Test candidate topics with limit parameter."""
        response = client.get(
            "/api/v1/analytics/topics/candidates",
            params={"limit": 150}  # Over max limit
        )
        
        assert response.status_code == 200
        # Should handle the limit gracefully


class TestTopicSentimentEndpoints:
    """Test topic-sentiment correlation endpoints."""
    
    def test_topic_sentiment_correlation_empty_database(self):
        """Test topic sentiment correlation with empty database."""
        response = client.get("/api/v1/analytics/topics/sentiment")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["topic_sentiment_analysis"] == []
        assert data["total_topics_analyzed"] == 0
    
    def test_topic_sentiment_correlation_with_data(self, sample_data_with_topics):
        """Test topic sentiment correlation with sample data."""
        # Generate topic assignments
        client.post(
            "/api/v1/analytics/topics/batch",
            params={"use_dummy": True, "limit": 5}
        )
        
        # Generate sentiment analysis
        client.post(
            "/api/v1/analytics/sentiment/batch",
            params={"use_dummy": True, "limit": 5}
        )
        
        response = client.get("/api/v1/analytics/topics/sentiment")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["topic_sentiment_analysis"], list)
        assert data["total_topics_analyzed"] >= 0
        
        # Check topic sentiment structure
        for topic in data["topic_sentiment_analysis"]:
            assert "topic_name" in topic
            assert "analyzed_messages" in topic
            assert "avg_sentiment" in topic
            assert "positive_count" in topic
            assert "negative_count" in topic
            assert "neutral_count" in topic
            assert "positive_pct" in topic
            assert "negative_pct" in topic
            assert "neutral_pct" in topic
            
            # Check percentage totals
            total_pct = topic["positive_pct"] + topic["negative_pct"] + topic["neutral_pct"]
            assert abs(total_pct - 100.0) < 0.1


class TestTopicAPIErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_endpoints(self):
        """Test invalid endpoint access."""
        response = client.get("/api/v1/analytics/topics/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_parameters(self, sample_data_with_topics):
        """Test endpoints with invalid parameters."""
        # Invalid day parameter (should be handled gracefully)
        response = client.get(
            "/api/v1/analytics/topics/trending",
            params={"days": -1}
        )
        assert response.status_code == 200  # Should handle gracefully
        
        # Invalid limit parameter
        response = client.get(
            "/api/v1/analytics/topics/candidates",
            params={"limit": -1}
        )
        assert response.status_code == 200  # Should handle gracefully
    
    def test_malformed_requests(self):
        """Test malformed request handling."""
        # Invalid JSON
        response = client.post(
            "/api/v1/analytics/topics/analyze",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
        # Missing required fields handled by validation
        response = client.post(
            "/api/v1/analytics/topics/analyze",
            json={"invalid_field": "value"}
        )
        assert response.status_code == 400


class TestTopicAPIIntegration:
    """Test topic API integration scenarios."""
    
    def test_complete_topic_analysis_workflow(self, sample_data_with_topics):
        """Test complete topic analysis workflow."""
        # 1. Check initial state
        overview_response = client.get("/api/v1/analytics/topics/overview")
        initial_overview = overview_response.json()
        assert initial_overview["needs_analysis"] is True
        
        # 2. Run batch analysis
        batch_response = client.post(
            "/api/v1/analytics/topics/batch",
            params={"use_dummy": True, "limit": 5}
        )
        assert batch_response.json()["status"] == "success"
        
        # 3. Check updated overview
        overview_response = client.get("/api/v1/analytics/topics/overview")
        updated_overview = overview_response.json()
        assert updated_overview["needs_analysis"] is False
        assert updated_overview["total_topics"] > 0
        
        # 4. Get trending topics
        trending_response = client.get("/api/v1/analytics/topics/trending")
        trending_data = trending_response.json()
        assert trending_data["total_topics"] > 0
        
        # 5. Analyze specific message
        messages = sample_data_with_topics["messages"]
        if messages:
            analyze_response = client.post(
                "/api/v1/analytics/topics/analyze",
                json={"message_id": messages[0].id}
            )
            analyze_data = analyze_response.json()
            assert len(analyze_data["assigned_topics"]) > 0
    
    def test_topic_sentiment_integration(self, sample_data_with_topics):
        """Test topic-sentiment analysis integration."""
        # Generate both topic and sentiment data
        client.post(
            "/api/v1/analytics/topics/batch",
            params={"use_dummy": True, "limit": 5}
        )
        
        client.post(
            "/api/v1/analytics/sentiment/batch",
            params={"use_dummy": True, "limit": 5}
        )
        
        # Test correlation endpoint
        correlation_response = client.get("/api/v1/analytics/topics/sentiment")
        correlation_data = correlation_response.json()
        
        if correlation_data["total_topics_analyzed"] > 0:
            # Verify correlation data structure
            for topic in correlation_data["topic_sentiment_analysis"]:
                assert topic["analyzed_messages"] > 0
                assert -1.0 <= topic["avg_sentiment"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
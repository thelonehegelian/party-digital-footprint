"""
Comprehensive tests for engagement analytics API endpoints.

Tests cover:
- Engagement analysis endpoints with dummy and real data
- Engagement overview and statistics endpoints
- Platform performance comparison
- Viral content analysis
- Batch engagement processing
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
from src.models import Base, Message, Source, Candidate, Constituency, EngagementMetrics, Party
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
def sample_data_with_engagement(db_session):
    """Create comprehensive sample data with engagement metrics."""
    # Create party
    party = Party(
        name="Test Progressive Party",
        short_name="TPP",
        description="Test party for engagement analytics",
        website_url="https://testparty.example.com",
        social_media_accounts={
            "twitter": "@testparty",
            "facebook": "testparty",
            "instagram": "testparty"
        },
        founded_year=2020,
        active=True
    )
    db_session.add(party)
    db_session.flush()
    
    # Create sources
    sources = [
        Source(
            name="Test Twitter Account",
            source_type="twitter",
            url="https://twitter.com/test",
            party_id=party.id,
            active=True,
            last_scraped=datetime.utcnow()
        ),
        Source(
            name="Test Facebook Page",
            source_type="facebook",
            url="https://facebook.com/test",
            party_id=party.id,
            active=True,
            last_scraped=datetime.utcnow()
        ),
        Source(
            name="Test Website",
            source_type="website",
            url="https://example.com",
            party_id=party.id,
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
            party_id=party.id,
            candidate_type="local"
        ),
        Candidate(
            name="Bob Smith",
            constituency_id=constituencies[1].id,
            party_id=party.id,
            candidate_type="local"
        )
    ]
    db_session.add_all(candidates)
    db_session.flush()
    
    # Create messages with varied content for engagement testing
    messages_data = [
        {
            "content": "Breaking: New policy announcement on immigration and border security measures.",
            "candidate": candidates[0],
            "source": sources[0],  # Twitter
            "published_at": datetime.utcnow() - timedelta(days=1)
        },
        {
            "content": "Healthcare reform update: NHS improvements and patient care initiatives launched today.",
            "candidate": candidates[1],
            "source": sources[1],  # Facebook
            "published_at": datetime.utcnow() - timedelta(days=2)
        },
        {
            "content": "Economic growth report shows positive trends in employment and business investment.",
            "candidate": candidates[0],
            "source": sources[2],  # Website
            "published_at": datetime.utcnow() - timedelta(days=3)
        },
        {
            "content": "Education policy announcement: New funding for schools and teacher training programs.",
            "candidate": candidates[1],
            "source": sources[0],  # Twitter
            "published_at": datetime.utcnow() - timedelta(days=4)
        },
        {
            "content": "Community safety initiative launched with increased police presence in local areas.",
            "candidate": candidates[0],
            "source": sources[1],  # Facebook
            "published_at": datetime.utcnow() - timedelta(days=5)
        }
    ]
    
    messages = []
    for msg_data in messages_data:
        message = Message(
            source_id=msg_data["source"].id,
            candidate_id=msg_data["candidate"].id,
            party_id=party.id,
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
        "sources": sources,
        "party": party
    }


class TestEngagementAnalysisEndpoints:
    """Test engagement analysis API endpoints."""
    
    def test_analyze_message_engagement_by_content(self):
        """Test engagement analysis with direct content."""
        response = client.post(
            "/api/v1/analytics/engagement/analyze",
            json={"content": "Breaking news: Major policy announcement on economic reforms and tax changes."},
            params={"use_dummy": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "content_preview" in data
        assert "engagement_score" in data
        assert "virality_score" in data
        assert "influence_score" in data
        assert "platform_metrics" in data
        assert "reach_metrics" in data
        assert "analysis_method" in data
        assert "analyzed_at" in data
        
        # Verify score ranges
        assert 0.0 <= data["engagement_score"] <= 1.0
        assert 0.0 <= data["virality_score"] <= 1.0
        assert 0.0 <= data["influence_score"] <= 1.0
        assert 0.0 <= data["interaction_quality"] <= 1.0
        assert 0.0 <= data["audience_relevance"] <= 1.0
        
        # Verify percentiles
        assert 0.0 <= data["platform_percentile"] <= 100.0
        assert 0.0 <= data["candidate_percentile"] <= 100.0
        
        assert data["analysis_method"] == "dummy_demo"
    
    def test_analyze_message_engagement_by_id(self, sample_data_with_engagement):
        """Test engagement analysis with existing message ID."""
        messages = sample_data_with_engagement["messages"]
        message_id = messages[0].id
        
        response = client.post(
            "/api/v1/analytics/engagement/analyze",
            json={"message_id": message_id},
            params={"use_dummy": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message_id"] == message_id
        assert "engagement_score" in data
        assert "virality_score" in data
        assert "influence_score" in data
        assert "platform_metrics" in data
        assert "reach_metrics" in data
        
        # Check that we got real engagement analysis
        assert "engagement_velocity" in data
        assert "platform_percentile" in data
        assert "candidate_percentile" in data
    
    def test_analyze_message_engagement_invalid_input(self):
        """Test engagement analysis with invalid input."""
        # No message_id or content
        response = client.post(
            "/api/v1/analytics/engagement/analyze",
            json={},
            params={"use_dummy": True}
        )
        
        assert response.status_code == 400
        assert "Either message_id or content must be provided" in response.json()["detail"]
    
    def test_analyze_message_engagement_not_found(self):
        """Test engagement analysis with non-existent message ID."""
        response = client.post(
            "/api/v1/analytics/engagement/analyze",
            json={"message_id": 99999},
            params={"use_dummy": True}
        )
        
        assert response.status_code == 404
        assert "Message not found" in response.json()["detail"]
    
    def test_batch_engagement_analysis(self, sample_data_with_engagement):
        """Test batch engagement analysis."""
        response = client.post(
            "/api/v1/analytics/engagement/batch",
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
    
    def test_batch_engagement_analysis_with_limit(self, sample_data_with_engagement):
        """Test batch engagement analysis with validation limits."""
        # Test with value over API limit - should get validation error
        response = client.post(
            "/api/v1/analytics/engagement/batch",
            params={"use_dummy": True, "limit": 1500}  # Over max limit
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test with valid high limit
        response = client.post(
            "/api/v1/analytics/engagement/batch",
            params={"use_dummy": True, "limit": 1000}  # At max limit
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be at the limit
        assert data["batch_limit"] == 1000
    
    def test_batch_engagement_analysis_regenerate(self, sample_data_with_engagement):
        """Test batch engagement analysis with regeneration."""
        # First run to create some data
        client.post(
            "/api/v1/analytics/engagement/batch",
            params={"use_dummy": True, "limit": 3}
        )
        
        # Then regenerate
        response = client.post(
            "/api/v1/analytics/engagement/batch",
            params={"use_dummy": True, "limit": 3, "regenerate": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["regenerate"] is True


class TestEngagementOverviewEndpoints:
    """Test engagement overview and statistics endpoints."""
    
    def test_engagement_overview_empty_database(self):
        """Test engagement overview with empty database."""
        response = client.get("/api/v1/analytics/engagement/overview")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_messages"] == 0
        assert data["analyzed_messages"] == 0
        assert data["coverage"] == 0.0
        assert data["needs_analysis"] is True
        assert data["avg_engagement"] == 0.0
        assert data["avg_virality"] == 0.0
        assert data["avg_influence"] == 0.0
        assert data["top_performing"] == []
    
    def test_engagement_overview_with_data(self, sample_data_with_engagement):
        """Test engagement overview with sample data."""
        # First generate some engagement analysis
        client.post(
            "/api/v1/analytics/engagement/batch",
            params={"use_dummy": True, "limit": 5}
        )
        
        response = client.get("/api/v1/analytics/engagement/overview")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_messages"] > 0
        assert data["analyzed_messages"] > 0
        assert data["coverage"] > 0.0
        assert data["needs_analysis"] is False
        assert isinstance(data["top_performing"], list)
        assert data["avg_engagement"] >= 0.0
        assert data["avg_virality"] >= 0.0
        assert data["avg_influence"] >= 0.0


class TestPlatformPerformanceEndpoints:
    """Test platform performance comparison endpoints."""
    
    def test_platform_performance_empty_database(self):
        """Test platform performance with empty database."""
        response = client.get("/api/v1/analytics/engagement/platforms")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["platform_comparison"] == []
        assert data["total_platforms"] == 0
        assert "analysis_date" in data
    
    def test_platform_performance_with_data(self, sample_data_with_engagement):
        """Test platform performance with sample data."""
        # Generate engagement analysis
        client.post(
            "/api/v1/analytics/engagement/batch",
            params={"use_dummy": True, "limit": 5}
        )
        
        response = client.get("/api/v1/analytics/engagement/platforms")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["platform_comparison"], list)
        assert data["total_platforms"] >= 0
        
        # Check platform comparison structure
        for platform in data["platform_comparison"]:
            assert "platform" in platform
            assert "message_count" in platform
            assert "avg_engagement" in platform
            assert "avg_virality" in platform
            assert "avg_influence" in platform
            
            # Verify score ranges
            assert platform["avg_engagement"] >= 0.0
            assert platform["avg_virality"] >= 0.0
            assert platform["avg_influence"] >= 0.0


class TestViralContentEndpoints:
    """Test viral content analysis endpoints."""
    
    def test_viral_content_empty_database(self):
        """Test viral content analysis with empty database."""
        response = client.get("/api/v1/analytics/engagement/viral")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["viral_threshold"] == 0.7
        assert data["viral_messages_found"] == 0
        assert data["viral_content"] == []
        assert "analysis_date" in data
    
    def test_viral_content_with_data(self, sample_data_with_engagement):
        """Test viral content analysis with sample data."""
        # Generate engagement analysis
        client.post(
            "/api/v1/analytics/engagement/batch",
            params={"use_dummy": True, "limit": 5}
        )
        
        response = client.get(
            "/api/v1/analytics/engagement/viral",
            params={"threshold": 0.5}  # Lower threshold to find content
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["viral_threshold"] == 0.5
        assert data["viral_messages_found"] >= 0
        assert isinstance(data["viral_content"], list)
        
        # Check viral content structure
        for content in data["viral_content"]:
            assert "message_id" in content
            assert "content_preview" in content
            assert "candidate_name" in content
            assert "virality_score" in content
            assert "engagement_score" in content
            assert "platform_metrics" in content
            
            # Verify virality score meets threshold
            assert content["virality_score"] >= 0.5
    
    def test_viral_content_with_threshold_limits(self, sample_data_with_engagement):
        """Test viral content with threshold parameter limits."""
        # Test threshold boundaries
        response = client.get(
            "/api/v1/analytics/engagement/viral",
            params={"threshold": 1.5}  # Over maximum
        )
        
        # Should handle gracefully (clamped to 1.0)
        assert response.status_code == 422  # Validation error for out of range
        
        response = client.get(
            "/api/v1/analytics/engagement/viral",
            params={"threshold": -0.1}  # Under minimum
        )
        
        # Should handle gracefully (clamped to 0.0)
        assert response.status_code == 422  # Validation error for out of range


class TestEngagementAPIErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_endpoints(self):
        """Test invalid endpoint access."""
        response = client.get("/api/v1/analytics/engagement/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_parameters(self, sample_data_with_engagement):
        """Test endpoints with invalid parameters."""
        # Invalid threshold parameter (handled by validation)
        response = client.get(
            "/api/v1/analytics/engagement/viral",
            params={"threshold": 2.0}
        )
        assert response.status_code == 422  # Validation error
        
        # Invalid limit parameter (should be handled gracefully)
        response = client.post(
            "/api/v1/analytics/engagement/batch",
            params={"limit": -1}
        )
        assert response.status_code == 422  # Validation error
    
    def test_malformed_requests(self):
        """Test malformed request handling."""
        # Invalid JSON
        response = client.post(
            "/api/v1/analytics/engagement/analyze",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
        # Missing required fields handled by validation
        response = client.post(
            "/api/v1/analytics/engagement/analyze",
            json={"invalid_field": "value"}
        )
        assert response.status_code == 400


class TestEngagementAPIIntegration:
    """Test engagement API integration scenarios."""
    
    def test_complete_engagement_analysis_workflow(self, sample_data_with_engagement):
        """Test complete engagement analysis workflow."""
        # 1. Check initial state
        overview_response = client.get("/api/v1/analytics/engagement/overview")
        initial_overview = overview_response.json()
        assert initial_overview["needs_analysis"] is True
        
        # 2. Run batch analysis
        batch_response = client.post(
            "/api/v1/analytics/engagement/batch",
            params={"use_dummy": True, "limit": 5}
        )
        assert batch_response.json()["status"] == "success"
        
        # 3. Check updated overview
        overview_response = client.get("/api/v1/analytics/engagement/overview")
        updated_overview = overview_response.json()
        assert updated_overview["needs_analysis"] is False
        assert updated_overview["analyzed_messages"] > 0
        
        # 4. Get platform performance
        platform_response = client.get("/api/v1/analytics/engagement/platforms")
        platform_data = platform_response.json()
        assert platform_data["total_platforms"] > 0
        
        # 5. Check viral content
        viral_response = client.get("/api/v1/analytics/engagement/viral")
        viral_data = viral_response.json()
        assert viral_data["viral_messages_found"] >= 0
        
        # 6. Analyze specific message
        messages = sample_data_with_engagement["messages"]
        if messages:
            analyze_response = client.post(
                "/api/v1/analytics/engagement/analyze",
                json={"message_id": messages[0].id}
            )
            analyze_data = analyze_response.json()
            assert analyze_data["engagement_score"] >= 0.0
    
    def test_platform_specific_analysis(self, sample_data_with_engagement):
        """Test platform-specific engagement analysis."""
        # Generate engagement data
        client.post(
            "/api/v1/analytics/engagement/batch",
            params={"use_dummy": True, "limit": 5}
        )
        
        # Get platform comparison
        platform_response = client.get("/api/v1/analytics/engagement/platforms")
        platform_data = platform_response.json()
        
        # Verify we have different platforms
        platforms = [p["platform"] for p in platform_data["platform_comparison"]]
        expected_platforms = ["twitter", "facebook", "website"]
        
        # Check that we have some of the expected platforms
        for platform in platforms:
            assert platform in expected_platforms + ["demo"]
    
    def test_engagement_score_consistency(self, sample_data_with_engagement):
        """Test engagement score calculation consistency."""
        messages = sample_data_with_engagement["messages"]
        
        if messages:
            # Analyze same message multiple times
            message_id = messages[0].id
            
            # First analysis
            response1 = client.post(
                "/api/v1/analytics/engagement/analyze",
                json={"message_id": message_id},
                params={"use_dummy": True}
            )
            
            # Second analysis (should return existing data)
            response2 = client.post(
                "/api/v1/analytics/engagement/analyze",
                json={"message_id": message_id},
                params={"use_dummy": True}
            )
            
            data1 = response1.json()
            data2 = response2.json()
            
            # Scores should be identical (using existing data)
            assert data1["engagement_score"] == data2["engagement_score"]
            assert data1["virality_score"] == data2["virality_score"]
            assert data1["influence_score"] == data2["influence_score"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
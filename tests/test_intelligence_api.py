"""
Tests for intelligence report API endpoints.

Comprehensive test suite for intelligence report generation system including:
- Report generation with various types and parameters
- Report listing and retrieval functionality  
- Export functionality in JSON and Markdown formats
- Error handling and validation testing
- Integration with sentiment, topic, and engagement analytics
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from src.api.main import app
from src.database import Base, get_session
from src.models import Message, Source, Candidate, Constituency


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_intelligence.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_session():
    """Override database session for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_session] = override_get_session
client = TestClient(app)


@pytest.fixture
def test_db():
    """Create test database with sample data."""
    db = TestingSessionLocal()
    
    # Clear existing data
    db.query(Message).delete()
    db.query(Source).delete()
    db.query(Candidate).delete()
    db.query(Constituency).delete()
    
    # Create test constituency
    constituency = Constituency(
        name="Test Constituency",
        region="England",
        constituency_type="county"
    )
    db.add(constituency)
    db.flush()
    
    # Create test candidate
    candidate = Candidate(
        name="Test Candidate",
        constituency_id=constituency.id,
        social_media_accounts={"twitter": "@testcandidate"},
        candidate_type="local"
    )
    db.add(candidate)
    db.flush()
    
    # Create test source
    source = Source(
        name="Test Source",
        source_type="twitter",
        url="https://twitter.com/testsource",
        active=True
    )
    db.add(source)
    db.flush()
    
    # Create test messages
    messages = [
        Message(
            source_id=source.id,
            candidate_id=candidate.id,
            content="Test message about immigration policy changes",
            url="https://example.com/1",
            published_at=datetime.now() - timedelta(days=1),
            message_type="tweet",
            geographic_scope="local"
        ),
        Message(
            source_id=source.id,
            candidate_id=candidate.id,
            content="Economic policy announcement for local businesses",
            url="https://example.com/2",
            published_at=datetime.now() - timedelta(days=2),
            message_type="tweet",
            geographic_scope="local"
        ),
        Message(
            source_id=source.id,
            content="Healthcare system improvements needed urgently",
            url="https://example.com/3",
            published_at=datetime.now() - timedelta(days=3),
            message_type="article",
            geographic_scope="national"
        )
    ]
    
    for message in messages:
        db.add(message)
    
    db.commit()
    
    yield db
    
    # Cleanup
    db.query(Message).delete()
    db.query(Source).delete()
    db.query(Candidate).delete()
    db.query(Constituency).delete()
    db.commit()
    db.close()


class TestIntelligenceReportGeneration:
    """Test intelligence report generation functionality."""
    
    def test_generate_daily_brief(self, test_db):
        """Test generating a daily brief intelligence report."""
        response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "daily_brief",
            "time_period_days": 1,
            "export_format": "json"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["report_type"] == "daily_brief"
        assert data["title"] == "Daily Intelligence Brief (24-Hour)"
        assert "executive_summary" in data
        assert "sections" in data
        assert "recommendations" in data
        assert len(data["sections"]) > 0
        assert len(data["recommendations"]) > 0
        assert data["data_sources"] == ["sentiment_analysis", "topic_modeling", "engagement_metrics"]
    
    def test_generate_weekly_summary(self, test_db):
        """Test generating a weekly summary intelligence report."""
        response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "weekly_summary",
            "time_period_days": 7,
            "export_format": "json"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["report_type"] == "weekly_summary"
        assert data["title"] == "Weekly Analysis Summary (7-Day)"
        assert "executive_summary" in data
        assert "sections" in data
        assert "recommendations" in data
        assert "time_period" in data
        assert "start" in data["time_period"]
        assert "end" in data["time_period"]
    
    def test_generate_monthly_analysis(self, test_db):
        """Test generating a monthly analysis intelligence report."""
        response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "monthly_analysis",
            "time_period_days": 30,
            "export_format": "json"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["report_type"] == "monthly_analysis"
        assert data["title"] == "Monthly Intelligence Analysis (30-Day)"
        assert len(data["sections"]) >= 3  # Should have multiple sections
    
    def test_generate_campaign_overview(self, test_db):
        """Test generating a campaign overview intelligence report."""
        response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "campaign_overview",
            "time_period_days": 14,
            "export_format": "json"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["report_type"] == "campaign_overview"
        assert len(data["sections"]) > 0  # Should have sections
    
    def test_generate_with_entity_filter(self, test_db):
        """Test generating report with entity filter."""
        response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "weekly_summary",
            "time_period_days": 7,
            "entity_filter": {"source_type": "twitter"},
            "export_format": "json"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Twitter Analysis" in data["title"]
        assert data["metadata"]["entity_filter"]["source_type"] == "twitter"
    
    def test_invalid_report_type(self, test_db):
        """Test error handling for invalid report type."""
        response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "invalid_type",
            "time_period_days": 7
        })
        
        assert response.status_code == 400
        assert "Invalid report_type" in response.json()["detail"]
    
    def test_invalid_time_period(self, test_db):
        """Test validation for time period limits."""
        response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "daily_brief",
            "time_period_days": 500  # Exceeds maximum
        })
        
        assert response.status_code == 422  # Validation error


class TestIntelligenceReportListing:
    """Test intelligence report listing functionality."""
    
    def test_list_all_reports(self, test_db):
        """Test listing all available intelligence reports."""
        response = client.get("/api/v1/analytics/reports/list")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "reports" in data
        assert "total_reports" in data
        assert "report_types" in data
        assert len(data["report_types"]) == 7  # All available report types
        assert "daily_brief" in data["report_types"]
        assert "weekly_summary" in data["report_types"]
    
    def test_list_reports_with_type_filter(self, test_db):
        """Test listing reports filtered by type."""
        response = client.get("/api/v1/analytics/reports/list?report_type=daily_brief")
        
        assert response.status_code == 200
        data = response.json()
        
        # All reports should be of the filtered type
        for report in data["reports"]:
            assert report["report_type"] == "daily_brief"
    
    def test_list_reports_with_limit(self, test_db):
        """Test listing reports with limit parameter."""
        response = client.get("/api/v1/analytics/reports/list?limit=3")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["reports"]) <= 3


class TestIntelligenceReportRetrieval:
    """Test intelligence report retrieval functionality."""
    
    def test_get_specific_report(self, test_db):
        """Test retrieving a specific intelligence report."""
        # First generate a report to get a valid ID format
        generate_response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "daily_brief",
            "time_period_days": 1
        })
        assert generate_response.status_code == 200
        report_id = generate_response.json()["report_id"]
        
        # Now retrieve it
        response = client.get(f"/api/v1/analytics/reports/{report_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["report_id"] == report_id
        assert data["report_type"] == "daily_brief"
        assert "sections" in data
        assert "executive_summary" in data
    
    def test_get_nonexistent_report(self, test_db):
        """Test error handling for nonexistent report."""
        response = client.get("/api/v1/analytics/reports/nonexistent_20241231_000")
        
        assert response.status_code == 404
        assert "Report not found" in response.json()["detail"]
    
    def test_get_report_invalid_id_format(self, test_db):
        """Test error handling for invalid report ID format."""
        response = client.get("/api/v1/analytics/reports/invalid")
        
        assert response.status_code == 400
        assert "Invalid report_id format" in response.json()["detail"]


class TestIntelligenceReportExport:
    """Test intelligence report export functionality."""
    
    def test_export_report_json(self, test_db):
        """Test exporting report in JSON format."""
        # Generate a report first
        generate_response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "weekly_summary",
            "time_period_days": 7
        })
        report_id = generate_response.json()["report_id"]
        
        # Export as JSON
        response = client.get(f"/api/v1/analytics/reports/{report_id}/export?format=json")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["export_format"] == "json"
        assert data["report_id"] == report_id
        assert data["filename"].endswith(".json")
        
        # Verify content is valid JSON
        exported_content = json.loads(data["content"])
        assert "report_id" in exported_content
        assert "sections" in exported_content
    
    def test_export_report_markdown(self, test_db):
        """Test exporting report in Markdown format."""
        # Generate a report first
        generate_response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "daily_brief",
            "time_period_days": 1
        })
        report_id = generate_response.json()["report_id"]
        
        # Export as Markdown
        response = client.get(f"/api/v1/analytics/reports/{report_id}/export?format=markdown")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["export_format"] == "markdown"
        assert data["report_id"] == report_id
        assert data["filename"].endswith(".md")
        
        # Verify content contains Markdown formatting
        content = data["content"]
        assert "# " in content  # Header
        assert "## " in content  # Subheaders
        assert "**" in content  # Bold text
    
    def test_export_invalid_format(self, test_db):
        """Test error handling for invalid export format."""
        response = client.get("/api/v1/analytics/reports/test_id/export?format=invalid")
        
        assert response.status_code == 400
        assert "Invalid export format" in response.json()["detail"]
    
    def test_export_nonexistent_report(self, test_db):
        """Test error handling for exporting nonexistent report."""
        response = client.get("/api/v1/analytics/reports/nonexistent_20241231_000/export")
        
        assert response.status_code == 404
        assert "Report not found" in response.json()["detail"]


class TestIntelligenceReportContent:
    """Test intelligence report content quality and structure."""
    
    def test_report_sections_structure(self, test_db):
        """Test that report sections have proper structure."""
        response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "weekly_summary",
            "time_period_days": 7
        })
        
        assert response.status_code == 200
        data = response.json()
        
        for section in data["sections"]:
            assert "title" in section
            assert "content" in section
            assert "data" in section
            assert "visualizations" in section
            assert "priority" in section
            assert section["priority"] in ["high", "medium", "low"]
    
    def test_executive_summary_quality(self, test_db):
        """Test executive summary content quality."""
        response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "daily_brief",
            "time_period_days": 1
        })
        
        assert response.status_code == 200
        data = response.json()
        
        executive_summary = data["executive_summary"]
        assert len(executive_summary) > 50  # Should be substantial
        assert "message" in executive_summary.lower()  # Should mention messages
    
    def test_recommendations_quality(self, test_db):
        """Test recommendations content quality."""
        response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "weekly_summary",
            "time_period_days": 7
        })
        
        assert response.status_code == 200
        data = response.json()
        
        recommendations = data["recommendations"]
        assert len(recommendations) >= 1  # Should have at least one recommendation
        
        for recommendation in recommendations:
            assert len(recommendation) > 20  # Should be meaningful
            assert isinstance(recommendation, str)
    
    def test_metadata_completeness(self, test_db):
        """Test report metadata completeness."""
        response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "campaign_overview",
            "time_period_days": 14,
            "entity_filter": {"source_type": "twitter"}
        })
        
        assert response.status_code == 200
        data = response.json()
        
        metadata = data["metadata"]
        assert "time_period_days" in metadata
        assert "entity_filter" in metadata
        assert "total_messages_analyzed" in metadata
        assert "data_completeness" in metadata
        assert metadata["time_period_days"] == 14
        assert metadata["entity_filter"]["source_type"] == "twitter"


class TestIntelligenceReportIntegration:
    """Test integration with other analytics systems."""
    
    def test_integration_with_all_analytics(self, test_db):
        """Test that reports integrate data from all analytics systems."""
        # Generate some analytics data first
        client.post("/api/v1/analytics/sentiment/batch?use_dummy=true&limit=10")
        client.post("/api/v1/analytics/topics/batch?use_dummy=true&limit=10")
        client.post("/api/v1/analytics/engagement/batch?use_dummy=true&limit=10")
        
        # Generate intelligence report
        response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "weekly_summary",
            "time_period_days": 7
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Should reference all three analytics systems
        data_sources = data["data_sources"]
        assert "sentiment_analysis" in data_sources
        assert "topic_modeling" in data_sources
        assert "engagement_metrics" in data_sources
    
    def test_empty_database_handling(self, test_db):
        """Test report generation with empty database."""
        # Clear all messages
        db = TestingSessionLocal()
        db.query(Message).delete()
        db.commit()
        db.close()
        
        response = client.post("/api/v1/analytics/reports/generate", json={
            "report_type": "daily_brief",
            "time_period_days": 1
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Should handle empty data gracefully
        assert "No messaging activity" in data["executive_summary"]
        assert data["metadata"]["total_messages_analyzed"] == 0


if __name__ == "__main__":
    pytest.main([__file__])
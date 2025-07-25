"""
Comprehensive tests for search functionality.
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.database import get_session
from src.models import Source, Message, Keyword, Candidate, Constituency, MessageSentiment
from src.api.schemas import SearchRequest, AutocompleteRequest


class TestSearchAPI:
    """Test the search API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def test_db(self):
        """Create test database session."""
        # This would be set up with test database
        pass
    
    @pytest.fixture
    def sample_data(self, test_db):
        """Create sample data for testing."""
        # Create test sources
        source1 = Source(
            name="Test Twitter",
            source_type="twitter",
            url="https://twitter.com/test",
            active=True
        )
        
        source2 = Source(
            name="Test Website",
            source_type="website", 
            url="https://test-website.com",
            active=True
        )
        
        # Create test constituency and candidate
        constituency = Constituency(
            name="Test Constituency",
            region="Test Region",
            constituency_type="district"
        )
        
        candidate = Candidate(
            name="John Smith",
            constituency=constituency,
            candidate_type="local",
            social_media_accounts={"twitter": "@johnsmith"}
        )
        
        # Create test messages
        message1 = Message(
            source=source1,
            candidate=candidate,
            content="This is a test message about immigration policy and economic reform",
            url="https://twitter.com/test/status/123",
            published_at=datetime.now() - timedelta(days=1),
            message_type="tweet",
            geographic_scope="national"
        )
        
        message2 = Message(
            source=source2,
            content="Healthcare reform is essential for our future prosperity",
            url="https://test-website.com/healthcare-reform",
            published_at=datetime.now() - timedelta(days=2),
            message_type="article",
            geographic_scope="national"
        )
        
        # Create test keywords
        keyword1 = Keyword(
            message=message1,
            keyword="immigration",
            confidence=0.95,
            extraction_method="nlp"
        )
        
        keyword2 = Keyword(
            message=message1,
            keyword="economic reform",
            confidence=0.88,
            extraction_method="nlp"
        )
        
        keyword3 = Keyword(
            message=message2,
            keyword="healthcare",
            confidence=0.92,
            extraction_method="nlp"
        )
        
        # Create test sentiment
        sentiment1 = MessageSentiment(
            message=message1,
            sentiment_score=0.3,
            sentiment_label="positive",
            confidence=0.85,
            political_tone="diplomatic",
            tone_confidence=0.78
        )
        
        test_db.add_all([
            source1, source2, constituency, candidate,
            message1, message2, keyword1, keyword2, keyword3, sentiment1
        ])
        test_db.commit()
        
        return {
            'sources': [source1, source2],
            'messages': [message1, message2],
            'keywords': [keyword1, keyword2, keyword3],
            'candidates': [candidate],
            'constituencies': [constituency]
        }
    
    def test_search_messages_basic(self, client, sample_data):
        """Test basic message search."""
        search_data = {
            "query": "immigration",
            "search_types": ["messages"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["query"] == "immigration"
        assert result["total_results"] >= 1
        assert "messages" in result["results"]
        assert result["results"]["messages"]["count"] >= 1
        
        message_result = result["results"]["messages"]["items"][0]
        assert "immigration" in message_result["content"].lower()
        assert message_result["source_type"] == "twitter"
        assert message_result["candidate_name"] == "John Smith"
    
    def test_search_messages_with_filters(self, client, sample_data):
        """Test message search with various filters."""
        # Test source type filter
        search_data = {
            "query": "reform",
            "search_types": ["messages"],
            "source_types": ["twitter"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        for message in result["results"]["messages"]["items"]:
            assert message["source_type"] == "twitter"
    
    def test_search_messages_date_filter(self, client, sample_data):
        """Test message search with date filters."""
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        
        search_data = {
            "query": "test",
            "search_types": ["messages"],
            "date_from": yesterday,
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        for message in result["results"]["messages"]["items"]:
            message_date = datetime.fromisoformat(message["published_at"].replace('Z', '+00:00'))
            assert message_date >= datetime.fromisoformat(yesterday)
    
    def test_search_messages_sentiment_filter(self, client, sample_data):
        """Test message search with sentiment filter."""
        search_data = {
            "query": "immigration",
            "search_types": ["messages"],
            "sentiment_filter": "positive",
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        for message in result["results"]["messages"]["items"]:
            if message["sentiment_label"]:
                assert message["sentiment_label"] == "positive"
    
    def test_search_keywords(self, client, sample_data):
        """Test keyword search."""
        search_data = {
            "query": "healthcare",
            "search_types": ["keywords"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "keywords" in result["results"]
        assert result["results"]["keywords"]["count"] >= 1
        
        keyword_result = result["results"]["keywords"]["items"][0]
        assert "healthcare" in keyword_result["keyword"].lower()
        assert keyword_result["message_count"] >= 1
        assert 0 <= keyword_result["confidence"] <= 1
    
    def test_search_candidates(self, client, sample_data):
        """Test candidate search."""
        search_data = {
            "query": "John",
            "search_types": ["candidates"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "candidates" in result["results"]
        assert result["results"]["candidates"]["count"] >= 1
        
        candidate_result = result["results"]["candidates"]["items"][0]
        assert "john" in candidate_result["candidate_name"].lower()
        assert candidate_result["constituency_name"] == "Test Constituency"
        assert candidate_result["message_count"] >= 0
    
    def test_search_sources(self, client, sample_data):
        """Test source search."""
        search_data = {
            "query": "Twitter",
            "search_types": ["sources"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "sources" in result["results"]
        
        if result["results"]["sources"]["count"] > 0:
            source_result = result["results"]["sources"]["items"][0]
            assert "twitter" in source_result["source_name"].lower()
            assert source_result["source_type"] in ["twitter", "website", "facebook", "meta_ads"]
    
    def test_search_multiple_types(self, client, sample_data):
        """Test searching across multiple content types."""
        search_data = {
            "query": "reform",
            "search_types": ["messages", "keywords", "candidates"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        assert len(result["results"]) == 3
        assert "messages" in result["results"]
        assert "keywords" in result["results"] 
        assert "candidates" in result["results"]
    
    def test_search_empty_query(self, client):
        """Test search with empty query."""
        search_data = {
            "query": "",
            "search_types": ["messages"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 422  # Validation error
    
    def test_search_no_results(self, client, sample_data):
        """Test search with no matching results."""
        search_data = {
            "query": "nonexistentterm123456",
            "search_types": ["messages", "keywords", "candidates"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["total_results"] == 0
        assert result["results"]["messages"]["count"] == 0
        assert result["results"]["keywords"]["count"] == 0
        assert result["results"]["candidates"]["count"] == 0
    
    def test_search_pagination(self, client, sample_data):
        """Test search result pagination."""
        search_data = {
            "query": "test",
            "search_types": ["messages"],
            "limit": 1
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        assert len(result["results"]["messages"]["items"]) <= 1
    
    def test_autocomplete_basic(self, client, sample_data):
        """Test basic autocomplete functionality."""
        autocomplete_data = {
            "query": "imm",
            "search_type": "keywords",
            "limit": 5
        }
        
        response = client.post("/api/v1/search/autocomplete", json=autocomplete_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["query"] == "imm"
        assert isinstance(result["suggestions"], list)
        
        if result["suggestions"]:
            suggestion = result["suggestions"][0]
            assert "text" in suggestion
            assert "type" in suggestion
            assert "count" in suggestion
            assert "imm" in suggestion["text"].lower()
    
    def test_autocomplete_candidates(self, client, sample_data):
        """Test autocomplete for candidates."""
        autocomplete_data = {
            "query": "Jo",
            "search_type": "candidates",
            "limit": 5
        }
        
        response = client.post("/api/v1/search/autocomplete", json=autocomplete_data)
        assert response.status_code == 200
        
        result = response.json()
        for suggestion in result["suggestions"]:
            assert suggestion["type"] == "candidate"
            assert "jo" in suggestion["text"].lower()
    
    def test_autocomplete_all_types(self, client, sample_data):
        """Test autocomplete across all types."""
        autocomplete_data = {
            "query": "test",
            "search_type": "all",
            "limit": 10
        }
        
        response = client.post("/api/v1/search/autocomplete", json=autocomplete_data)
        assert response.status_code == 200
        
        result = response.json()
        suggestion_types = {s["type"] for s in result["suggestions"]}
        # Should include multiple types
        assert len(suggestion_types) >= 1
    
    def test_search_performance(self, client, sample_data):
        """Test search performance metrics."""
        search_data = {
            "query": "test",
            "search_types": ["messages", "keywords"],
            "limit": 50
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "search_time_ms" in result
        assert isinstance(result["search_time_ms"], (int, float))
        assert result["search_time_ms"] >= 0
        # Performance should be reasonable (under 5 seconds)
        assert result["search_time_ms"] < 5000
    
    def test_search_relevance_scoring(self, client, sample_data):
        """Test relevance scoring in search results."""
        search_data = {
            "query": "immigration policy",
            "search_types": ["messages"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        if result["results"]["messages"]["count"] > 1:
            messages = result["results"]["messages"]["items"]
            # Results should be sorted by relevance (descending)
            for i in range(len(messages) - 1):
                assert messages[i]["relevance_score"] >= messages[i + 1]["relevance_score"]
    
    def test_search_with_candidate_filter(self, client, sample_data):
        """Test search with candidate ID filter."""
        # First get candidate ID
        candidate_search = {
            "query": "John",
            "search_types": ["candidates"],
            "limit": 1
        }
        
        response = client.post("/api/v1/search", json=candidate_search)
        candidate_result = response.json()
        
        if candidate_result["results"]["candidates"]["count"] > 0:
            candidate_id = candidate_result["results"]["candidates"]["items"][0]["candidate_id"]
            
            # Now search messages for that candidate
            message_search = {
                "query": "test",
                "search_types": ["messages"],
                "candidate_ids": [candidate_id],
                "limit": 10
            }
            
            response = client.post("/api/v1/search", json=message_search)
            assert response.status_code == 200
            
            result = response.json()
            for message in result["results"]["messages"]["items"]:
                # All results should be from the specified candidate
                assert message["candidate_name"] == "John Smith"


class TestSearchValidation:
    """Test search input validation."""
    
    def test_invalid_search_types(self, client):
        """Test search with invalid search types."""
        search_data = {
            "query": "test",
            "search_types": ["invalid_type"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        # Should either filter out invalid types or return validation error
        assert response.status_code == 200  # Depends on implementation
    
    def test_invalid_source_types(self, client):
        """Test search with invalid source types."""
        search_data = {
            "query": "test", 
            "search_types": ["messages"],
            "source_types": ["invalid_source"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        # Should handle gracefully
        assert response.status_code == 200
    
    def test_query_too_long(self, client):
        """Test search with query exceeding max length."""
        long_query = "a" * 1000  # Assuming max is 500 chars
        search_data = {
            "query": long_query,
            "search_types": ["messages"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 422  # Validation error
    
    def test_limit_too_high(self, client):
        """Test search with limit exceeding maximum."""
        search_data = {
            "query": "test",
            "search_types": ["messages"],
            "limit": 1000  # Assuming max is 200
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_date_range(self, client):
        """Test search with invalid date range."""
        search_data = {
            "query": "test",
            "search_types": ["messages"],
            "date_from": "2024-12-31T23:59:59Z",
            "date_to": "2024-01-01T00:00:00Z",  # End before start
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        # Should handle gracefully or return validation error
        assert response.status_code in [200, 422]


class TestSearchEdgeCases:
    """Test edge cases in search functionality."""
    
    def test_search_special_characters(self, client):
        """Test search with special characters."""
        search_data = {
            "query": "test@#$%^&*()",
            "search_types": ["messages"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
    
    def test_search_unicode_characters(self, client):
        """Test search with unicode characters."""
        search_data = {
            "query": "tést üñíçødé",
            "search_types": ["messages"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
    
    def test_search_very_short_query(self, client):
        """Test search with very short query."""
        search_data = {
            "query": "a",
            "search_types": ["messages"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
    
    def test_search_whitespace_query(self, client):
        """Test search with whitespace-only query."""
        search_data = {
            "query": "   ",
            "search_types": ["messages"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        # Should handle gracefully
        assert response.status_code in [200, 422]
    
    def test_concurrent_searches(self, client):
        """Test concurrent search requests."""
        import concurrent.futures
        
        def perform_search(query):
            search_data = {
                "query": f"test {query}",
                "search_types": ["messages"],
                "limit": 10
            }
            response = client.post("/api/v1/search", json=search_data)
            return response.status_code
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(perform_search, i) for i in range(10)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        assert all(status == 200 for status in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
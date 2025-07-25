"""
Integration tests for search functionality.
Tests the complete search workflow from API to database.
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.database import get_session, Base
from src.models import Source, Message, Keyword, Candidate, Constituency, MessageSentiment, TopicModel, MessageTopic, EngagementMetrics


class TestSearchIntegration:
    """Integration tests for complete search workflow."""
    
    @pytest.fixture(scope="function")
    def test_db_engine(self):
        """Create test database engine."""
        # Use in-memory SQLite for testing
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        return engine
    
    @pytest.fixture(scope="function")
    def test_db_session(self, test_db_engine):
        """Create test database session."""
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
        session = TestSessionLocal()
        
        # Override the dependency
        def override_get_session():
            try:
                yield session
            finally:
                session.close()
        
        app.dependency_overrides[get_session] = override_get_session
        
        yield session
        
        session.close()
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def comprehensive_test_data(self, test_db_session):
        """Create comprehensive test data."""
        # Create sources
        twitter_source = Source(
            name="Test Party Twitter",
            source_type="twitter",
            url="https://twitter.com/testparty",
            active=True
        )
        
        website_source = Source(
            name="Test Party Website",
            source_type="website",
            url="https://testparty.com",
            active=True
        )
        
        facebook_source = Source(
            name="Test Party Facebook",
            source_type="facebook",
            url="https://facebook.com/testparty",
            active=True
        )
        
        # Create constituencies
        constituency1 = Constituency(
            name="Test North",
            region="North Region",
            constituency_type="district"
        )
        
        constituency2 = Constituency(
            name="Test South",
            region="South Region", 
            constituency_type="county"
        )
        
        # Create candidates
        candidate1 = Candidate(
            name="Alice Johnson",
            constituency=constituency1,
            candidate_type="local",
            social_media_accounts={"twitter": "@alice_j", "facebook": "alice.johnson"}
        )
        
        candidate2 = Candidate(
            name="Bob Williams",
            constituency=constituency2,
            candidate_type="national",
            social_media_accounts={"twitter": "@bob_w"}
        )
        
        candidate3 = Candidate(
            name="Carol Davis",
            constituency=constituency1,
            candidate_type="local"
        )
        
        # Create messages with varied content
        messages = [
            Message(
                source=twitter_source,
                candidate=candidate1,
                content="Our comprehensive immigration policy will secure borders while supporting legal pathways. Britain first, compassionate approach. #ImmigrationReform #BritainFirst",
                url="https://twitter.com/testparty/status/1001",
                published_at=datetime(2024, 4, 15, 10, 30),
                message_type="tweet",
                geographic_scope="national",
                message_metadata={"hashtags": ["ImmigrationReform", "BritainFirst"], "retweets": 145, "likes": 892}
            ),
            Message(
                source=website_source,
                content="Healthcare Reform: A Vision for Britain's Future. Our NHS deserves better funding, improved efficiency, and modern technology integration.",
                url="https://testparty.com/healthcare-reform-vision",
                published_at=datetime(2024, 4, 14, 14, 20),
                message_type="article",
                geographic_scope="national",
                message_metadata={"word_count": 1250, "author": "Policy Team"}
            ),
            Message(
                source=facebook_source,
                candidate=candidate2,
                content="Small businesses are the backbone of our economy. Our economic policy will reduce red tape, lower taxes, and support entrepreneurship across all regions.",
                url="https://facebook.com/testparty/posts/123456",
                published_at=datetime(2024, 4, 13, 19, 45),
                message_type="post",
                geographic_scope="regional",
                message_metadata={"likes": 234, "comments": 45, "shares": 67}
            ),
            Message(
                source=twitter_source,
                candidate=candidate1,
                content="Climate change requires practical solutions, not ideology. We support nuclear energy, renewable innovation, and green technology jobs.",
                url="https://twitter.com/testparty/status/1002",
                published_at=datetime(2024, 4, 12, 8, 15),
                message_type="tweet",
                geographic_scope="national",
                message_metadata={"hashtags": ["ClimateAction", "PracticalSolutions"], "retweets": 78, "likes": 445}
            ),
            Message(
                source=website_source,
                candidate=candidate3,
                content="Local housing crisis needs immediate attention. We propose fast-track planning for affordable homes and support for first-time buyers.",
                url="https://testparty.com/local-housing-solutions",
                published_at=datetime(2024, 4, 11, 16, 30),
                message_type="press_release",
                geographic_scope="local",
                message_metadata={"constituency": "Test North", "local_media": True}
            ),
            Message(
                source=facebook_source,
                content="Education excellence starts with supporting our teachers. Better pay, modern resources, and parental choice in schooling options.",
                url="https://facebook.com/testparty/posts/789012",
                published_at=datetime(2024, 4, 10, 12, 0),
                message_type="post",
                geographic_scope="national",
                message_metadata={"likes": 567, "comments": 89, "shares": 123}
            )
        ]
        
        # Add all to session
        test_db_session.add_all([
            twitter_source, website_source, facebook_source,
            constituency1, constituency2,
            candidate1, candidate2, candidate3
        ] + messages)
        test_db_session.flush()  # Get IDs
        
        # Create keywords
        keywords = [
            Keyword(message=messages[0], keyword="immigration", confidence=0.95, extraction_method="spacy"),
            Keyword(message=messages[0], keyword="policy", confidence=0.88, extraction_method="spacy"),
            Keyword(message=messages[0], keyword="borders", confidence=0.92, extraction_method="spacy"),
            Keyword(message=messages[1], keyword="healthcare", confidence=0.94, extraction_method="nlp"),
            Keyword(message=messages[1], keyword="NHS", confidence=0.98, extraction_method="nlp"),
            Keyword(message=messages[1], keyword="reform", confidence=0.91, extraction_method="nlp"),
            Keyword(message=messages[2], keyword="economy", confidence=0.89, extraction_method="spacy"),
            Keyword(message=messages[2], keyword="small business", confidence=0.93, extraction_method="spacy"),
            Keyword(message=messages[2], keyword="entrepreneurship", confidence=0.87, extraction_method="spacy"),
            Keyword(message=messages[3], keyword="climate change", confidence=0.96, extraction_method="nlp"),
            Keyword(message=messages[3], keyword="nuclear energy", confidence=0.90, extraction_method="nlp"),
            Keyword(message=messages[4], keyword="housing", confidence=0.94, extraction_method="spacy"),
            Keyword(message=messages[4], keyword="affordable homes", confidence=0.92, extraction_method="spacy"),
            Keyword(message=messages[5], keyword="education", confidence=0.95, extraction_method="nlp"),
            Keyword(message=messages[5], keyword="teachers", confidence=0.93, extraction_method="nlp")
        ]
        
        # Create sentiment analysis data
        sentiments = [
            MessageSentiment(
                message=messages[0], sentiment_score=0.2, sentiment_label="positive",
                confidence=0.85, political_tone="nationalist", tone_confidence=0.78,
                analysis_method="textblob"
            ),
            MessageSentiment(
                message=messages[1], sentiment_score=0.4, sentiment_label="positive",
                confidence=0.82, political_tone="diplomatic", tone_confidence=0.75,
                analysis_method="textblob"
            ),
            MessageSentiment(
                message=messages[2], sentiment_score=0.3, sentiment_label="positive",
                confidence=0.88, political_tone="populist", tone_confidence=0.81,
                analysis_method="textblob"
            ),
            MessageSentiment(
                message=messages[3], sentiment_score=0.1, sentiment_label="neutral",
                confidence=0.79, political_tone="diplomatic", tone_confidence=0.72,
                analysis_method="textblob"
            ),
            MessageSentiment(
                message=messages[4], sentiment_score=-0.1, sentiment_label="negative",
                confidence=0.83, political_tone="aggressive", tone_confidence=0.76,
                analysis_method="textblob"
            ),
            MessageSentiment(
                message=messages[5], sentiment_score=0.5, sentiment_label="positive",
                confidence=0.91, political_tone="diplomatic", tone_confidence=0.84,
                analysis_method="textblob"
            )
        ]
        
        # Add keywords and sentiments
        test_db_session.add_all(keywords + sentiments)
        test_db_session.commit()
        
        return {
            'sources': [twitter_source, website_source, facebook_source],
            'constituencies': [constituency1, constituency2],
            'candidates': [candidate1, candidate2, candidate3],
            'messages': messages,
            'keywords': keywords,
            'sentiments': sentiments
        }
    
    def test_search_messages_full_workflow(self, client, comprehensive_test_data):
        """Test complete message search workflow."""
        search_data = {
            "query": "immigration policy",
            "search_types": ["messages"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["query"] == "immigration policy" 
        assert result["total_results"] >= 1
        assert "messages" in result["results"]
        
        message_result = result["results"]["messages"]["items"][0]
        assert "immigration" in message_result["content"].lower()
        assert message_result["source_type"] == "twitter"
        assert message_result["candidate_name"] == "Alice Johnson"
        assert message_result["message_type"] == "tweet"
        assert len(message_result["keywords"]) > 0
        assert message_result["sentiment_score"] is not None
        assert message_result["relevance_score"] > 0
    
    def test_search_with_source_type_filter(self, client, comprehensive_test_data):
        """Test search with source type filtering."""
        search_data = {
            "query": "reform",
            "search_types": ["messages"],
            "source_types": ["website"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        for message in result["results"]["messages"]["items"]:
            assert message["source_type"] == "website"
    
    def test_search_with_date_range_filter(self, client, comprehensive_test_data):
        """Test search with date range filtering."""
        search_data = {
            "query": "policy",
            "search_types": ["messages"],
            "date_from": "2024-04-13T00:00:00Z",
            "date_to": "2024-04-15T23:59:59Z",
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        for message in result["results"]["messages"]["items"]:
            message_date = datetime.fromisoformat(message["published_at"].replace('Z', '+00:00'))
            assert datetime(2024, 4, 13) <= message_date <= datetime(2024, 4, 16)
    
    def test_search_with_sentiment_filter(self, client, comprehensive_test_data):
        """Test search with sentiment filtering."""
        search_data = {
            "query": "support",
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
    
    def test_search_with_geographic_scope_filter(self, client, comprehensive_test_data):
        """Test search with geographic scope filtering."""
        search_data = {
            "query": "housing",
            "search_types": ["messages"],
            "geographic_scope": "local",
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        for message in result["results"]["messages"]["items"]:
            assert message["geographic_scope"] == "local"
    
    def test_search_with_candidate_filter(self, client, comprehensive_test_data):
        """Test search with candidate ID filtering."""
        # Get Alice Johnson's ID
        alice = comprehensive_test_data['candidates'][0]  # Alice Johnson
        
        search_data = {
            "query": "climate",
            "search_types": ["messages"],
            "candidate_ids": [alice.id],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        for message in result["results"]["messages"]["items"]:
            assert message["candidate_name"] == "Alice Johnson"
    
    def test_search_keywords_integration(self, client, comprehensive_test_data):
        """Test keyword search integration."""
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
        assert len(keyword_result["recent_messages"]) > 0
    
    def test_search_candidates_integration(self, client, comprehensive_test_data):
        """Test candidate search integration."""
        search_data = {
            "query": "Alice",
            "search_types": ["candidates"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "candidates" in result["results"]
        assert result["results"]["candidates"]["count"] >= 1
        
        candidate_result = result["results"]["candidates"]["items"][0]
        assert "alice" in candidate_result["candidate_name"].lower()
        assert candidate_result["constituency_name"] == "Test North"
        assert candidate_result["message_count"] >= 1
        assert len(candidate_result["top_keywords"]) > 0
    
    def test_search_sources_integration(self, client, comprehensive_test_data):
        """Test source search integration."""
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
            assert source_result["source_type"] == "twitter"
            assert source_result["message_count"] >= 1
            assert source_result["active"] is True
    
    def test_search_multiple_types_integration(self, client, comprehensive_test_data):
        """Test searching across multiple content types."""
        search_data = {
            "query": "policy",
            "search_types": ["messages", "keywords", "candidates"],
            "limit": 5
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        assert len(result["results"]) == 3
        assert result["total_results"] > 0
        
        # Should have results in multiple categories
        assert "messages" in result["results"]
        assert "keywords" in result["results"]
        assert "candidates" in result["results"]
    
    def test_autocomplete_integration(self, client, comprehensive_test_data):
        """Test autocomplete functionality integration."""
        autocomplete_data = {
            "query": "immigr",
            "search_type": "keywords",
            "limit": 5
        }
        
        response = client.post("/api/v1/search/autocomplete", json=autocomplete_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["query"] == "immigr"
        assert isinstance(result["suggestions"], list)
        
        # Should find "immigration" keyword
        immigration_found = any(
            "immigration" in suggestion["text"].lower() 
            for suggestion in result["suggestions"]
        )
        assert immigration_found
    
    def test_search_performance_integration(self, client, comprehensive_test_data):
        """Test search performance with realistic data."""
        search_data = {
            "query": "economic policy reform healthcare",
            "search_types": ["messages", "keywords", "candidates", "sources"],
            "limit": 20
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        
        # Performance check
        assert result["search_time_ms"] < 2000  # Under 2 seconds
        
        # Should handle complex queries
        assert isinstance(result["total_results"], int)
        assert result["total_results"] >= 0
    
    def test_search_relevance_integration(self, client, comprehensive_test_data):
        """Test search relevance scoring integration."""
        search_data = {
            "query": "immigration policy borders",
            "search_types": ["messages"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        
        if result["results"]["messages"]["count"] > 1:
            messages = result["results"]["messages"]["items"]
            
            # Messages should be sorted by relevance (descending)
            for i in range(len(messages) - 1):
                current_score = messages[i]["relevance_score"]
                next_score = messages[i + 1]["relevance_score"]
                assert current_score >= next_score
            
            # Message with all three terms should score highest
            top_message = messages[0]
            top_content = top_message["content"].lower()
            assert "immigration" in top_content
            assert "policy" in top_content
            assert "borders" in top_content
    
    def test_search_error_handling_integration(self, client, comprehensive_test_data):
        """Test search error handling in integration environment."""
        # Test with invalid search types
        search_data = {
            "query": "test",
            "search_types": ["invalid_type"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        # Should handle gracefully (implementation dependent)
        assert response.status_code in [200, 422]
        
        # Test with query too long
        long_query = "a" * 1000
        search_data = {
            "query": long_query,
            "search_types": ["messages"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 422  # Validation error
    
    def test_search_empty_database(self, client, test_db_session):
        """Test search with empty database."""
        search_data = {
            "query": "anything",
            "search_types": ["messages", "keywords", "candidates", "sources"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["total_results"] == 0
        assert result["results"]["messages"]["count"] == 0
        assert result["results"]["keywords"]["count"] == 0
        assert result["results"]["candidates"]["count"] == 0
        assert result["results"]["sources"]["count"] == 0
    
    def test_search_concurrent_requests_integration(self, client, comprehensive_test_data):
        """Test concurrent search requests."""
        import concurrent.futures
        import threading
        
        def perform_search(query_suffix):
            search_data = {
                "query": f"policy {query_suffix}",
                "search_types": ["messages"],
                "limit": 5
            }
            response = client.post("/api/v1/search", json=search_data)
            return response.status_code, response.json()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(perform_search, i) 
                for i in range(10)
            ]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        for status_code, result in results:
            assert status_code == 200
            assert "results" in result
            assert isinstance(result["total_results"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
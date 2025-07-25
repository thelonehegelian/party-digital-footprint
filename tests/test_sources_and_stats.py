"""
Tests for sources and statistics endpoints.
"""

import pytest
import requests
from typing import Dict, Any


class TestSourcesEndpoint:
    """Test sources endpoint."""

    def test_list_sources(self, api_client: requests.Session, api_base_url: str):
        """Test listing all sources."""
        response = api_client.get(f"{api_base_url}/api/v1/sources")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            source = data[0]
            assert "id" in source
            assert "name" in source
            assert "source_type" in source
            assert "url" in source
            assert "active" in source
            assert "last_scraped" in source
            assert "message_count" in source
            
            # Validate data types
            assert isinstance(source["id"], int)
            assert isinstance(source["name"], str)
            assert isinstance(source["source_type"], str)
            assert isinstance(source["active"], bool)
            assert isinstance(source["message_count"], int)

    def test_sources_data_validation(self, api_client: requests.Session, api_base_url: str):
        """Test that sources have valid data."""
        response = api_client.get(f"{api_base_url}/api/v1/sources")
        data = response.json()
        
        if len(data) > 0:
            # Check source types
            source_types = [source["source_type"] for source in data]
            expected_types = ["twitter", "facebook", "website", "meta_ads"]
            
            for source_type in source_types:
                # Should be one of the expected types (though custom types are allowed)
                assert isinstance(source_type, str)
                assert len(source_type) > 0
            
            # Check URLs format
            for source in data:
                if source["url"]:
                    assert isinstance(source["url"], str)
                    # Basic URL validation
                    assert any(source["url"].startswith(protocol) 
                             for protocol in ["http://", "https://"])

    def test_sources_message_count_accuracy(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test that source message counts are accurate."""
        # Get sources
        sources_response = api_client.get(f"{api_base_url}/api/v1/sources")
        sources = sources_response.json()
        
        # Get overall stats
        stats_response = api_client.get(f"{api_base_url}/api/v1/messages/stats")
        stats = stats_response.json()
        
        # Sum of individual source message counts should relate to total messages
        total_source_messages = sum(source["message_count"] for source in sources)
        total_messages = stats["total_messages"]
        
        # They should be equal (assuming no orphaned messages)
        assert total_source_messages == total_messages


class TestStatisticsEndpoint:
    """Test statistics endpoint."""

    def test_get_message_stats(self, api_client: requests.Session, api_base_url: str):
        """Test getting message statistics."""
        response = api_client.get(f"{api_base_url}/api/v1/messages/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = [
            "total_messages", "total_keywords", "total_sources",
            "total_constituencies", "total_candidates",
            "by_source_type", "by_geographic_scope"
        ]
        
        for field in required_fields:
            assert field in data
        
        # Validate data types
        assert isinstance(data["total_messages"], int)
        assert isinstance(data["total_keywords"], int)
        assert isinstance(data["total_sources"], int)
        assert isinstance(data["total_constituencies"], int)
        assert isinstance(data["total_candidates"], int)
        assert isinstance(data["by_source_type"], dict)
        assert isinstance(data["by_geographic_scope"], dict)
        
        # All counts should be non-negative
        assert data["total_messages"] >= 0
        assert data["total_keywords"] >= 0
        assert data["total_sources"] >= 0
        assert data["total_constituencies"] >= 0
        assert data["total_candidates"] >= 0

    def test_source_type_distribution(self, api_client: requests.Session, api_base_url: str):
        """Test source type distribution in statistics."""
        response = api_client.get(f"{api_base_url}/api/v1/messages/stats")
        data = response.json()
        
        by_source_type = data["by_source_type"]
        
        # Should be a dictionary with source types as keys
        for source_type, count in by_source_type.items():
            assert isinstance(source_type, str)
            assert isinstance(count, int)
            assert count >= 0
        
        # Sum of source type counts should equal total messages
        total_by_source = sum(by_source_type.values())
        assert total_by_source == data["total_messages"]

    def test_geographic_scope_distribution(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test geographic scope distribution in statistics."""
        response = api_client.get(f"{api_base_url}/api/v1/messages/stats")
        data = response.json()
        
        by_geographic_scope = data["by_geographic_scope"]
        
        # Should be a dictionary with scopes as keys
        for scope, count in by_geographic_scope.items():
            assert isinstance(scope, str)
            assert isinstance(count, int)
            assert count >= 0
        
        # Expected scopes
        expected_scopes = ["national", "regional", "local"]
        for scope in by_geographic_scope.keys():
            assert scope in expected_scopes

    def test_statistics_consistency(self, api_client: requests.Session, api_base_url: str):
        """Test consistency between different statistics."""
        response = api_client.get(f"{api_base_url}/api/v1/messages/stats")
        data = response.json()
        
        # If there are messages, there should be sources
        if data["total_messages"] > 0:
            assert data["total_sources"] > 0
        
        # If there are candidates, there should be constituencies
        if data["total_candidates"] > 0:
            assert data["total_constituencies"] > 0
        
        # Keywords count should be reasonable relative to messages
        # (not necessarily equal, but should be in a reasonable range)
        if data["total_messages"] > 0:
            keyword_to_message_ratio = data["total_keywords"] / data["total_messages"]
            # Should have some keywords per message on average
            assert keyword_to_message_ratio >= 0
            # But not an unreasonable amount
            assert keyword_to_message_ratio <= 100  # Max 100 keywords per message

    def test_phase2_statistics_presence(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test that Phase 2 statistics are present and reasonable."""
        response = api_client.get(f"{api_base_url}/api/v1/messages/stats")
        data = response.json()
        
        # Phase 2 should have constituencies and candidates
        constituencies = data["total_constituencies"]
        candidates = data["total_candidates"]
        
        # Based on our test data, we should have Phase 2 data
        if constituencies > 0:
            # Should have a reasonable distribution
            assert constituencies <= 1000  # Not more than total UK constituencies
            
            # Should have some candidates if we have constituencies
            # (though not necessarily - depends on test data)
            assert candidates >= 0
        
        # Geographic scope should include local messages (Phase 2 feature)
        geographic_stats = data["by_geographic_scope"]
        if geographic_stats and "local" in geographic_stats:
            assert geographic_stats["local"] >= 0


class TestDataIntegrity:
    """Test data integrity across endpoints."""

    def test_source_message_relationship(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test that source-message relationships are maintained."""
        # Get sources
        sources_response = api_client.get(f"{api_base_url}/api/v1/sources")
        sources = sources_response.json()
        
        # Get statistics
        stats_response = api_client.get(f"{api_base_url}/api/v1/messages/stats")
        stats = stats_response.json()
        
        # Total messages from sources should match stats
        source_message_total = sum(source["message_count"] for source in sources)
        assert source_message_total == stats["total_messages"]

    def test_constituency_candidate_counts(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test constituency candidate count accuracy."""
        # Get constituencies
        const_response = api_client.get(f"{api_base_url}/api/v1/constituencies")
        constituencies = const_response.json()
        
        # Get candidates
        cand_response = api_client.get(f"{api_base_url}/api/v1/candidates")
        candidates = cand_response.json()
        
        if len(constituencies) > 0 and len(candidates) > 0:
            # Count candidates by constituency
            candidate_counts = {}
            for candidate in candidates:
                const_id = candidate["constituency_id"]
                if const_id:
                    candidate_counts[const_id] = candidate_counts.get(const_id, 0) + 1
            
            # Check against constituency candidate_count field
            for constituency in constituencies:
                const_id = constituency["id"]
                expected_count = candidate_counts.get(const_id, 0)
                assert constituency["candidate_count"] == expected_count
"""
Tests for Phase 2 endpoints: constituencies, candidates, and candidate messages.
"""

import pytest
import requests
from typing import Dict, Any, List


class TestConstituenciesEndpoint:
    """Test constituencies endpoint (Phase 2)."""

    def test_list_constituencies(self, api_client: requests.Session, api_base_url: str):
        """Test listing all constituencies."""
        response = api_client.get(f"{api_base_url}/api/v1/constituencies")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            constituency = data[0]
            assert "id" in constituency
            assert "name" in constituency
            assert "region" in constituency
            assert "constituency_type" in constituency
            assert "candidate_count" in constituency
            
            # Validate data types
            assert isinstance(constituency["id"], int)
            assert isinstance(constituency["name"], str)
            assert isinstance(constituency["candidate_count"], int)

    def test_constituencies_data_structure(self, api_client: requests.Session, api_base_url: str):
        """Test that constituencies have expected data structure."""
        response = api_client.get(f"{api_base_url}/api/v1/constituencies")
        data = response.json()
        
        if len(data) > 0:
            # Check for UK regions
            regions = [const["region"] for const in data]
            expected_regions = ["England", "Scotland", "Wales", "Northern Ireland", 
                              "West Midlands", "North West", "Yorkshire and The Humber"]
            
            # At least some expected regions should be present
            assert any(region in expected_regions for region in regions)
            
            # Check constituency types
            types = [const["constituency_type"] for const in data if const["constituency_type"]]
            expected_types = ["county", "district", "unitary"]
            assert any(const_type in expected_types for const_type in types)


class TestCandidatesEndpoint:
    """Test candidates endpoint (Phase 2)."""

    def test_list_candidates(self, api_client: requests.Session, api_base_url: str):
        """Test listing all candidates."""
        response = api_client.get(f"{api_base_url}/api/v1/candidates")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            candidate = data[0]
            assert "id" in candidate
            assert "name" in candidate
            assert "constituency_id" in candidate
            assert "constituency_name" in candidate
            assert "social_media_accounts" in candidate
            assert "candidate_type" in candidate
            assert "message_count" in candidate
            
            # Validate data types
            assert isinstance(candidate["id"], int)
            assert isinstance(candidate["name"], str)
            assert isinstance(candidate["message_count"], int)

    def test_list_candidates_filtered_by_constituency(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test filtering candidates by constituency."""
        # First get a constituency ID
        constituencies_response = api_client.get(f"{api_base_url}/api/v1/constituencies")
        constituencies = constituencies_response.json()
        
        if len(constituencies) > 0:
            constituency_id = constituencies[0]["id"]
            
            response = api_client.get(
                f"{api_base_url}/api/v1/candidates",
                params={"constituency_id": constituency_id}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # All returned candidates should belong to the specified constituency
            for candidate in data:
                assert candidate["constituency_id"] == constituency_id

    def test_candidates_social_media_structure(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test social media accounts data structure."""
        response = api_client.get(f"{api_base_url}/api/v1/candidates")
        data = response.json()
        
        if len(data) > 0:
            candidate = data[0]
            social_media = candidate["social_media_accounts"]
            
            if social_media:
                assert isinstance(social_media, dict)
                # Check for expected platforms
                expected_platforms = ["twitter", "facebook"]
                for platform in expected_platforms:
                    if platform in social_media:
                        assert isinstance(social_media[platform], str)
                        if platform == "twitter":
                            assert social_media[platform].startswith("@")
                        elif platform == "facebook":
                            assert "facebook.com" in social_media[platform]


class TestCandidateMessagesEndpoint:
    """Test candidate messages endpoint (Phase 2)."""

    def test_get_candidate_messages_success(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test getting messages for a specific candidate."""
        # First get a candidate with messages
        candidates_response = api_client.get(f"{api_base_url}/api/v1/candidates")
        candidates = candidates_response.json()
        
        # Find a candidate with messages
        candidate_with_messages = None
        for candidate in candidates:
            if candidate["message_count"] > 0:
                candidate_with_messages = candidate
                break
        
        if candidate_with_messages:
            candidate_id = candidate_with_messages["id"]
            
            response = api_client.get(
                f"{api_base_url}/api/v1/candidates/{candidate_id}/messages"
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "candidate" in data
            assert "messages" in data
            
            # Validate candidate info
            candidate_info = data["candidate"]
            assert candidate_info["id"] == candidate_id
            assert "name" in candidate_info
            assert "constituency_name" in candidate_info
            
            # Validate messages structure
            messages = data["messages"]
            assert isinstance(messages, list)
            
            if len(messages) > 0:
                message = messages[0]
                assert "id" in message
                assert "content" in message
                assert "published_at" in message
                assert "message_type" in message
                assert "geographic_scope" in message
                assert "source_name" in message

    def test_get_candidate_messages_not_found(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test getting messages for non-existent candidate."""
        response = api_client.get(f"{api_base_url}/api/v1/candidates/99999/messages")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_candidate_messages_content_truncation(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test that message content is properly truncated in candidate messages."""
        candidates_response = api_client.get(f"{api_base_url}/api/v1/candidates")
        candidates = candidates_response.json()
        
        for candidate in candidates:
            if candidate["message_count"] > 0:
                response = api_client.get(
                    f"{api_base_url}/api/v1/candidates/{candidate['id']}/messages"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    messages = data["messages"]
                    
                    for message in messages:
                        content = message["content"]
                        # Content should be truncated to 200 chars + "..." if longer
                        if content.endswith("..."):
                            assert len(content) <= 203  # 200 + "..."
                        else:
                            assert len(content) <= 200
                break


class TestPhase2Integration:
    """Test Phase 2 integration features."""

    def test_statistics_include_phase2_data(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test that statistics endpoint includes Phase 2 data."""
        response = api_client.get(f"{api_base_url}/api/v1/messages/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include Phase 2 statistics
        assert "total_constituencies" in data
        assert "total_candidates" in data
        assert "by_geographic_scope" in data
        
        assert isinstance(data["total_constituencies"], int)
        assert isinstance(data["total_candidates"], int)
        assert isinstance(data["by_geographic_scope"], dict)

    def test_geographic_scope_distribution(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test geographic scope distribution in statistics."""
        response = api_client.get(f"{api_base_url}/api/v1/messages/stats")
        data = response.json()
        
        geographic_stats = data["by_geographic_scope"]
        expected_scopes = ["national", "regional", "local"]
        
        # Should have at least some geographic scope data
        if geographic_stats:
            for scope, count in geographic_stats.items():
                assert scope in expected_scopes + [None]  # None is allowed
                assert isinstance(count, int)
                assert count >= 0

    def test_constituency_candidate_relationship(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test that constituency-candidate relationships are maintained."""
        # Get constituencies
        const_response = api_client.get(f"{api_base_url}/api/v1/constituencies")
        constituencies = const_response.json()
        
        # Get candidates
        cand_response = api_client.get(f"{api_base_url}/api/v1/candidates")
        candidates = cand_response.json()
        
        if len(constituencies) > 0 and len(candidates) > 0:
            # Verify that candidate constituency_ids match actual constituency ids
            constituency_ids = {const["id"] for const in constituencies}
            
            for candidate in candidates:
                if candidate["constituency_id"]:
                    assert candidate["constituency_id"] in constituency_ids
                    
                    # Find the corresponding constituency
                    matching_const = next(
                        (c for c in constituencies if c["id"] == candidate["constituency_id"]),
                        None
                    )
                    assert matching_const is not None
                    assert candidate["constituency_name"] == matching_const["name"]
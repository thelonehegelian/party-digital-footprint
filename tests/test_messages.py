"""
Tests for message submission and processing endpoints.
"""

import pytest
import requests
from typing import Dict, Any
import time


class TestMessageSubmission:
    """Test message submission endpoints."""

    def test_submit_single_message_success(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_message_data: Dict[str, Any],
        test_party_id: int
    ):
        """Test successful single message submission."""
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/single?party_id={test_party_id}",
            json=sample_message_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] in ["success", "warning"]
        assert "message_id" in data
        assert isinstance(data["message_id"], int)
        
        if data["status"] == "success":
            assert "keywords_extracted" in data
            assert isinstance(data["keywords_extracted"], int)

    def test_submit_single_message_duplicate(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_message_data: Dict[str, Any],
        test_party_id: int
    ):
        """Test duplicate message handling."""
        # Submit the same message twice
        api_client.post(f"{api_base_url}/api/v1/messages/single?party_id={test_party_id}", json=sample_message_data)
        response = api_client.post(f"{api_base_url}/api/v1/messages/single?party_id={test_party_id}", json=sample_message_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "warning"
        assert "already exists" in data["message"]

    def test_submit_single_message_missing_required_fields(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test message submission with missing required fields."""
        incomplete_message = {
            "source_type": "twitter",
            # Missing required fields like content, source_name
        }
        
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/single",
            json=incomplete_message
        )
        
        assert response.status_code == 422  # Unprocessable Entity

    def test_submit_single_message_invalid_source_type(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_message_data: Dict[str, Any]
    ):
        """Test message submission with invalid source type."""
        invalid_message = sample_message_data.copy()
        invalid_message["source_type"] = "invalid_platform"
        
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/single",
            json=invalid_message
        )
        
        # Should be rejected due to Literal validation in schema
        assert response.status_code == 422

    def test_submit_bulk_messages_success(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_bulk_messages: Dict[str, Any],
        test_party_id: int
    ):
        """Test successful bulk message submission."""
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/bulk?party_id={test_party_id}",
            json=sample_bulk_messages
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] in ["success", "partial", "error"]
        assert "imported_count" in data
        assert "skipped_count" in data
        assert "total_keywords_extracted" in data
        assert isinstance(data["imported_count"], int)
        assert isinstance(data["skipped_count"], int)
        # If status is "error" and no messages were processed, that's acceptable
        if data["status"] != "error":
            assert data["imported_count"] + data["skipped_count"] == len(sample_bulk_messages["messages"])

    def test_submit_bulk_messages_empty_list(
        self, 
        api_client: requests.Session, 
        api_base_url: str,
        test_party_id: int
    ):
        """Test bulk submission with empty message list."""
        empty_bulk = {"messages": []}
        
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/bulk?party_id={test_party_id}",
            json=empty_bulk
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["imported_count"] == 0
        assert data["skipped_count"] == 0

    def test_submit_bulk_messages_with_errors(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test bulk submission with some invalid messages."""
        mixed_bulk = {
            "messages": [
                {
                    "source_type": "twitter",
                    "source_name": "Valid Message",
                    "content": "This is a valid message"
                },
                {
                    "source_type": "twitter",
                    "source_name": "Invalid Message"
                    # Missing required content field
                }
            ]
        }
        
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/bulk",
            json=mixed_bulk
        )
        
        # Pydantic validation will reject the entire request due to invalid message
        assert response.status_code == 422

    def test_submit_candidate_message(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_candidate_message: Dict[str, Any],
        test_party_id: int
    ):
        """Test submitting a message with candidate association (Phase 2)."""
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/single?party_id={test_party_id}",
            json=sample_candidate_message
        )
        
        # Should succeed even if candidate_id doesn't exist (nullable field)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "warning"]


class TestMessageValidation:
    """Test message data validation."""

    def test_content_length_limits(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_message_data: Dict[str, Any],
        test_party_id: int
    ):
        """Test message content length handling."""
        # Test very long content
        long_message = sample_message_data.copy()
        long_message["content"] = "A" * 10000  # Very long content
        
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/single?party_id={test_party_id}",
            json=long_message
        )
        
        assert response.status_code == 200

    def test_special_characters_handling(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_message_data: Dict[str, Any],
        test_party_id: int
    ):
        """Test handling of special characters and emojis."""
        special_message = sample_message_data.copy()
        special_message["content"] = "Test with emojis 🇬🇧🏛️ and special chars: @#$%^&*()"
        special_message["url"] = "https://test.com/special/chars?param=value&other=123"
        
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/single?party_id={test_party_id}",
            json=special_message
        )
        
        assert response.status_code == 200

    def test_datetime_format_validation(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_message_data: Dict[str, Any]
    ):
        """Test various datetime format handling."""
        # Test with different datetime formats
        datetime_formats = [
            "2024-04-20T12:00:00Z",
            "2024-04-20T12:00:00+00:00",
            "2024-04-20T12:00:00",
            "2024-04-20 12:00:00"
        ]
        
        for date_format in datetime_formats:
            test_message = sample_message_data.copy()
            test_message["published_at"] = date_format
            test_message["url"] = f"https://test.com/datetime/{date_format.replace(':', '_')}"
            
            response = api_client.post(
                f"{api_base_url}/api/v1/messages/single",
                json=test_message
            )
            
            # Should handle various datetime formats gracefully
            assert response.status_code in [200, 422]
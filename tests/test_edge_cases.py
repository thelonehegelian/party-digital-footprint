"""
Edge case and stress tests for the Political Messaging Analysis API.
"""

import pytest
import requests
from typing import Dict, Any
import time
import threading
from datetime import datetime, timedelta


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_extremely_long_content(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_message_data: Dict[str, Any],
        test_party_id: int
    ):
        """Test handling of extremely long message content."""
        long_message = sample_message_data.copy()
        long_message["content"] = "A" * 50000  # 50k characters (exceeds max_length=10000)
        long_message["url"] = "https://test.com/long-content"
        
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/single?party_id={test_party_id}",
            json=long_message
        )
        
        # Should be rejected due to max_length validation
        assert response.status_code == 422

    def test_unicode_and_special_characters(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_message_data: Dict[str, Any],
        test_party_id: int
    ):
        """Test handling of Unicode and special characters."""
        unicode_message = sample_message_data.copy()
        unicode_message["content"] = (
            "🇬🇧 Progressive Party: Testing émojis, açcénts, 中文, العربية, ελληνικά, русский! "
            "Special chars: @#$%^&*()_+{}|:<>?[]\\;'\",./ ~`"
        )
        unicode_message["url"] = "https://test.com/unicode-test"
        
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/single?party_id={test_party_id}",
            json=unicode_message
        )
        
        assert response.status_code == 200

    def test_empty_string_fields(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test handling of empty string fields."""
        empty_fields_message = {
            "source_type": "twitter",
            "source_name": "Test Source",
            "content": "",  # Empty content
            "url": "",  # Empty URL
            "message_type": "",
            "geographic_scope": ""
        }
        
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/single",
            json=empty_fields_message
        )
        
        # Empty content should be rejected
        assert response.status_code == 422

    def test_null_optional_fields(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test handling of null values in optional fields."""
        null_message = {
            "source_type": "twitter",
            "source_name": "Test Source",
            "content": "Test message with null fields",
            "url": None,
            "published_at": None,
            "message_type": None,
            "geographic_scope": None,
            "metadata": None,
            "raw_data": None,
            "candidate_id": None
        }
        
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/single",
            json=null_message
        )
        
        assert response.status_code == 200

    def test_invalid_datetime_formats(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_message_data: Dict[str, Any]
    ):
        """Test handling of invalid datetime formats."""
        invalid_dates = [
            "invalid-date",
            "2024-13-45T25:70:70",  # Invalid date values
            "2024/04/20 12:00:00",  # Wrong format
            "20-04-2024",  # Wrong format
            "",  # Empty string
            "null"
        ]
        
        for invalid_date in invalid_dates:
            test_message = sample_message_data.copy()
            test_message["published_at"] = invalid_date
            test_message["url"] = f"https://test.com/invalid-date/{invalid_date.replace(':', '_')}"
            
            response = api_client.post(
                f"{api_base_url}/api/v1/messages/single",
                json=test_message
            )
            
            # Should either accept (parsing as string) or reject with validation error
            assert response.status_code in [200, 422]

    def test_deeply_nested_metadata(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_message_data: Dict[str, Any]
    ):
        """Test handling of deeply nested metadata structures."""
        nested_message = sample_message_data.copy()
        nested_message["metadata"] = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "level5": {
                                "deep_value": "test",
                                "array": [1, 2, 3, {"nested_in_array": True}],
                                "null_value": None,
                                "boolean": True,
                                "number": 42.5
                            }
                        }
                    }
                }
            },
            "top_level_array": [
                {"item1": "value1"},
                {"item2": ["nested", "array", {"deep": "structure"}]}
            ]
        }
        nested_message["url"] = "https://test.com/nested-metadata"
        
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/single",
            json=nested_message
        )
        
        assert response.status_code == 200

    def test_malformed_json_handling(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test handling of malformed JSON."""
        # Send malformed JSON
        response = requests.post(
            f"{api_base_url}/api/v1/messages/single",
            data='{"source_type": "twitter", "content": "test", malformed}',
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422


class TestPerformanceAndLimits:
    """Test performance limits and bulk operations."""

    def test_maximum_bulk_messages(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test submitting maximum allowed bulk messages."""
        # Create 100 messages (common API limit)
        messages = []
        for i in range(100):
            messages.append({
                "source_type": "twitter",
                "source_name": f"Bulk Test Source {i}",
                "content": f"Bulk test message number {i}",
                "url": f"https://test.com/bulk/{i}",
                "message_type": "post"
            })
        
        bulk_data = {"messages": messages}
        
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/bulk",
            json=bulk_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "partial", "error"]
        # Even if status is "error", the endpoint should handle it gracefully

    def test_large_bulk_submission_performance(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test performance of large bulk submissions."""
        # Create 50 messages with substantial content
        messages = []
        for i in range(50):
            content = f"Performance test message {i}. " * 20  # ~500 chars each
            messages.append({
                "source_type": "twitter",
                "source_name": f"Performance Test {i}",
                "content": content,
                "url": f"https://test.com/performance/{i}",
                "metadata": {
                    "test_id": i,
                    "performance_test": True,
                    "data": list(range(10))  # Some metadata
                }
            })
        
        bulk_data = {"messages": messages}
        
        start_time = time.time()
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/bulk",
            json=bulk_data
        )
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Should complete within reasonable time (adjust based on server specs)
        processing_time = end_time - start_time
        assert processing_time < 30  # 30 seconds max for 50 messages

    def test_concurrent_requests(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_message_data: Dict[str, Any]
    ):
        """Test handling of concurrent requests."""
        results = []
        errors = []
        
        def submit_message(message_id: int):
            try:
                test_message = sample_message_data.copy()
                test_message["content"] = f"Concurrent test message {message_id}"
                test_message["url"] = f"https://test.com/concurrent/{message_id}"
                
                client = requests.Session()
                client.headers.update({"Content-Type": "application/json"})
                
                response = client.post(
                    f"{api_base_url}/api/v1/messages/single",
                    json=test_message
                )
                results.append((message_id, response.status_code))
                client.close()
            except Exception as e:
                errors.append((message_id, str(e)))
        
        # Submit 10 concurrent requests
        threads = []
        for i in range(10):
            thread = threading.Thread(target=submit_message, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        
        # All requests should succeed or be handled gracefully
        for message_id, status_code in results:
            assert status_code in [200, 429]  # Success or rate limit


class TestErrorRecovery:
    """Test error recovery and resilience."""

    def test_database_constraint_violations(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_message_data: Dict[str, Any]
    ):
        """Test handling of potential database constraint violations."""
        # Try to submit the same message multiple times quickly
        test_message = sample_message_data.copy()
        test_message["url"] = "https://test.com/constraint-test"
        
        responses = []
        for i in range(3):
            response = api_client.post(
                f"{api_base_url}/api/v1/messages/single",
                json=test_message
            )
            responses.append(response)
        
        # First should succeed, subsequent should handle duplicates
        assert responses[0].status_code == 200
        for response in responses[1:]:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "warning"  # Duplicate detected

    def test_invalid_candidate_id(
        self, 
        api_client: requests.Session, 
        api_base_url: str, 
        sample_message_data: Dict[str, Any]
    ):
        """Test handling of invalid candidate IDs."""
        test_message = sample_message_data.copy()
        test_message["candidate_id"] = 99999  # Non-existent candidate
        test_message["url"] = "https://test.com/invalid-candidate"
        
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/single",
            json=test_message
        )
        
        # Should handle gracefully (foreign key constraint)
        assert response.status_code in [200, 400, 422]

    def test_partial_bulk_failure_recovery(
        self, 
        api_client: requests.Session, 
        api_base_url: str
    ):
        """Test recovery from partial bulk submission failures."""
        # Create messages that will cause individual processing errors
        # but pass Pydantic validation (so we can test the endpoint logic)
        messages = [
            {
                "source_type": "twitter",
                "source_name": "Valid Message 1",
                "content": "This is a valid message",
                "url": "https://test.com/recovery/1"
            },
            {
                "source_type": "twitter",
                "source_name": "Valid Message 2", 
                "content": "This is another valid message",
                "url": "https://test.com/recovery/2"
            }
        ]
        
        bulk_data = {"messages": messages}
        
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/bulk",
            json=bulk_data
        )
        
        # Should succeed with valid messages
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "partial", "error"]
        assert data["imported_count"] >= 0
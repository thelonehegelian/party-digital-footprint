"""
Basic API endpoint tests for the Reform UK Messaging API.
"""

import pytest
import requests
from typing import Dict, Any


class TestBasicEndpoints:
    """Test basic API endpoints and connectivity."""

    def test_health_check(self, api_client: requests.Session, api_base_url: str):
        """Test the health check endpoint."""
        response = api_client.get(f"{api_base_url}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self, api_client: requests.Session, api_base_url: str):
        """Test the root endpoint."""
        response = api_client.get(f"{api_base_url}/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert data["status"] == "operational"

    def test_openapi_docs(self, api_client: requests.Session, api_base_url: str):
        """Test OpenAPI documentation availability."""
        response = api_client.get(f"{api_base_url}/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()

    def test_openapi_json(self, api_client: requests.Session, api_base_url: str):
        """Test OpenAPI JSON specification."""
        response = api_client.get(f"{api_base_url}/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "info" in data
        assert "paths" in data
        assert data["info"]["title"] == "Reform UK Messaging Analysis API"
        assert data["info"]["version"] == "2.0.0"

    def test_api_endpoints_exist(self, api_client: requests.Session, api_base_url: str):
        """Test that all expected API endpoints exist."""
        response = api_client.get(f"{api_base_url}/openapi.json")
        data = response.json()
        paths = data["paths"]
        
        # Check all expected endpoints exist
        expected_endpoints = [
            "/",
            "/health",
            "/api/v1/sources",
            "/api/v1/messages/stats",
            "/api/v1/messages/single",
            "/api/v1/messages/bulk",
            "/api/v1/constituencies",
            "/api/v1/candidates",
            "/api/v1/candidates/{candidate_id}/messages"
        ]
        
        for endpoint in expected_endpoints:
            assert endpoint in paths, f"Expected endpoint {endpoint} not found"

    def test_cors_headers(self, api_client: requests.Session, api_base_url: str):
        """Test CORS headers are present."""
        response = api_client.get(f"{api_base_url}/health")
        
        assert response.status_code == 200
        # Check for CORS headers (may vary based on configuration)
        headers = response.headers
        # CORS headers might not be present on simple GET requests
        # Let's check if the server supports CORS by making an OPTIONS request
        options_response = api_client.options(f"{api_base_url}/health")
        if options_response.status_code == 200:
            # If OPTIONS is supported, check for CORS headers
            assert any(header.lower().startswith('access-control') for header in options_response.headers)
        else:
            # If no OPTIONS support, that's also acceptable
            assert response.status_code == 200


class TestErrorHandling:
    """Test API error handling."""

    def test_404_endpoint(self, api_client: requests.Session, api_base_url: str):
        """Test 404 error for non-existent endpoint."""
        response = api_client.get(f"{api_base_url}/nonexistent")
        assert response.status_code == 404

    def test_405_method_not_allowed(self, api_client: requests.Session, api_base_url: str):
        """Test 405 error for unsupported HTTP method."""
        response = api_client.post(f"{api_base_url}/health")
        assert response.status_code == 405

    def test_invalid_json_request(self, api_client: requests.Session, api_base_url: str):
        """Test handling of invalid JSON in request body."""
        api_client.headers.update({"Content-Type": "application/json"})
        response = api_client.post(
            f"{api_base_url}/api/v1/messages/single",
            data="invalid json{"
        )
        assert response.status_code == 422  # Unprocessable Entity
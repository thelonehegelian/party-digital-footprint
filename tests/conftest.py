"""
Test configuration and fixtures for the Reform UK Messaging API tests.
"""

import pytest
import requests
from typing import Generator
import time


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Base URL for the API server."""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def api_client(api_base_url: str) -> Generator[requests.Session, None, None]:
    """HTTP client for API requests."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Verify API server is running
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = session.get(f"{api_base_url}/health")
            if response.status_code == 200:
                break
        except requests.ConnectionError:
            if attempt == max_retries - 1:
                pytest.skip("API server not available. Start with: uvicorn src.api.main:app --reload")
            time.sleep(1)
    
    yield session
    session.close()


@pytest.fixture
def sample_message_data() -> dict:
    """Sample message data for testing."""
    return {
        "source_type": "twitter",
        "source_name": "Test Reform UK Twitter",
        "source_url": "https://twitter.com/test_reform",
        "content": "Test message: Reform UK stands for common sense policies! #ReformUK #TestMessage",
        "url": "https://twitter.com/test_reform/status/123456789",
        "published_at": "2024-04-20T12:00:00Z",
        "message_type": "post",
        "geographic_scope": "national",
        "metadata": {
            "hashtags": ["ReformUK", "TestMessage"],
            "metrics": {
                "retweet_count": 25,
                "like_count": 75,
                "reply_count": 5
            }
        },
        "raw_data": {
            "tweet_id": "123456789",
            "user_id": "test_reform_user"
        }
    }


@pytest.fixture
def sample_bulk_messages() -> dict:
    """Sample bulk message data for testing."""
    return {
        "messages": [
            {
                "source_type": "twitter",
                "source_name": "Test Twitter Bulk 1",
                "content": "First test message for bulk submission",
                "url": "https://twitter.com/test/status/1",
                "message_type": "post",
                "geographic_scope": "local"
            },
            {
                "source_type": "facebook",
                "source_name": "Test Facebook Bulk 1",
                "content": "Second test message for bulk submission",
                "url": "https://facebook.com/test/post/2",
                "message_type": "post",
                "geographic_scope": "regional",
                "metadata": {
                    "engagement": {
                        "likes": 50,
                        "shares": 10
                    }
                }
            },
            {
                "source_type": "website",
                "source_name": "Test Website Bulk 1",
                "content": "Third test message - website article for bulk submission",
                "url": "https://test-site.uk/article/3",
                "message_type": "article",
                "geographic_scope": "national"
            }
        ]
    }


@pytest.fixture
def sample_candidate_message() -> dict:
    """Sample candidate message data for Phase 2 testing."""
    return {
        "source_type": "twitter",
        "source_name": "Test Candidate Twitter",
        "content": "As your Reform UK candidate for Test Constituency, I believe in putting local families first!",
        "url": "https://twitter.com/test_candidate/status/456789",
        "message_type": "post",
        "geographic_scope": "local",
        "candidate_id": 1,  # Assuming candidate with ID 1 exists
        "metadata": {
            "engagement": {
                "likes": 30,
                "retweets": 8,
                "replies": 3
            }
        }
    }
#!/usr/bin/env python3
"""
Test script for the Reform UK Messaging API.
"""

import sys
import requests
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.schemas import MessageInput, BulkMessageInput


def test_api_connection(base_url: str = "http://localhost:8000"):
    """Test basic API connectivity."""
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ API server is running and healthy")
            return True
        else:
            print(f"❌ API server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("   Make sure to start the server with: uvicorn src.api.main:app --reload")
        return False


def test_single_message_submission(base_url: str = "http://localhost:8000"):
    """Test submitting a single message."""
    test_message = {
        "source_type": "twitter",
        "source_name": "Reform UK Twitter Test",
        "source_url": "https://twitter.com/reformparty_uk",
        "content": "Test message: Reform UK calls for common sense policies to put Britain first! #ReformUK #BritainFirst",
        "url": "https://twitter.com/reformparty_uk/status/test123",
        "published_at": "2024-04-20T12:00:00Z",
        "message_type": "post",
        "metadata": {
            "hashtags": ["ReformUK", "BritainFirst"],
            "metrics": {
                "retweet_count": 50,
                "like_count": 150
            }
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/messages/single",
            json=test_message,
            headers={"Content-Type": "application/json"}
        )
        
        result = response.json()
        
        if response.status_code == 200:
            print("✅ Single message submission successful")
            print(f"   Message ID: {result.get('message_id')}")
            print(f"   Keywords extracted: {result.get('keywords_extracted')}")
            return True
        else:
            print(f"❌ Single message submission failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error submitting single message: {e}")
        return False


def test_bulk_message_submission(base_url: str = "http://localhost:8000"):
    """Test submitting multiple messages."""
    test_messages = [
        {
            "source_type": "website",
            "source_name": "Reform UK Website Test",
            "content": "Test article: Reform UK outlines comprehensive immigration policy",
            "url": "https://www.reformparty.uk/test/article1",
            "message_type": "article"
        },
        {
            "source_type": "facebook",
            "source_name": "Reform UK Facebook Test",
            "content": "Test post: 🇬🇧 Britain needs strong leadership and common sense policies!",
            "url": "https://www.facebook.com/test/post1",
            "message_type": "post",
            "metadata": {
                "engagement": {
                    "likes": 100,
                    "shares": 25
                }
            }
        }
    ]
    
    bulk_data = {
        "messages": test_messages
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/messages/bulk",
            json=bulk_data,
            headers={"Content-Type": "application/json"}
        )
        
        result = response.json()
        
        if response.status_code == 200:
            print("✅ Bulk message submission successful")
            print(f"   Status: {result.get('status')}")
            print(f"   Imported: {result.get('imported_count')}")
            print(f"   Skipped: {result.get('skipped_count')}")
            print(f"   Total keywords: {result.get('total_keywords_extracted')}")
            return True
        else:
            print(f"❌ Bulk message submission failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error submitting bulk messages: {e}")
        return False


def test_api_endpoints(base_url: str = "http://localhost:8000"):
    """Test various API endpoints."""
    endpoints_to_test = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/api/v1/sources", "List sources"),
        ("/api/v1/messages/stats", "Message statistics")
    ]
    
    for endpoint, description in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            if response.status_code == 200:
                print(f"✅ {description}: OK")
                if endpoint == "/api/v1/messages/stats":
                    stats = response.json()
                    print(f"   Total messages: {stats.get('total_messages', 0)}")
                    print(f"   Total keywords: {stats.get('total_keywords', 0)}")
            else:
                print(f"❌ {description}: Status {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: Error - {e}")


def main():
    """Run all API tests."""
    print("=== Reform UK Messaging API Test Suite ===\n")
    
    base_url = "http://localhost:8000"
    
    # Test 1: API Connection
    print("1. Testing API Connection:")
    if not test_api_connection(base_url):
        print("\n❌ Cannot proceed with tests - API server not available")
        print("\nTo start the API server, run:")
        print("   uvicorn src.api.main:app --reload")
        return
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Endpoints
    print("2. Testing API Endpoints:")
    test_api_endpoints(base_url)
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Single Message
    print("3. Testing Single Message Submission:")
    test_single_message_submission(base_url)
    
    print("\n" + "="*50 + "\n")
    
    # Test 4: Bulk Messages
    print("4. Testing Bulk Message Submission:")
    test_bulk_message_submission(base_url)
    
    print("\n" + "="*50 + "\n")
    
    # Test 5: Final Stats
    print("5. Final Statistics:")
    test_api_endpoints(base_url)
    
    print("\n✅ API testing completed!")
    print("\n💡 View API documentation at: http://localhost:8000/docs")
    print("💡 View dashboard at: streamlit run dashboard.py")


if __name__ == "__main__":
    main()
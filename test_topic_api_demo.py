#!/usr/bin/env python3
"""
Topic modeling API demo script.

This script demonstrates the topic modeling API endpoints in action,
showing the complete workflow from topic analysis to trending topics.
"""

import requests
import json
from datetime import datetime


# API base URL
BASE_URL = "http://localhost:8000/api/v1"


def test_topic_api_demo():
    """Demonstrate topic modeling API capabilities."""
    
    print("=== Topic Modeling API Demo ===\n")
    
    try:
        # Test 1: Analyze direct content
        print("1. Testing direct content analysis...")
        content_analysis = {
            "content": "We need stronger immigration policies and border security to protect British workers and our communities."
        }
        
        response = requests.post(
            f"{BASE_URL}/analytics/topics/analyze",
            json=content_analysis,
            params={"use_dummy": True}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Content analyzed successfully")
            print(f"  Primary topic: {data['primary_topic']['topic_name']}")
            print(f"  Probability: {data['primary_topic']['probability']:.3f}")
            print(f"  Total topics assigned: {len(data['assigned_topics'])}")
        else:
            print(f"✗ Content analysis failed: {response.status_code}")
            print(f"  Error: {response.text}")
        
        # Test 2: Get topic overview
        print(f"\n2. Getting topic overview...")
        response = requests.get(f"{BASE_URL}/analytics/topics/overview")
        
        if response.status_code == 200:
            overview = response.json()
            print(f"✓ Topic overview retrieved")
            print(f"  Total topics: {overview['total_topics']}")
            print(f"  Total assignments: {overview['total_assignments']}")
            print(f"  Coverage: {overview['coverage']:.1f}%")
            print(f"  Needs analysis: {overview['needs_analysis']}")
        else:
            print(f"✗ Overview failed: {response.status_code}")
        
        # Test 3: Run batch analysis if needed
        if overview.get('needs_analysis', True):
            print(f"\n3. Running batch topic analysis...")
            response = requests.post(
                f"{BASE_URL}/analytics/topics/batch",
                params={"use_dummy": True, "limit": 20}
            )
            
            if response.status_code == 200:
                batch_data = response.json()
                print(f"✓ Batch analysis completed")
                print(f"  Analyzed messages: {batch_data['analyzed_count']}")
                print(f"  Processing time: {batch_data['processing_time_seconds']:.2f}s")
                print(f"  Method: {batch_data['analysis_method']}")
            else:
                print(f"✗ Batch analysis failed: {response.status_code}")
        
        # Test 4: Get trending topics
        print(f"\n4. Getting trending topics...")
        response = requests.get(
            f"{BASE_URL}/analytics/topics/trending",
            params={"days": 7, "limit": 5}
        )
        
        if response.status_code == 200:
            trending = response.json()
            print(f"✓ Trending topics retrieved")
            print(f"  Time period: {trending['time_period_days']} days")
            print(f"  Active topics: {trending['active_topics']}")
            print(f"  Total topics: {trending['total_topics']}")
            
            if trending['trending_topics']:
                print(f"  Top trending topics:")
                for i, topic in enumerate(trending['trending_topics'][:3], 1):
                    print(f"    {i}. {topic['topic_name']} (score: {topic['trend_score']:.3f})")
        else:
            print(f"✗ Trending topics failed: {response.status_code}")
        
        # Test 5: Get topic trends over time
        print(f"\n5. Getting topic trends over time...")
        response = requests.get(
            f"{BASE_URL}/analytics/topics/trends",
            params={"days": 30}
        )
        
        if response.status_code == 200:
            trends = response.json()
            print(f"✓ Topic trends retrieved")
            print(f"  Time period: {trends['time_period_days']} days")
            print(f"  Topics with data: {len(trends['topics_summary'])}")
            print(f"  Daily data points: {len(trends['daily_data'])}")
        else:
            print(f"✗ Topic trends failed: {response.status_code}")
        
        # Test 6: Get candidate topic analysis
        print(f"\n6. Getting candidate topic analysis...")
        response = requests.get(
            f"{BASE_URL}/analytics/topics/candidates",
            params={"limit": 10}
        )
        
        if response.status_code == 200:
            candidates = response.json()
            print(f"✓ Candidate topics retrieved")
            print(f"  Candidates analyzed: {candidates['total_candidates_analyzed']}")
            
            if candidates['candidate_topic_analysis']:
                print(f"  Sample candidates:")
                for candidate in candidates['candidate_topic_analysis'][:3]:
                    print(f"    • {candidate['candidate_name']}: {candidate['total_messages']} messages, {candidate['topic_diversity']} topics")
        else:
            print(f"✗ Candidate topics failed: {response.status_code}")
        
        # Test 7: Get topic-sentiment correlation
        print(f"\n7. Getting topic-sentiment correlation...")
        response = requests.get(f"{BASE_URL}/analytics/topics/sentiment")
        
        if response.status_code == 200:
            correlation = response.json()
            print(f"✓ Topic-sentiment correlation retrieved")
            print(f"  Topics analyzed: {correlation['total_topics_analyzed']}")
            
            if correlation['topic_sentiment_analysis']:
                print(f"  Sample correlations:")
                for topic in correlation['topic_sentiment_analysis'][:3]:
                    print(f"    • {topic['topic_name']}: avg sentiment {topic['avg_sentiment']:.3f}")
        else:
            print(f"✗ Topic-sentiment correlation failed: {response.status_code}")
        
        # Test 8: List all topics
        print(f"\n8. Listing all topics...")
        response = requests.get(f"{BASE_URL}/analytics/topics/list")
        
        if response.status_code == 200:
            topics_list = response.json()
            print(f"✓ Topics list retrieved")
            print(f"  Total topics: {topics_list['total_topics']}")
            
            if topics_list['topics']:
                print(f"  Available topics:")
                for topic in topics_list['topics'][:5]:
                    print(f"    • {topic['topic_name']}: {topic['message_count']} messages")
        else:
            print(f"✗ Topics list failed: {response.status_code}")
        
        print(f"\n🎉 Topic modeling API demo completed successfully!")
        print(f"\nThe API provides:")
        print(f"  • Political topic detection and classification")
        print(f"  • Individual message and batch analysis")
        print(f"  • Trending topics identification")
        print(f"  • Time-series trend analysis")
        print(f"  • Candidate topic distribution")
        print(f"  • Topic-sentiment correlation analysis")
        print(f"  • Comprehensive topic management")
        
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API server")
        print("  Make sure the API server is running on http://localhost:8000")
        print("  Start it with: uvicorn src.api.main:app --reload")
    except Exception as e:
        print(f"✗ Demo failed with error: {e}")


if __name__ == "__main__":
    test_topic_api_demo()
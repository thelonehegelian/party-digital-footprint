#!/usr/bin/env python3
"""
Engagement analytics API demo script.

This script demonstrates the engagement analytics API endpoints in action,
showing the complete workflow from engagement analysis to viral content detection.
"""

import requests
import json
from datetime import datetime


# API base URL
BASE_URL = "http://localhost:8000/api/v1"


def test_engagement_api_demo():
    """Demonstrate engagement analytics API capabilities."""
    
    print("=== Engagement Analytics API Demo ===\n")
    
    try:
        # Test 1: Analyze direct content
        print("1. Testing direct content engagement analysis...")
        content_analysis = {
            "content": "BREAKING: Major economic policy announcement - new tax reforms and business incentives launched to boost growth and create jobs across the nation."
        }
        
        response = requests.post(
            f"{BASE_URL}/analytics/engagement/analyze",
            json=content_analysis,
            params={"use_dummy": True}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Content analyzed successfully")
            print(f"  Engagement score: {data['engagement_score']:.3f}")
            print(f"  Virality score: {data['virality_score']:.3f}")
            print(f"  Influence score: {data['influence_score']:.3f}")
            print(f"  Platform percentile: {data['platform_percentile']:.1f}%")
            print(f"  Candidate percentile: {data['candidate_percentile']:.1f}%")
            print(f"  Platform metrics: {list(data['platform_metrics'].keys())}")
        else:
            print(f"✗ Content analysis failed: {response.status_code}")
            print(f"  Error: {response.text}")
        
        # Test 2: Get engagement overview
        print(f"\n2. Getting engagement overview...")
        response = requests.get(f"{BASE_URL}/analytics/engagement/overview")
        
        if response.status_code == 200:
            overview = response.json()
            print(f"✓ Engagement overview retrieved")
            print(f"  Total messages: {overview['total_messages']}")
            print(f"  Analyzed messages: {overview['analyzed_messages']}")
            print(f"  Coverage: {overview['coverage']:.1f}%")
            print(f"  Needs analysis: {overview['needs_analysis']}")
            print(f"  Avg engagement: {overview['avg_engagement']:.3f}")
            print(f"  Avg virality: {overview['avg_virality']:.3f}")
            print(f"  Avg influence: {overview['avg_influence']:.3f}")
        else:
            print(f"✗ Overview failed: {response.status_code}")
        
        # Test 3: Run batch analysis if needed
        if overview.get('needs_analysis', True):
            print(f"\n3. Running batch engagement analysis...")
            response = requests.post(
                f"{BASE_URL}/analytics/engagement/batch",
                params={"use_dummy": True, "limit": 20}
            )
            
            if response.status_code == 200:
                batch_data = response.json()
                print(f"✓ Batch analysis completed")
                print(f"  Analyzed messages: {batch_data['analyzed_count']}")
                print(f"  Processing time: {batch_data['processing_time_seconds']:.2f}s")
                print(f"  Method: {batch_data['analysis_method']}")
                print(f"  Regenerate: {batch_data['regenerate']}")
            else:
                print(f"✗ Batch analysis failed: {response.status_code}")
        
        # Test 4: Get platform performance comparison
        print(f"\n4. Getting platform performance comparison...")
        response = requests.get(f"{BASE_URL}/analytics/engagement/platforms")
        
        if response.status_code == 200:
            platforms = response.json()
            print(f"✓ Platform performance retrieved")
            print(f"  Total platforms: {platforms['total_platforms']}")
            
            if platforms['platform_comparison']:
                print(f"  Platform performance comparison:")
                for platform in platforms['platform_comparison']:
                    print(f"    • {platform['platform']}: {platform['message_count']} messages")
                    print(f"      - Avg engagement: {platform['avg_engagement']:.3f}")
                    print(f"      - Avg virality: {platform['avg_virality']:.3f}")
                    print(f"      - Avg influence: {platform['avg_influence']:.3f}")
        else:
            print(f"✗ Platform performance failed: {response.status_code}")
        
        # Test 5: Get viral content analysis
        print(f"\n5. Getting viral content analysis...")
        response = requests.get(
            f"{BASE_URL}/analytics/engagement/viral",
            params={"threshold": 0.5}  # Lower threshold to find content
        )
        
        if response.status_code == 200:
            viral = response.json()
            print(f"✓ Viral content analysis retrieved")
            print(f"  Viral threshold: {viral['viral_threshold']}")
            print(f"  Viral messages found: {viral['viral_messages_found']}")
            
            if viral['viral_content']:
                print(f"  Top viral content:")
                for i, content in enumerate(viral['viral_content'][:3], 1):
                    print(f"    {i}. {content['content_preview'][:80]}...")
                    print(f"       Virality: {content['virality_score']:.3f}, Engagement: {content['engagement_score']:.3f}")
                    print(f"       Candidate: {content['candidate_name']}")
            else:
                print(f"  No viral content found above threshold {viral['viral_threshold']}")
        else:
            print(f"✗ Viral content analysis failed: {response.status_code}")
        
        # Test 6: Test with different viral thresholds
        print(f"\n6. Testing viral content with different thresholds...")
        thresholds = [0.3, 0.5, 0.7, 0.9]
        
        for threshold in thresholds:
            response = requests.get(
                f"{BASE_URL}/analytics/engagement/viral",
                params={"threshold": threshold}
            )
            
            if response.status_code == 200:
                viral_data = response.json()
                count = viral_data['viral_messages_found']
                print(f"  Threshold {threshold}: {count} viral messages")
            else:
                print(f"  Threshold {threshold}: Failed to retrieve")
        
        # Test 7: Demonstrate platform-specific metrics
        print(f"\n7. Testing platform-specific engagement metrics...")
        
        # Test different content types
        content_tests = [
            {
                "content": "🚨 URGENT: Immigration policy update affects thousands of families nationwide. Share to spread awareness! #PolicyUpdate #Immigration",
                "description": "Social media style with emoji and hashtag"
            },
            {
                "content": "Economic analysis: GDP growth reaches 3.2% this quarter, driven by increased business investment and consumer confidence according to latest government statistics.",
                "description": "News article style content"
            },
            {
                "content": "Join our town hall meeting next Thursday 7pm at the community center. Your voice matters in shaping local policies.",
                "description": "Community engagement post"
            }
        ]
        
        for i, test in enumerate(content_tests, 1):
            response = requests.post(
                f"{BASE_URL}/analytics/engagement/analyze",
                json={"content": test["content"]},
                params={"use_dummy": True}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Test {i} ({test['description']}):")
                print(f"    Engagement: {data['engagement_score']:.3f}")
                print(f"    Virality: {data['virality_score']:.3f}")
                print(f"    Platform metrics: {data['platform_metrics']}")
        
        print(f"\n🎉 Engagement analytics API demo completed successfully!")
        print(f"\nThe API provides:")
        print(f"  • Comprehensive engagement scoring (0.0-1.0 scale)")
        print(f"  • Virality prediction and influence assessment")
        print(f"  • Platform-specific metrics analysis")
        print(f"  • Cross-platform performance comparison")
        print(f"  • Viral content detection and ranking")
        print(f"  • Quality indicators and audience relevance")
        print(f"  • Batch processing for large datasets")
        print(f"  • Real-time engagement velocity tracking")
        
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API server")
        print("  Make sure the API server is running on http://localhost:8000")
        print("  Start it with: uvicorn src.api.main:app --reload")
    except Exception as e:
        print(f"✗ Demo failed with error: {e}")


if __name__ == "__main__":
    test_engagement_api_demo()
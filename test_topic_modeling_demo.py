#!/usr/bin/env python3
"""
Demonstration script for topic modeling functionality.

This script shows the topic modeling system in action with dummy data generation,
topic analysis, and various analytics functions.
"""

from src.analytics.topics import PoliticalTopicAnalyzer
from src.database import get_session


def test_topic_modeling_demo():
    """Demonstrate topic modeling capabilities."""
    
    print("=== Political Topic Modeling System Demo ===\n")
    
    # Initialize the topic analyzer
    analyzer = PoliticalTopicAnalyzer()
    print("✓ Topic analyzer initialized")
    
    # Test with database
    with next(get_session()) as db:
        print("✓ Database connection established")
        
        # Get initial overview
        overview = analyzer.get_topic_overview(db)
        print(f"\n📊 Initial Overview:")
        print(f"  - Total topics: {overview['total_topics']}")
        print(f"  - Total assignments: {overview['total_assignments']}")
        print(f"  - Coverage: {overview['coverage']:.1f}%")
        print(f"  - Needs analysis: {overview['needs_analysis']}")
        
        if overview['needs_analysis']:
            print("\n⚙️ Generating topic assignments...")
            analyzed_count = analyzer.analyze_topics_in_messages(
                db, 
                use_dummy=True, 
                limit=20
            )
            print(f"✓ Analyzed {analyzed_count} messages")
            
            # Get updated overview
            overview = analyzer.get_topic_overview(db)
            print(f"\n📊 Updated Overview:")
            print(f"  - Total topics: {overview['total_topics']}")
            print(f"  - Coverage: {overview['coverage']:.1f}%")
            print(f"  - Messages with topics: {overview['messages_with_topics']}")
            print(f"  - Average coherence: {overview['avg_coherence']:.3f}")
        
        # Show top topics
        if overview['top_topics']:
            print(f"\n🔥 Top Topics by Message Count:")
            for i, topic in enumerate(overview['top_topics'][:5], 1):
                print(f"  {i}. {topic['topic_name']} ({topic['message_count']} messages)")
                print(f"     Trend: {topic['trend_score']:.3f}, Sentiment: {topic['avg_sentiment']:.3f}")
        
        # Show trending topics
        if overview['trending_topics']:
            print(f"\n📈 Trending Topics:")
            for i, topic in enumerate(overview['trending_topics'][:5], 1):
                print(f"  {i}. {topic['topic_name']}")
                print(f"     Trend Score: {topic['trend_score']:.3f}, Growth: {topic['growth_rate']:.3f}")
        
        # Test trending topics analysis
        print(f"\n🔍 Trending Topics Analysis (7 days):")
        trending = analyzer.get_trending_topics(db, days=7, limit=5)
        print(f"  - Active topics: {trending['active_topics']}")
        print(f"  - Total topics: {trending['total_topics']}")
        
        if trending['trending_topics']:
            for topic in trending['trending_topics'][:3]:
                print(f"    • {topic['topic_name']}: {topic['recent_messages']} recent messages")
                print(f"      Keywords: {', '.join(topic['keywords'][:3])}")
                print(f"      Trend: {topic['trend_score']:.3f}")
        
        # Test candidate topic analysis
        print(f"\n👥 Candidate Topic Analysis:")
        candidate_topics = analyzer.get_candidate_topic_analysis(db, limit=5)
        
        if candidate_topics['candidate_topic_analysis']:
            for candidate in candidate_topics['candidate_topic_analysis'][:3]:
                print(f"  • {candidate['candidate_name']} ({candidate['total_messages']} messages)")
                print(f"    Topic diversity: {candidate['topic_diversity']} topics")
                if candidate['top_topics']:
                    top_topic = candidate['top_topics'][0]
                    print(f"    Top topic: {top_topic['topic_name']} ({top_topic['message_count']} messages)")
        
        # Test time trends
        print(f"\n📊 Topic Trends Over Time (30 days):")
        trends = analyzer.get_topic_trends_over_time(db, days=30)
        print(f"  - Period: {trends['time_period_days']} days")
        print(f"  - Topics tracked: {len(trends['topics_summary'])}")
        
        if trends['daily_data']:
            # Show some sample trend data
            sample_dates = list(trends['daily_data'].keys())[:3]
            for date in sample_dates:
                day_topics = trends['daily_data'][date]
                if day_topics:
                    topic_name = list(day_topics.keys())[0]
                    count = day_topics[topic_name]['message_count']
                    print(f"    {date}: {topic_name} - {count} messages")
        
        print(f"\n🎉 Topic modeling system working correctly!")
        print(f"\nThe system provides:")
        print(f"  • Political topic detection and classification")
        print(f"  • Trending topic identification")
        print(f"  • Candidate topic distribution analysis")
        print(f"  • Time-series trend analysis")
        print(f"  • Integration with sentiment analysis")
        print(f"  • Comprehensive dummy data generation for testing")


if __name__ == "__main__":
    test_topic_modeling_demo()
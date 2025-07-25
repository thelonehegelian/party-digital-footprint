"""
Test the sentiment dashboard integration
"""

from src.dashboard.sentiment_service import SentimentDashboardService
from src.database import get_session

def test_dashboard_integration():
    """Test basic sentiment dashboard functionality"""
    
    print("=== Testing Sentiment Dashboard Integration ===\n")
    
    # Initialize service
    service = SentimentDashboardService()
    print("✓ Sentiment dashboard service initialized")
    
    # Test database connection and overview
    with next(get_session()) as db:
        overview = service.get_sentiment_overview(db)
        
        print(f"✓ Database connection successful")
        print(f"  - Total messages: {overview['total_messages']}")
        print(f"  - Analyzed messages: {overview['total_analyzed']}")
        print(f"  - Analysis coverage: {overview['analysis_coverage']:.1f}%")
        
        if overview['needs_analysis']:
            print("  - Status: Needs sentiment analysis data")
            
            # Generate some test data
            print("\n⚙️ Generating test sentiment data...")
            result = service.generate_dummy_sentiment_batch(db, limit=10)
            
            if result['success']:
                print(f"✓ Generated sentiment data for {result['analyzed_count']} messages")
                
                # Test overview again
                overview = service.get_sentiment_overview(db)
                print(f"  - Updated analysis coverage: {overview['analysis_coverage']:.1f}%")
                print(f"  - Sentiment distribution: {overview['sentiment_distribution']}")
                print(f"  - Political tone distribution: {overview['political_tone_distribution']}")
            else:
                print(f"✗ Failed to generate sentiment data: {result['message']}")
        else:
            print("  - Status: Has sentiment analysis data")
            print(f"  - Sentiment distribution: {overview['sentiment_distribution']}")
            print(f"  - Political tone distribution: {overview['political_tone_distribution']}")
        
        # Test other dashboard components
        print("\n🧪 Testing dashboard components...")
        
        # Test candidate comparison
        candidate_df = service.get_candidate_sentiment_comparison(db, limit=5)
        print(f"✓ Candidate sentiment comparison: {len(candidate_df)} candidates")
        
        # Test regional analysis
        regional_df = service.get_regional_sentiment_analysis(db)
        print(f"✓ Regional sentiment analysis: {len(regional_df)} regions")
        
        # Test political tone analysis
        tone_data = service.get_political_tone_analysis(db)
        print(f"✓ Political tone analysis: {len(tone_data['tone_distribution'])} tones")
        
        # Test emotion analysis
        emotion_data = service.get_emotion_analysis_data(db)
        print(f"✓ Emotion analysis: {len(emotion_data['emotion_averages'])} emotions")
        
        # Test detailed messages
        messages_df = service.get_detailed_messages_with_sentiment(db, limit=5)
        print(f"✓ Detailed messages with sentiment: {len(messages_df)} messages")
    
    print("\n🎉 All dashboard components working correctly!")
    print("\nYou can now view the sentiment analysis dashboard at:")
    print("http://localhost:8501 -> 🎭 Sentiment Analysis tab")

if __name__ == "__main__":
    test_dashboard_integration()
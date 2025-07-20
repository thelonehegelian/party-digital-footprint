#!/usr/bin/env python3
"""
Test script to verify the Reform UK messaging analysis system works with mock data.
"""

import asyncio
import subprocess
import sys
from pathlib import Path
from loguru import logger

from src.database import get_session, create_tables
from src.models import Source, Message, Keyword
from src.nlp.processor import BasicNLPProcessor


def test_database_connection():
    """Test database connection and table creation."""
    try:
        create_tables()
        
        with next(get_session()) as db:
            source_count = db.query(Source).count()
            message_count = db.query(Message).count()
            keyword_count = db.query(Keyword).count()
            
        logger.info(f"Database connection successful")
        logger.info(f"Sources: {source_count}, Messages: {message_count}, Keywords: {keyword_count}")
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def test_nlp_processing():
    """Test NLP processing functionality."""
    try:
        nlp_processor = BasicNLPProcessor()
        nlp_processor.load_model()
        
        if not nlp_processor.nlp:
            logger.warning("spaCy model not available - install with: python -m spacy download en_core_web_sm")
            return False
        
        # Test with sample text
        test_text = "Reform UK calls for immediate action on immigration crisis affecting British families and the NHS waiting lists."
        
        keywords = nlp_processor.extract_keywords(test_text)
        themes = nlp_processor.extract_message_themes(test_text)
        sentiment = nlp_processor.analyze_sentiment(test_text)
        
        logger.info(f"NLP test successful")
        logger.info(f"Keywords extracted: {len(keywords)}")
        logger.info(f"Themes identified: {themes}")
        logger.info(f"Sentiment: {sentiment['sentiment']}")
        
        return True
        
    except Exception as e:
        logger.error(f"NLP processing failed: {e}")
        return False


def test_mock_data_import():
    """Test importing mock data."""
    try:
        # Run the import script
        import_script = Path(__file__).parent / "import_mock_data.py"
        result = subprocess.run([sys.executable, str(import_script)], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Mock data import successful")
            
            # Verify data was imported
            with next(get_session()) as db:
                message_count = db.query(Message).count()
                keyword_count = db.query(Keyword).count()
                
            logger.info(f"After import - Messages: {message_count}, Keywords: {keyword_count}")
            return message_count > 0
            
        else:
            logger.error(f"Mock data import failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing mock data import: {e}")
        return False


def test_dashboard_functionality():
    """Test if dashboard can be launched (basic check)."""
    try:
        dashboard_file = Path(__file__).parent.parent / "dashboard.py"
        
        if dashboard_file.exists():
            logger.info("Dashboard file exists - manual test required")
            logger.info("Run: streamlit run dashboard.py")
            return True
        else:
            logger.error("Dashboard file not found")
            return False
            
    except Exception as e:
        logger.error(f"Dashboard test failed: {e}")
        return False


def run_comprehensive_test():
    """Run all system tests."""
    logger.info("Starting comprehensive system test...")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("NLP Processing", test_nlp_processing),
        ("Mock Data Import", test_mock_data_import),
        ("Dashboard Check", test_dashboard_functionality)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n=== Testing {test_name} ===")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "="*50)
    print("SYSTEM TEST RESULTS")
    print("="*50)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    passed_count = sum(1 for passed in results.values() if passed)
    total_count = len(results)
    
    print(f"\nOverall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! System is ready for use.")
        print("\nNext steps:")
        print("1. Launch dashboard: streamlit run dashboard.py")
        print("2. Explore the mock data")
        print("3. Configure real API credentials when ready")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("\nCommon fixes:")
        print("- Install spaCy model: python -m spacy download en_core_web_sm")
        print("- Check database configuration in .env")
        print("- Ensure all dependencies are installed: uv pip install -e .")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
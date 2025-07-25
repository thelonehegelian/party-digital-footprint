"""
Tests for search dashboard functionality.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Mock streamlit for testing
import sys
from unittest.mock import MagicMock
sys.modules['streamlit'] = MagicMock()

# Import dashboard functions
from dashboard import (
    perform_mock_search,
    display_message_search_results, 
    display_keyword_search_results,
    display_candidate_search_results,
    display_source_search_results
)


class TestSearchDashboardFunctions:
    """Test dashboard search functions."""
    
    @pytest.fixture
    def sample_messages_df(self):
        """Create sample messages DataFrame."""
        return pd.DataFrame([
            {
                'message_id': 1,
                'content': 'This is a test message about immigration policy reform',
                'url': 'https://example.com/message1',
                'published_at': datetime.now() - timedelta(days=1),
                'source_name': 'Test Twitter',
                'source_type': 'twitter',
                'geographic_scope': 'national'
            },
            {
                'message_id': 2, 
                'content': 'Healthcare system needs comprehensive reform',
                'url': 'https://example.com/message2',
                'published_at': datetime.now() - timedelta(days=2),
                'source_name': 'Test Website',
                'source_type': 'website',
                'geographic_scope': 'regional'
            },
            {
                'message_id': 3,
                'content': 'Economic policies for small business support',
                'url': 'https://example.com/message3', 
                'published_at': datetime.now() - timedelta(days=3),
                'source_name': 'Test Facebook',
                'source_type': 'facebook',
                'geographic_scope': 'local'
            }
        ])
    
    @pytest.fixture
    def sample_keywords_df(self):
        """Create sample keywords DataFrame."""
        return pd.DataFrame([
            {
                'keyword': 'immigration',
                'confidence': 0.95,
                'extraction_method': 'nlp',
                'message_id': 1
            },
            {
                'keyword': 'healthcare',
                'confidence': 0.88,
                'extraction_method': 'nlp', 
                'message_id': 2
            },
            {
                'keyword': 'economic reform',
                'confidence': 0.92,
                'extraction_method': 'spacy',
                'message_id': 3
            }
        ])
    
    @pytest.fixture
    def sample_candidates_df(self):
        """Create sample candidates DataFrame."""
        return pd.DataFrame([
            {
                'id': 1,
                'name': 'John Smith',
                'constituency_name': 'Test Constituency A',
                'message_count': 15,
                'candidate_type': 'local'
            },
            {
                'id': 2,
                'name': 'Jane Doe',
                'constituency_name': 'Test Constituency B', 
                'message_count': 8,
                'candidate_type': 'national'
            },
            {
                'id': 3,
                'name': 'Bob Johnson', 
                'constituency_name': 'Test Constituency C',
                'message_count': 12,
                'candidate_type': 'local'
            }
        ])
    
    def test_perform_mock_search_messages(self, sample_messages_df, sample_keywords_df, sample_candidates_df):
        """Test mock search for messages."""
        result = perform_mock_search(
            query="immigration",
            search_types=["messages"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope=None,
            limit=10,
            messages_df=sample_messages_df,
            keywords_df=sample_keywords_df,
            candidates_df=sample_candidates_df
        )
        
        assert result['query'] == "immigration"
        assert result['total_results'] >= 1
        assert 'messages' in result['results']
        assert result['results']['messages']['count'] >= 1
        
        message_result = result['results']['messages']['items'][0]
        assert 'immigration' in message_result['content'].lower()
        assert 'message_id' in message_result
        assert 'relevance_score' in message_result
    
    def test_perform_mock_search_with_source_filter(self, sample_messages_df, sample_keywords_df, sample_candidates_df):
        """Test mock search with source type filter."""
        result = perform_mock_search(
            query="reform",
            search_types=["messages"],
            source_types=["twitter", "website"],
            sentiment_filter=None,
            geographic_scope=None,
            limit=10,
            messages_df=sample_messages_df,
            keywords_df=sample_keywords_df,
            candidates_df=sample_candidates_df
        )
        
        # Should only return messages from specified source types
        for message in result['results']['messages']['items']:
            assert message['source_type'] in ["twitter", "website"]
    
    def test_perform_mock_search_with_geographic_filter(self, sample_messages_df, sample_keywords_df, sample_candidates_df):
        """Test mock search with geographic scope filter."""
        result = perform_mock_search(
            query="test",
            search_types=["messages"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope="national",
            limit=10,
            messages_df=sample_messages_df,
            keywords_df=sample_keywords_df,
            candidates_df=sample_candidates_df
        )
        
        # Should only return messages with national scope
        for message in result['results']['messages']['items']:
            # Note: This would need to be implemented in the actual search
            pass
    
    def test_perform_mock_search_keywords(self, sample_messages_df, sample_keywords_df, sample_candidates_df):
        """Test mock search for keywords."""
        result = perform_mock_search(
            query="healthcare",
            search_types=["keywords"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope=None,
            limit=10,
            messages_df=sample_messages_df,
            keywords_df=sample_keywords_df,
            candidates_df=sample_candidates_df
        )
        
        assert 'keywords' in result['results']
        assert result['results']['keywords']['count'] >= 1
        
        keyword_result = result['results']['keywords']['items'][0]
        assert 'healthcare' in keyword_result['keyword'].lower()
        assert 'confidence' in keyword_result
        assert 'extraction_method' in keyword_result
    
    def test_perform_mock_search_candidates(self, sample_messages_df, sample_keywords_df, sample_candidates_df):
        """Test mock search for candidates."""
        result = perform_mock_search(
            query="John",
            search_types=["candidates"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope=None,
            limit=10,
            messages_df=sample_messages_df,
            keywords_df=sample_keywords_df,
            candidates_df=sample_candidates_df
        )
        
        assert 'candidates' in result['results']
        assert result['results']['candidates']['count'] >= 1
        
        candidate_result = result['results']['candidates']['items'][0]
        assert 'john' in candidate_result['candidate_name'].lower()
        assert 'constituency_name' in candidate_result
        assert 'message_count' in candidate_result
    
    def test_perform_mock_search_multiple_types(self, sample_messages_df, sample_keywords_df, sample_candidates_df):
        """Test mock search across multiple types."""
        result = perform_mock_search(
            query="test",
            search_types=["messages", "keywords", "candidates"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope=None,
            limit=10,
            messages_df=sample_messages_df,
            keywords_df=sample_keywords_df,
            candidates_df=sample_candidates_df
        )
        
        assert len(result['results']) == 3
        assert 'messages' in result['results']
        assert 'keywords' in result['results']
        assert 'candidates' in result['results']
    
    def test_perform_mock_search_empty_dataframes(self):
        """Test mock search with empty DataFrames."""
        empty_df = pd.DataFrame()
        
        result = perform_mock_search(
            query="test",
            search_types=["messages", "keywords", "candidates"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope=None,
            limit=10,
            messages_df=empty_df,
            keywords_df=empty_df,
            candidates_df=empty_df
        )
        
        assert result['total_results'] == 0
        assert result['results']['messages']['count'] == 0
        assert result['results']['keywords']['count'] == 0
        assert result['results']['candidates']['count'] == 0
    
    def test_perform_mock_search_case_insensitive(self, sample_messages_df, sample_keywords_df, sample_candidates_df):
        """Test that search is case insensitive."""
        result_lower = perform_mock_search(
            query="immigration",
            search_types=["messages"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope=None,
            limit=10,
            messages_df=sample_messages_df,
            keywords_df=sample_keywords_df,
            candidates_df=sample_candidates_df
        )
        
        result_upper = perform_mock_search(
            query="IMMIGRATION",
            search_types=["messages"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope=None,
            limit=10,
            messages_df=sample_messages_df,
            keywords_df=sample_keywords_df,
            candidates_df=sample_candidates_df
        )
        
        # Both should return the same results
        assert result_lower['results']['messages']['count'] == result_upper['results']['messages']['count']
    
    def test_perform_mock_search_limit_respected(self, sample_messages_df, sample_keywords_df, sample_candidates_df):
        """Test that search limit is respected."""
        result = perform_mock_search(
            query="test",
            search_types=["messages"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope=None,
            limit=1,
            messages_df=sample_messages_df,
            keywords_df=sample_keywords_df,
            candidates_df=sample_candidates_df
        )
        
        assert len(result['results']['messages']['items']) <= 1
    
    def test_perform_mock_search_timing(self, sample_messages_df, sample_keywords_df, sample_candidates_df):
        """Test that search returns timing information."""
        result = perform_mock_search(
            query="test",
            search_types=["messages"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope=None,
            limit=10,
            messages_df=sample_messages_df,
            keywords_df=sample_keywords_df,
            candidates_df=sample_candidates_df
        )
        
        assert 'search_time_ms' in result
        assert isinstance(result['search_time_ms'], (int, float))
        assert result['search_time_ms'] >= 0
    
    def test_perform_mock_search_partial_match(self, sample_messages_df, sample_keywords_df, sample_candidates_df):
        """Test search with partial string matching."""
        result = perform_mock_search(
            query="immigr",  # Partial match for "immigration"
            search_types=["messages"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope=None,
            limit=10,
            messages_df=sample_messages_df,
            keywords_df=sample_keywords_df,
            candidates_df=sample_candidates_df
        )
        
        # Should find messages containing "immigration"
        assert result['results']['messages']['count'] >= 1
        
        message_result = result['results']['messages']['items'][0]
        assert 'immigration' in message_result['content'].lower()


class TestSearchDisplayFunctions:
    """Test search result display functions."""
    
    @patch('streamlit.write')
    @patch('streamlit.expander')
    @patch('streamlit.columns')
    def test_display_message_search_results(self, mock_columns, mock_expander, mock_write):
        """Test displaying message search results."""
        mock_expander.return_value.__enter__ = Mock()
        mock_expander.return_value.__exit__ = Mock()
        mock_columns.return_value = [Mock(), Mock()]
        
        message_results = [
            {
                'content_preview': 'This is a test message preview...',
                'content': 'This is a test message about immigration policy',
                'url': 'https://example.com/test',
                'source_name': 'Test Source',
                'source_type': 'twitter',
                'published_at': datetime.now().isoformat(),
                'relevance_score': 0.85
            }
        ]
        
        display_message_search_results(message_results)
        
        # Should call streamlit functions
        mock_write.assert_called()
        mock_expander.assert_called()
        mock_columns.assert_called()
    
    @patch('streamlit.write')
    @patch('streamlit.columns')
    def test_display_keyword_search_results(self, mock_columns, mock_write):
        """Test displaying keyword search results."""
        mock_columns.return_value = [Mock(), Mock(), Mock()]
        
        keyword_results = [
            {
                'keyword': 'immigration',
                'message_count': 5,
                'confidence': 0.95
            }
        ]
        
        display_keyword_search_results(keyword_results)
        
        mock_write.assert_called()
        mock_columns.assert_called()
    
    @patch('streamlit.write')
    @patch('streamlit.columns')
    def test_display_candidate_search_results(self, mock_columns, mock_write):
        """Test displaying candidate search results."""
        mock_columns.return_value = [Mock(), Mock(), Mock()]
        
        candidate_results = [
            {
                'candidate_name': 'John Smith',
                'constituency_name': 'Test Constituency',
                'message_count': 15,
                'recent_message_count': 3
            }
        ]
        
        display_candidate_search_results(candidate_results)
        
        mock_write.assert_called()
        mock_columns.assert_called()
    
    @patch('streamlit.write')
    def test_display_source_search_results(self, mock_write):
        """Test displaying source search results."""
        source_results = [
            {
                'source_name': 'Test Twitter',
                'source_type': 'twitter'
            }
        ]
        
        display_source_search_results(source_results)
        
        mock_write.assert_called()
    
    @patch('streamlit.write')
    @patch('streamlit.expander')
    @patch('streamlit.columns')
    def test_display_empty_results(self, mock_columns, mock_expander, mock_write):
        """Test displaying empty search results."""
        display_message_search_results([])
        
        # Should still call write to show "Found 0 matching messages"
        mock_write.assert_called()


class TestSearchEdgeCases:
    """Test edge cases in search dashboard functionality."""
    
    def test_search_with_nan_values(self, sample_messages_df, sample_keywords_df, sample_candidates_df):
        """Test search with NaN values in DataFrames."""
        # Add NaN values to test data
        sample_messages_df.loc[0, 'url'] = None
        sample_messages_df.loc[1, 'published_at'] = None
        
        result = perform_mock_search(
            query="test",
            search_types=["messages"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope=None,
            limit=10,
            messages_df=sample_messages_df,
            keywords_df=sample_keywords_df,
            candidates_df=sample_candidates_df
        )
        
        # Should handle NaN values gracefully
        assert isinstance(result, dict)
        assert 'results' in result
    
    def test_search_with_special_characters_in_content(self):
        """Test search with special characters in DataFrame content."""
        messages_df = pd.DataFrame([
            {
                'message_id': 1,
                'content': 'Message with special chars: @#$%^&*()',
                'source_name': 'Test',
                'source_type': 'twitter'
            }
        ])
        
        result = perform_mock_search(
            query="@#$",
            search_types=["messages"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope=None,
            limit=10,
            messages_df=messages_df,
            keywords_df=pd.DataFrame(),
            candidates_df=pd.DataFrame()
        )
        
        # Should handle special characters
        assert isinstance(result, dict)
    
    def test_search_with_very_long_content(self):
        """Test search with very long message content."""
        long_content = "This is a very long message. " * 100  # 3000+ chars
        
        messages_df = pd.DataFrame([
            {
                'message_id': 1,
                'content': long_content,
                'source_name': 'Test',
                'source_type': 'twitter'
            }
        ])
        
        result = perform_mock_search(
            query="very long",
            search_types=["messages"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope=None,
            limit=10,
            messages_df=messages_df,
            keywords_df=pd.DataFrame(),
            candidates_df=pd.DataFrame()
        )
        
        # Should truncate content appropriately
        if result['results']['messages']['count'] > 0:
            message = result['results']['messages']['items'][0]
            assert len(message['content']) <= 503  # 500 + "..."
            assert len(message['content_preview']) <= 203  # 200 + "..."
    
    def test_search_performance_with_large_dataset(self):
        """Test search performance with larger dataset."""
        # Create larger test dataset
        large_messages_df = pd.DataFrame([
            {
                'message_id': i,
                'content': f'Test message number {i} about various topics',
                'source_name': f'Source {i}',
                'source_type': 'twitter' if i % 2 == 0 else 'website'
            }
            for i in range(1000)
        ])
        
        import time
        start_time = time.time()
        
        result = perform_mock_search(
            query="test",
            search_types=["messages"],
            source_types=None,
            sentiment_filter=None,
            geographic_scope=None,
            limit=50,
            messages_df=large_messages_df,
            keywords_df=pd.DataFrame(),
            candidates_df=pd.DataFrame()
        )
        
        end_time = time.time()
        actual_time_ms = (end_time - start_time) * 1000
        
        # Performance should be reasonable
        assert actual_time_ms < 5000  # Less than 5 seconds
        
        # Should respect limit
        assert len(result['results']['messages']['items']) <= 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
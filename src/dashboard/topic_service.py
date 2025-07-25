"""
Topic modeling data service for Streamlit dashboard.

Provides data retrieval and processing functions for topic modeling
visualizations in the dashboard, with built-in caching and error handling.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case

from ..models import Message, Source, Candidate, Constituency, TopicModel, MessageTopic, MessageSentiment
from ..analytics.topics import PoliticalTopicAnalyzer


class TopicDashboardService:
    """
    Service class for topic modeling data operations in Streamlit dashboard.
    
    Provides methods to:
    - Load topic data with proper caching
    - Generate dummy topic data for testing
    - Format data for Streamlit visualizations
    - Handle API-like data transformations
    """
    
    def __init__(self):
        """Initialize the topic dashboard service."""
        self.analyzer = PoliticalTopicAnalyzer()
    
    def get_topic_overview(self, db: Session) -> Dict:
        """
        Get overall topic modeling statistics.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with topic overview statistics
        """
        return self.analyzer.get_topic_overview(db)
    
    def get_trending_topics(self, db: Session, days: int = 7, limit: int = 10) -> Dict:
        """
        Get trending topics for the specified time period.
        
        Args:
            db: Database session
            days: Number of days to analyze for trends
            limit: Maximum number of topics to return
            
        Returns:
            Dictionary with trending topic data
        """
        return self.analyzer.get_trending_topics(db, days=days, limit=limit)
    
    def get_topic_trends_over_time(self, db: Session, days: int = 30, topic_id: Optional[int] = None) -> Dict:
        """
        Get topic trends over time for visualization.
        
        Args:
            db: Database session
            days: Number of days to analyze
            topic_id: Specific topic ID, or None for all topics
            
        Returns:
            Dictionary with time-series trend data
        """
        return self.analyzer.get_topic_trends_over_time(db, topic_id=topic_id, days=days)
    
    def get_candidate_topic_analysis(self, db: Session, limit: int = 10) -> Dict:
        """
        Get topic distribution analysis by candidate.
        
        Args:
            db: Database session
            limit: Maximum number of candidates to include
            
        Returns:
            Dictionary with candidate topic data
        """
        return self.analyzer.get_candidate_topic_analysis(db, limit=limit)
    
    def get_topic_sentiment_analysis(self, db: Session) -> Dict:
        """
        Get topic-sentiment correlation analysis.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with topic-sentiment correlations
        """
        return self.analyzer.get_topic_sentiment_analysis(db)
    
    def get_regional_topic_analysis(self, db: Session) -> pd.DataFrame:
        """
        Get topic analysis grouped by UK regions.
        
        Args:
            db: Database session
            
        Returns:
            DataFrame with regional topic data
        """
        # Get regional topic aggregations
        regional_topics = db.query(
            Constituency.region,
            TopicModel.topic_name,
            func.count(MessageTopic.id).label('message_count'),
            func.avg(MessageTopic.probability).label('avg_probability')
        ).join(Candidate, Constituency.id == Candidate.constituency_id)\
         .join(Message, Candidate.id == Message.candidate_id)\
         .join(MessageTopic, Message.id == MessageTopic.message_id)\
         .join(TopicModel, MessageTopic.topic_id == TopicModel.id)\
         .group_by(Constituency.region, TopicModel.topic_name)\
         .having(func.count(MessageTopic.id) > 0)\
         .order_by(Constituency.region, func.count(MessageTopic.id).desc())\
         .all()
        
        if not regional_topics:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for row in regional_topics:
            data.append({
                'region': row.region,
                'topic_name': row.topic_name,
                'message_count': row.message_count,
                'avg_probability': float(row.avg_probability or 0)
            })
        
        return pd.DataFrame(data)
    
    def get_detailed_messages_with_topics(
        self, 
        db: Session, 
        limit: int = 20,
        topic_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get recent messages with topic assignments for detailed view.
        
        Args:
            db: Database session
            limit: Number of messages to return
            topic_filter: Filter by topic name
            
        Returns:
            DataFrame with message and topic data
        """
        query = db.query(
            Message.id,
            Message.content,
            Message.url,
            Message.published_at,
            Message.source_id,
            Source.name.label('source_name'),
            Source.source_type,
            Candidate.name.label('candidate_name'),
            Constituency.name.label('constituency_name'),
            Constituency.region,
            TopicModel.topic_name.label('primary_topic'),
            MessageTopic.probability.label('topic_probability'),
            MessageTopic.is_primary_topic,
            MessageTopic.assigned_at
        ).join(Source, Message.source_id == Source.id)\
         .join(MessageTopic, Message.id == MessageTopic.message_id)\
         .join(TopicModel, MessageTopic.topic_id == TopicModel.id)\
         .outerjoin(Candidate, Message.candidate_id == Candidate.id)\
         .outerjoin(Constituency, Candidate.constituency_id == Constituency.id)\
         .filter(MessageTopic.is_primary_topic == True)  # Only primary topics
        
        # Apply topic filter
        if topic_filter:
            query = query.filter(TopicModel.topic_name == topic_filter)
        
        # Order by most recent
        query = query.order_by(Message.published_at.desc().nullslast(), Message.scraped_at.desc())
        
        messages = query.limit(limit).all()
        
        if not messages:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for msg in messages:
            data.append({
                'id': msg.id,
                'content': msg.content,
                'url': msg.url,
                'published_at': msg.published_at,
                'source_name': msg.source_name,
                'source_type': msg.source_type,
                'candidate_name': msg.candidate_name,
                'constituency_name': msg.constituency_name,
                'region': msg.region,
                'primary_topic': msg.primary_topic,
                'topic_probability': float(msg.topic_probability),
                'is_primary_topic': msg.is_primary_topic,
                'assigned_at': msg.assigned_at
            })
        
        df = pd.DataFrame(data)
        if not df.empty and 'published_at' in df.columns:
            df['published_at'] = pd.to_datetime(df['published_at'])
        
        return df
    
    def get_topic_distribution_data(self, db: Session) -> Dict:
        """
        Get topic distribution data for pie charts and overviews.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with topic distribution data
        """
        # Get topic message counts
        topic_counts = db.query(
            TopicModel.topic_name,
            TopicModel.message_count,
            TopicModel.trend_score,
            TopicModel.avg_sentiment,
            TopicModel.coherence_score
        ).filter(TopicModel.message_count > 0)\
         .order_by(TopicModel.message_count.desc())\
         .all()
        
        if not topic_counts:
            return {"topics": [], "total_messages": 0}
        
        topics_data = []
        total_messages = 0
        
        for topic in topic_counts:
            topics_data.append({
                "topic_name": topic.topic_name,
                "message_count": topic.message_count,
                "trend_score": float(topic.trend_score),
                "avg_sentiment": float(topic.avg_sentiment or 0),
                "coherence_score": float(topic.coherence_score or 0)
            })
            total_messages += topic.message_count
        
        return {
            "topics": topics_data,
            "total_messages": total_messages
        }
    
    def get_topic_keywords_data(self, db: Session, limit: int = 10) -> List[Dict]:
        """
        Get topic keywords for word clouds and keyword analysis.
        
        Args:
            db: Database session
            limit: Maximum number of topics to include
            
        Returns:
            List of topics with their keywords
        """
        topics = db.query(TopicModel)\
                   .filter(TopicModel.keywords.isnot(None))\
                   .order_by(TopicModel.message_count.desc())\
                   .limit(limit)\
                   .all()
        
        keywords_data = []
        for topic in topics:
            if topic.keywords:
                keywords = []
                for kw in topic.keywords:
                    if isinstance(kw, dict) and 'word' in kw and 'weight' in kw:
                        keywords.append({
                            'word': kw['word'],
                            'weight': float(kw['weight']),
                            'topic_name': topic.topic_name
                        })
                
                keywords_data.append({
                    'topic_name': topic.topic_name,
                    'keywords': keywords,
                    'message_count': topic.message_count,
                    'description': topic.description
                })
        
        return keywords_data
    
    def generate_dummy_topic_batch(self, db: Session, limit: int = 50) -> Dict:
        """
        Generate dummy topic data for testing dashboard functionality.
        
        Args:
            db: Database session
            limit: Number of messages to analyze
            
        Returns:
            Dictionary with operation results
        """
        try:
            analyzed_count = self.analyzer.analyze_topics_in_messages(
                db, 
                use_dummy=True, 
                limit=limit
            )
            
            return {
                "success": True,
                "analyzed_count": analyzed_count,
                "message": f"Successfully analyzed {analyzed_count} messages with dummy topic data"
            }
        except Exception as e:
            return {
                "success": False,
                "analyzed_count": 0,
                "message": f"Error generating topic data: {str(e)}"
            }
    
    def get_topic_coherence_analysis(self, db: Session) -> Dict:
        """
        Get topic coherence quality analysis.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with coherence analysis
        """
        topics = db.query(
            TopicModel.topic_name,
            TopicModel.coherence_score,
            TopicModel.message_count,
            TopicModel.trend_score
        ).filter(TopicModel.coherence_score.isnot(None))\
         .order_by(TopicModel.coherence_score.desc())\
         .all()
        
        if not topics:
            return {
                "coherence_data": [],
                "avg_coherence": 0.0,
                "quality_distribution": {}
            }
        
        coherence_data = []
        coherence_scores = []
        
        for topic in topics:
            coherence_score = float(topic.coherence_score)
            coherence_data.append({
                "topic_name": topic.topic_name,
                "coherence_score": coherence_score,
                "message_count": topic.message_count,
                "trend_score": float(topic.trend_score)
            })
            coherence_scores.append(coherence_score)
        
        # Calculate quality distribution
        quality_distribution = {
            "high": sum(1 for score in coherence_scores if score >= 0.7),
            "medium": sum(1 for score in coherence_scores if 0.5 <= score < 0.7),
            "low": sum(1 for score in coherence_scores if score < 0.5)
        }
        
        avg_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
        
        return {
            "coherence_data": coherence_data,
            "avg_coherence": avg_coherence,
            "quality_distribution": quality_distribution
        }
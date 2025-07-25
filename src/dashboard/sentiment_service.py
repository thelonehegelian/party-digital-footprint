"""
Sentiment analysis data service for Streamlit dashboard.

Provides data retrieval and processing functions for sentiment analysis
visualizations in the dashboard, with built-in caching and error handling.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case

from ..models import Message, MessageSentiment, Source, Candidate, Constituency
from ..analytics.sentiment import PoliticalSentimentAnalyzer


class SentimentDashboardService:
    """
    Service class for sentiment analysis data operations in Streamlit dashboard.
    
    Provides methods to:
    - Load sentiment data with proper caching
    - Generate dummy sentiment data for testing
    - Format data for Streamlit visualizations
    - Handle API-like data transformations
    """
    
    def __init__(self):
        """Initialize the sentiment dashboard service."""
        self.analyzer = PoliticalSentimentAnalyzer()
    
    def get_sentiment_overview(self, db: Session) -> Dict:
        """
        Get overall sentiment analysis statistics.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with sentiment overview statistics
        """
        # Basic counts
        total_messages = db.query(Message).count()
        total_analyzed = db.query(MessageSentiment).count()
        
        if total_analyzed == 0:
            return {
                "total_messages": total_messages,
                "total_analyzed": 0,
                "analysis_coverage": 0.0,
                "sentiment_distribution": {},
                "political_tone_distribution": {},
                "emotion_distribution": {},
                "average_sentiment_score": 0.0,
                "average_confidence": 0.0,
                "needs_analysis": True
            }
        
        # Sentiment distribution
        sentiment_dist = db.query(
            MessageSentiment.sentiment_label,
            func.count(MessageSentiment.id)
        ).group_by(MessageSentiment.sentiment_label).all()
        
        # Political tone distribution
        tone_dist = db.query(
            MessageSentiment.political_tone,
            func.count(MessageSentiment.id)
        ).group_by(MessageSentiment.political_tone).all()
        
        # Emotion analysis - aggregate all emotions
        emotion_data = db.query(MessageSentiment.emotions).all()
        emotion_totals = {}
        for (emotions,) in emotion_data:
            if emotions:
                for emotion, score in emotions.items():
                    emotion_totals[emotion] = emotion_totals.get(emotion, 0) + 1
        
        # Average scores
        avg_sentiment = db.query(func.avg(MessageSentiment.sentiment_score)).scalar() or 0.0
        avg_confidence = db.query(func.avg(MessageSentiment.confidence)).scalar() or 0.0
        
        return {
            "total_messages": total_messages,
            "total_analyzed": total_analyzed,
            "analysis_coverage": (total_analyzed / total_messages * 100) if total_messages > 0 else 0.0,
            "sentiment_distribution": dict(sentiment_dist),
            "political_tone_distribution": dict(tone_dist),
            "emotion_distribution": emotion_totals,
            "average_sentiment_score": float(avg_sentiment),
            "average_confidence": float(avg_confidence),
            "needs_analysis": False
        }
    
    def get_sentiment_trends(self, db: Session, days: int = 30) -> Dict:
        """
        Get sentiment trends over time for dashboard visualization.
        
        Args:
            db: Database session
            days: Number of days to analyze
            
        Returns:
            Dictionary with formatted trend data for Streamlit
        """
        return self.analyzer.get_sentiment_trends(db, days=days)
    
    def get_candidate_sentiment_comparison(self, db: Session, limit: int = 10) -> pd.DataFrame:
        """
        Get sentiment comparison data for top candidates.
        
        Args:
            db: Database session
            limit: Number of top candidates to include
            
        Returns:
            DataFrame with candidate sentiment data
        """
        # Get candidate sentiment aggregations
        candidate_sentiment = db.query(
            Candidate.name,
            Candidate.id,
            func.count(MessageSentiment.id).label('message_count'),
            func.avg(MessageSentiment.sentiment_score).label('avg_sentiment'),
            func.avg(MessageSentiment.confidence).label('avg_confidence'),
            func.sum(case((MessageSentiment.sentiment_label == 'positive', 1), else_=0)).label('positive_count'),
            func.sum(case((MessageSentiment.sentiment_label == 'negative', 1), else_=0)).label('negative_count'),
            func.sum(case((MessageSentiment.sentiment_label == 'neutral', 1), else_=0)).label('neutral_count')
        ).join(Message, Candidate.id == Message.candidate_id)\
         .join(MessageSentiment, Message.id == MessageSentiment.message_id)\
         .group_by(Candidate.id, Candidate.name)\
         .having(func.count(MessageSentiment.id) > 0)\
         .order_by(func.count(MessageSentiment.id).desc())\
         .limit(limit)\
         .all()
        
        if not candidate_sentiment:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for row in candidate_sentiment:
            data.append({
                'candidate_name': row.name,
                'candidate_id': row.id,
                'message_count': row.message_count,
                'avg_sentiment': float(row.avg_sentiment or 0),
                'avg_confidence': float(row.avg_confidence or 0),
                'positive_count': row.positive_count or 0,
                'negative_count': row.negative_count or 0,
                'neutral_count': row.neutral_count or 0,
                'positive_pct': (row.positive_count or 0) / row.message_count * 100,
                'negative_pct': (row.negative_count or 0) / row.message_count * 100,
                'neutral_pct': (row.neutral_count or 0) / row.message_count * 100
            })
        
        return pd.DataFrame(data)
    
    def get_regional_sentiment_analysis(self, db: Session) -> pd.DataFrame:
        """
        Get sentiment analysis grouped by UK regions.
        
        Args:
            db: Database session
            
        Returns:
            DataFrame with regional sentiment data
        """
        # Get regional sentiment aggregations
        regional_sentiment = db.query(
            Constituency.region,
            func.count(MessageSentiment.id).label('message_count'),
            func.avg(MessageSentiment.sentiment_score).label('avg_sentiment'),
            func.sum(case((MessageSentiment.sentiment_label == 'positive', 1), else_=0)).label('positive_count'),
            func.sum(case((MessageSentiment.sentiment_label == 'negative', 1), else_=0)).label('negative_count'),
            func.sum(case((MessageSentiment.sentiment_label == 'neutral', 1), else_=0)).label('neutral_count')
        ).join(Candidate, Constituency.id == Candidate.constituency_id)\
         .join(Message, Candidate.id == Message.candidate_id)\
         .join(MessageSentiment, Message.id == MessageSentiment.message_id)\
         .group_by(Constituency.region)\
         .having(func.count(MessageSentiment.id) > 0)\
         .order_by(func.count(MessageSentiment.id).desc())\
         .all()
        
        if not regional_sentiment:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for row in regional_sentiment:
            total_messages = row.message_count
            data.append({
                'region': row.region,
                'message_count': total_messages,
                'avg_sentiment': float(row.avg_sentiment or 0),
                'positive_count': row.positive_count or 0,
                'negative_count': row.negative_count or 0,
                'neutral_count': row.neutral_count or 0,
                'positive_pct': (row.positive_count or 0) / total_messages * 100,
                'negative_pct': (row.negative_count or 0) / total_messages * 100,
                'neutral_pct': (row.neutral_count or 0) / total_messages * 100
            })
        
        return pd.DataFrame(data)
    
    def get_political_tone_analysis(self, db: Session) -> Dict:
        """
        Get detailed political tone analysis for visualization.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with political tone breakdown and trends
        """
        # Overall tone distribution
        tone_dist = db.query(
            MessageSentiment.political_tone,
            func.count(MessageSentiment.id).label('count'),
            func.avg(MessageSentiment.tone_confidence).label('avg_confidence')
        ).group_by(MessageSentiment.political_tone)\
         .order_by(func.count(MessageSentiment.id).desc())\
         .all()
        
        # Tone by candidate (top 10 candidates)
        tone_by_candidate = db.query(
            Candidate.name,
            MessageSentiment.political_tone,
            func.count(MessageSentiment.id).label('count')
        ).join(Message, Candidate.id == Message.candidate_id)\
         .join(MessageSentiment, Message.id == MessageSentiment.message_id)\
         .group_by(Candidate.name, MessageSentiment.political_tone)\
         .order_by(func.count(MessageSentiment.id).desc())\
         .limit(50)\
         .all()
        
        # Format tone distribution
        tone_distribution = {}
        tone_confidence = {}
        for row in tone_dist:
            tone_distribution[row.political_tone] = row.count
            tone_confidence[row.political_tone] = float(row.avg_confidence or 0)
        
        # Format candidate tone data
        candidate_tone_data = []
        for row in tone_by_candidate:
            candidate_tone_data.append({
                'candidate': row.name,
                'political_tone': row.political_tone,
                'count': row.count
            })
        
        return {
            "tone_distribution": tone_distribution,
            "tone_confidence": tone_confidence,
            "candidate_tone_data": candidate_tone_data
        }
    
    def get_detailed_messages_with_sentiment(
        self, 
        db: Session, 
        limit: int = 20,
        sentiment_filter: Optional[str] = None,
        tone_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get recent messages with sentiment analysis data for detailed view.
        
        Args:
            db: Database session
            limit: Number of messages to return
            sentiment_filter: Filter by sentiment label (positive/negative/neutral)
            tone_filter: Filter by political tone
            
        Returns:
            DataFrame with message and sentiment data
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
            MessageSentiment.sentiment_score,
            MessageSentiment.sentiment_label,
            MessageSentiment.confidence,
            MessageSentiment.political_tone,
            MessageSentiment.tone_confidence,
            MessageSentiment.emotions,
            MessageSentiment.analysis_method,
            MessageSentiment.analyzed_at
        ).join(Source, Message.source_id == Source.id)\
         .join(MessageSentiment, Message.id == MessageSentiment.message_id)\
         .outerjoin(Candidate, Message.candidate_id == Candidate.id)\
         .outerjoin(Constituency, Candidate.constituency_id == Constituency.id)
        
        # Apply filters
        if sentiment_filter:
            query = query.filter(MessageSentiment.sentiment_label == sentiment_filter)
        
        if tone_filter:
            query = query.filter(MessageSentiment.political_tone == tone_filter)
        
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
                'sentiment_score': float(msg.sentiment_score),
                'sentiment_label': msg.sentiment_label,
                'confidence': float(msg.confidence),
                'political_tone': msg.political_tone,
                'tone_confidence': float(msg.tone_confidence),
                'emotions': msg.emotions or {},
                'analysis_method': msg.analysis_method,
                'analyzed_at': msg.analyzed_at
            })
        
        df = pd.DataFrame(data)
        if not df.empty and 'published_at' in df.columns:
            df['published_at'] = pd.to_datetime(df['published_at'])
        
        return df
    
    def generate_dummy_sentiment_batch(self, db: Session, limit: int = 50) -> Dict:
        """
        Generate dummy sentiment data for testing dashboard functionality.
        
        Args:
            db: Database session
            limit: Number of messages to analyze
            
        Returns:
            Dictionary with operation results
        """
        try:
            analyzed_count = self.analyzer.analyze_batch_messages(
                db, 
                use_dummy=True, 
                limit=limit
            )
            
            return {
                "success": True,
                "analyzed_count": analyzed_count,
                "message": f"Successfully analyzed {analyzed_count} messages with dummy sentiment data"
            }
        except Exception as e:
            return {
                "success": False,
                "analyzed_count": 0,
                "message": f"Error generating sentiment data: {str(e)}"
            }
    
    def get_emotion_analysis_data(self, db: Session) -> Dict:
        """
        Get emotion analysis data for visualization.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with emotion analysis data
        """
        # Get all sentiment records with emotions
        sentiment_records = db.query(MessageSentiment.emotions).filter(
            MessageSentiment.emotions.isnot(None)
        ).all()
        
        if not sentiment_records:
            return {
                "emotion_totals": {},
                "emotion_averages": {},
                "total_records": 0
            }
        
        # Aggregate emotion data
        emotion_totals = {}
        emotion_counts = {}
        
        for (emotions,) in sentiment_records:
            if emotions:
                for emotion, score in emotions.items():
                    if emotion != 'neutral':  # Skip neutral entries
                        emotion_totals[emotion] = emotion_totals.get(emotion, 0) + score
                        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Calculate averages
        emotion_averages = {}
        for emotion, total in emotion_totals.items():
            count = emotion_counts[emotion]
            emotion_averages[emotion] = total / count if count > 0 else 0
        
        return {
            "emotion_totals": emotion_totals,
            "emotion_averages": emotion_averages,
            "emotion_counts": emotion_counts,
            "total_records": len(sentiment_records)
        }
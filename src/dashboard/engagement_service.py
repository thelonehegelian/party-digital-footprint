"""
Engagement analytics data service for Streamlit dashboard.

Provides data retrieval and processing functions for engagement analytics
visualizations in the dashboard, with built-in caching and error handling.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case

from ..models import Message, Source, Candidate, Constituency, EngagementMetrics
from ..analytics.engagement import PoliticalEngagementAnalyzer


class EngagementDashboardService:
    """
    Service class for engagement analytics data operations in Streamlit dashboard.
    
    Provides methods to:
    - Load engagement data with proper caching
    - Generate dummy engagement data for testing
    - Format data for Streamlit visualizations
    - Handle API-like data transformations
    """
    
    def __init__(self):
        """Initialize the engagement dashboard service."""
        self.analyzer = PoliticalEngagementAnalyzer()
    
    def get_engagement_overview(self, db: Session) -> Dict:
        """
        Get overall engagement statistics.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with engagement overview statistics
        """
        return self.analyzer.get_engagement_overview(db)
    
    def get_platform_performance_comparison(self, db: Session) -> Dict:
        """
        Get platform performance comparison data.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with platform comparison data
        """
        return self.analyzer.get_platform_performance_comparison(db)
    
    def get_viral_content_analysis(self, db: Session, threshold: float = 0.7) -> Dict:
        """
        Get viral content analysis.
        
        Args:
            db: Database session
            threshold: Virality score threshold
            
        Returns:
            Dictionary with viral content data
        """
        return self.analyzer.get_viral_content_analysis(db, threshold)
    
    def get_engagement_trends_over_time(self, db: Session, days: int = 30) -> Dict:
        """
        Get engagement trends over time for visualization.
        
        Args:
            db: Database session
            days: Number of days to analyze
            
        Returns:
            Dictionary with time-series engagement data
        """
        try:
            # Get engagement data over time
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Query engagement metrics grouped by date
            daily_engagement = db.query(
                func.date(EngagementMetrics.calculated_at).label('date'),
                func.avg(EngagementMetrics.engagement_score).label('avg_engagement'),
                func.avg(EngagementMetrics.virality_score).label('avg_virality'),
                func.avg(EngagementMetrics.influence_score).label('avg_influence'),
                func.count(EngagementMetrics.id).label('message_count')
            ).filter(
                EngagementMetrics.calculated_at >= start_date
            ).group_by(func.date(EngagementMetrics.calculated_at))\
             .order_by(func.date(EngagementMetrics.calculated_at))\
             .all()
            
            # Format data for visualization
            daily_data = {}
            for row in daily_engagement:
                date_str = row.date.strftime('%Y-%m-%d')
                daily_data[date_str] = {
                    'avg_engagement': float(row.avg_engagement or 0),
                    'avg_virality': float(row.avg_virality or 0),
                    'avg_influence': float(row.avg_influence or 0),
                    'message_count': row.message_count
                }
            
            return {
                "time_period_days": days,
                "daily_data": daily_data,
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception:
            # Handle empty database or missing tables
            return {
                "time_period_days": days,
                "daily_data": {},
                "analysis_date": datetime.now().isoformat()
            }
    
    def get_candidate_engagement_analysis(self, db: Session, limit: int = 15) -> pd.DataFrame:
        """
        Get engagement analysis grouped by candidate.
        
        Args:
            db: Database session
            limit: Maximum number of candidates to include
            
        Returns:
            DataFrame with candidate engagement data
        """
        try:
            # Get candidate engagement aggregations
            candidate_engagement = db.query(
                Candidate.name.label('candidate_name'),
                Constituency.name.label('constituency_name'),
                Constituency.region,
                func.count(EngagementMetrics.id).label('message_count'),
                func.avg(EngagementMetrics.engagement_score).label('avg_engagement'),
                func.avg(EngagementMetrics.virality_score).label('avg_virality'),
                func.avg(EngagementMetrics.influence_score).label('avg_influence'),
                func.max(EngagementMetrics.engagement_score).label('max_engagement'),
                func.sum(case((EngagementMetrics.virality_score > 0.7, 1), else_=0)).label('viral_content')
            ).join(Message, Candidate.id == Message.candidate_id)\
             .join(EngagementMetrics, Message.id == EngagementMetrics.message_id)\
             .join(Constituency, Candidate.constituency_id == Constituency.id)\
             .group_by(Candidate.name, Constituency.name, Constituency.region)\
             .having(func.count(EngagementMetrics.id) > 0)\
             .order_by(func.avg(EngagementMetrics.engagement_score).desc())\
             .limit(limit)\
             .all()
            
            if not candidate_engagement:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for row in candidate_engagement:
                data.append({
                    'candidate_name': row.candidate_name,
                    'constituency_name': row.constituency_name,
                    'region': row.region,
                    'message_count': row.message_count,
                    'avg_engagement': float(row.avg_engagement or 0),
                    'avg_virality': float(row.avg_virality or 0),
                    'avg_influence': float(row.avg_influence or 0),
                    'max_engagement': float(row.max_engagement or 0),
                    'viral_content': row.viral_content or 0
                })
            
            return pd.DataFrame(data)
            
        except Exception:
            # Handle database errors
            return pd.DataFrame()
    
    def get_top_performing_messages(self, db: Session, metric: str = "engagement", limit: int = 20) -> pd.DataFrame:
        """
        Get top performing messages by engagement metric.
        
        Args:
            db: Database session
            metric: Metric to sort by ('engagement', 'virality', 'influence')
            limit: Number of messages to return
            
        Returns:
            DataFrame with top performing messages
        """
        try:
            # Map metric names to database columns
            metric_mapping = {
                'engagement': EngagementMetrics.engagement_score,
                'virality': EngagementMetrics.virality_score,
                'influence': EngagementMetrics.influence_score
            }
            
            sort_column = metric_mapping.get(metric, EngagementMetrics.engagement_score)
            
            # Query top performing messages
            top_messages = db.query(
                Message.id,
                Message.content,
                Message.url,
                Message.published_at,
                Source.name.label('source_name'),
                Source.source_type,
                Candidate.name.label('candidate_name'),
                Constituency.name.label('constituency_name'),
                Constituency.region,
                EngagementMetrics.engagement_score,
                EngagementMetrics.virality_score,
                EngagementMetrics.influence_score,
                EngagementMetrics.platform_metrics,
                EngagementMetrics.reach_metrics,
                EngagementMetrics.platform_percentile,
                EngagementMetrics.candidate_percentile
            ).join(EngagementMetrics, Message.id == EngagementMetrics.message_id)\
             .join(Source, Message.source_id == Source.id)\
             .outerjoin(Candidate, Message.candidate_id == Candidate.id)\
             .outerjoin(Constituency, Candidate.constituency_id == Constituency.id)\
             .order_by(desc(sort_column))\
             .limit(limit)\
             .all()
            
            if not top_messages:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for msg in top_messages:
                data.append({
                    'id': msg.id,
                    'content': msg.content,
                    'content_preview': msg.content[:150] + "..." if len(msg.content) > 150 else msg.content,
                    'url': msg.url,
                    'published_at': msg.published_at,
                    'source_name': msg.source_name,
                    'source_type': msg.source_type,
                    'candidate_name': msg.candidate_name or 'Unknown',
                    'constituency_name': msg.constituency_name,
                    'region': msg.region,
                    'engagement_score': float(msg.engagement_score),
                    'virality_score': float(msg.virality_score),
                    'influence_score': float(msg.influence_score),
                    'platform_metrics': msg.platform_metrics or {},
                    'reach_metrics': msg.reach_metrics or {},
                    'platform_percentile': float(msg.platform_percentile or 0),
                    'candidate_percentile': float(msg.candidate_percentile or 0)
                })
            
            df = pd.DataFrame(data)
            if not df.empty and 'published_at' in df.columns:
                df['published_at'] = pd.to_datetime(df['published_at'])
            
            return df
            
        except Exception:
            # Handle database errors
            return pd.DataFrame()
    
    def get_engagement_distribution_data(self, db: Session) -> Dict:
        """
        Get engagement score distribution for histograms.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with engagement distribution data
        """
        try:
            # Get engagement score distribution
            engagement_scores = db.query(
                EngagementMetrics.engagement_score,
                EngagementMetrics.virality_score,
                EngagementMetrics.influence_score
            ).all()
            
            if not engagement_scores:
                return {
                    "engagement_scores": [],
                    "virality_scores": [],
                    "influence_scores": [],
                    "total_analyzed": 0
                }
            
            return {
                "engagement_scores": [float(score.engagement_score) for score in engagement_scores],
                "virality_scores": [float(score.virality_score) for score in engagement_scores],
                "influence_scores": [float(score.influence_score) for score in engagement_scores],
                "total_analyzed": len(engagement_scores)
            }
            
        except Exception:
            # Handle database errors
            return {
                "engagement_scores": [],
                "virality_scores": [],
                "influence_scores": [],
                "total_analyzed": 0
            }
    
    def generate_dummy_engagement_batch(self, db: Session, limit: int = 50) -> Dict:
        """
        Generate dummy engagement data for testing dashboard functionality.
        
        Args:
            db: Database session
            limit: Number of messages to analyze
            
        Returns:
            Dictionary with operation results
        """
        try:
            analyzed_count = self.analyzer.analyze_engagement_in_messages(
                db, 
                use_dummy=True, 
                limit=limit
            )
            
            return {
                "success": True,
                "analyzed_count": analyzed_count,
                "message": f"Successfully analyzed {analyzed_count} messages with dummy engagement data"
            }
        except Exception as e:
            return {
                "success": False,
                "analyzed_count": 0,
                "message": f"Error generating engagement data: {str(e)}"
            }
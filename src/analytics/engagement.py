"""
Political engagement analytics system.

Provides engagement metrics calculation, virality analysis, and comparative
performance assessment for political messaging.
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from ..models import Message, EngagementMetrics, Source, Candidate, Constituency


class PoliticalEngagementAnalyzer:
    """
    Analyzes engagement metrics for political messages.
    
    Provides:
    - Engagement score calculation based on platform metrics
    - Virality prediction and influence scoring
    - Comparative performance analysis
    - Audience quality assessment
    - Time-based engagement patterns
    """
    
    def __init__(self):
        """Initialize the engagement analyzer."""
        self.platform_weights = {
            'twitter': {'likes': 0.3, 'retweets': 0.4, 'replies': 0.3},
            'facebook': {'likes': 0.25, 'shares': 0.4, 'comments': 0.35},
            'website': {'views': 0.6, 'time_on_page': 0.4},
            'meta_ads': {'clicks': 0.4, 'impressions': 0.2, 'ctr': 0.4}
        }
    
    def calculate_engagement_score(self, platform_metrics: Dict, source_type: str) -> float:
        """
        Calculate normalized engagement score (0.0 to 1.0).
        
        Args:
            platform_metrics: Raw platform engagement data
            source_type: Platform type (twitter, facebook, etc.)
            
        Returns:
            Engagement score between 0.0 and 1.0
        """
        if not platform_metrics or source_type not in self.platform_weights:
            return 0.0
        
        weights = self.platform_weights[source_type]
        weighted_score = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if metric in platform_metrics:
                # Normalize using log scale for high numbers
                raw_value = platform_metrics[metric]
                if raw_value > 0:
                    normalized = min(1.0, math.log10(raw_value + 1) / 4.0)  # Scale to 0-1
                    weighted_score += normalized * weight
                    total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def calculate_virality_score(self, platform_metrics: Dict, time_since_publish: timedelta) -> float:
        """
        Calculate virality potential based on engagement velocity.
        
        Args:
            platform_metrics: Raw engagement data
            time_since_publish: Time elapsed since publication
            
        Returns:
            Virality score between 0.0 and 1.0
        """
        if time_since_publish.total_seconds() <= 0:
            return 0.0
        
        # Calculate engagement rate per hour
        hours_elapsed = max(1, time_since_publish.total_seconds() / 3600)
        
        total_engagement = 0
        viral_actions = 0  # Shares, retweets, etc.
        
        for metric, value in platform_metrics.items():
            if metric in ['retweets', 'shares', 'reposts']:
                viral_actions += value
            total_engagement += value
        
        # Virality favors shares/retweets over likes
        viral_ratio = viral_actions / max(1, total_engagement)
        engagement_velocity = total_engagement / hours_elapsed
        
        # Combine velocity and viral ratio
        virality_raw = (engagement_velocity * viral_ratio) ** 0.5
        return min(1.0, virality_raw / 10.0)  # Normalize to 0-1
    
    def calculate_influence_score(self, engagement_score: float, reach_metrics: Dict) -> float:
        """
        Calculate message influence based on reach and engagement quality.
        
        Args:
            engagement_score: Calculated engagement score
            reach_metrics: Reach and impression data
            
        Returns:
            Influence score between 0.0 and 1.0
        """
        estimated_reach = reach_metrics.get('estimated_reach', 0)
        impressions = reach_metrics.get('impressions', 0)
        
        # Use the higher of reach or impressions
        reach = max(estimated_reach, impressions)
        
        if reach <= 0:
            return engagement_score * 0.5  # Lower influence without reach data
        
        # Influence combines engagement quality with reach
        reach_factor = min(1.0, math.log10(reach + 1) / 6.0)  # Normalize reach
        return (engagement_score * 0.7) + (reach_factor * 0.3)
    
    def generate_dummy_engagement_data(self, message: Message) -> Dict:
        """
        Generate realistic dummy engagement data for testing.
        
        Args:
            message: Message to generate engagement for
            
        Returns:
            Dictionary with platform metrics, reach data, and quality scores
        """
        source_type = message.source.source_type
        
        # Base engagement influenced by content length and type
        content_words = len(message.content.split())
        base_multiplier = max(0.5, min(2.0, math.log10(content_words + 1)))
        
        # Platform-specific dummy data
        if source_type == 'twitter':
            likes = random.randint(5, 500) * base_multiplier
            retweets = random.randint(1, int(likes * 0.3))
            replies = random.randint(0, int(likes * 0.2))
            
            platform_metrics = {
                'likes': int(likes),
                'retweets': int(retweets),
                'replies': int(replies)
            }
            
            reach_metrics = {
                'estimated_reach': int(likes * random.uniform(3, 8)),
                'impressions': int(likes * random.uniform(5, 15))
            }
            
        elif source_type == 'facebook':
            likes = random.randint(10, 800) * base_multiplier
            shares = random.randint(1, int(likes * 0.25))
            comments = random.randint(0, int(likes * 0.15))
            
            platform_metrics = {
                'likes': int(likes),
                'shares': int(shares),
                'comments': int(comments)
            }
            
            reach_metrics = {
                'estimated_reach': int(likes * random.uniform(4, 12)),
                'impressions': int(likes * random.uniform(6, 20))
            }
            
        elif source_type == 'website':
            views = random.randint(50, 2000) * base_multiplier
            time_on_page = random.uniform(30, 300)  # seconds
            
            platform_metrics = {
                'views': int(views),
                'time_on_page': time_on_page,
                'bounce_rate': random.uniform(0.3, 0.8)
            }
            
            reach_metrics = {
                'estimated_reach': int(views * random.uniform(0.8, 1.2)),
                'impressions': int(views)
            }
            
        elif source_type == 'meta_ads':
            impressions = random.randint(1000, 50000) * base_multiplier
            clicks = random.randint(10, int(impressions * 0.05))
            ctr = clicks / impressions if impressions > 0 else 0
            
            platform_metrics = {
                'impressions': int(impressions),
                'clicks': int(clicks),
                'ctr': ctr,
                'spend': random.uniform(10, 500)
            }
            
            reach_metrics = {
                'estimated_reach': int(impressions * random.uniform(0.6, 0.9)),
                'impressions': int(impressions)
            }
            
        else:
            # Default generic engagement
            platform_metrics = {
                'interactions': random.randint(5, 200) * base_multiplier
            }
            reach_metrics = {
                'estimated_reach': random.randint(100, 1000) * base_multiplier
            }
        
        # Generate quality metrics
        interaction_quality = random.uniform(0.3, 0.9)
        audience_relevance = random.uniform(0.4, 0.95)
        
        return {
            'platform_metrics': platform_metrics,
            'reach_metrics': reach_metrics,
            'interaction_quality': interaction_quality,
            'audience_relevance': audience_relevance
        }
    
    def analyze_message_engagement(
        self, 
        db: Session, 
        message: Message, 
        use_dummy: bool = False
    ) -> EngagementMetrics:
        """
        Analyze engagement for a single message.
        
        Args:
            db: Database session
            message: Message to analyze
            use_dummy: Whether to generate dummy data for testing
            
        Returns:
            EngagementMetrics object
        """
        # Check if engagement already exists
        existing = db.query(EngagementMetrics).filter_by(message_id=message.id).first()
        if existing:
            return existing
        
        if use_dummy:
            # Generate dummy engagement data
            dummy_data = self.generate_dummy_engagement_data(message)
            platform_metrics = dummy_data['platform_metrics']
            reach_metrics = dummy_data['reach_metrics']
            interaction_quality = dummy_data['interaction_quality']
            audience_relevance = dummy_data['audience_relevance']
            
        else:
            # Use real data from message metadata
            metadata = message.message_metadata or {}
            platform_metrics = metadata.get('engagement_stats', {})
            reach_metrics = metadata.get('reach_stats', {})
            interaction_quality = metadata.get('interaction_quality', 0.5)
            audience_relevance = metadata.get('audience_relevance', 0.5)
        
        # Calculate core scores
        engagement_score = self.calculate_engagement_score(
            platform_metrics, message.source.source_type
        )
        
        time_since_publish = datetime.utcnow() - (message.published_at or message.scraped_at)
        virality_score = self.calculate_virality_score(platform_metrics, time_since_publish)
        influence_score = self.calculate_influence_score(engagement_score, reach_metrics)
        
        # Calculate comparative percentiles (simplified for dummy data)
        platform_percentile = min(95, engagement_score * 100 + random.uniform(-10, 10))
        candidate_percentile = min(95, engagement_score * 100 + random.uniform(-15, 15))
        
        # Calculate engagement velocity (engagement per hour)
        engagement_velocity = sum(platform_metrics.values()) / max(1, time_since_publish.total_seconds() / 3600)
        
        # Peak engagement time (simulate)
        peak_hours_after = random.uniform(0.5, 24)
        peak_engagement_time = (message.published_at or message.scraped_at) + timedelta(hours=peak_hours_after)
        
        # Create engagement metrics
        engagement_metrics = EngagementMetrics(
            message_id=message.id,
            engagement_score=engagement_score,
            virality_score=virality_score,
            influence_score=influence_score,
            platform_metrics=platform_metrics,
            reach_metrics=reach_metrics,
            interaction_quality=interaction_quality,
            audience_relevance=audience_relevance,
            platform_percentile=max(0, min(100, platform_percentile)),
            candidate_percentile=max(0, min(100, candidate_percentile)),
            engagement_velocity=engagement_velocity,
            peak_engagement_time=peak_engagement_time,
            calculation_method="dummy_generator" if use_dummy else "real_data"
        )
        
        db.add(engagement_metrics)
        db.commit()
        
        return engagement_metrics
    
    def analyze_engagement_in_messages(
        self, 
        db: Session, 
        use_dummy: bool = True, 
        limit: Optional[int] = None
    ) -> int:
        """
        Analyze engagement for multiple messages.
        
        Args:
            db: Database session
            use_dummy: Whether to generate dummy data
            limit: Maximum number of messages to analyze
            
        Returns:
            Number of messages analyzed
        """
        # Get messages without engagement analysis
        query = db.query(Message).outerjoin(EngagementMetrics)\
                  .filter(EngagementMetrics.id.is_(None))
        
        if limit:
            query = query.limit(limit)
        
        messages = query.all()
        
        analyzed_count = 0
        for message in messages:
            try:
                self.analyze_message_engagement(db, message, use_dummy=use_dummy)
                analyzed_count += 1
            except Exception as e:
                print(f"Error analyzing engagement for message {message.id}: {e}")
                continue
        
        return analyzed_count
    
    def get_engagement_overview(self, db: Session) -> Dict:
        """
        Get overall engagement statistics.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with engagement overview data
        """
        try:
            total_messages = db.query(Message).count()
            analyzed_messages = db.query(EngagementMetrics).count()
        except Exception:
            # Handle empty database or missing tables
            total_messages = 0
            analyzed_messages = 0
        
        if analyzed_messages == 0:
            return {
                "total_messages": total_messages,
                "analyzed_messages": 0,
                "coverage": 0.0,
                "needs_analysis": True,
                "avg_engagement": 0.0,
                "avg_virality": 0.0,
                "avg_influence": 0.0,
                "top_performing": []
            }
        
        # Calculate averages
        engagement_stats = db.query(
            func.avg(EngagementMetrics.engagement_score).label('avg_engagement'),
            func.avg(EngagementMetrics.virality_score).label('avg_virality'),
            func.avg(EngagementMetrics.influence_score).label('avg_influence')
        ).first()
        
        # Get top performing messages
        top_performing = db.query(EngagementMetrics, Message.content)\
                          .join(Message)\
                          .order_by(desc(EngagementMetrics.engagement_score))\
                          .limit(5)\
                          .all()
        
        top_messages = []
        for metrics, content in top_performing:
            top_messages.append({
                "message_id": metrics.message_id,
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
                "engagement_score": float(metrics.engagement_score),
                "virality_score": float(metrics.virality_score)
            })
        
        return {
            "total_messages": total_messages,
            "analyzed_messages": analyzed_messages,
            "coverage": (analyzed_messages / total_messages * 100) if total_messages > 0 else 0,
            "needs_analysis": analyzed_messages < total_messages * 0.1,  # Need analysis if <10% covered
            "avg_engagement": float(engagement_stats.avg_engagement or 0),
            "avg_virality": float(engagement_stats.avg_virality or 0),
            "avg_influence": float(engagement_stats.avg_influence or 0),
            "top_performing": top_messages
        }
    
    def get_platform_performance_comparison(self, db: Session) -> Dict:
        """
        Compare engagement performance across platforms.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with platform comparison data
        """
        try:
            platform_stats = db.query(
                Source.source_type,
                func.count(EngagementMetrics.id).label('message_count'),
                func.avg(EngagementMetrics.engagement_score).label('avg_engagement'),
                func.avg(EngagementMetrics.virality_score).label('avg_virality'),
                func.avg(EngagementMetrics.influence_score).label('avg_influence')
            ).join(Message, Source.id == Message.source_id)\
             .join(EngagementMetrics, Message.id == EngagementMetrics.message_id)\
             .group_by(Source.source_type)\
             .all()
        except Exception:
            # Handle empty database or missing tables
            platform_stats = []
        
        platform_data = []
        for stats in platform_stats:
            platform_data.append({
                "platform": stats.source_type,
                "message_count": stats.message_count,
                "avg_engagement": float(stats.avg_engagement or 0),
                "avg_virality": float(stats.avg_virality or 0),
                "avg_influence": float(stats.avg_influence or 0)
            })
        
        return {
            "platform_comparison": platform_data,
            "total_platforms": len(platform_data)
        }
    
    def get_viral_content_analysis(self, db: Session, threshold: float = 0.7) -> Dict:
        """
        Identify and analyze viral content.
        
        Args:
            db: Database session
            threshold: Virality score threshold for viral content
            
        Returns:
            Dictionary with viral content analysis
        """
        try:
            viral_messages = db.query(EngagementMetrics, Message, Candidate)\
                              .join(Message, EngagementMetrics.message_id == Message.id)\
                              .outerjoin(Candidate, Message.candidate_id == Candidate.id)\
                              .filter(EngagementMetrics.virality_score >= threshold)\
                              .order_by(desc(EngagementMetrics.virality_score))\
                              .limit(20)\
                              .all()
        except Exception:
            # Handle empty database or missing tables
            viral_messages = []
        
        viral_content = []
        for metrics, message, candidate in viral_messages:
            viral_content.append({
                "message_id": message.id,
                "content_preview": message.content[:150] + "..." if len(message.content) > 150 else message.content,
                "candidate_name": candidate.name if candidate else "Unknown",
                "virality_score": float(metrics.virality_score),
                "engagement_score": float(metrics.engagement_score),
                "platform_metrics": metrics.platform_metrics,
                "published_at": message.published_at.isoformat() if message.published_at else None
            })
        
        return {
            "viral_threshold": threshold,
            "viral_messages_found": len(viral_content),
            "viral_content": viral_content
        }
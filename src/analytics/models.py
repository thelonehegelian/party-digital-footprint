"""
Analytics data models for political messaging analysis.

This module defines SQLAlchemy models for storing analytics results including
sentiment analysis, topic modeling, engagement metrics, and intelligence insights.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, Index, JSON, ARRAY
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from ..models import Base


class MessageSentiment(Base):
    """Sentiment analysis results for messages."""
    __tablename__ = "message_sentiment"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    
    # Basic sentiment metrics
    sentiment_score = Column(Float, nullable=False)  # -1.0 to 1.0
    sentiment_label = Column(String(20), nullable=False)  # positive/negative/neutral
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Political tone analysis
    political_tone = Column(String(50))  # aggressive/diplomatic/populist/etc
    tone_confidence = Column(Float)
    
    # Emotional categories (stored as JSON)
    emotions = Column(JSON)  # {anger: 0.3, hope: 0.7, fear: 0.1, etc}
    
    # Analysis metadata
    analysis_method = Column(String(50), default="transformers")  # model used
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("Message", back_populates="sentiment_analysis")


class TopicModel(Base):
    """Topic modeling results and trending topics."""
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True)
    topic_name = Column(String(200), nullable=False)
    topic_number = Column(Integer)  # LDA topic number
    
    # Topic characteristics
    keywords = Column(JSON, nullable=False)  # [{"word": "immigration", "weight": 0.4}, ...]
    description = Column(Text)  # Human-readable topic description
    
    # Topic metrics
    coherence_score = Column(Float)  # Topic coherence metric
    message_count = Column(Integer, default=0)  # Messages assigned to this topic
    avg_sentiment = Column(Float)  # Average sentiment for topic
    
    # Trending analysis
    trend_score = Column(Float, default=0.0)  # Trending strength
    growth_rate = Column(Float, default=0.0)  # Rate of growth
    
    # Time tracking
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Analysis metadata
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message_assignments = relationship("MessageTopic", back_populates="topic")


class MessageTopic(Base):
    """Many-to-many relationship between messages and topics."""
    __tablename__ = "message_topics"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    
    # Assignment strength
    probability = Column(Float, nullable=False)  # 0.0 to 1.0
    is_primary_topic = Column(Boolean, default=False)  # Main topic for message
    
    # Assignment metadata
    assigned_at = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String(50))
    
    # Relationships
    message = relationship("Message")
    topic = relationship("TopicModel", back_populates="message_assignments")


class EngagementMetrics(Base):
    """Message engagement and virality analysis."""
    __tablename__ = "engagement_metrics"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    
    # Core engagement metrics
    engagement_score = Column(Float, nullable=False)  # 0.0 to 1.0 normalized score
    virality_score = Column(Float, default=0.0)  # Predicted viral potential
    influence_score = Column(Float, default=0.0)  # Message influence metric
    
    # Platform-specific metrics (stored as JSON)
    platform_metrics = Column(JSON)  # {likes: 100, shares: 50, comments: 25, etc}
    reach_metrics = Column(JSON)  # {estimated_reach: 5000, impressions: 8000, etc}
    
    # Engagement quality analysis
    interaction_quality = Column(Float)  # Quality of comments/replies
    audience_relevance = Column(Float)  # How relevant to target audience
    
    # Comparative metrics
    platform_percentile = Column(Float)  # Performance vs other platform messages
    candidate_percentile = Column(Float)  # Performance vs candidate's other messages
    
    # Time-based metrics
    engagement_velocity = Column(Float)  # Speed of initial engagement
    peak_engagement_time = Column(DateTime)  # When engagement peaked
    
    # Analysis metadata
    calculated_at = Column(DateTime, default=datetime.utcnow)
    calculation_method = Column(String(50))
    
    # Relationships
    message = relationship("Message", back_populates="engagement_metrics")


class TrendingAlert(Base):
    """Alerts for trending topics and unusual patterns."""
    __tablename__ = "trending_alerts"
    
    id = Column(Integer, primary_key=True)
    alert_type = Column(String(50), nullable=False)  # topic_trending/sentiment_shift/viral_content
    
    # Alert details
    title = Column(String(200), nullable=False)
    description = Column(Text)
    severity = Column(String(20), default="medium")  # low/medium/high/critical
    
    # Related entities
    topic_id = Column(Integer, ForeignKey("topics.id"))
    message_id = Column(Integer, ForeignKey("messages.id"))
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    
    # Alert metrics
    confidence = Column(Float)  # Alert confidence score
    impact_score = Column(Float)  # Estimated impact
    
    # Alert metadata
    triggered_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    status = Column(String(20), default="active")  # active/acknowledged/resolved
    
    # Relationships
    topic = relationship("TopicModel")
    message = relationship("Message")
    candidate = relationship("Candidate")


class AnalyticsCache(Base):
    """Cache for expensive analytics computations."""
    __tablename__ = "analytics_cache"
    
    id = Column(Integer, primary_key=True)
    cache_key = Column(String(200), nullable=False, unique=True)
    cache_type = Column(String(50), nullable=False)  # sentiment_trends/topic_analysis/etc
    
    # Cached data
    data = Column(JSON, nullable=False)  # Cached result
    
    # Cache metadata
    parameters = Column(JSON)  # Parameters used to generate cache
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    hit_count = Column(Integer, default=0)
    
    # Data freshness
    data_version = Column(String(50))  # Version of underlying data
    is_valid = Column(Boolean, default=True)


# Indexes for performance
Index('idx_message_sentiment_message_id', MessageSentiment.message_id)
Index('idx_message_sentiment_label', MessageSentiment.sentiment_label)
Index('idx_message_sentiment_analyzed_at', MessageSentiment.analyzed_at)

Index('idx_topics_trend_score', TopicModel.trend_score.desc())
Index('idx_topics_message_count', TopicModel.message_count.desc())
Index('idx_topics_last_updated', TopicModel.last_updated)

Index('idx_message_topics_message_id', MessageTopic.message_id)
Index('idx_message_topics_topic_id', MessageTopic.topic_id)
Index('idx_message_topics_probability', MessageTopic.probability.desc())

Index('idx_engagement_score', EngagementMetrics.engagement_score.desc())
Index('idx_engagement_virality', EngagementMetrics.virality_score.desc())
Index('idx_engagement_calculated_at', EngagementMetrics.calculated_at)

Index('idx_alerts_type_status', TrendingAlert.alert_type, TrendingAlert.status)
Index('idx_alerts_triggered_at', TrendingAlert.triggered_at)
Index('idx_alerts_severity', TrendingAlert.severity)

Index('idx_cache_key', AnalyticsCache.cache_key)
Index('idx_cache_type_valid', AnalyticsCache.cache_type, AnalyticsCache.is_valid)
Index('idx_cache_expires_at', AnalyticsCache.expires_at)


# Pydantic models for API responses
class SentimentResult(BaseModel):
    """Sentiment analysis result."""
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str = Field(..., pattern="^(positive|negative|neutral)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    political_tone: Optional[str] = None
    tone_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    emotions: Optional[Dict[str, float]] = None
    analysis_method: str = "transformers"
    
    class Config:
        from_attributes = True


class TopicResult(BaseModel):
    """Topic modeling result."""
    topic_name: str
    topic_number: Optional[int] = None
    keywords: List[Dict[str, float]]  # [{"word": "immigration", "weight": 0.4}]
    description: Optional[str] = None
    coherence_score: Optional[float] = None
    message_count: int = 0
    avg_sentiment: Optional[float] = None
    trend_score: float = 0.0
    
    class Config:
        from_attributes = True


class EngagementResult(BaseModel):
    """Engagement analysis result."""
    engagement_score: float = Field(..., ge=0.0, le=1.0)
    virality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    influence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    platform_metrics: Optional[Dict[str, Any]] = None
    reach_metrics: Optional[Dict[str, Any]] = None
    interaction_quality: Optional[float] = Field(None, ge=0.0, le=1.0)
    platform_percentile: Optional[float] = Field(None, ge=0.0, le=100.0)
    
    class Config:
        from_attributes = True


class TrendingTopicResult(BaseModel):
    """Trending topic result."""
    topic_name: str
    keywords: List[str]
    message_count: int
    trend_score: float
    growth_rate: float
    avg_sentiment: Optional[float] = None
    time_period: str
    
    class Config:
        from_attributes = True


class AlertResult(BaseModel):
    """Alert result."""
    alert_type: str
    title: str
    description: str
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    impact_score: Optional[float] = None
    triggered_at: datetime
    status: str = Field(default="active", pattern="^(active|acknowledged|resolved)$")
    
    class Config:
        from_attributes = True
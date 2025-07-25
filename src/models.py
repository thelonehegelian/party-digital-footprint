from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, Index, JSON, ARRAY
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

Base = declarative_base()


class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    url = Column(Text)
    source_type = Column(String(50))  # 'website', 'twitter', 'facebook', 'meta_ads'
    last_scraped = Column(DateTime)
    active = Column(Boolean, default=True)
    
    messages = relationship("Message", back_populates="source")


class Constituency(Base):
    __tablename__ = "constituencies"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    region = Column(String(100))
    constituency_type = Column(String(50))  # 'county', 'district', 'unitary'
    
    candidates = relationship("Candidate", back_populates="constituency")


class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    constituency_id = Column(Integer, ForeignKey("constituencies.id"))
    social_media_accounts = Column(JSON)  # {twitter: @handle, facebook: url}
    candidate_type = Column(String(50), default='local')  # 'national', 'local', 'both'
    
    constituency = relationship("Constituency", back_populates="candidates")
    messages = relationship("Message", back_populates="candidate")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    content = Column(Text, nullable=False)
    url = Column(Text)
    published_at = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    message_type = Column(String(50))  # 'post', 'article', 'press_release', 'ad'
    geographic_scope = Column(String(50))  # 'national', 'regional', 'local'
    message_metadata = Column(JSON)  # hashtags, media_urls, engagement_stats
    raw_data = Column(JSON)  # store original API response
    
    source = relationship("Source", back_populates="messages")
    candidate = relationship("Candidate", back_populates="messages")
    keywords = relationship("Keyword", back_populates="message")
    
    # Analytics relationships - using string references to avoid circular imports
    sentiment_analysis = relationship("MessageSentiment", back_populates="message", uselist=False)
    engagement_metrics = relationship("EngagementMetrics", back_populates="message", uselist=False)


class Keyword(Base):
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    keyword = Column(String(100))
    confidence = Column(Float, default=1.0)
    extraction_method = Column(String(50))  # 'manual', 'nltk', 'spacy', 'regex'
    
    message = relationship("Message", back_populates="keywords")


# Indexes
Index('idx_messages_published_at', Message.published_at)
Index('idx_messages_source_id', Message.source_id)
Index('idx_keywords_keyword', Keyword.keyword)


# Pydantic models for API
class SourceCreate(BaseModel):
    name: str
    url: Optional[str] = None
    source_type: str
    active: bool = True


class SourceResponse(BaseModel):
    id: int
    name: str
    url: Optional[str]
    source_type: str
    last_scraped: Optional[datetime]
    active: bool
    
    class Config:
        from_attributes = True


class ConstituencyCreate(BaseModel):
    name: str
    region: Optional[str] = None
    constituency_type: Optional[str] = None


class ConstituencyResponse(BaseModel):
    id: int
    name: str
    region: Optional[str]
    constituency_type: Optional[str]
    
    class Config:
        from_attributes = True


class CandidateCreate(BaseModel):
    name: str
    constituency_id: int
    social_media_accounts: Optional[Dict[str, str]] = None
    candidate_type: str = 'local'


class CandidateResponse(BaseModel):
    id: int
    name: str
    constituency_id: int
    social_media_accounts: Optional[Dict[str, str]]
    candidate_type: str
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    source_id: int
    candidate_id: Optional[int] = None
    content: str
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    message_type: Optional[str] = None
    geographic_scope: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    id: int
    source_id: int
    candidate_id: Optional[int]
    content: str
    url: Optional[str]
    published_at: Optional[datetime]
    scraped_at: datetime
    message_type: Optional[str]
    geographic_scope: Optional[str]
    message_metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class KeywordCreate(BaseModel):
    message_id: int
    keyword: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    extraction_method: str


class KeywordResponse(BaseModel):
    id: int
    message_id: int
    keyword: str
    confidence: float
    extraction_method: str
    
    class Config:
        from_attributes = True


# ===== ANALYTICS MODELS =====

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


# Additional indexes for analytics performance
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


# ===== ANALYTICS PYDANTIC MODELS =====

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
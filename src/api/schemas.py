from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field, validator


class MessageMetadata(BaseModel):
    """Base metadata structure that can be extended per source type."""
    pass


class TwitterMetadata(MessageMetadata):
    """Twitter-specific metadata."""
    hashtags: Optional[List[str]] = []
    mentions: Optional[List[str]] = []
    urls: Optional[List[str]] = []
    media_urls: Optional[List[str]] = []
    metrics: Optional[Dict[str, int]] = {}
    tweet_type: Optional[str] = None
    context_annotations: Optional[List[Dict[str, str]]] = []


class FacebookMetadata(MessageMetadata):
    """Facebook-specific metadata."""
    post_type: Optional[str] = None
    engagement: Optional[Dict[str, int]] = {}
    link: Optional[Dict[str, str]] = {}
    media: Optional[Dict[str, str]] = {}
    place: Optional[Dict[str, Any]] = {}


class WebsiteMetadata(MessageMetadata):
    """Website-specific metadata."""
    title: Optional[str] = None
    author: Optional[str] = None
    word_count: Optional[int] = None
    url_path: Optional[str] = None
    tags: Optional[List[str]] = []
    category: Optional[str] = None


class MetaAdsMetadata(MessageMetadata):
    """Meta Ads Library-specific metadata."""
    page_name: Optional[str] = None
    funding_entity: Optional[str] = None
    currency: Optional[str] = None
    publisher_platforms: Optional[List[str]] = []
    estimated_audience_size: Optional[Dict[str, int]] = {}
    delivery_dates: Optional[Dict[str, str]] = {}
    spend: Optional[Dict[str, int]] = {}
    impressions: Optional[Dict[str, int]] = {}
    demographics: Optional[Dict[str, List[str]]] = {}
    delivery_regions: Optional[List[str]] = []


class MessageInput(BaseModel):
    """Input schema for message submission."""
    source_type: Literal["website", "twitter", "facebook", "meta_ads"] = Field(
        description="Type of source platform"
    )
    source_name: str = Field(description="Human-readable source name")
    source_url: Optional[str] = Field(None, description="Base URL of the source")
    content: str = Field(
        min_length=1, 
        max_length=10000,
        description="Main message content"
    )
    url: Optional[str] = Field(None, description="Direct URL to the content")
    published_at: Optional[datetime] = Field(None, description="When content was published")
    message_type: Optional[str] = Field(None, description="Type categorization")
    candidate_id: Optional[int] = Field(None, description="ID of associated candidate (Phase 2)")
    geographic_scope: Optional[Literal["national", "regional", "local"]] = Field(None, description="Geographic scope of message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Source-specific metadata")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Original API response")

    @validator('content')
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()


class BulkMessageInput(BaseModel):
    """Input schema for bulk message submission."""
    messages: List[MessageInput] = Field(
        max_items=100,
        description="List of messages to import"
    )


class MessageResponse(BaseModel):
    """Response schema for single message submission."""
    status: Literal["success", "error", "warning"]
    message_id: Optional[int] = None
    keywords_extracted: Optional[int] = None
    error_code: Optional[str] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class BulkMessageResponse(BaseModel):
    """Response schema for bulk message submission."""
    status: Literal["success", "error", "partial"]
    imported_count: int
    skipped_count: int
    errors: List[Dict[str, Any]]
    total_keywords_extracted: int


class ErrorResponse(BaseModel):
    """Standard error response."""
    status: Literal["error"]
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None


# Data transformation schemas for scrapers
class ScrapedMessage(BaseModel):
    """Standardized format for scraped data before API submission."""
    source_type: str
    content: str
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    message_type: Optional[str] = None
    candidate_id: Optional[int] = None
    geographic_scope: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None

    def to_api_format(self, source_name: str, source_url: Optional[str] = None) -> MessageInput:
        """Convert to API submission format."""
        return MessageInput(
            source_type=self.source_type,
            source_name=source_name,
            source_url=source_url,
            content=self.content,
            url=self.url,
            published_at=self.published_at,
            message_type=self.message_type,
            candidate_id=self.candidate_id,
            geographic_scope=self.geographic_scope,
            metadata=self.metadata,
            raw_data=self.raw_data
        )


# Analytics schemas
class SentimentAnalysisRequest(BaseModel):
    """Request schema for sentiment analysis."""
    message_id: Optional[int] = Field(None, description="ID of message to analyze")
    content: Optional[str] = Field(None, description="Content to analyze directly")
    
    @validator('content')
    def validate_input(cls, v, values):
        if not values.get('message_id') and not v:
            raise ValueError('Either message_id or content must be provided')
        return v
    
    class Config:
        validate_assignment = True


class SentimentAnalysisResponse(BaseModel):
    """Response schema for sentiment analysis."""
    message_id: Optional[int] = None
    content_preview: str
    sentiment_score: float = Field(description="Sentiment score from -1 (negative) to 1 (positive)")
    sentiment_label: str = Field(description="Sentiment classification: positive, negative, or neutral")
    confidence: float = Field(description="Confidence score from 0 to 1")
    political_tone: str = Field(description="Political tone: aggressive, diplomatic, populist, or nationalist")
    tone_confidence: float = Field(description="Political tone confidence from 0 to 1")
    emotions: Dict[str, float] = Field(description="Emotional content scores")
    analysis_method: str = Field(description="Method used for analysis")
    analyzed_at: datetime


class SentimentTrendsResponse(BaseModel):
    """Response schema for sentiment trends."""
    period_days: int
    daily_data: List[Dict[str, Any]] = Field(description="Daily sentiment data")
    overall_stats: Dict[str, Any] = Field(description="Overall statistics for the period")


# Topic modeling schemas
class TopicAnalysisRequest(BaseModel):
    """Request schema for topic analysis."""
    message_id: Optional[int] = Field(None, description="ID of message to analyze")
    content: Optional[str] = Field(None, description="Content to analyze directly")
    
    @validator('content')
    def validate_input(cls, v, values):
        if not values.get('message_id') and not v:
            raise ValueError('Either message_id or content must be provided')
        return v
    
    class Config:
        validate_assignment = True


class TopicAnalysisResponse(BaseModel):
    """Response schema for topic analysis."""
    message_id: Optional[int] = None
    content_preview: str
    assigned_topics: List[Dict[str, Any]] = Field(description="Topics assigned to the message")
    primary_topic: Dict[str, Any] = Field(description="Primary topic assignment")
    analysis_method: str = Field(description="Method used for analysis")
    analyzed_at: datetime


class TopicOverviewResponse(BaseModel):
    """Response schema for topic overview."""
    total_topics: int
    total_assignments: int
    total_messages: int
    coverage: float = Field(description="Percentage of messages with topic assignments")
    messages_with_topics: int
    needs_analysis: bool
    top_topics: List[Dict[str, Any]] = Field(description="Top topics by message count")
    trending_topics: List[Dict[str, Any]] = Field(description="Most trending topics")
    avg_coherence: float = Field(description="Average topic coherence score")


class TrendingTopicsResponse(BaseModel):
    """Response schema for trending topics."""
    time_period_days: int
    trending_topics: List[Dict[str, Any]] = Field(description="Trending topics data")
    total_topics: int
    active_topics: int
    analysis_date: str


class TopicTrendsResponse(BaseModel):
    """Response schema for topic trends over time."""
    time_period_days: int
    daily_data: Dict[str, Dict[str, Dict[str, Any]]] = Field(description="Daily topic activity data")
    topics_summary: Dict[str, Dict[str, Any]] = Field(description="Topic summary information")
    analysis_date: str


class CandidateTopicsResponse(BaseModel):
    """Response schema for candidate topic analysis."""
    candidate_topic_analysis: List[Dict[str, Any]] = Field(description="Candidate topic distributions")
    total_candidates_analyzed: int
    analysis_date: str


class TopicSentimentResponse(BaseModel):
    """Response schema for topic-sentiment correlation."""
    topic_sentiment_analysis: List[Dict[str, Any]] = Field(description="Topic sentiment correlations")
    total_topics_analyzed: int
    analysis_date: str


# ===== ENGAGEMENT ANALYSIS SCHEMAS =====

class EngagementAnalysisRequest(BaseModel):
    """Request schema for engagement analysis."""
    message_id: Optional[int] = None
    content: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": 123,
                "content": "Breaking: New policy announcement on immigration reform..."
            }
        }


class EngagementAnalysisResponse(BaseModel):
    """Response schema for engagement analysis."""
    message_id: Optional[int] = None
    content_preview: str
    engagement_score: float = Field(description="Normalized engagement score (0.0-1.0)")
    virality_score: float = Field(description="Virality potential score (0.0-1.0)")
    influence_score: float = Field(description="Message influence score (0.0-1.0)")
    platform_metrics: Dict[str, Any] = Field(description="Platform-specific engagement metrics")
    reach_metrics: Dict[str, Any] = Field(description="Reach and impression data")
    interaction_quality: float = Field(description="Quality of audience interactions")
    audience_relevance: float = Field(description="Relevance to target audience")
    platform_percentile: float = Field(description="Performance vs other platform messages")
    candidate_percentile: float = Field(description="Performance vs candidate's other messages")
    engagement_velocity: float = Field(description="Speed of initial engagement")
    analysis_method: str = Field(description="Method used for analysis")
    analyzed_at: datetime


class EngagementBatchResponse(BaseModel):
    """Response schema for batch engagement analysis."""
    status: str = Field(description="Analysis status")
    analyzed_count: int = Field(description="Number of messages analyzed")
    processing_time_seconds: float = Field(description="Time taken for analysis")
    analysis_method: str = Field(description="Method used for analysis")
    batch_limit: int = Field(description="Batch size limit applied")
    regenerate: bool = Field(description="Whether existing data was regenerated")


class EngagementOverviewResponse(BaseModel):
    """Response schema for engagement overview."""
    total_messages: int
    analyzed_messages: int
    coverage: float = Field(description="Percentage of messages with engagement analysis")
    needs_analysis: bool
    avg_engagement: float = Field(description="Average engagement score")
    avg_virality: float = Field(description="Average virality score")
    avg_influence: float = Field(description="Average influence score")
    top_performing: List[Dict[str, Any]] = Field(description="Top performing messages")


class PlatformPerformanceResponse(BaseModel):
    """Response schema for platform performance comparison."""
    platform_comparison: List[Dict[str, Any]] = Field(description="Platform performance data")
    total_platforms: int
    analysis_date: str


class ViralContentResponse(BaseModel):
    """Response schema for viral content analysis."""
    viral_threshold: float = Field(description="Virality score threshold used")
    viral_messages_found: int
    viral_content: List[Dict[str, Any]] = Field(description="Viral messages data")
    analysis_date: str


class CandidateEngagementResponse(BaseModel):
    """Response schema for candidate engagement analysis."""
    candidate_engagement_analysis: List[Dict[str, Any]] = Field(description="Candidate engagement data")
    total_candidates_analyzed: int
    analysis_date: str


class EngagementTrendsResponse(BaseModel):
    """Response schema for engagement trends over time."""
    time_period_days: int
    daily_data: Dict[str, Dict[str, Any]] = Field(description="Daily engagement data")
    trends_summary: Dict[str, Any] = Field(description="Engagement trends summary")
    analysis_date: str
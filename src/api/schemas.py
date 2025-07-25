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


# ===== INTELLIGENCE REPORT SCHEMAS =====

class ReportGenerationRequest(BaseModel):
    """Request schema for intelligence report generation."""
    report_type: str = Field(description="Type of report to generate")
    time_period_days: int = Field(default=7, ge=1, le=365, description="Number of days to analyze")
    entity_filter: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters")
    export_format: str = Field(default="json", description="Export format (json, markdown)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_type": "weekly_summary",
                "time_period_days": 7,
                "entity_filter": {"source_type": "twitter"},
                "export_format": "markdown"
            }
        }


class ReportSectionResponse(BaseModel):
    """Response schema for report section."""
    title: str
    content: str
    data: Dict[str, Any] = Field(description="Section data")
    visualizations: List[str] = Field(description="Suggested visualizations")
    priority: str = Field(description="Section priority level")


class IntelligenceReportResponse(BaseModel):
    """Response schema for intelligence report."""
    report_id: str
    report_type: str
    title: str
    executive_summary: str
    generated_at: datetime
    time_period: Dict[str, str] = Field(description="Analysis time period")
    sections: List[ReportSectionResponse] = Field(description="Report sections")
    metadata: Dict[str, Any] = Field(description="Report metadata")
    recommendations: List[str] = Field(description="Actionable recommendations")
    data_sources: List[str] = Field(description="Data sources used")


class ReportListResponse(BaseModel):
    """Response schema for report listing."""
    reports: List[Dict[str, Any]] = Field(description="Available reports")
    total_reports: int
    report_types: List[str] = Field(description="Available report types")


class ReportExportResponse(BaseModel):
    """Response schema for report export."""
    report_id: str
    export_format: str
    content: str = Field(description="Exported report content")
    filename: str = Field(description="Suggested filename")
    generated_at: datetime


# ===== SEARCH SCHEMAS =====

class SearchRequest(BaseModel):
    """Request schema for search functionality."""
    query: str = Field(min_length=1, max_length=500, description="Search query text")
    search_types: Optional[List[str]] = Field(
        default=["messages", "keywords", "candidates"], 
        description="Types of content to search: messages, keywords, candidates, sources"
    )
    source_types: Optional[List[str]] = Field(
        default=None,
        description="Filter by source types: website, twitter, facebook, meta_ads"
    )
    candidate_ids: Optional[List[int]] = Field(
        default=None, 
        description="Filter by specific candidate IDs"
    )
    date_from: Optional[datetime] = Field(
        default=None, 
        description="Search messages from this date onwards"
    )
    date_to: Optional[datetime] = Field(
        default=None, 
        description="Search messages up to this date"
    )
    sentiment_filter: Optional[str] = Field(
        default=None,
        description="Filter by sentiment: positive, negative, neutral"
    )
    geographic_scope: Optional[str] = Field(
        default=None,
        description="Filter by geographic scope: national, regional, local"
    )
    limit: Optional[int] = Field(
        default=50, 
        ge=1, 
        le=200, 
        description="Maximum number of results per search type"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "immigration policy reform",
                "search_types": ["messages", "keywords"],
                "source_types": ["twitter", "website"],
                "date_from": "2024-01-01T00:00:00Z",
                "limit": 20
            }
        }


class MessageSearchResult(BaseModel):
    """Individual message search result."""
    message_id: int
    content: str = Field(description="Message content (truncated if long)")
    content_preview: str = Field(description="Short preview of content")
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    source_name: str
    source_type: str
    candidate_name: Optional[str] = None
    message_type: Optional[str] = None
    geographic_scope: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    keywords: List[str] = Field(description="Associated keywords")
    relevance_score: float = Field(description="Search relevance score (0.0-1.0)")


class KeywordSearchResult(BaseModel):
    """Individual keyword search result."""
    keyword: str
    message_count: int = Field(description="Number of messages containing this keyword")
    confidence: float = Field(description="Average extraction confidence")
    extraction_method: str
    recent_messages: List[Dict[str, Any]] = Field(description="Recent messages with this keyword")


class CandidateSearchResult(BaseModel):
    """Individual candidate search result."""
    candidate_id: int
    candidate_name: str
    constituency_name: Optional[str] = None
    constituency_region: Optional[str] = None
    message_count: int = Field(description="Total messages from this candidate")
    recent_message_count: int = Field(description="Messages in last 30 days")
    social_media_accounts: Optional[Dict[str, str]] = None
    avg_sentiment: Optional[float] = None
    top_keywords: List[str] = Field(description="Most common keywords in candidate's messages")


class SourceSearchResult(BaseModel):
    """Individual source search result."""
    source_id: int
    source_name: str
    source_type: str
    source_url: Optional[str] = None
    message_count: int = Field(description="Total messages from this source")
    last_activity: Optional[datetime] = Field(description="Last message timestamp")
    active: bool


class SearchResponse(BaseModel):
    """Response schema for search results."""
    query: str
    total_results: int
    search_time_ms: float = Field(description="Search execution time in milliseconds")
    results: Dict[str, Any] = Field(description="Search results grouped by type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "immigration policy",
                "total_results": 47,
                "search_time_ms": 125.6,
                "results": {
                    "messages": {
                        "count": 23,
                        "items": []
                    },
                    "keywords": {
                        "count": 12,
                        "items": []
                    },
                    "candidates": {
                        "count": 8,
                        "items": []
                    },
                    "sources": {
                        "count": 4,
                        "items": []
                    }
                }
            }
        }


class AutocompleteRequest(BaseModel):
    """Request schema for search autocomplete."""
    query: str = Field(min_length=1, max_length=100, description="Partial search query")
    search_type: str = Field(
        default="all",
        description="Type of suggestions: all, keywords, candidates, sources"
    )
    limit: Optional[int] = Field(default=10, ge=1, le=50, description="Max suggestions")


class AutocompleteResponse(BaseModel):
    """Response schema for search autocomplete."""
    query: str
    suggestions: List[Dict[str, Any]] = Field(description="Autocomplete suggestions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "immig",
                "suggestions": [
                    {"text": "immigration", "type": "keyword", "count": 45},
                    {"text": "immigration policy", "type": "phrase", "count": 23},
                    {"text": "immigration reform", "type": "phrase", "count": 18}
                ]
            }
        }
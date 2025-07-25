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
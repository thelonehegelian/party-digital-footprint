from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, Index, JSON
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


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    content = Column(Text, nullable=False)
    url = Column(Text)
    published_at = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    message_type = Column(String(50))  # 'post', 'article', 'press_release', 'ad'
    message_metadata = Column(JSON)  # hashtags, media_urls, engagement_stats
    raw_data = Column(JSON)  # store original API response
    
    source = relationship("Source", back_populates="messages")
    keywords = relationship("Keyword", back_populates="message")


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


class MessageCreate(BaseModel):
    source_id: int
    content: str
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    message_type: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    id: int
    source_id: int
    content: str
    url: Optional[str]
    published_at: Optional[datetime]
    scraped_at: datetime
    message_type: Optional[str]
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
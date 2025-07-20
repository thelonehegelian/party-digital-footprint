from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from loguru import logger

from ..database import get_session
from ..models import Source, Message, Keyword
from ..nlp.processor import BasicNLPProcessor
from .schemas import (
    MessageInput, BulkMessageInput, MessageResponse, 
    BulkMessageResponse, ErrorResponse
)

router = APIRouter(prefix="/api/v1", tags=["messages"])

# Initialize NLP processor
nlp_processor = BasicNLPProcessor()
nlp_processor.load_model()


def get_or_create_source(db: Session, source_name: str, source_type: str, source_url: str = None) -> Source:
    """Get existing source or create new one."""
    source = db.query(Source).filter(
        Source.name == source_name,
        Source.source_type == source_type
    ).first()
    
    if not source:
        source = Source(
            name=source_name,
            source_type=source_type,
            url=source_url,
            active=True,
            last_scraped=datetime.utcnow()
        )
        db.add(source)
        db.flush()
        logger.info(f"Created new source: {source_name}")
    else:
        # Update last scraped time
        source.last_scraped = datetime.utcnow()
    
    return source


def extract_and_store_keywords(db: Session, message: Message) -> int:
    """Extract keywords from message content and store them."""
    if not nlp_processor.nlp:
        return 0
    
    try:
        keywords = nlp_processor.extract_keywords(message.content)
        keywords_count = 0
        
        for kw_data in keywords:
            keyword = Keyword(
                message_id=message.id,
                keyword=kw_data['keyword'],
                confidence=kw_data['confidence'],
                extraction_method=kw_data['extraction_method']
            )
            db.add(keyword)
            keywords_count += 1
        
        return keywords_count
        
    except Exception as e:
        logger.error(f"Error extracting keywords for message {message.id}: {e}")
        return 0


def check_duplicate_message(db: Session, source_id: int, content: str, url: str = None) -> Message:
    """Check if message already exists."""
    # Check by URL first if available
    if url:
        existing = db.query(Message).filter(
            Message.source_id == source_id,
            Message.url == url
        ).first()
        if existing:
            return existing
    
    # Check by content hash (first 100 chars as simple duplicate detection)
    content_sample = content[:100]
    existing = db.query(Message).filter(
        Message.source_id == source_id,
        Message.content.like(f"{content_sample}%")
    ).first()
    
    return existing


@router.post("/messages/single", response_model=MessageResponse)
async def submit_single_message(
    message_data: MessageInput,
    db: Session = Depends(get_session)
):
    """Submit a single message for analysis."""
    try:
        # Get or create source
        source = get_or_create_source(
            db, 
            message_data.source_name, 
            message_data.source_type,
            message_data.source_url
        )
        
        # Check for duplicates
        existing_message = check_duplicate_message(
            db, 
            source.id, 
            message_data.content, 
            message_data.url
        )
        
        if existing_message:
            return MessageResponse(
                status="warning",
                message="Message already exists",
                message_id=existing_message.id
            )
        
        # Create new message
        message = Message(
            source_id=source.id,
            content=message_data.content,
            url=message_data.url,
            published_at=message_data.published_at,
            message_type=message_data.message_type,
            message_metadata=message_data.metadata,
            raw_data=message_data.raw_data,
            scraped_at=datetime.utcnow()
        )
        
        db.add(message)
        db.flush()
        
        # Extract keywords
        keywords_count = extract_and_store_keywords(db, message)
        
        db.commit()
        
        return MessageResponse(
            status="success",
            message_id=message.id,
            keywords_extracted=keywords_count
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.post("/messages/bulk", response_model=BulkMessageResponse)
async def submit_bulk_messages(
    bulk_data: BulkMessageInput,
    db: Session = Depends(get_session)
):
    """Submit multiple messages for analysis."""
    imported_count = 0
    skipped_count = 0
    total_keywords = 0
    errors = []
    
    try:
        for i, message_data in enumerate(bulk_data.messages):
            try:
                # Get or create source
                source = get_or_create_source(
                    db,
                    message_data.source_name,
                    message_data.source_type,
                    message_data.source_url
                )
                
                # Check for duplicates
                existing_message = check_duplicate_message(
                    db,
                    source.id,
                    message_data.content,
                    message_data.url
                )
                
                if existing_message:
                    skipped_count += 1
                    continue
                
                # Create new message
                message = Message(
                    source_id=source.id,
                    content=message_data.content,
                    url=message_data.url,
                    published_at=message_data.published_at,
                    message_type=message_data.message_type,
                    message_metadata=message_data.metadata,
                    raw_data=message_data.raw_data,
                    scraped_at=datetime.utcnow()
                )
                
                db.add(message)
                db.flush()
                
                # Extract keywords
                keywords_count = extract_and_store_keywords(db, message)
                total_keywords += keywords_count
                
                imported_count += 1
                
            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e),
                    "content_preview": message_data.content[:50] + "..."
                })
                continue
        
        db.commit()
        
        # Determine overall status
        if imported_count == 0:
            status_result = "error"
        elif errors:
            status_result = "partial"
        else:
            status_result = "success"
        
        return BulkMessageResponse(
            status=status_result,
            imported_count=imported_count,
            skipped_count=skipped_count,
            errors=errors,
            total_keywords_extracted=total_keywords
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing bulk messages: {str(e)}"
        )


@router.get("/sources")
async def list_sources(db: Session = Depends(get_session)):
    """List all configured sources."""
    sources = db.query(Source).all()
    return [
        {
            "id": source.id,
            "name": source.name,
            "source_type": source.source_type,
            "url": source.url,
            "active": source.active,
            "last_scraped": source.last_scraped,
            "message_count": len(source.messages)
        }
        for source in sources
    ]


@router.get("/messages/stats")
async def get_message_stats(db: Session = Depends(get_session)):
    """Get overall message statistics."""
    total_messages = db.query(Message).count()
    total_keywords = db.query(Keyword).count()
    total_sources = db.query(Source).count()
    
    # Messages by source type
    source_stats = db.query(Source.source_type, db.func.count(Message.id))\
        .join(Message)\
        .group_by(Source.source_type)\
        .all()
    
    return {
        "total_messages": total_messages,
        "total_keywords": total_keywords,
        "total_sources": total_sources,
        "by_source_type": dict(source_stats)
    }
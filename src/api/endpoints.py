from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from ..database import get_session
from ..models import Source, Message, Keyword, Constituency, Candidate, MessageSentiment
from ..nlp.processor import BasicNLPProcessor
from ..analytics.sentiment import PoliticalSentimentAnalyzer
from .schemas import (
    MessageInput, BulkMessageInput, MessageResponse, 
    BulkMessageResponse, ErrorResponse, SentimentAnalysisRequest,
    SentimentAnalysisResponse, SentimentTrendsResponse
)

router = APIRouter(prefix="/api/v1", tags=["messages"])

# Initialize NLP processor and sentiment analyzer
nlp_processor = BasicNLPProcessor()
nlp_processor.load_model()
sentiment_analyzer = PoliticalSentimentAnalyzer()


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
            last_scraped=datetime.now()
        )
        db.add(source)
        db.flush()
        logger.info(f"Created new source: {source_name}")
    else:
        # Update last scraped time
        source.last_scraped = datetime.now()
    
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


@router.post("/messages/single", response_model=MessageResponse, tags=["messages"])
async def submit_single_message(
    message_data: MessageInput,
    db: Session = Depends(get_session)
):
    """
    Submit a single political message for analysis.
    
    Processes and stores a single message with the following features:
    - Automatic source creation/linking
    - Candidate association (Phase 2)
    - NLP keyword extraction
    - Duplicate detection
    - Geographic scope classification
    
    **Returns:**
    - Success/warning status
    - Message ID for reference
    - Number of keywords extracted
    """
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
            candidate_id=message_data.candidate_id,
            content=message_data.content,
            url=message_data.url,
            published_at=message_data.published_at,
            message_type=message_data.message_type,
            geographic_scope=message_data.geographic_scope,
            message_metadata=message_data.metadata,
            raw_data=message_data.raw_data,
            scraped_at=datetime.now()
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


@router.post("/messages/bulk", response_model=BulkMessageResponse, tags=["messages"])
async def submit_bulk_messages(
    bulk_data: BulkMessageInput,
    db: Session = Depends(get_session)
):
    """
    Submit multiple political messages for bulk analysis.
    
    Efficiently processes up to 100 messages with:
    - Batch processing with error handling
    - Individual message validation
    - Automatic source management
    - Candidate association (Phase 2)
    - Bulk keyword extraction
    - Comprehensive error reporting
    
    **Returns:**
    - Overall processing status (success/partial/error)
    - Count of imported vs skipped messages
    - Detailed error information for failed messages
    - Total keywords extracted
    """
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
                    candidate_id=message_data.candidate_id,
                    content=message_data.content,
                    url=message_data.url,
                    published_at=message_data.published_at,
                    message_type=message_data.message_type,
                    geographic_scope=message_data.geographic_scope,
                    message_metadata=message_data.metadata,
                    raw_data=message_data.raw_data,
                    scraped_at=datetime.now()
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


@router.get("/sources", tags=["sources"])
async def list_sources(db: Session = Depends(get_session)):
    """
    List all configured data sources.
    
    Returns information about all configured data sources including:
    - Source name and type (twitter, facebook, website, meta_ads)
    - Source URL and activity status
    - Last scraping timestamp
    - Total message count per source
    """
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


@router.get("/messages/stats", tags=["statistics"])
async def get_message_stats(db: Session = Depends(get_session)):
    """
    Get comprehensive system statistics.
    
    Returns overall statistics including:
    - Total counts: messages, keywords, sources, constituencies, candidates
    - Message distribution by source type (twitter, facebook, website, etc.)
    - Geographic distribution by scope (national, regional, local)
    
    This endpoint provides key metrics for Phase 2 analytics and reporting.
    """
    total_messages = db.query(Message).count()
    total_keywords = db.query(Keyword).count()
    total_sources = db.query(Source).count()
    total_constituencies = db.query(Constituency).count()
    total_candidates = db.query(Candidate).count()
    
    # Messages by source type
    source_stats = db.query(Source.source_type, func.count(Message.id))\
        .join(Message)\
        .group_by(Source.source_type)\
        .all()
    
    # Messages by geographic scope (Phase 2)
    geographic_stats = db.query(Message.geographic_scope, func.count(Message.id))\
        .filter(Message.geographic_scope.isnot(None))\
        .group_by(Message.geographic_scope)\
        .all()
    
    return {
        "total_messages": total_messages,
        "total_keywords": total_keywords,
        "total_sources": total_sources,
        "total_constituencies": total_constituencies,
        "total_candidates": total_candidates,
        "by_source_type": dict(source_stats),
        "by_geographic_scope": dict(geographic_stats)
    }


@router.get("/constituencies", tags=["constituencies"])
async def list_constituencies(db: Session = Depends(get_session)):
    """
    List all UK constituencies with candidate counts.
    
    Returns constituency information including:
    - Constituency name and ID
    - UK region (England, Scotland, Wales, Northern Ireland)
    - Constituency type (county, district, unitary)
    - Number of Reform UK candidates
    
    This endpoint supports Phase 2 geographic analysis features.
    """
    constituencies = db.query(Constituency).all()
    return [
        {
            "id": const.id,
            "name": const.name,
            "region": const.region,
            "constituency_type": const.constituency_type,
            "candidate_count": len(const.candidates)
        }
        for const in constituencies
    ]


@router.get("/candidates", tags=["candidates"])
async def list_candidates(
    constituency_id: Optional[int] = None,
    db: Session = Depends(get_session)
):
    """
    List Reform UK candidates with their messaging activity.
    
    Returns candidate information including:
    - Candidate name and ID
    - Associated constituency and region
    - Social media account handles (Twitter, Facebook)
    - Candidate type (local, national, both)
    - Total message count
    
    **Parameters:**
    - `constituency_id` (optional): Filter candidates by specific constituency
    
    This endpoint enables Phase 2 candidate-level analysis and social media tracking.
    """
    query = db.query(Candidate)
    
    if constituency_id:
        query = query.filter(Candidate.constituency_id == constituency_id)
    
    candidates = query.all()
    
    return [
        {
            "id": cand.id,
            "name": cand.name,
            "constituency_id": cand.constituency_id,
            "constituency_name": cand.constituency.name if cand.constituency else None,
            "social_media_accounts": cand.social_media_accounts,
            "candidate_type": cand.candidate_type,
            "message_count": len(cand.messages)
        }
        for cand in candidates
    ]


@router.get("/candidates/{candidate_id}/messages", tags=["candidates"])
async def get_candidate_messages(
    candidate_id: int,
    db: Session = Depends(get_session)
):
    """
    Get all messages for a specific Reform UK candidate.
    
    Returns detailed messaging activity for an individual candidate including:
    - Full candidate profile information
    - All messages with content preview (truncated to 200 chars)
    - Message metadata (URL, publish date, type, geographic scope)
    - Source information (platform, account name)
    
    **Parameters:**
    - `candidate_id`: Unique identifier for the candidate
    
    **Errors:**
    - `404`: Candidate not found
    
    This endpoint is essential for Phase 2 candidate-level message analysis.
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    messages = db.query(Message).filter(Message.candidate_id == candidate_id).all()
    
    return {
        "candidate": {
            "id": candidate.id,
            "name": candidate.name,
            "constituency_name": candidate.constituency.name if candidate.constituency else None
        },
        "messages": [
            {
                "id": msg.id,
                "content": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content,
                "url": msg.url,
                "published_at": msg.published_at,
                "message_type": msg.message_type,
                "geographic_scope": msg.geographic_scope,
                "source_name": msg.source.name if msg.source else None
            }
            for msg in messages
        ]
    }


@router.post("/analytics/sentiment/analyze", response_model=SentimentAnalysisResponse, tags=["analytics"])
async def analyze_message_sentiment(
    request: SentimentAnalysisRequest,
    use_dummy: bool = True,
    db: Session = Depends(get_session)
):
    """
    Analyze sentiment for a specific message or batch of messages.
    
    Provides political sentiment analysis including:
    - Basic sentiment scoring (-1 to 1, negative to positive)
    - Sentiment classification (positive, negative, neutral)
    - Political tone detection (aggressive, diplomatic, populist, nationalist)
    - Emotional categorization (anger, fear, hope, pride)
    - Confidence scores for all classifications
    
    **Parameters:**
    - `message_id` (optional): Analyze specific message by ID
    - `content` (optional): Analyze provided text content directly  
    - `use_dummy`: Use dummy data generator for testing (default: true)
    
    **Returns:**
    - Comprehensive sentiment analysis results
    - Political tone and emotional classifications
    - Analysis metadata including method used
    """
    try:
        if request.message_id:
            # Analyze existing message by ID
            message = db.query(Message).filter(Message.id == request.message_id).first()
            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Message not found"
                )
            
            # Check if sentiment already exists
            existing_sentiment = db.query(MessageSentiment)\
                .filter(MessageSentiment.message_id == message.id)\
                .first()
            
            if existing_sentiment:
                return SentimentAnalysisResponse(
                    message_id=message.id,
                    content_preview=message.content[:100] + "...",
                    sentiment_score=existing_sentiment.sentiment_score,
                    sentiment_label=existing_sentiment.sentiment_label,
                    confidence=existing_sentiment.confidence,
                    political_tone=existing_sentiment.political_tone,
                    tone_confidence=existing_sentiment.tone_confidence,
                    emotions=existing_sentiment.emotions,
                    analysis_method=existing_sentiment.analysis_method,
                    analyzed_at=existing_sentiment.analyzed_at
                )
            
            # Generate new sentiment analysis
            if use_dummy:
                sentiment_result = sentiment_analyzer.generate_dummy_sentiment(message)
            else:
                sentiment_result = sentiment_analyzer.analyze_message_sentiment(message.content)
            
            # Store in database
            sentiment_record = MessageSentiment(
                message_id=message.id,
                sentiment_score=sentiment_result.sentiment_score,
                sentiment_label=sentiment_result.sentiment_label,
                confidence=sentiment_result.confidence,
                political_tone=sentiment_result.political_tone,
                tone_confidence=sentiment_result.tone_confidence,
                emotions=sentiment_result.emotions,
                analysis_method=sentiment_result.analysis_method,
                analyzed_at=datetime.utcnow()
            )
            db.add(sentiment_record)
            db.commit()
            
            return SentimentAnalysisResponse(
                message_id=message.id,
                content_preview=message.content[:100] + "...",
                sentiment_score=sentiment_result.sentiment_score,
                sentiment_label=sentiment_result.sentiment_label,
                confidence=sentiment_result.confidence,
                political_tone=sentiment_result.political_tone,
                tone_confidence=sentiment_result.tone_confidence,
                emotions=sentiment_result.emotions,
                analysis_method=sentiment_result.analysis_method,
                analyzed_at=sentiment_record.analyzed_at
            )
            
        elif request.content:
            # Analyze provided content directly (no database storage)
            if use_dummy:
                # Create temporary message object for dummy analysis
                temp_message = Message(content=request.content)
                sentiment_result = sentiment_analyzer.generate_dummy_sentiment(temp_message)
            else:
                sentiment_result = sentiment_analyzer.analyze_message_sentiment(request.content)
            
            return SentimentAnalysisResponse(
                content_preview=request.content[:100] + "..." if len(request.content) > 100 else request.content,
                sentiment_score=sentiment_result.sentiment_score,
                sentiment_label=sentiment_result.sentiment_label,
                confidence=sentiment_result.confidence,
                political_tone=sentiment_result.political_tone,
                tone_confidence=sentiment_result.tone_confidence,
                emotions=sentiment_result.emotions,
                analysis_method=sentiment_result.analysis_method,
                analyzed_at=datetime.utcnow()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either message_id or content must be provided"
            )
            
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing sentiment: {str(e)}"
        )


@router.post("/analytics/sentiment/batch", tags=["analytics"])
async def analyze_batch_sentiment(
    use_dummy: bool = True,
    limit: int = 100,
    db: Session = Depends(get_session)
):
    """
    Analyze sentiment for all messages without existing sentiment data.
    
    Batch processes messages for sentiment analysis with the following features:
    - Processes messages without existing sentiment records
    - Configurable batch size (default: 100, max: 1000)
    - Choice between real TextBlob analysis or dummy data generation
    - Comprehensive progress reporting
    
    **Parameters:**
    - `use_dummy`: Use dummy sentiment generator for testing (default: true)
    - `limit`: Maximum number of messages to process (default: 100, max: 1000)
    
    **Returns:**
    - Number of messages analyzed
    - Processing summary with timing information
    - Error count if any failures occurred
    """
    try:
        if limit > 1000:
            limit = 1000
            
        start_time = datetime.utcnow()
        analyzed_count = sentiment_analyzer.analyze_batch_messages(db, use_dummy=use_dummy, limit=limit)
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        return {
            "status": "success",
            "analyzed_count": analyzed_count,
            "processing_time_seconds": processing_time,
            "analysis_method": "dummy_generator" if use_dummy else "textblob_political",
            "batch_limit": limit,
            "completed_at": end_time
        }
        
    except Exception as e:
        logger.error(f"Error in batch sentiment analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing batch sentiment analysis: {str(e)}"
        )


@router.get("/analytics/sentiment/trends", response_model=SentimentTrendsResponse, tags=["analytics"])
async def get_sentiment_trends(
    days: int = 7,
    db: Session = Depends(get_session)
):
    """
    Get sentiment trends over time for Reform UK messaging.
    
    Analyzes sentiment patterns across time periods with:
    - Daily sentiment averages and message counts
    - Sentiment distribution (positive, negative, neutral)
    - Political tone trends over time
    - Overall statistics for the specified period
    
    **Parameters:**
    - `days`: Number of days to analyze (default: 7, max: 90)
    
    **Returns:**
    - Daily sentiment data with averages and counts
    - Overall sentiment statistics for the period
    - Sentiment distribution breakdown
    - Political tone analysis trends
    """
    try:
        if days > 90:
            days = 90
            
        trends_data = sentiment_analyzer.get_sentiment_trends(db, days=days)
        
        return SentimentTrendsResponse(
            period_days=trends_data['period_days'],
            daily_data=trends_data['daily_data'],
            overall_stats=trends_data['overall_stats']
        )
        
    except Exception as e:
        logger.error(f"Error getting sentiment trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving sentiment trends: {str(e)}"
        )


@router.get("/analytics/sentiment/stats", tags=["analytics"])
async def get_sentiment_statistics(db: Session = Depends(get_session)):
    """
    Get comprehensive sentiment analysis statistics.
    
    Provides overall sentiment analysis metrics including:
    - Total messages with sentiment analysis
    - Sentiment distribution (positive, negative, neutral percentages)
    - Political tone distribution (aggressive, diplomatic, populist, nationalist)
    - Average sentiment scores and confidence levels
    - Analysis method breakdown (TextBlob vs dummy data)
    
    **Returns:**
    - Complete sentiment analysis overview
    - Statistical breakdowns by classification type
    - Analysis quality metrics
    """
    try:
        # Basic counts
        total_analyzed = db.query(MessageSentiment).count()
        total_messages = db.query(Message).count()
        
        if total_analyzed == 0:
            return {
                "total_messages": total_messages,
                "total_analyzed": 0,
                "analysis_coverage": 0.0,
                "sentiment_distribution": {},
                "political_tone_distribution": {},
                "average_sentiment_score": 0.0,
                "average_confidence": 0.0
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
        
        # Average scores
        avg_sentiment = db.query(func.avg(MessageSentiment.sentiment_score)).scalar() or 0.0
        avg_confidence = db.query(func.avg(MessageSentiment.confidence)).scalar() or 0.0
        
        return {
            "total_messages": total_messages,
            "total_analyzed": total_analyzed,
            "analysis_coverage": (total_analyzed / total_messages * 100) if total_messages > 0 else 0.0,
            "sentiment_distribution": dict(sentiment_dist),
            "political_tone_distribution": dict(tone_dist),
            "average_sentiment_score": float(avg_sentiment),
            "average_confidence": float(avg_confidence)
        }
        
    except Exception as e:
        logger.error(f"Error getting sentiment statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving sentiment statistics: {str(e)}"
        )
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from ..database import get_session
from ..models import Party, PartyCreate, PartyResponse, Source, Message, Keyword, Constituency, Candidate, MessageSentiment, TopicModel, MessageTopic, EngagementMetrics
from ..nlp.processor import BasicNLPProcessor
from ..analytics.sentiment import PoliticalSentimentAnalyzer
from ..analytics.topics import PoliticalTopicAnalyzer
from ..analytics.engagement import PoliticalEngagementAnalyzer
from ..analytics.intelligence import IntelligenceReportGenerator, ReportType
from .schemas import (
    MessageInput, BulkMessageInput, MessageResponse, 
    BulkMessageResponse, ErrorResponse, SentimentAnalysisRequest,
    SentimentAnalysisResponse, SentimentTrendsResponse,
    TopicAnalysisRequest, TopicAnalysisResponse, TopicOverviewResponse,
    TrendingTopicsResponse, TopicTrendsResponse, CandidateTopicsResponse,
    TopicSentimentResponse, EngagementAnalysisRequest, EngagementAnalysisResponse,
    EngagementBatchResponse, EngagementOverviewResponse, PlatformPerformanceResponse,
    ViralContentResponse, CandidateEngagementResponse, EngagementTrendsResponse,
    ReportGenerationRequest, IntelligenceReportResponse, ReportListResponse,
    ReportExportResponse, ReportSectionResponse, SearchRequest, SearchResponse,
    AutocompleteRequest, AutocompleteResponse, MessageSearchResult, KeywordSearchResult,
    CandidateSearchResult, SourceSearchResult
)

router = APIRouter(prefix="/api/v1", tags=["messages"])

# Initialize NLP processor and analytics engines
nlp_processor = BasicNLPProcessor()
nlp_processor.load_model()
sentiment_analyzer = PoliticalSentimentAnalyzer()
topic_analyzer = PoliticalTopicAnalyzer()
engagement_analyzer = PoliticalEngagementAnalyzer()
intelligence_generator = IntelligenceReportGenerator()


# ===== PARTY MANAGEMENT ENDPOINTS =====

@router.post("/parties", response_model=PartyResponse)
def create_party(party: PartyCreate, db: Session = Depends(get_session)):
    """Create a new political party."""
    try:
        # Check if party already exists
        existing = db.query(Party).filter(Party.name == party.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Party with name '{party.name}' already exists"
            )
        
        # Create new party
        db_party = Party(**party.model_dump())
        db.add(db_party)
        db.commit()
        db.refresh(db_party)
        
        logger.info(f"Created new party: {party.name}")
        return db_party
        
    except Exception as e:
        logger.error(f"Error creating party: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create party"
        )


@router.get("/parties", response_model=List[PartyResponse])
def list_parties(
    active_only: bool = Query(True, description="Filter to active parties only"),
    db: Session = Depends(get_session)
):
    """List all political parties."""
    try:
        query = db.query(Party)
        if active_only:
            query = query.filter(Party.active == True)
        
        parties = query.order_by(Party.name).all()
        return parties
        
    except Exception as e:
        logger.error(f"Error listing parties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve parties"
        )


@router.get("/parties/{party_id}", response_model=PartyResponse)
def get_party(party_id: int, db: Session = Depends(get_session)):
    """Get a specific party by ID."""
    try:
        party = db.query(Party).filter(Party.id == party_id).first()
        if not party:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Party with ID {party_id} not found"
            )
        
        return party
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving party {party_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve party"
        )


@router.put("/parties/{party_id}", response_model=PartyResponse)
def update_party(party_id: int, party_update: PartyCreate, db: Session = Depends(get_session)):
    """Update a party's information."""
    try:
        party = db.query(Party).filter(Party.id == party_id).first()
        if not party:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Party with ID {party_id} not found"
            )
        
        # Check if new name conflicts with existing party
        if party_update.name != party.name:
            existing = db.query(Party).filter(
                Party.name == party_update.name,
                Party.id != party_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Party with name '{party_update.name}' already exists"
                )
        
        # Update party fields
        for field, value in party_update.model_dump().items():
            setattr(party, field, value)
        
        party.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(party)
        
        logger.info(f"Updated party: {party.name}")
        return party
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating party {party_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update party"
        )


@router.delete("/parties/{party_id}")
def delete_party(party_id: int, db: Session = Depends(get_session)):
    """Delete a party (soft delete - sets active=False)."""
    try:
        party = db.query(Party).filter(Party.id == party_id).first()
        if not party:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Party with ID {party_id} not found"
            )
        
        # Check if party has associated data
        message_count = db.query(Message).filter(Message.party_id == party_id).count()
        if message_count > 0:
            # Soft delete - keep data but mark as inactive
            party.active = False
            party.updated_at = datetime.utcnow()
            db.commit()
            logger.info(f"Soft deleted party: {party.name} (had {message_count} messages)")
            return {"message": f"Party '{party.name}' deactivated successfully"}
        else:
            # Hard delete if no associated data
            db.delete(party)
            db.commit()
            logger.info(f"Hard deleted party: {party.name}")
            return {"message": f"Party '{party.name}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting party {party_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete party"
        )


def get_or_create_source(db: Session, source_name: str, source_type: str, source_url: str = None, party_id: int = None) -> Source:
    """Get existing source or create new one."""
    query = db.query(Source).filter(
        Source.name == source_name,
        Source.source_type == source_type
    )
    
    # Filter by party_id if provided
    if party_id:
        query = query.filter(Source.party_id == party_id)
    
    source = query.first()
    
    if not source:
        source = Source(
            party_id=party_id or 1,  # Default to party 1 for backward compatibility
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
    party_id: int = Query(..., description="ID of the political party this message belongs to"),
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
        # Validate party exists
        party = db.query(Party).filter(Party.id == party_id, Party.active == True).first()
        if not party:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Party with ID {party_id} not found or inactive"
            )
        
        # Get or create source
        source = get_or_create_source(
            db, 
            message_data.source_name, 
            message_data.source_type,
            message_data.source_url,
            party_id
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
            party_id=party_id,
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
    party_id: int = Query(..., description="ID of the political party these messages belong to"),
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
        # Validate party exists
        party = db.query(Party).filter(Party.id == party_id, Party.active == True).first()
        if not party:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Party with ID {party_id} not found or inactive"
            )
        
        for i, message_data in enumerate(bulk_data.messages):
            try:
                # Get or create source
                source = get_or_create_source(
                    db,
                    message_data.source_name,
                    message_data.source_type,
                    message_data.source_url,
                    party_id
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
                    party_id=party_id,
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


# Topic Modeling Endpoints

@router.post("/analytics/topics/analyze", response_model=TopicAnalysisResponse, tags=["analytics"])
async def analyze_message_topics(
    request: TopicAnalysisRequest,
    use_dummy: bool = True,
    db: Session = Depends(get_session)
):
    """
    Analyze topics for a specific message or content.
    
    Provides political topic modeling including:
    - Topic detection and classification (Immigration, Economy, Healthcare, etc.)
    - Primary topic identification with probability scores
    - Multiple topic assignments per message
    - Political issue categorization
    - Topic coherence and relevance scoring
    
    **Parameters:**
    - `message_id` (optional): Analyze specific message by ID
    - `content` (optional): Analyze provided text content directly  
    - `use_dummy`: Use dummy data generator for testing (default: true)
    
    **Returns:**
    - Topic assignments with probabilities
    - Primary topic identification
    - Topic keywords and descriptions
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
            
            # Check if topic assignments already exist
            existing_assignments = db.query(MessageTopic)\
                .filter(MessageTopic.message_id == message.id)\
                .all()
            
            if existing_assignments:
                # Format existing assignments
                assigned_topics = []
                primary_topic = None
                
                for assignment in existing_assignments:
                    topic_data = {
                        "topic_id": assignment.topic_id,
                        "topic_name": assignment.topic.topic_name,
                        "probability": assignment.probability,
                        "is_primary": assignment.is_primary_topic,
                        "keywords": assignment.topic.keywords[:5] if assignment.topic.keywords else [],
                        "description": assignment.topic.description
                    }
                    assigned_topics.append(topic_data)
                    
                    if assignment.is_primary_topic:
                        primary_topic = topic_data
                
                return TopicAnalysisResponse(
                    message_id=message.id,
                    content_preview=message.content[:100] + "...",
                    assigned_topics=assigned_topics,
                    primary_topic=primary_topic or assigned_topics[0],
                    analysis_method="existing_assignment",
                    analyzed_at=existing_assignments[0].assigned_at
                )
            
            # Generate new topic analysis
            analyzed_count = topic_analyzer.analyze_topics_in_messages(
                db, 
                use_dummy=use_dummy, 
                limit=1
            )
            
            if analyzed_count > 0:
                # Retrieve the new assignments
                new_assignments = db.query(MessageTopic)\
                    .filter(MessageTopic.message_id == message.id)\
                    .all()
                
                assigned_topics = []
                primary_topic = None
                
                for assignment in new_assignments:
                    topic_data = {
                        "topic_id": assignment.topic_id,
                        "topic_name": assignment.topic.topic_name,
                        "probability": assignment.probability,
                        "is_primary": assignment.is_primary_topic,
                        "keywords": assignment.topic.keywords[:5] if assignment.topic.keywords else [],
                        "description": assignment.topic.description
                    }
                    assigned_topics.append(topic_data)
                    
                    if assignment.is_primary_topic:
                        primary_topic = topic_data
                
                return TopicAnalysisResponse(
                    message_id=message.id,
                    content_preview=message.content[:100] + "...",
                    assigned_topics=assigned_topics,
                    primary_topic=primary_topic or assigned_topics[0],
                    analysis_method="dummy_generator" if use_dummy else "lda_topic_model",
                    analyzed_at=new_assignments[0].assigned_at
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate topic analysis"
                )
            
        elif request.content:
            # Analyze provided content directly (no database storage)
            # Create temporary message for analysis
            temp_message = Message(content=request.content)
            
            # For direct content analysis, we'll simulate topic assignment
            analyzer_topics = topic_analyzer.political_topics
            topic_names = list(analyzer_topics.keys())
            
            # Simple keyword matching for demo purposes
            assigned_topics = []
            content_lower = request.content.lower()
            
            for topic_name, topic_info in analyzer_topics.items():
                # Check if any keywords match
                keyword_matches = sum(1 for kw in topic_info["keywords"] if kw in content_lower)
                if keyword_matches > 0:
                    probability = min(0.9, keyword_matches * 0.3)
                    assigned_topics.append({
                        "topic_name": topic_name,
                        "probability": probability,
                        "is_primary": len(assigned_topics) == 0,  # First match is primary
                        "keywords": topic_info["keywords"][:5],
                        "description": topic_info["description"],
                        "keyword_matches": keyword_matches
                    })
            
            # If no matches, assign a random topic for demo
            if not assigned_topics:
                import random
                topic_name = random.choice(topic_names)
                topic_info = analyzer_topics[topic_name]
                assigned_topics.append({
                    "topic_name": topic_name,
                    "probability": 0.4,
                    "is_primary": True,
                    "keywords": topic_info["keywords"][:5],
                    "description": topic_info["description"],
                    "keyword_matches": 0
                })
            
            primary_topic = next((t for t in assigned_topics if t["is_primary"]), assigned_topics[0])
            
            return TopicAnalysisResponse(
                content_preview=request.content[:100] + "..." if len(request.content) > 100 else request.content,
                assigned_topics=assigned_topics,
                primary_topic=primary_topic,
                analysis_method="keyword_matching_demo",
                analyzed_at=datetime.utcnow()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either message_id or content must be provided"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logger.error(f"Error analyzing topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing topics: {str(e)}"
        )


@router.post("/analytics/topics/batch", tags=["analytics"])
async def analyze_batch_topics(
    use_dummy: bool = True,
    limit: int = 100,
    regenerate: bool = False,
    db: Session = Depends(get_session)
):
    """
    Analyze topics for all messages without existing topic assignments.
    
    Batch processes messages for topic modeling with the following features:
    - Processes messages without existing topic assignments
    - Configurable batch size (default: 100, max: 1000)
    - Choice between real LDA analysis or dummy data generation
    - Option to regenerate existing assignments
    - Comprehensive progress reporting
    
    **Parameters:**
    - `use_dummy`: Use dummy topic generator for testing (default: true)
    - `limit`: Maximum number of messages to process (default: 100, max: 1000)
    - `regenerate`: Regenerate existing topic assignments (default: false)
    
    **Returns:**
    - Number of messages analyzed
    - Processing summary with timing information
    - Topic assignments created
    """
    try:
        if limit > 1000:
            limit = 1000
            
        start_time = datetime.utcnow()
        analyzed_count = topic_analyzer.analyze_topics_in_messages(
            db, 
            use_dummy=use_dummy, 
            limit=limit,
            regenerate=regenerate
        )
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        return {
            "status": "success",
            "analyzed_count": analyzed_count,
            "processing_time_seconds": processing_time,
            "analysis_method": "dummy_generator" if use_dummy else "lda_topic_model",
            "batch_limit": limit,
            "regenerate": regenerate,
            "completed_at": end_time
        }
        
    except Exception as e:
        logger.error(f"Error in batch topic analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing batch topic analysis: {str(e)}"
        )


@router.get("/analytics/topics/overview", response_model=TopicOverviewResponse, tags=["analytics"])
async def get_topic_overview(db: Session = Depends(get_session)):
    """
    Get comprehensive topic modeling overview.
    
    Provides overall topic analysis metrics including:
    - Total topics and message assignments
    - Analysis coverage (percentage of messages with topics)
    - Top topics by message count
    - Most trending topics by score
    - Average topic coherence quality
    
    **Returns:**
    - Complete topic modeling overview
    - Top performing topics
    - Trending topics analysis
    - System coverage metrics
    """
    try:
        overview_data = topic_analyzer.get_topic_overview(db)
        
        return TopicOverviewResponse(
            total_topics=overview_data["total_topics"],
            total_assignments=overview_data["total_assignments"],
            total_messages=overview_data["total_messages"],
            coverage=overview_data["coverage"],
            messages_with_topics=overview_data.get("messages_with_topics", 0),
            needs_analysis=overview_data["needs_analysis"],
            top_topics=overview_data["top_topics"],
            trending_topics=overview_data["trending_topics"],
            avg_coherence=overview_data["avg_coherence"]
        )
        
    except Exception as e:
        logger.error(f"Error getting topic overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving topic overview: {str(e)}"
        )


@router.get("/analytics/topics/trending", response_model=TrendingTopicsResponse, tags=["analytics"])
async def get_trending_topics(
    days: int = 7,
    limit: int = 10,
    db: Session = Depends(get_session)
):
    """
    Get trending topics for political messaging analysis.
    
    Analyzes topic trends over time periods with:
    - Topic popularity and growth rates
    - Recent message activity per topic
    - Trending score calculations
    - Topic keyword extraction
    - Time-based trend analysis
    
    **Parameters:**
    - `days`: Number of days to analyze (default: 7, max: 90)
    - `limit`: Maximum number of topics to return (default: 10, max: 50)
    
    **Returns:**
    - Trending topics with scores and growth rates
    - Recent activity metrics
    - Topic keywords and descriptions
    - Time period statistics
    """
    try:
        if days > 90:
            days = 90
        if limit > 50:
            limit = 50
            
        trending_data = topic_analyzer.get_trending_topics(db, days=days, limit=limit)
        
        return TrendingTopicsResponse(
            time_period_days=trending_data["time_period_days"],
            trending_topics=trending_data["trending_topics"],
            total_topics=trending_data["total_topics"],
            active_topics=trending_data["active_topics"],
            analysis_date=trending_data["analysis_date"]
        )
        
    except Exception as e:
        logger.error(f"Error getting trending topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving trending topics: {str(e)}"
        )


@router.get("/analytics/topics/trends", response_model=TopicTrendsResponse, tags=["analytics"])
async def get_topic_trends(
    days: int = 30,
    topic_id: Optional[int] = None,
    db: Session = Depends(get_session)
):
    """
    Get topic trends over time for visualization.
    
    Analyzes topic activity patterns across time periods with:
    - Daily topic message counts
    - Topic probability trends
    - Individual or all topics analysis
    - Time-series data for dashboard charts
    
    **Parameters:**
    - `days`: Number of days to analyze (default: 30, max: 365)
    - `topic_id` (optional): Analyze specific topic only
    
    **Returns:**
    - Daily topic activity data
    - Topic summary information
    - Time-series trend data for visualizations
    """
    try:
        if days > 365:
            days = 365
            
        trends_data = topic_analyzer.get_topic_trends_over_time(
            db, 
            topic_id=topic_id, 
            days=days
        )
        
        return TopicTrendsResponse(
            time_period_days=trends_data["time_period_days"],
            daily_data=trends_data["daily_data"],
            topics_summary=trends_data["topics_summary"],
            analysis_date=trends_data["analysis_date"]
        )
        
    except Exception as e:
        logger.error(f"Error getting topic trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving topic trends: {str(e)}"
        )


@router.get("/analytics/topics/candidates", response_model=CandidateTopicsResponse, tags=["analytics"])
async def get_candidate_topics(
    limit: int = 20,
    db: Session = Depends(get_session)
):
    """
    Get topic distribution analysis by candidate.
    
    Analyzes how different candidates focus on various political topics:
    - Topic distribution per candidate
    - Candidate messaging diversity
    - Top topics for each candidate
    - Message count analysis
    
    **Parameters:**
    - `limit`: Maximum number of candidates to analyze (default: 20, max: 100)
    
    **Returns:**
    - Candidate topic distribution data
    - Topic diversity metrics
    - Top topics per candidate
    """
    try:
        if limit > 100:
            limit = 100
            
        candidate_data = topic_analyzer.get_candidate_topic_analysis(db, limit=limit)
        
        return CandidateTopicsResponse(
            candidate_topic_analysis=candidate_data["candidate_topic_analysis"],
            total_candidates_analyzed=candidate_data["total_candidates_analyzed"],
            analysis_date=candidate_data["analysis_date"]
        )
        
    except Exception as e:
        logger.error(f"Error getting candidate topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving candidate topics: {str(e)}"
        )


@router.get("/analytics/topics/sentiment", response_model=TopicSentimentResponse, tags=["analytics"])
async def get_topic_sentiment_correlation(db: Session = Depends(get_session)):
    """
    Get topic-sentiment correlation analysis.
    
    Analyzes the relationship between political topics and sentiment:
    - Average sentiment per topic
    - Sentiment distribution by topic (positive/negative/neutral)
    - Topic-based emotional analysis
    - Correlation insights between issues and public sentiment
    
    **Returns:**
    - Topic sentiment correlations
    - Sentiment distribution per topic
    - Emotional content analysis by topic
    - Statistical insights
    """
    try:
        correlation_data = topic_analyzer.get_topic_sentiment_analysis(db)
        
        return TopicSentimentResponse(
            topic_sentiment_analysis=correlation_data["topic_sentiment_analysis"],
            total_topics_analyzed=correlation_data["total_topics_analyzed"],
            analysis_date=correlation_data["analysis_date"]
        )
        
    except Exception as e:
        logger.error(f"Error getting topic sentiment correlation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving topic sentiment correlation: {str(e)}"
        )


@router.get("/analytics/topics/list", tags=["analytics"])
async def list_all_topics(db: Session = Depends(get_session)):
    """
    List all available political topics.
    
    Returns information about all configured political topics including:
    - Topic names and descriptions
    - Keywords and key phrases
    - Message counts and statistics
    - Topic coherence scores
    - Trending information
    
    **Returns:**
    - Complete list of political topics
    - Topic metadata and statistics
    - Keywords and descriptions
    """
    try:
        topics = db.query(TopicModel).all()
        
        return {
            "topics": [
                {
                    "id": topic.id,
                    "topic_name": topic.topic_name,
                    "topic_number": topic.topic_number,
                    "description": topic.description,
                    "keywords": topic.keywords,
                    "message_count": topic.message_count,
                    "coherence_score": topic.coherence_score,
                    "trend_score": topic.trend_score,
                    "growth_rate": topic.growth_rate,
                    "avg_sentiment": topic.avg_sentiment,
                    "created_at": topic.created_at,
                    "last_updated": topic.last_updated
                }
                for topic in topics
            ],
            "total_topics": len(topics)
        }
        
    except Exception as e:
        logger.error(f"Error listing topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving topics list: {str(e)}"
        )


# ===== ENGAGEMENT ANALYSIS ENDPOINTS =====

@router.post("/analytics/engagement/analyze", response_model=EngagementAnalysisResponse)
async def analyze_message_engagement(
    request: EngagementAnalysisRequest,
    use_dummy: bool = Query(True, description="Use dummy engagement data for testing"),
    db: Session = Depends(get_session)
):
    """Analyze engagement metrics for a message."""
    try:
        # Validate input
        if not request.message_id and not request.content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either message_id or content must be provided"
            )
        
        if request.message_id:
            # Analyze existing message
            try:
                message = db.query(Message).filter(Message.id == request.message_id).first()
            except Exception as e:
                logger.error(f"Database error when finding message: {e}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Message not found"
                )
            
            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Message not found"
                )
            
            engagement_metrics = engagement_analyzer.analyze_message_engagement(
                db, message, use_dummy=use_dummy
            )
            
            return EngagementAnalysisResponse(
                message_id=message.id,
                content_preview=message.content[:200] + "..." if len(message.content) > 200 else message.content,
                engagement_score=engagement_metrics.engagement_score,
                virality_score=engagement_metrics.virality_score,
                influence_score=engagement_metrics.influence_score,
                platform_metrics=engagement_metrics.platform_metrics,
                reach_metrics=engagement_metrics.reach_metrics,
                interaction_quality=engagement_metrics.interaction_quality,
                audience_relevance=engagement_metrics.audience_relevance,
                platform_percentile=engagement_metrics.platform_percentile,
                candidate_percentile=engagement_metrics.candidate_percentile,
                engagement_velocity=engagement_metrics.engagement_velocity,
                analysis_method=engagement_metrics.calculation_method,
                analyzed_at=engagement_metrics.calculated_at
            )
        
        else:
            # Analyze provided content (demo mode)
            dummy_message = Message(
                content=request.content,
                source=Source(source_type="demo", name="Demo Source"),
                published_at=datetime.now()
            )
            
            dummy_data = engagement_analyzer.generate_dummy_engagement_data(dummy_message)
            platform_metrics = dummy_data['platform_metrics']
            reach_metrics = dummy_data['reach_metrics']
            
            engagement_score = engagement_analyzer.calculate_engagement_score(platform_metrics, "demo")
            virality_score = engagement_analyzer.calculate_virality_score(platform_metrics, timedelta(hours=2))
            influence_score = engagement_analyzer.calculate_influence_score(engagement_score, reach_metrics)
            
            return EngagementAnalysisResponse(
                content_preview=request.content[:200] + "..." if len(request.content) > 200 else request.content,
                engagement_score=engagement_score,
                virality_score=virality_score,
                influence_score=influence_score,
                platform_metrics=platform_metrics,
                reach_metrics=reach_metrics,
                interaction_quality=dummy_data['interaction_quality'],
                audience_relevance=dummy_data['audience_relevance'],
                platform_percentile=random.uniform(20, 90),
                candidate_percentile=random.uniform(15, 95),
                engagement_velocity=random.uniform(1, 50),
                analysis_method="dummy_demo",
                analyzed_at=datetime.now()
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing engagement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing engagement: {str(e)}"
        )


@router.post("/analytics/engagement/batch", response_model=EngagementBatchResponse)
async def batch_engagement_analysis(
    use_dummy: bool = Query(True, description="Use dummy engagement data"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum messages to analyze"),
    regenerate: bool = Query(False, description="Regenerate existing engagement data"),
    db: Session = Depends(get_session)
):
    """Analyze engagement for multiple messages in batch."""
    try:
        start_time = time.time()
        
        # Apply limit cap
        limit = min(limit, 1000)
        
        if regenerate:
            # Clear existing engagement data
            db.query(EngagementMetrics).delete()
            db.commit()
        
        analyzed_count = engagement_analyzer.analyze_engagement_in_messages(
            db, use_dummy=use_dummy, limit=limit
        )
        
        processing_time = time.time() - start_time
        
        return EngagementBatchResponse(
            status="success",
            analyzed_count=analyzed_count,
            processing_time_seconds=round(processing_time, 2),
            analysis_method="dummy_generator" if use_dummy else "real_data",
            batch_limit=limit,
            regenerate=regenerate
        )
        
    except Exception as e:
        logger.error(f"Error in batch engagement analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in batch engagement analysis: {str(e)}"
        )


@router.get("/analytics/engagement/overview", response_model=EngagementOverviewResponse)
async def get_engagement_overview(db: Session = Depends(get_session)):
    """Get engagement analysis overview and statistics."""
    try:
        overview_data = engagement_analyzer.get_engagement_overview(db)
        
        return EngagementOverviewResponse(
            total_messages=overview_data["total_messages"],
            analyzed_messages=overview_data["analyzed_messages"],
            coverage=overview_data["coverage"],
            needs_analysis=overview_data["needs_analysis"],
            avg_engagement=overview_data["avg_engagement"],
            avg_virality=overview_data["avg_virality"],
            avg_influence=overview_data["avg_influence"],
            top_performing=overview_data["top_performing"]
        )
        
    except Exception as e:
        logger.error(f"Error getting engagement overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving engagement overview: {str(e)}"
        )


@router.get("/analytics/engagement/platforms", response_model=PlatformPerformanceResponse)
async def get_platform_performance(db: Session = Depends(get_session)):
    """Get platform performance comparison."""
    try:
        platform_data = engagement_analyzer.get_platform_performance_comparison(db)
        
        return PlatformPerformanceResponse(
            platform_comparison=platform_data["platform_comparison"],
            total_platforms=platform_data["total_platforms"],
            analysis_date=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting platform performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving platform performance: {str(e)}"
        )


@router.get("/analytics/engagement/viral", response_model=ViralContentResponse)
async def get_viral_content(
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Virality score threshold"),
    db: Session = Depends(get_session)
):
    """Get viral content analysis."""
    try:
        viral_data = engagement_analyzer.get_viral_content_analysis(db, threshold)
        
        return ViralContentResponse(
            viral_threshold=viral_data["viral_threshold"],
            viral_messages_found=viral_data["viral_messages_found"],
            viral_content=viral_data["viral_content"],
            analysis_date=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting viral content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving viral content: {str(e)}"
        )


@router.get("/analytics/engagement/candidates", response_model=CandidateEngagementResponse)
async def get_candidate_engagement(
    limit: int = Query(20, ge=1, le=100, description="Maximum candidates to analyze"),
    db: Session = Depends(get_session)
):
    """Get engagement analysis by candidate."""
    try:
        candidate_data = engagement_analyzer.get_candidate_engagement_analysis(db, limit)
        
        return CandidateEngagementResponse(
            candidate_engagement_analysis=candidate_data["candidate_engagement_analysis"],
            total_candidates_analyzed=candidate_data["total_candidates_analyzed"],
            analysis_date=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting candidate engagement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving candidate engagement: {str(e)}"
        )


@router.get("/analytics/engagement/trends", response_model=EngagementTrendsResponse)
async def get_engagement_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_session)
):
    """Get engagement trends over time."""
    try:
        trends_data = engagement_analyzer.get_engagement_trends_over_time(db, days)
        
        return EngagementTrendsResponse(
            time_period_days=trends_data["time_period_days"],
            daily_data=trends_data["daily_data"],
            trends_summary=trends_data["trends_summary"],
            analysis_date=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting engagement trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving engagement trends: {str(e)}"
        )


# ===== INTELLIGENCE REPORT ENDPOINTS =====

@router.post("/analytics/reports/generate", response_model=IntelligenceReportResponse)
async def generate_intelligence_report(
    request: ReportGenerationRequest,
    db: Session = Depends(get_session)
):
    """
    Generate comprehensive intelligence reports combining all analytics.
    
    Creates multi-source intelligence reports with:
    - Sentiment, topic, and engagement analysis integration
    - Multiple report types (daily_brief, weekly_summary, etc.)
    - Time-based filtering and analysis
    - Executive summaries and actionable recommendations
    - Export capabilities in JSON and Markdown formats
    
    **Report Types:**
    - `daily_brief`: Focused daily intelligence summary
    - `weekly_summary`: Comprehensive weekly analysis
    - `monthly_analysis`: Extended monthly intelligence report
    - `campaign_overview`: Complete campaign messaging analysis
    - `candidate_profile`: Individual candidate focus analysis
    - `issue_tracker`: Topic-specific messaging tracking
    - `comparative_analysis`: Multi-entity comparison report
    
    **Parameters:**
    - `report_type`: Type of intelligence report to generate
    - `time_period_days`: Analysis period (1-365 days)
    - `entity_filter` (optional): Filter by candidate_id, source_type, etc.
    - `export_format`: Output format (json, markdown)
    
    **Returns:**
    - Complete intelligence report with executive summary
    - Multi-section analysis breakdown
    - Actionable recommendations
    - Data sources and methodology information
    """
    try:
        # Validate report type
        try:
            report_type_enum = ReportType(request.report_type)
        except ValueError:
            valid_types = [rt.value for rt in ReportType]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report_type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Generate the intelligence report
        report = intelligence_generator.generate_report(
            db=db,
            report_type=report_type_enum,
            time_period_days=request.time_period_days,
            entity_filter=request.entity_filter
        )
        
        # Convert sections to response format
        response_sections = []
        for section in report.sections:
            response_sections.append(ReportSectionResponse(
                title=section.title,
                content=section.content,
                data=section.data,
                visualizations=section.visualizations,
                priority=section.priority
            ))
        
        # Format time period for response
        time_period_formatted = {
            "start": report.time_period["start"].isoformat(),
            "end": report.time_period["end"].isoformat()
        }
        
        return IntelligenceReportResponse(
            report_id=report.report_id,
            report_type=report.report_type.value,
            title=report.title,
            executive_summary=report.executive_summary,
            generated_at=report.generated_at,
            time_period=time_period_formatted,
            sections=response_sections,
            metadata=report.metadata,
            recommendations=report.recommendations,
            data_sources=report.data_sources
        )
        
    except HTTPException:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Error generating intelligence report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating intelligence report: {str(e)}"
        )


@router.get("/analytics/reports/list", response_model=ReportListResponse)
async def list_intelligence_reports(
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum reports to return"),
    db: Session = Depends(get_session)
):
    """
    List available intelligence reports.
    
    Returns information about previously generated intelligence reports:
    - Report metadata and generation timestamps
    - Report type and time period information
    - Executive summary previews
    - Available export formats
    
    **Parameters:**
    - `report_type` (optional): Filter by specific report type
    - `limit`: Maximum number of reports to return
    
    **Returns:**
    - List of available reports with metadata
    - Report type information and statistics
    - Summary data for quick reference
    
    Note: This endpoint currently provides a simulated response since report 
    persistence is not implemented in the current version.
    """
    try:
        # For now, return example data as report persistence is not implemented
        # In a full implementation, this would query a reports table
        
        available_report_types = [rt.value for rt in ReportType]
        
        # Generate some example report metadata
        example_reports = []
        for i, report_type_value in enumerate(available_report_types[:limit]):
            example_reports.append({
                "report_id": f"{report_type_value}_{datetime.now().strftime('%Y%m%d')}_{i:03d}",
                "report_type": report_type_value,
                "title": f"{report_type_value.replace('_', ' ').title()} Report",
                "generated_at": (datetime.now() - timedelta(days=i)).isoformat(),
                "time_period_days": 7 if "daily" in report_type_value else 30,
                "summary": f"Generated {report_type_value} intelligence report with multi-source analytics.",
                "data_sources": ["sentiment_analysis", "topic_modeling", "engagement_metrics"],
                "sections_count": 4 + (i % 3),
                "export_formats": ["json", "markdown"]
            })
        
        # Filter by report type if specified
        if report_type:
            example_reports = [r for r in example_reports if r["report_type"] == report_type]
        
        return ReportListResponse(
            reports=example_reports,
            total_reports=len(example_reports),
            report_types=available_report_types
        )
        
    except Exception as e:
        logger.error(f"Error listing intelligence reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving intelligence reports list: {str(e)}"
        )


@router.get("/analytics/reports/{report_id}", response_model=IntelligenceReportResponse)
async def get_intelligence_report(
    report_id: str,
    db: Session = Depends(get_session)
):
    """
    Retrieve a specific intelligence report by ID.
    
    Returns the complete intelligence report including:
    - Full report content and sections
    - Executive summary and recommendations
    - Analysis metadata and data sources
    - Generation timestamp and parameters
    
    **Parameters:**
    - `report_id`: Unique identifier for the intelligence report
    
    **Returns:**
    - Complete intelligence report data
    - All sections with analysis content
    - Recommendations and insights
    - Report metadata
    
    **Errors:**
    - `404`: Report not found
    
    Note: This endpoint currently regenerates reports as report persistence 
    is not implemented in the current version.
    """
    try:
        # Parse report ID to extract type and parameters
        # Format: {report_type}_{date}_{sequence}
        parts = report_id.split('_')
        if len(parts) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid report_id format"
            )
        
        report_type_str = '_'.join(parts[:-2]) if len(parts) > 2 else parts[0]
        
        try:
            report_type_enum = ReportType(report_type_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # For demonstration, regenerate the report
        # In a full implementation, this would retrieve from storage
        report = intelligence_generator.generate_report(
            db=db,
            report_type=report_type_enum,
            time_period_days=7,  # Default parameters
            entity_filter=None
        )
        
        # Override report ID to match requested
        report.report_id = report_id
        
        # Convert sections to response format
        response_sections = []
        for section in report.sections:
            response_sections.append(ReportSectionResponse(
                title=section.title,
                content=section.content,
                data=section.data,
                visualizations=section.visualizations,
                priority=section.priority
            ))
        
        # Format time period for response
        time_period_formatted = {
            "start": report.time_period["start"].isoformat(),
            "end": report.time_period["end"].isoformat()
        }
        
        return IntelligenceReportResponse(
            report_id=report.report_id,
            report_type=report.report_type.value,
            title=report.title,
            executive_summary=report.executive_summary,
            generated_at=report.generated_at,
            time_period=time_period_formatted,
            sections=response_sections,
            metadata=report.metadata,
            recommendations=report.recommendations,
            data_sources=report.data_sources
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving intelligence report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving intelligence report: {str(e)}"
        )


@router.get("/analytics/reports/{report_id}/export", response_model=ReportExportResponse)
async def export_intelligence_report(
    report_id: str,
    format: str = Query("json", description="Export format: json or markdown"),
    db: Session = Depends(get_session)
):
    """
    Export intelligence report in specified format.
    
    Exports complete intelligence reports with:
    - JSON format for programmatic access and integration
    - Markdown format for documentation and sharing
    - Formatted content with proper structure
    - Metadata and generation information
    
    **Parameters:**
    - `report_id`: Unique identifier for the intelligence report
    - `format`: Export format (json, markdown)
    
    **Returns:**
    - Exported report content in requested format
    - Suggested filename for download
    - Export metadata and timing
    
    **Supported Formats:**
    - `json`: Structured JSON data for API integration
    - `markdown`: Formatted Markdown for documentation
    
    **Errors:**
    - `404`: Report not found
    - `400`: Invalid export format
    """
    try:
        # Validate export format
        if format not in ["json", "markdown"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid export format. Must be 'json' or 'markdown'"
            )
        
        # Parse report ID to extract type and parameters
        parts = report_id.split('_')
        if len(parts) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid report_id format"
            )
        
        report_type_str = '_'.join(parts[:-2]) if len(parts) > 2 else parts[0]
        
        try:
            report_type_enum = ReportType(report_type_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Generate the report (in full implementation, retrieve from storage)
        report = intelligence_generator.generate_report(
            db=db,
            report_type=report_type_enum,
            time_period_days=7,
            entity_filter=None
        )
        
        # Override report ID to match requested
        report.report_id = report_id
        
        # Export in requested format
        if format == "json":
            content = intelligence_generator.export_report_json(report)
            filename = f"{report_id}.json"
        else:  # markdown
            content = intelligence_generator.export_report_markdown(report)
            filename = f"{report_id}.md"
        
        return ReportExportResponse(
            report_id=report_id,
            export_format=format,
            content=content,
            filename=filename,
            generated_at=datetime.now()
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error exporting intelligence report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting intelligence report: {str(e)}"
        )


# ===== SEARCH ENDPOINTS =====

@router.post("/search", tags=["search"])
def search_content(
    search_request: SearchRequest,
    db: Session = Depends(get_session)
) -> SearchResponse:
    """
    Search across messages, keywords, candidates, and sources.
    
    Supports full-text search with filters for:
    - Content type (messages, keywords, candidates, sources)
    - Source platforms (website, twitter, facebook, meta_ads)
    - Date ranges
    - Sentiment filtering
    - Geographic scope
    - Specific candidates
    """
    start_time = time.time()
    
    try:
        results = {}
        total_results = 0
        
        query_lower = search_request.query.lower()
        
        # Search Messages
        if "messages" in search_request.search_types:
            message_results = search_messages(db, search_request, query_lower)
            results["messages"] = {
                "count": len(message_results),
                "items": message_results
            }
            total_results += len(message_results)
        
        # Search Keywords
        if "keywords" in search_request.search_types:
            keyword_results = search_keywords(db, search_request, query_lower)
            results["keywords"] = {
                "count": len(keyword_results),
                "items": keyword_results
            }
            total_results += len(keyword_results)
        
        # Search Candidates
        if "candidates" in search_request.search_types:
            candidate_results = search_candidates(db, search_request, query_lower)
            results["candidates"] = {
                "count": len(candidate_results),
                "items": candidate_results
            }
            total_results += len(candidate_results)
        
        # Search Sources
        if "sources" in search_request.search_types:
            source_results = search_sources(db, search_request, query_lower)
            results["sources"] = {
                "count": len(source_results),
                "items": source_results
            }
            total_results += len(source_results)
        
        search_time_ms = (time.time() - start_time) * 1000
        
        return SearchResponse(
            query=search_request.query,
            total_results=total_results,
            search_time_ms=round(search_time_ms, 2),
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {str(e)}"
        )


@router.post("/search/autocomplete", tags=["search"])
def search_autocomplete(
    autocomplete_request: AutocompleteRequest,
    db: Session = Depends(get_session)
) -> AutocompleteResponse:
    """
    Provide autocomplete suggestions for search queries.
    
    Returns suggestions based on:
    - Popular keywords
    - Candidate names
    - Source names
    - Common phrases
    """
    try:
        suggestions = []
        query_lower = autocomplete_request.query.lower()
        
        if autocomplete_request.search_type in ["all", "keywords"]:
            # Get keyword suggestions
            keyword_suggestions = db.query(Keyword.keyword, func.count(Keyword.id).label('count'))\
                .filter(Keyword.keyword.ilike(f'%{query_lower}%'))\
                .group_by(Keyword.keyword)\
                .order_by(func.count(Keyword.id).desc())\
                .limit(autocomplete_request.limit // 2)\
                .all()
            
            for kw, count in keyword_suggestions:
                suggestions.append({
                    "text": kw,
                    "type": "keyword",
                    "count": count
                })
        
        if autocomplete_request.search_type in ["all", "candidates"]:
            # Get candidate suggestions
            candidate_suggestions = db.query(Candidate.name)\
                .filter(Candidate.name.ilike(f'%{query_lower}%'))\
                .limit(autocomplete_request.limit // 3)\
                .all()
            
            for (name,) in candidate_suggestions:
                suggestions.append({
                    "text": name,
                    "type": "candidate",
                    "count": 1
                })
        
        if autocomplete_request.search_type in ["all", "sources"]:
            # Get source suggestions
            source_suggestions = db.query(Source.name)\
                .filter(Source.name.ilike(f'%{query_lower}%'))\
                .limit(autocomplete_request.limit // 3)\
                .all()
            
            for (name,) in source_suggestions:
                suggestions.append({
                    "text": name,
                    "type": "source", 
                    "count": 1
                })
        
        # Sort by count and limit
        suggestions = sorted(suggestions, key=lambda x: x["count"], reverse=True)
        suggestions = suggestions[:autocomplete_request.limit]
        
        return AutocompleteResponse(
            query=autocomplete_request.query,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Error generating autocomplete suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Autocomplete error: {str(e)}"
        )


def search_messages(db: Session, search_request: SearchRequest, query_lower: str) -> List[MessageSearchResult]:
    """Search for messages matching the query."""
    query = db.query(Message).join(Source)
    
    # Apply text search
    query = query.filter(Message.content.ilike(f'%{query_lower}%'))
    
    # Apply filters
    if search_request.source_types:
        query = query.filter(Source.source_type.in_(search_request.source_types))
    
    if search_request.candidate_ids:
        query = query.filter(Message.candidate_id.in_(search_request.candidate_ids))
    
    if search_request.date_from:
        query = query.filter(Message.published_at >= search_request.date_from)
    
    if search_request.date_to:
        query = query.filter(Message.published_at <= search_request.date_to)
    
    if search_request.geographic_scope:
        query = query.filter(Message.geographic_scope == search_request.geographic_scope)
    
    # Add sentiment filter if provided
    if search_request.sentiment_filter:
        query = query.join(MessageSentiment, isouter=True)\
            .filter(MessageSentiment.sentiment_label == search_request.sentiment_filter)
    
    # Order by relevance (published date for now, could be enhanced with full-text search scoring)
    query = query.order_by(Message.published_at.desc())
    
    messages = query.limit(search_request.limit).all()
    
    results = []
    for message in messages:
        # Get keywords for this message
        keywords = [kw.keyword for kw in message.keywords[:5]]  # Limit to top 5 keywords
        
        # Get sentiment data if available
        sentiment_score = None
        sentiment_label = None
        if message.sentiment_analysis:
            sentiment_score = message.sentiment_analysis.sentiment_score
            sentiment_label = message.sentiment_analysis.sentiment_label
        
        # Calculate relevance score (simple keyword matching for now)
        relevance_score = calculate_relevance_score(message.content, search_request.query)
        
        # Create preview (first 200 chars)
        content_preview = message.content[:200] + "..." if len(message.content) > 200 else message.content
        
        results.append(MessageSearchResult(
            message_id=message.id,
            content=message.content[:1000],  # Truncate very long content
            content_preview=content_preview,
            url=message.url,
            published_at=message.published_at,
            source_name=message.source.name,
            source_type=message.source.source_type,
            candidate_name=message.candidate.name if message.candidate else None,
            message_type=message.message_type,
            geographic_scope=message.geographic_scope,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            keywords=keywords,
            relevance_score=relevance_score
        ))
    
    # Sort by relevance score
    results.sort(key=lambda x: x.relevance_score, reverse=True)
    return results


def search_keywords(db: Session, search_request: SearchRequest, query_lower: str) -> List[KeywordSearchResult]:
    """Search for keywords matching the query."""
    query = db.query(Keyword.keyword, 
                    func.count(Keyword.id).label('message_count'),
                    func.avg(Keyword.confidence).label('avg_confidence'),
                    Keyword.extraction_method)\
        .filter(Keyword.keyword.ilike(f'%{query_lower}%'))\
        .group_by(Keyword.keyword, Keyword.extraction_method)\
        .order_by(func.count(Keyword.id).desc())\
        .limit(search_request.limit)
    
    keyword_data = query.all()
    
    results = []
    for keyword, message_count, avg_confidence, extraction_method in keyword_data:
        # Get recent messages with this keyword
        recent_messages = db.query(Message)\
            .join(Keyword)\
            .filter(Keyword.keyword == keyword)\
            .order_by(Message.published_at.desc())\
            .limit(3)\
            .all()
        
        recent_messages_data = []
        for msg in recent_messages:
            recent_messages_data.append({
                "message_id": msg.id,
                "content_preview": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                "published_at": msg.published_at.isoformat() if msg.published_at else None,
                "source_name": msg.source.name
            })
        
        results.append(KeywordSearchResult(
            keyword=keyword,
            message_count=message_count,
            confidence=round(avg_confidence or 0.0, 3),
            extraction_method=extraction_method,
            recent_messages=recent_messages_data
        ))
    
    return results


def search_candidates(db: Session, search_request: SearchRequest, query_lower: str) -> List[CandidateSearchResult]:
    """Search for candidates matching the query."""
    query = db.query(Candidate).join(Constituency, isouter=True)\
        .filter(Candidate.name.ilike(f'%{query_lower}%'))\
        .limit(search_request.limit)
    
    candidates = query.all()
    
    results = []
    for candidate in candidates:
        # Get message statistics
        message_count = db.query(func.count(Message.id))\
            .filter(Message.candidate_id == candidate.id)\
            .scalar() or 0
        
        # Get recent message count (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_message_count = db.query(func.count(Message.id))\
            .filter(Message.candidate_id == candidate.id,
                   Message.published_at >= thirty_days_ago)\
            .scalar() or 0
        
        # Get average sentiment
        avg_sentiment = db.query(func.avg(MessageSentiment.sentiment_score))\
            .join(Message)\
            .filter(Message.candidate_id == candidate.id)\
            .scalar()
        
        # Get top keywords
        top_keywords = db.query(Keyword.keyword)\
            .join(Message)\
            .filter(Message.candidate_id == candidate.id)\
            .group_by(Keyword.keyword)\
            .order_by(func.count(Keyword.id).desc())\
            .limit(5)\
            .all()
        
        top_keywords_list = [kw[0] for kw in top_keywords]
        
        results.append(CandidateSearchResult(
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            constituency_name=candidate.constituency.name if candidate.constituency else None,
            constituency_region=candidate.constituency.region if candidate.constituency else None,
            message_count=message_count,
            recent_message_count=recent_message_count,
            social_media_accounts=candidate.social_media_accounts,
            avg_sentiment=round(avg_sentiment, 3) if avg_sentiment else None,
            top_keywords=top_keywords_list
        ))
    
    return results


def search_sources(db: Session, search_request: SearchRequest, query_lower: str) -> List[SourceSearchResult]:
    """Search for sources matching the query."""
    query = db.query(Source)\
        .filter(Source.name.ilike(f'%{query_lower}%'))
    
    if search_request.source_types:
        query = query.filter(Source.source_type.in_(search_request.source_types))
    
    sources = query.limit(search_request.limit).all()
    
    results = []
    for source in sources:
        # Get message count
        message_count = db.query(func.count(Message.id))\
            .filter(Message.source_id == source.id)\
            .scalar() or 0
        
        # Get last activity
        last_activity = db.query(func.max(Message.published_at))\
            .filter(Message.source_id == source.id)\
            .scalar()
        
        results.append(SourceSearchResult(
            source_id=source.id,
            source_name=source.name,
            source_type=source.source_type,
            source_url=source.url,
            message_count=message_count,
            last_activity=last_activity,
            active=source.active
        ))
    
    return results


def calculate_relevance_score(content: str, query: str) -> float:
    """Calculate a simple relevance score based on keyword matching."""
    content_lower = content.lower()
    query_terms = query.lower().split()
    
    total_score = 0.0
    for term in query_terms:
        # Count occurrences of each term
        count = content_lower.count(term)
        # Weight by term length to favor longer, more specific terms
        term_weight = len(term) / 10.0
        total_score += count * term_weight
    
    # Normalize by content length to prevent bias toward longer content
    content_length_factor = min(len(content) / 1000.0, 1.0)
    relevance_score = total_score / (1.0 + content_length_factor)
    
    # Cap at 1.0
    return min(relevance_score, 1.0)
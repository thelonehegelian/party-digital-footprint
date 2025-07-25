"""
Political sentiment analysis engine for Reform UK messaging data.

This module provides sentiment analysis capabilities specifically tuned for political content,
including basic sentiment scoring, political tone analysis, and emotional categorization.
"""

import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from textblob import TextBlob

from ..models import Message, MessageSentiment, SentimentResult


class PoliticalSentimentAnalyzer:
    """
    Sentiment analysis engine for political messaging content.
    
    Features:
    - Basic sentiment analysis (positive/negative/neutral)
    - Political tone detection (aggressive, diplomatic, populist)
    - Emotional categorization (anger, hope, fear, pride)
    - Confidence scoring for all classifications
    """
    
    def __init__(self):
        """Initialize the sentiment analyzer."""
        self.political_keywords = {
            'aggressive': [
                'fight', 'battle', 'war', 'destroy', 'crush', 'attack', 'defeat', 'enemy',
                'betrayal', 'disaster', 'crisis', 'fail', 'broken', 'corrupt', 'lies'
            ],
            'diplomatic': [
                'negotiate', 'discuss', 'consider', 'dialogue', 'cooperation', 'partnership',
                'balance', 'understanding', 'respect', 'compromise', 'collaboration'
            ],
            'populist': [
                'people', 'ordinary', 'working', 'families', 'elite', 'establishment',
                'common sense', 'real', 'hardworking', 'forgotten', 'betrayed', 'left behind'
            ],
            'nationalist': [
                'britain', 'british', 'country', 'nation', 'sovereignty', 'independence',
                'control', 'borders', 'immigration', 'patriot', 'heritage', 'identity'
            ]
        }
        
        self.emotion_keywords = {
            'anger': [
                'outrage', 'furious', 'angry', 'disgusted', 'sick', 'fed up', 'enough',
                'betrayed', 'cheated', 'lied to', 'insulted', 'ignored'
            ],
            'fear': [
                'worried', 'concerned', 'afraid', 'scared', 'threatening', 'dangerous',
                'risk', 'threat', 'unsafe', 'vulnerable', 'crisis', 'collapse'
            ],
            'hope': [
                'future', 'better', 'improve', 'progress', 'opportunity', 'potential',
                'optimistic', 'confident', 'believe', 'achieve', 'success', 'bright'
            ],
            'pride': [
                'proud', 'great', 'achievement', 'success', 'excellence', 'strong',
                'winning', 'victory', 'champion', 'best', 'superior', 'leading'
            ]
        }
    
    def analyze_message_sentiment(self, content: str) -> SentimentResult:
        """
        Analyze sentiment of a single political message.
        
        Args:
            content: Message content to analyze
            
        Returns:
            SentimentResult with sentiment score, label, tone, and emotions
        """
        # Basic sentiment analysis using TextBlob
        blob = TextBlob(content)
        sentiment_score = blob.sentiment.polarity  # -1 to 1
        
        # Classify sentiment label
        if sentiment_score > 0.1:
            sentiment_label = "positive"
        elif sentiment_score < -0.1:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        # Calculate confidence based on absolute score
        confidence = min(abs(sentiment_score) + 0.3, 1.0)
        
        # Analyze political tone
        political_tone, tone_confidence = self._analyze_political_tone(content)
        
        # Analyze emotions
        emotions = self._analyze_emotions(content)
        
        return SentimentResult(
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            confidence=confidence,
            political_tone=political_tone,
            tone_confidence=tone_confidence,
            emotions=emotions,
            analysis_method="textblob_political"
        )
    
    def _analyze_political_tone(self, content: str) -> Tuple[str, float]:
        """Analyze political tone of the message."""
        content_lower = content.lower()
        tone_scores = {}
        
        for tone, keywords in self.political_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                tone_scores[tone] = score / len(keywords)  # Normalize by keyword count
        
        if not tone_scores:
            return "neutral", 0.5
        
        # Get the tone with highest score
        dominant_tone = max(tone_scores.items(), key=lambda x: x[1])
        return dominant_tone[0], min(dominant_tone[1] * 2, 1.0)  # Scale confidence
    
    def _analyze_emotions(self, content: str) -> Dict[str, float]:
        """Analyze emotional content of the message."""
        content_lower = content.lower()
        emotions = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                emotions[emotion] = min(score / len(keywords) * 3, 1.0)  # Scale and cap at 1.0
        
        return emotions if emotions else {"neutral": 0.8}
    
    def generate_dummy_sentiment(self, message: Message) -> SentimentResult:
        """
        Generate realistic dummy sentiment data for testing.
        
        This creates believable sentiment patterns based on political messaging themes.
        """
        content_lower = message.content.lower()
        
        # Determine sentiment based on content themes
        negative_indicators = [
            'crisis', 'broken', 'failed', 'corrupt', 'lies', 'betrayed', 'disaster',
            'problem', 'wrong', 'bad', 'terrible', 'awful', 'destroy', 'damage'
        ]
        
        positive_indicators = [
            'great', 'excellent', 'success', 'achieve', 'win', 'better', 'improve',
            'progress', 'opportunity', 'future', 'hope', 'proud', 'strong', 'good'
        ]
        
        # Calculate base sentiment
        negative_count = sum(1 for word in negative_indicators if word in content_lower)
        positive_count = sum(1 for word in positive_indicators if word in content_lower)
        
        if positive_count > negative_count:
            sentiment_score = random.uniform(0.2, 0.8)
            sentiment_label = "positive"
        elif negative_count > positive_count:
            sentiment_score = random.uniform(-0.8, -0.2)
            sentiment_label = "negative"
        else:
            sentiment_score = random.uniform(-0.3, 0.3)
            sentiment_label = "neutral"
        
        # Add some noise for realism
        sentiment_score += random.uniform(-0.1, 0.1)
        sentiment_score = max(-1.0, min(1.0, sentiment_score))  # Clamp to [-1, 1]
        
        # Generate political tone based on content
        if any(word in content_lower for word in ['fight', 'attack', 'destroy', 'enemy']):
            political_tone = "aggressive"
            tone_confidence = random.uniform(0.6, 0.9)
        elif any(word in content_lower for word in ['people', 'working', 'families', 'elite']):
            political_tone = "populist"
            tone_confidence = random.uniform(0.5, 0.8)
        elif any(word in content_lower for word in ['britain', 'british', 'borders', 'control']):
            political_tone = "nationalist"
            tone_confidence = random.uniform(0.6, 0.9)
        else:
            political_tone = "diplomatic"
            tone_confidence = random.uniform(0.3, 0.7)
        
        # Generate emotions
        emotions = {}
        if sentiment_score < -0.3:
            emotions['anger'] = random.uniform(0.3, 0.8)
            if 'crisis' in content_lower or 'threat' in content_lower:
                emotions['fear'] = random.uniform(0.2, 0.6)
        elif sentiment_score > 0.3:
            emotions['hope'] = random.uniform(0.4, 0.9)
            if 'britain' in content_lower or 'great' in content_lower:
                emotions['pride'] = random.uniform(0.3, 0.7)
        else:
            emotions['neutral'] = random.uniform(0.5, 0.8)
        
        confidence = random.uniform(0.7, 0.95)  # High confidence for dummy data
        
        return SentimentResult(
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            confidence=confidence,
            political_tone=political_tone,
            tone_confidence=tone_confidence,
            emotions=emotions,
            analysis_method="dummy_generator"
        )
    
    def analyze_batch_messages(self, db: Session, use_dummy: bool = True, limit: int = None) -> int:
        """
        Analyze sentiment for all messages without existing sentiment data.
        
        Args:
            db: Database session
            use_dummy: If True, use dummy data generator; if False, use real TextBlob
            
        Returns:
            Number of messages analyzed
        """
        # Get messages without sentiment analysis
        query = db.query(Message)\
            .outerjoin(MessageSentiment, Message.id == MessageSentiment.message_id)\
            .filter(MessageSentiment.id.is_(None))
        
        if limit:
            query = query.limit(limit)
            
        messages_without_sentiment = query.all()
        
        analyzed_count = 0
        
        for message in messages_without_sentiment:
            # Generate sentiment analysis
            if use_dummy:
                sentiment_result = self.generate_dummy_sentiment(message)
            else:
                sentiment_result = self.analyze_message_sentiment(message.content)
            
            # Create database record
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
            analyzed_count += 1
        
        db.commit()
        return analyzed_count
    
    def get_sentiment_trends(self, db: Session, days: int = 7) -> Dict:
        """
        Get sentiment trends over time.
        
        Args:
            db: Database session
            days: Number of days to analyze
            
        Returns:
            Dictionary with sentiment trend data
        """
        from sqlalchemy import func, and_
        from datetime import timedelta
        
        # Get sentiment data from the last N days
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Query sentiment by day
        daily_sentiment = db.query(
            func.date(Message.published_at).label('date'),
            func.avg(MessageSentiment.sentiment_score).label('avg_sentiment'),
            func.count(MessageSentiment.id).label('message_count'),
            func.sum(case((MessageSentiment.sentiment_label == 'positive', 1), else_=0)).label('positive_count'),
            func.sum(case((MessageSentiment.sentiment_label == 'negative', 1), else_=0)).label('negative_count'),
            func.sum(case((MessageSentiment.sentiment_label == 'neutral', 1), else_=0)).label('neutral_count')
        ).join(Message, MessageSentiment.message_id == Message.id)\
         .filter(Message.published_at >= cutoff_date)\
         .group_by(func.date(Message.published_at))\
         .order_by(func.date(Message.published_at))\
         .all()
        
        # Format results
        trends = {
            'period_days': days,
            'daily_data': [],
            'overall_stats': {
                'avg_sentiment': 0.0,
                'total_messages': 0,
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0}
            }
        }
        
        total_sentiment = 0
        total_messages = 0
        total_positive = 0
        total_negative = 0
        total_neutral = 0
        
        for row in daily_sentiment:
            daily_data = {
                'date': str(row.date),
                'avg_sentiment': float(row.avg_sentiment or 0),
                'message_count': row.message_count,
                'positive_count': row.positive_count or 0,
                'negative_count': row.negative_count or 0,
                'neutral_count': row.neutral_count or 0
            }
            trends['daily_data'].append(daily_data)
            
            total_sentiment += daily_data['avg_sentiment'] * daily_data['message_count']
            total_messages += daily_data['message_count']
            total_positive += daily_data['positive_count']
            total_negative += daily_data['negative_count']
            total_neutral += daily_data['neutral_count']
        
        if total_messages > 0:
            trends['overall_stats'] = {
                'avg_sentiment': total_sentiment / total_messages,
                'total_messages': total_messages,
                'sentiment_distribution': {
                    'positive': total_positive,
                    'negative': total_negative,
                    'neutral': total_neutral
                }
            }
        
        return trends


# Fix the missing import for case function
from sqlalchemy import case
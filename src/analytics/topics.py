"""
Political topic modeling and trend analysis for messaging content.

This module provides topic modeling capabilities including:
- LDA-based topic extraction from political messages
- Trending topic identification and tracking  
- Political issue classification and clustering
- Dummy data generation for testing and development
"""

import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case
from collections import defaultdict
import json

from ..models import Message, Source, Candidate, TopicModel, MessageTopic


class PoliticalTopicAnalyzer:
    """
    Advanced topic modeling system for political messaging analysis.
    
    Provides comprehensive topic extraction, trend analysis, and political
    issue classification with built-in dummy data generation for testing.
    """
    
    def __init__(self):
        """Initialize the political topic analyzer."""
        # Political topic templates for dummy data generation
        self.political_topics = {
            "Immigration and Border Security": {
                "keywords": ["immigration", "border", "security", "asylum", "deportation", "migrants"],
                "description": "Policy discussions around immigration control and border security measures",
                "typical_sentiment": 0.2,
                "common_tones": ["nationalist", "populist"]
            },
            "Economic Policy": {
                "keywords": ["economy", "jobs", "taxation", "spending", "deficit", "growth"], 
                "description": "Economic policy proposals and fiscal responsibility discussions",
                "typical_sentiment": 0.1,
                "common_tones": ["populist", "diplomatic"]
            },
            "Healthcare Reform": {
                "keywords": ["healthcare", "NHS", "medical", "hospitals", "doctors", "patients"],
                "description": "Healthcare system reform and medical service improvements",
                "typical_sentiment": 0.3,
                "common_tones": ["diplomatic", "populist"]
            },
            "Education and Schools": {
                "keywords": ["education", "schools", "teachers", "students", "curriculum", "universities"],
                "description": "Educational policy and school system improvements",
                "typical_sentiment": 0.4,
                "common_tones": ["diplomatic", "populist"]
            },
            "Law and Order": {
                "keywords": ["crime", "police", "justice", "courts", "safety", "security"],
                "description": "Criminal justice system and public safety measures",
                "typical_sentiment": 0.0,
                "common_tones": ["aggressive", "nationalist"]
            },
            "European Union Relations": {
                "keywords": ["EU", "Europe", "Brexit", "sovereignty", "trade", "Brussels"],
                "description": "European Union relationships and post-Brexit policies",
                "typical_sentiment": -0.1,
                "common_tones": ["nationalist", "aggressive"]
            },
            "Climate and Environment": {
                "keywords": ["climate", "environment", "green", "carbon", "energy", "renewable"],
                "description": "Environmental policy and climate change responses",
                "typical_sentiment": 0.2,
                "common_tones": ["diplomatic", "populist"]
            },
            "Housing and Local Issues": {
                "keywords": ["housing", "planning", "development", "local", "community", "residents"],
                "description": "Housing policy and local community development",
                "typical_sentiment": 0.3,
                "common_tones": ["populist", "diplomatic"]
            },
            "Foreign Policy": {
                "keywords": ["foreign", "international", "diplomacy", "alliance", "defense", "military"],
                "description": "International relations and foreign policy positions",
                "typical_sentiment": 0.0,
                "common_tones": ["nationalist", "diplomatic"]
            },
            "Media and Democracy": {
                "keywords": ["media", "democracy", "freedom", "speech", "press", "censorship"],
                "description": "Media freedom and democratic institutions",
                "typical_sentiment": 0.1,
                "common_tones": ["populist", "aggressive"]
            }
        }
        
        # Coherence score ranges for different topic qualities
        self.coherence_ranges = {
            "high": (0.7, 0.9),
            "medium": (0.5, 0.7),
            "low": (0.3, 0.5)
        }
    
    def analyze_topics_in_messages(
        self, 
        db: Session, 
        use_dummy: bool = True,
        limit: Optional[int] = None,
        regenerate: bool = False
    ) -> int:
        """
        Analyze topics in messages using LDA or dummy data generation.
        
        Args:
            db: Database session
            use_dummy: Whether to use dummy data generation
            limit: Maximum number of messages to analyze
            regenerate: Whether to regenerate existing topic assignments
            
        Returns:
            Number of messages analyzed
        """
        # Get messages without topic analysis or regenerate all
        query = db.query(Message)
        
        if not regenerate:
            # Only get messages without existing topic assignments
            analyzed_message_ids = db.query(MessageTopic.message_id).distinct()
            query = query.filter(~Message.id.in_(analyzed_message_ids))
        
        messages = query.order_by(Message.published_at.desc())
        
        if limit:
            messages = messages.limit(limit)
        
        messages = messages.all()
        
        if not messages:
            return 0
        
        if use_dummy:
            return self._generate_dummy_topic_assignments(db, messages)
        else:
            return self._perform_real_topic_analysis(db, messages)
    
    def _generate_dummy_topic_assignments(self, db: Session, messages: List[Message]) -> int:
        """Generate realistic dummy topic assignments for testing."""
        # Ensure we have topics in the database
        self._ensure_topics_exist(db)
        
        # Get all available topics
        topics = db.query(TopicModel).all()
        if not topics:
            return 0
        
        analyzed_count = 0
        
        for message in messages:
            # Remove existing assignments if regenerating
            db.query(MessageTopic).filter(MessageTopic.message_id == message.id).delete()
            
            # Assign 1-3 topics per message with probabilities
            num_topics = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
            assigned_topics = random.sample(topics, min(num_topics, len(topics)))
            
            # Generate topic probabilities that sum to < 1.0
            probabilities = []
            remaining_prob = 0.95  # Leave some probability unassigned
            
            for i, topic in enumerate(assigned_topics):
                if i == len(assigned_topics) - 1:
                    # Last topic gets remaining probability
                    prob = remaining_prob
                else:
                    # Random probability within reasonable range
                    max_prob = min(0.7, remaining_prob - 0.1 * (len(assigned_topics) - i - 1))
                    prob = random.uniform(0.15, max_prob)
                    remaining_prob -= prob
                
                probabilities.append(prob)
            
            # Create topic assignments
            for i, (topic, probability) in enumerate(zip(assigned_topics, probabilities)):
                assignment = MessageTopic(
                    message_id=message.id,
                    topic_id=topic.id,
                    probability=probability,
                    is_primary_topic=(i == 0),  # First topic is primary
                    assigned_at=datetime.utcnow(),
                    model_version="dummy_v1.0"
                )
                db.add(assignment)
                
                # Update topic message count
                topic.message_count += 1
                topic.last_updated = datetime.utcnow()
            
            analyzed_count += 1
        
        db.commit()
        return analyzed_count
    
    def _ensure_topics_exist(self, db: Session):
        """Ensure political topics exist in the database."""
        existing_topics = {topic.topic_name for topic in db.query(TopicModel).all()}
        
        for topic_name, topic_info in self.political_topics.items():
            if topic_name not in existing_topics:
                # Generate topic keywords with weights
                keywords = []
                for i, keyword in enumerate(topic_info["keywords"]):
                    weight = 1.0 - (i * 0.1)  # Decreasing weights
                    keywords.append({"word": keyword, "weight": max(0.1, weight)})
                
                # Generate realistic topic metrics
                coherence_score = random.uniform(*self.coherence_ranges["medium"])
                trend_score = random.uniform(0.1, 0.8)
                growth_rate = random.uniform(-0.2, 0.5)
                
                topic = TopicModel(
                    topic_name=topic_name,
                    topic_number=len(existing_topics) + 1,
                    keywords=keywords,
                    description=topic_info["description"],
                    coherence_score=coherence_score,
                    message_count=0,
                    avg_sentiment=topic_info["typical_sentiment"],
                    trend_score=trend_score,
                    growth_rate=growth_rate,
                    first_seen=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    last_updated=datetime.utcnow(),
                    model_version="political_v1.0",
                    created_at=datetime.utcnow()
                )
                db.add(topic)
                existing_topics.add(topic_name)
        
        db.commit()
    
    def _perform_real_topic_analysis(self, db: Session, messages: List[Message]) -> int:
        """Perform real topic analysis using NLP models (placeholder)."""
        # In a real implementation, this would:
        # 1. Preprocess message content
        # 2. Train or use pre-trained LDA model
        # 3. Extract topics and assign to messages
        # 4. Calculate coherence scores
        # 5. Update topic trends
        
        # For now, fall back to dummy generation
        return self._generate_dummy_topic_assignments(db, messages)
    
    def get_trending_topics(
        self, 
        db: Session, 
        days: int = 7,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get trending topics for the specified time period.
        
        Args:
            db: Database session
            days: Number of days to analyze for trends
            limit: Maximum number of topics to return
            
        Returns:
            Dictionary with trending topic data
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Get topics with recent activity
        trending_topics = db.query(
            TopicModel.id,
            TopicModel.topic_name,
            TopicModel.keywords,
            TopicModel.description,
            TopicModel.trend_score,
            TopicModel.growth_rate,
            TopicModel.avg_sentiment,
            func.count(MessageTopic.id).label('recent_messages'),
            func.avg(MessageTopic.probability).label('avg_probability')
        ).join(MessageTopic, TopicModel.id == MessageTopic.topic_id)\
         .join(Message, MessageTopic.message_id == Message.id)\
         .filter(Message.published_at >= since_date)\
         .group_by(TopicModel.id)\
         .order_by(desc(TopicModel.trend_score))\
         .limit(limit)\
         .all()
        
        # Format results
        topics_data = []
        for topic in trending_topics:
            # Extract top keywords
            top_keywords = []
            if topic.keywords:
                sorted_keywords = sorted(topic.keywords, key=lambda x: x.get('weight', 0), reverse=True)
                top_keywords = [kw['word'] for kw in sorted_keywords[:5]]
            
            topics_data.append({
                'topic_id': topic.id,
                'topic_name': topic.topic_name,
                'description': topic.description,
                'keywords': top_keywords,
                'trend_score': float(topic.trend_score),
                'growth_rate': float(topic.growth_rate),
                'avg_sentiment': float(topic.avg_sentiment or 0),
                'recent_messages': topic.recent_messages,
                'avg_probability': float(topic.avg_probability or 0)
            })
        
        # Calculate overall trending statistics
        total_topics = db.query(TopicModel).count()
        active_topics = db.query(TopicModel).join(MessageTopic)\
                                          .join(Message)\
                                          .filter(Message.published_at >= since_date)\
                                          .distinct().count()
        
        return {
            "time_period_days": days,
            "trending_topics": topics_data,
            "total_topics": total_topics,
            "active_topics": active_topics,
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    def get_topic_trends_over_time(
        self, 
        db: Session, 
        topic_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get topic trends over time for visualization.
        
        Args:
            db: Database session
            topic_id: Specific topic ID, or None for all topics
            days: Number of days to analyze
            
        Returns:
            Dictionary with time-series trend data
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Base query for topic activity over time
        # Use strftime for SQLite compatibility
        query = db.query(
            func.strftime('%Y-%m-%d', Message.published_at).label('date'),
            TopicModel.topic_name,
            TopicModel.id.label('topic_id'),
            func.count(MessageTopic.id).label('message_count'),
            func.avg(MessageTopic.probability).label('avg_probability')
        ).join(MessageTopic, TopicModel.id == MessageTopic.topic_id)\
         .join(Message, MessageTopic.message_id == Message.id)\
         .filter(Message.published_at >= since_date)
        
        if topic_id:
            query = query.filter(TopicModel.id == topic_id)
        
        trends = query.group_by(
            func.strftime('%Y-%m-%d', Message.published_at),
            TopicModel.id,
            TopicModel.topic_name
        ).order_by(func.strftime('%Y-%m-%d', Message.published_at)).all()
        
        # Format data for visualization
        daily_data = defaultdict(lambda: defaultdict(dict))
        topics_info = {}
        
        for trend in trends:
            date_str = trend.date  # Already a string from strftime
            topic_name = trend.topic_name
            
            daily_data[date_str][topic_name] = {
                'message_count': trend.message_count,
                'avg_probability': float(trend.avg_probability or 0),
                'topic_id': trend.topic_id
            }
            
            if topic_name not in topics_info:
                topics_info[topic_name] = {
                    'topic_id': trend.topic_id,
                    'total_messages': trend.message_count
                }
            else:
                topics_info[topic_name]['total_messages'] += trend.message_count
        
        return {
            "time_period_days": days,
            "daily_data": dict(daily_data),
            "topics_summary": topics_info,
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    def get_topic_sentiment_analysis(self, db: Session) -> Dict[str, Any]:
        """
        Get sentiment analysis breakdown by topic.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with topic-sentiment correlations
        """
        # Import here to avoid circular imports
        from ..models import MessageSentiment
        
        # Get topic-sentiment correlations
        topic_sentiment = db.query(
            TopicModel.topic_name,
            TopicModel.id.label('topic_id'),
            func.count(MessageSentiment.id).label('analyzed_messages'),
            func.avg(MessageSentiment.sentiment_score).label('avg_sentiment'),
            func.sum(case((MessageSentiment.sentiment_label == 'positive', 1), else_=0)).label('positive_count'),
            func.sum(case((MessageSentiment.sentiment_label == 'negative', 1), else_=0)).label('negative_count'),
            func.sum(case((MessageSentiment.sentiment_label == 'neutral', 1), else_=0)).label('neutral_count')
        ).join(MessageTopic, TopicModel.id == MessageTopic.topic_id)\
         .join(Message, MessageTopic.message_id == Message.id)\
         .join(MessageSentiment, Message.id == MessageSentiment.message_id)\
         .group_by(TopicModel.id, TopicModel.topic_name)\
         .order_by(func.count(MessageSentiment.id).desc())\
         .all()
        
        # Format results
        topic_sentiment_data = []
        for row in topic_sentiment:
            total_analyzed = row.analyzed_messages
            if total_analyzed > 0:
                topic_sentiment_data.append({
                    'topic_name': row.topic_name,
                    'topic_id': row.topic_id,
                    'analyzed_messages': total_analyzed,
                    'avg_sentiment': float(row.avg_sentiment or 0),
                    'positive_count': row.positive_count or 0,
                    'negative_count': row.negative_count or 0,
                    'neutral_count': row.neutral_count or 0,
                    'positive_pct': (row.positive_count or 0) / total_analyzed * 100,
                    'negative_pct': (row.negative_count or 0) / total_analyzed * 100,
                    'neutral_pct': (row.neutral_count or 0) / total_analyzed * 100
                })
        
        return {
            "topic_sentiment_analysis": topic_sentiment_data,
            "total_topics_analyzed": len(topic_sentiment_data),
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    def get_candidate_topic_analysis(
        self, 
        db: Session, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get topic distribution analysis by candidate.
        
        Args:
            db: Database session
            limit: Maximum number of candidates to analyze
            
        Returns:
            Dictionary with candidate-topic data
        """
        # Get candidate topic distributions
        candidate_topics = db.query(
            Candidate.name.label('candidate_name'),
            Candidate.id.label('candidate_id'),
            TopicModel.topic_name,
            TopicModel.id.label('topic_id'),
            func.count(MessageTopic.id).label('message_count'),
            func.avg(MessageTopic.probability).label('avg_probability')
        ).join(Message, Candidate.id == Message.candidate_id)\
         .join(MessageTopic, Message.id == MessageTopic.message_id)\
         .join(TopicModel, MessageTopic.topic_id == TopicModel.id)\
         .group_by(
             Candidate.id, Candidate.name,
             TopicModel.id, TopicModel.topic_name
         ).order_by(
             Candidate.name,
             func.count(MessageTopic.id).desc()
         ).all()
        
        # Organize data by candidate
        candidates_data = defaultdict(lambda: {
            'candidate_id': None,
            'topics': [],
            'total_messages': 0
        })
        
        for row in candidate_topics:
            candidate_name = row.candidate_name
            if candidates_data[candidate_name]['candidate_id'] is None:
                candidates_data[candidate_name]['candidate_id'] = row.candidate_id
            
            candidates_data[candidate_name]['topics'].append({
                'topic_name': row.topic_name,
                'topic_id': row.topic_id,
                'message_count': row.message_count,
                'avg_probability': float(row.avg_probability or 0)
            })
            candidates_data[candidate_name]['total_messages'] += row.message_count
        
        # Convert to list and limit results
        result_data = []
        for candidate_name, data in candidates_data.items():
            # Sort topics by message count
            data['topics'].sort(key=lambda x: x['message_count'], reverse=True)
            result_data.append({
                'candidate_name': candidate_name,
                'candidate_id': data['candidate_id'],
                'total_messages': data['total_messages'],
                'top_topics': data['topics'][:5],  # Top 5 topics per candidate
                'topic_diversity': len(data['topics'])  # Number of different topics
            })
        
        # Sort by total messages and limit
        result_data.sort(key=lambda x: x['total_messages'], reverse=True)
        result_data = result_data[:limit]
        
        return {
            "candidate_topic_analysis": result_data,
            "total_candidates_analyzed": len(result_data),
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    def get_topic_overview(self, db: Session) -> Dict[str, Any]:
        """
        Get comprehensive topic modeling overview.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with topic modeling overview statistics
        """
        # Basic counts
        total_topics = db.query(TopicModel).count()
        total_assignments = db.query(MessageTopic).count()
        total_messages = db.query(Message).count()
        
        if total_assignments == 0:
            return {
                "total_topics": total_topics,
                "total_assignments": 0,
                "total_messages": total_messages,
                "coverage": 0.0,
                "needs_analysis": True,
                "top_topics": [],
                "trending_topics": [],
                "avg_coherence": 0.0
            }
        
        # Coverage calculation
        messages_with_topics = db.query(MessageTopic.message_id).distinct().count()
        coverage = (messages_with_topics / total_messages * 100) if total_messages > 0 else 0.0
        
        # Top topics by message count
        top_topics = db.query(
            TopicModel.topic_name,
            TopicModel.message_count,
            TopicModel.trend_score,
            TopicModel.avg_sentiment
        ).order_by(TopicModel.message_count.desc()).limit(5).all()
        
        # Most trending topics
        trending_topics = db.query(
            TopicModel.topic_name,
            TopicModel.trend_score,
            TopicModel.growth_rate,
            TopicModel.message_count
        ).order_by(TopicModel.trend_score.desc()).limit(5).all()
        
        # Average coherence score
        avg_coherence = db.query(func.avg(TopicModel.coherence_score)).scalar() or 0.0
        
        return {
            "total_topics": total_topics,
            "total_assignments": total_assignments,
            "total_messages": total_messages,
            "coverage": coverage,
            "messages_with_topics": messages_with_topics,
            "needs_analysis": coverage < 10.0,  # Less than 10% coverage
            "top_topics": [
                {
                    "topic_name": topic.topic_name,
                    "message_count": topic.message_count,
                    "trend_score": float(topic.trend_score),
                    "avg_sentiment": float(topic.avg_sentiment or 0)
                }
                for topic in top_topics
            ],
            "trending_topics": [
                {
                    "topic_name": topic.topic_name,
                    "trend_score": float(topic.trend_score),
                    "growth_rate": float(topic.growth_rate),
                    "message_count": topic.message_count
                }
                for topic in trending_topics
            ],
            "avg_coherence": float(avg_coherence),
            "analysis_date": datetime.utcnow().isoformat()
        }
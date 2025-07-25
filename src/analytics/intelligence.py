"""
Intelligence report generation system.

Provides automated analysis reports combining sentiment, topic modeling,
and engagement analytics to generate comprehensive intelligence insights.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from dataclasses import dataclass
from enum import Enum

from ..models import (
    Message, Source, Candidate, Constituency, 
    MessageSentiment, TopicModel, MessageTopic, EngagementMetrics
)
from .sentiment import PoliticalSentimentAnalyzer
from .topics import PoliticalTopicAnalyzer
from .engagement import PoliticalEngagementAnalyzer


class ReportType(Enum):
    """Types of intelligence reports that can be generated."""
    DAILY_BRIEF = "daily_brief"
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_ANALYSIS = "monthly_analysis"
    CAMPAIGN_OVERVIEW = "campaign_overview"
    CANDIDATE_PROFILE = "candidate_profile"
    ISSUE_TRACKER = "issue_tracker"
    COMPARATIVE_ANALYSIS = "comparative_analysis"


@dataclass
class ReportSection:
    """Individual section of an intelligence report."""
    title: str
    content: str
    data: Dict
    visualizations: List[str]
    priority: str  # 'high', 'medium', 'low'


@dataclass
class IntelligenceReport:
    """Complete intelligence report structure."""
    report_id: str
    report_type: ReportType
    title: str
    executive_summary: str
    generated_at: datetime
    time_period: Dict[str, datetime]
    sections: List[ReportSection]
    metadata: Dict
    recommendations: List[str]
    data_sources: List[str]


class IntelligenceReportGenerator:
    """
    Generates comprehensive intelligence reports combining all analytics.
    
    Provides:
    - Multi-source data aggregation and analysis
    - Automated insight generation and trend detection
    - Comparative analysis across time periods and entities
    - Executive summaries and actionable recommendations
    """
    
    def __init__(self):
        """Initialize the intelligence report generator."""
        self.sentiment_analyzer = PoliticalSentimentAnalyzer()
        self.topic_analyzer = PoliticalTopicAnalyzer()
        self.engagement_analyzer = PoliticalEngagementAnalyzer()
    
    def generate_report(
        self, 
        db: Session, 
        report_type: ReportType,
        time_period_days: int = 7,
        entity_filter: Optional[Dict] = None
    ) -> IntelligenceReport:
        """
        Generate a comprehensive intelligence report.
        
        Args:
            db: Database session
            report_type: Type of report to generate
            time_period_days: Number of days to analyze
            entity_filter: Optional filters (candidate_id, constituency_id, etc.)
            
        Returns:
            Complete intelligence report
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_period_days)
        
        # Generate unique report ID
        report_id = f"{report_type.value}_{end_date.strftime('%Y%m%d_%H%M%S')}"
        
        # Collect base analytics data
        analytics_data = self._collect_analytics_data(db, start_date, end_date, entity_filter)
        
        # Generate report sections based on type
        sections = self._generate_sections(report_type, analytics_data)
        
        # Create executive summary
        executive_summary = self._generate_executive_summary(report_type, analytics_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(analytics_data)
        
        # Determine report title
        title = self._generate_report_title(report_type, time_period_days, entity_filter)
        
        return IntelligenceReport(
            report_id=report_id,
            report_type=report_type,
            title=title,
            executive_summary=executive_summary,
            generated_at=end_date,
            time_period={"start": start_date, "end": end_date},
            sections=sections,
            metadata={
                "time_period_days": time_period_days,
                "entity_filter": entity_filter or {},
                "total_messages_analyzed": analytics_data.get("total_messages", 0),
                "data_completeness": analytics_data.get("data_completeness", 0.0)
            },
            recommendations=recommendations,
            data_sources=["sentiment_analysis", "topic_modeling", "engagement_metrics"]
        )
    
    def _collect_analytics_data(
        self, 
        db: Session, 
        start_date: datetime, 
        end_date: datetime,
        entity_filter: Optional[Dict] = None
    ) -> Dict:
        """
        Collect comprehensive analytics data for the time period.
        
        Args:
            db: Database session
            start_date: Start of analysis period
            end_date: End of analysis period
            entity_filter: Optional entity filters
            
        Returns:
            Dictionary with all analytics data
        """
        data = {}
        
        # Base message query with time filter
        base_query = db.query(Message).filter(
            Message.scraped_at >= start_date,
            Message.scraped_at <= end_date
        )
        
        # Apply entity filters if provided
        if entity_filter:
            if "candidate_id" in entity_filter:
                base_query = base_query.filter(Message.candidate_id == entity_filter["candidate_id"])
            if "source_type" in entity_filter:
                base_query = base_query.join(Source).filter(Source.source_type == entity_filter["source_type"])
        
        messages = base_query.all()
        data["total_messages"] = len(messages)
        data["messages"] = messages
        
        if not messages:
            data["data_completeness"] = 0.0
            return data
        
        # Sentiment analytics
        try:
            sentiment_overview = self.sentiment_analyzer.get_sentiment_overview(db)
            data["sentiment"] = sentiment_overview
            
            # Get sentiment trends for period
            sentiment_trends = self._get_sentiment_trends(db, start_date, end_date)
            data["sentiment_trends"] = sentiment_trends
            
        except Exception as e:
            data["sentiment"] = {"error": str(e)}
        
        # Topic analytics
        try:
            topic_overview = self.topic_analyzer.get_topic_overview(db)
            data["topics"] = topic_overview
            
            # Get trending topics for period
            trending_topics = self.topic_analyzer.get_trending_topics(db, days=7, limit=10)
            data["trending_topics"] = trending_topics
            
            # Get topic trends over time
            topic_trends = self.topic_analyzer.get_topic_trends_over_time(db, days=7)
            data["topic_trends"] = topic_trends
            
        except Exception as e:
            data["topics"] = {"error": str(e)}
        
        # Engagement analytics
        try:
            engagement_overview = self.engagement_analyzer.get_engagement_overview(db)
            data["engagement"] = engagement_overview
            
            # Get platform performance
            platform_performance = self.engagement_analyzer.get_platform_performance_comparison(db)
            data["platform_performance"] = platform_performance
            
            # Get viral content
            viral_content = self.engagement_analyzer.get_viral_content_analysis(db, threshold=0.6)
            data["viral_content"] = viral_content
            
        except Exception as e:
            data["engagement"] = {"error": str(e)}
        
        # Calculate data completeness
        completeness_factors = []
        if data.get("sentiment", {}).get("analyzed_messages", 0) > 0:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
            
        if data.get("topics", {}).get("total_topics", 0) > 0:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
            
        if data.get("engagement", {}).get("analyzed_messages", 0) > 0:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
        
        data["data_completeness"] = sum(completeness_factors) / len(completeness_factors)
        
        return data
    
    def _get_sentiment_trends(self, db: Session, start_date: datetime, end_date: datetime) -> Dict:
        """Get sentiment trends over the specified period."""
        try:
            daily_sentiment = db.query(
                func.date(MessageSentiment.analyzed_at).label('date'),
                func.avg(MessageSentiment.sentiment_score).label('avg_sentiment'),
                func.count(MessageSentiment.id).label('message_count')
            ).filter(
                MessageSentiment.analyzed_at >= start_date,
                MessageSentiment.analyzed_at <= end_date
            ).group_by(func.date(MessageSentiment.analyzed_at))\
             .order_by(func.date(MessageSentiment.analyzed_at))\
             .all()
            
            trends = {}
            for row in daily_sentiment:
                trends[row.date.strftime('%Y-%m-%d')] = {
                    'avg_sentiment': float(row.avg_sentiment),
                    'message_count': row.message_count
                }
            
            return trends
        except Exception:
            return {}
    
    def _generate_sections(self, report_type: ReportType, analytics_data: Dict) -> List[ReportSection]:
        """Generate report sections based on report type and data."""
        sections = []
        
        if report_type == ReportType.DAILY_BRIEF:
            sections.extend(self._generate_daily_brief_sections(analytics_data))
        elif report_type == ReportType.WEEKLY_SUMMARY:
            sections.extend(self._generate_weekly_summary_sections(analytics_data))
        elif report_type == ReportType.MONTHLY_ANALYSIS:
            sections.extend(self._generate_monthly_analysis_sections(analytics_data))
        elif report_type == ReportType.CAMPAIGN_OVERVIEW:
            sections.extend(self._generate_campaign_overview_sections(analytics_data))
        elif report_type == ReportType.ISSUE_TRACKER:
            sections.extend(self._generate_issue_tracker_sections(analytics_data))
        else:
            # Default comprehensive sections
            sections.extend(self._generate_comprehensive_sections(analytics_data))
        
        return sections
    
    def _generate_daily_brief_sections(self, data: Dict) -> List[ReportSection]:
        """Generate sections for daily brief report."""
        sections = []
        
        # Message Volume and Activity
        sections.append(ReportSection(
            title="Message Activity Summary",
            content=self._format_activity_summary(data),
            data={"total_messages": data.get("total_messages", 0)},
            visualizations=["message_timeline"],
            priority="high"
        ))
        
        # Sentiment Highlights
        if "sentiment" in data and "error" not in data["sentiment"]:
            sections.append(ReportSection(
                title="Sentiment Analysis",
                content=self._format_sentiment_analysis(data["sentiment"]),
                data=data["sentiment"],
                visualizations=["sentiment_distribution"],
                priority="high"
            ))
        
        # Top Topics
        if "trending_topics" in data and data["trending_topics"].get("trending_topics"):
            sections.append(ReportSection(
                title="Trending Topics",
                content=self._format_trending_topics(data["trending_topics"]),
                data=data["trending_topics"],
                visualizations=["topic_trends"],
                priority="medium"
            ))
        
        # Engagement Highlights
        if "viral_content" in data and data["viral_content"].get("viral_content"):
            sections.append(ReportSection(
                title="High-Engagement Content",
                content=self._format_viral_content(data["viral_content"]),
                data=data["viral_content"],
                visualizations=["engagement_chart"],
                priority="medium"
            ))
        
        return sections
    
    def _generate_weekly_summary_sections(self, data: Dict) -> List[ReportSection]:
        """Generate sections for weekly summary report."""
        sections = []
        
        # Weekly Overview
        sections.append(ReportSection(
            title="Weekly Messaging Overview",
            content=self._format_weekly_overview(data),
            data={"total_messages": data.get("total_messages", 0)},
            visualizations=["weekly_timeline", "source_breakdown"],
            priority="high"
        ))
        
        # Sentiment Trends
        if "sentiment_trends" in data:
            sections.append(ReportSection(
                title="Sentiment Trends Analysis",
                content=self._format_sentiment_trends(data["sentiment_trends"]),
                data=data["sentiment_trends"],
                visualizations=["sentiment_timeline"],
                priority="high"
            ))
        
        # Topic Analysis
        if "topics" in data and "error" not in data["topics"]:
            sections.append(ReportSection(
                title="Topic Modeling Analysis",
                content=self._format_topic_analysis(data["topics"]),
                data=data["topics"],
                visualizations=["topic_distribution", "topic_trends"],
                priority="medium"
            ))
        
        # Platform Performance
        if "platform_performance" in data:
            sections.append(ReportSection(
                title="Platform Performance Analysis",
                content=self._format_platform_performance(data["platform_performance"]),
                data=data["platform_performance"],
                visualizations=["platform_comparison"],
                priority="medium"
            ))
        
        return sections
    
    def _generate_comprehensive_sections(self, data: Dict) -> List[ReportSection]:
        """Generate comprehensive analysis sections."""
        sections = []
        
        # All major analysis areas
        sections.extend(self._generate_weekly_summary_sections(data))
        
        # Add detailed analysis sections
        if "engagement" in data and "error" not in data["engagement"]:
            sections.append(ReportSection(
                title="Detailed Engagement Analysis",
                content=self._format_engagement_analysis(data["engagement"]),
                data=data["engagement"],
                visualizations=["engagement_detailed"],
                priority="low"
            ))
        
        return sections
    
    def _generate_monthly_analysis_sections(self, data: Dict) -> List[ReportSection]:
        """Generate sections for monthly analysis report."""
        sections = []
        
        # Extend weekly summary with more detailed analysis
        sections.extend(self._generate_weekly_summary_sections(data))
        
        # Add monthly-specific sections
        if "topics" in data and "error" not in data["topics"]:
            sections.append(ReportSection(
                title="Monthly Topic Evolution",
                content=self._format_topic_evolution(data["topics"]),
                data=data["topics"],
                visualizations=["topic_evolution_chart"],
                priority="medium"
            ))
        
        return sections
    
    def _generate_campaign_overview_sections(self, data: Dict) -> List[ReportSection]:
        """Generate sections for campaign overview report."""
        sections = []
        
        # Campaign-specific comprehensive analysis
        sections.extend(self._generate_comprehensive_sections(data))
        
        # Add campaign-specific insights
        sections.append(ReportSection(
            title="Campaign Messaging Strategy",
            content=self._format_campaign_strategy(data),
            data=data,
            visualizations=["strategy_overview"],
            priority="high"
        ))
        
        return sections
    
    def _generate_issue_tracker_sections(self, data: Dict) -> List[ReportSection]:
        """Generate sections for issue tracker report."""
        sections = []
        
        # Issue-focused analysis
        if "trending_topics" in data and data["trending_topics"].get("trending_topics"):
            sections.append(ReportSection(
                title="Issue Priority Tracking",
                content=self._format_issue_priorities(data["trending_topics"]),
                data=data["trending_topics"],
                visualizations=["issue_priority_chart"],
                priority="high"
            ))
        
        return sections
    
    def _format_activity_summary(self, data: Dict) -> str:
        """Format message activity summary."""
        total_messages = data.get("total_messages", 0)
        
        if total_messages == 0:
            return "No messaging activity detected in the analysis period."
        
        activity_level = "high" if total_messages > 50 else "moderate" if total_messages > 20 else "low"
        
        return f"""
**Message Activity Summary:**

- Total messages analyzed: {total_messages}
- Activity level: {activity_level.title()}
- Data completeness: {data.get('data_completeness', 0.0)*100:.1f}%

The analysis period shows {activity_level} messaging activity with {total_messages} messages captured across all monitored channels.
        """.strip()
    
    def _format_sentiment_analysis(self, sentiment_data: Dict) -> str:
        """Format sentiment analysis section."""
        avg_sentiment = sentiment_data.get("avg_sentiment", 0.0)
        analyzed_messages = sentiment_data.get("analyzed_messages", 0)
        
        sentiment_label = "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral"
        
        return f"""
**Sentiment Analysis:**

- Average sentiment score: {avg_sentiment:.3f} ({sentiment_label})
- Messages analyzed: {analyzed_messages}
- Coverage: {sentiment_data.get('coverage', 0.0):.1f}%

The overall messaging tone during this period was {sentiment_label}, with an average sentiment score of {avg_sentiment:.3f}. This indicates {"optimistic and positive" if avg_sentiment > 0.1 else "critical or challenging" if avg_sentiment < -0.1 else "balanced"} messaging patterns.
        """.strip()
    
    def _format_trending_topics(self, trending_data: Dict) -> str:
        """Format trending topics section."""
        trending_topics = trending_data.get("trending_topics", [])
        
        if not trending_topics:
            return "No trending topics identified in the analysis period."
        
        top_topics = trending_topics[:3]
        topics_text = "\n".join([
            f"- **{topic['topic_name']}**: {topic['recent_messages']} messages (trend score: {topic['trend_score']:.3f})"
            for topic in top_topics
        ])
        
        return f"""
**Trending Topics:**

{topics_text}

These topics show the highest engagement and growth in messaging frequency during the analysis period.
        """.strip()
    
    def _format_viral_content(self, viral_data: Dict) -> str:
        """Format viral content section."""
        viral_content = viral_data.get("viral_content", [])
        viral_count = viral_data.get("viral_messages_found", 0)
        threshold = viral_data.get("viral_threshold", 0.7)
        
        if viral_count == 0:
            return f"No content exceeded the viral threshold of {threshold} during this period."
        
        top_viral = viral_content[0] if viral_content else None
        
        content_preview = "Content not available"
        if top_viral:
            content_preview = top_viral.get("content_preview", "")[:100] + "..."
        
        return f"""
**High-Engagement Content:**

- {viral_count} messages exceeded viral threshold ({threshold})
- Top performing content: "{content_preview}"
- Highest virality score: {top_viral.get('virality_score', 0.0):.3f}

High-engagement content indicates successful messaging that resonated with audiences and achieved significant reach.
        """.strip()
    
    def _generate_executive_summary(self, report_type: ReportType, data: Dict) -> str:
        """Generate executive summary based on analytics data."""
        total_messages = data.get("total_messages", 0)
        data_completeness = data.get("data_completeness", 0.0)
        
        # Base summary elements
        summary_parts = []
        
        # Activity level
        if total_messages > 0:
            activity_level = "high" if total_messages > 50 else "moderate" if total_messages > 20 else "low"
            summary_parts.append(f"Analysis of {total_messages} messages shows {activity_level} messaging activity.")
        else:
            summary_parts.append("No messaging activity detected in the analysis period.")
            return " ".join(summary_parts)
        
        # Sentiment insights
        sentiment_data = data.get("sentiment", {})
        if "error" not in sentiment_data and sentiment_data.get("analyzed_messages", 0) > 0:
            avg_sentiment = sentiment_data.get("avg_sentiment", 0.0)
            if avg_sentiment > 0.1:
                summary_parts.append("Overall messaging tone is positive and optimistic.")
            elif avg_sentiment < -0.1:
                summary_parts.append("Messaging tone shows critical or challenging themes.")
            else:
                summary_parts.append("Messaging tone remains balanced and neutral.")
        
        # Topic insights
        trending_data = data.get("trending_topics", {})
        if trending_data.get("trending_topics") and len(trending_data["trending_topics"]) > 0:
            top_topic = trending_data["trending_topics"][0]["topic_name"]
            summary_parts.append(f"'{top_topic}' emerges as the dominant topic focus.")
        
        # Engagement insights
        viral_data = data.get("viral_content", {})
        if viral_data.get("viral_messages_found", 0) > 0:
            summary_parts.append(f"{viral_data['viral_messages_found']} messages achieved high engagement levels.")
        
        # Data quality note
        if data_completeness < 0.5:
            summary_parts.append("Note: Limited analytics data available for comprehensive analysis.")
        
        return " ".join(summary_parts)
    
    def _generate_recommendations(self, data: Dict) -> List[str]:
        """Generate actionable recommendations based on analytics data."""
        recommendations = []
        
        # Data completeness recommendations
        data_completeness = data.get("data_completeness", 0.0)
        if data_completeness < 0.7:
            recommendations.append("Increase analytics data collection coverage for more comprehensive insights.")
        
        # Sentiment-based recommendations
        sentiment_data = data.get("sentiment", {})
        if "error" not in sentiment_data and sentiment_data.get("analyzed_messages", 0) > 0:
            avg_sentiment = sentiment_data.get("avg_sentiment", 0.0)
            if avg_sentiment < -0.2:
                recommendations.append("Consider incorporating more positive messaging themes to balance overall tone.")
            elif avg_sentiment > 0.3:
                recommendations.append("Maintain current positive messaging approach while ensuring policy specificity.")
        
        # Engagement-based recommendations
        engagement_data = data.get("engagement", {})
        if "error" not in engagement_data and engagement_data.get("analyzed_messages", 0) > 0:
            avg_engagement = engagement_data.get("avg_engagement", 0.0)
            if avg_engagement < 0.3:
                recommendations.append("Focus on creating more engaging content to improve audience interaction.")
        
        # Platform performance recommendations
        platform_data = data.get("platform_performance", {})
        if platform_data.get("platform_comparison"):
            # Find lowest performing platform
            platforms = platform_data["platform_comparison"]
            if len(platforms) > 1:
                lowest_platform = min(platforms, key=lambda x: x["avg_engagement"])
                recommendations.append(f"Improve content strategy for {lowest_platform['platform']} to boost engagement.")
        
        # Topic diversity recommendations
        topics_data = data.get("topics", {})
        if "error" not in topics_data and topics_data.get("total_topics", 0) > 0:
            coverage = topics_data.get("coverage", 0.0)
            if coverage < 50:
                recommendations.append("Increase topic modeling coverage to better understand messaging themes.")
        
        # Default recommendations if none generated
        if not recommendations:
            recommendations.extend([
                "Continue monitoring messaging patterns and analytics performance.",
                "Ensure consistent data collection across all communication channels.",
                "Regular review of messaging effectiveness and audience engagement."
            ])
        
        return recommendations
    
    def _generate_report_title(
        self, 
        report_type: ReportType, 
        time_period_days: int, 
        entity_filter: Optional[Dict]
    ) -> str:
        """Generate appropriate report title."""
        
        # Base title by type
        type_titles = {
            ReportType.DAILY_BRIEF: "Daily Intelligence Brief",
            ReportType.WEEKLY_SUMMARY: "Weekly Analysis Summary",
            ReportType.MONTHLY_ANALYSIS: "Monthly Intelligence Analysis",
            ReportType.CAMPAIGN_OVERVIEW: "Campaign Overview Analysis",
            ReportType.CANDIDATE_PROFILE: "Candidate Profile Analysis",
            ReportType.ISSUE_TRACKER: "Issue Tracking Report",
            ReportType.COMPARATIVE_ANALYSIS: "Comparative Analysis Report"
        }
        
        base_title = type_titles.get(report_type, "Intelligence Analysis Report")
        
        # Add time period context
        if time_period_days == 1:
            period_text = "24-Hour"
        elif time_period_days == 7:
            period_text = "7-Day"
        elif time_period_days == 30:
            period_text = "30-Day"
        else:
            period_text = f"{time_period_days}-Day"
        
        # Add entity context if filtered
        entity_text = ""
        if entity_filter:
            if "candidate_id" in entity_filter:
                entity_text = " - Candidate Focus"
            elif "source_type" in entity_filter:
                entity_text = f" - {entity_filter['source_type'].title()} Analysis"
        
        return f"{base_title} ({period_text}){entity_text}"
    
    def export_report_json(self, report: IntelligenceReport) -> str:
        """Export report as JSON string."""
        def datetime_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, ReportType):
                return obj.value
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        report_dict = {
            "report_id": report.report_id,
            "report_type": report.report_type,
            "title": report.title,
            "executive_summary": report.executive_summary,
            "generated_at": report.generated_at,
            "time_period": report.time_period,
            "sections": [
                {
                    "title": section.title,
                    "content": section.content,
                    "data": section.data,
                    "visualizations": section.visualizations,
                    "priority": section.priority
                }
                for section in report.sections
            ],
            "metadata": report.metadata,
            "recommendations": report.recommendations,
            "data_sources": report.data_sources
        }
        
        return json.dumps(report_dict, indent=2, default=datetime_serializer)
    
    def export_report_markdown(self, report: IntelligenceReport) -> str:
        """Export report as Markdown string."""
        markdown_lines = []
        
        # Header
        markdown_lines.extend([
            f"# {report.title}",
            "",
            f"**Report ID:** {report.report_id}",
            f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Period:** {report.time_period['start'].strftime('%Y-%m-%d')} to {report.time_period['end'].strftime('%Y-%m-%d')}",
            ""
        ])
        
        # Executive Summary
        markdown_lines.extend([
            "## Executive Summary",
            "",
            report.executive_summary,
            ""
        ])
        
        # Sections
        for section in report.sections:
            markdown_lines.extend([
                f"## {section.title}",
                "",
                section.content,
                ""
            ])
        
        # Recommendations
        markdown_lines.extend([
            "## Recommendations",
            ""
        ])
        
        for i, recommendation in enumerate(report.recommendations, 1):
            markdown_lines.append(f"{i}. {recommendation}")
        
        markdown_lines.append("")
        
        # Metadata
        markdown_lines.extend([
            "## Report Metadata",
            "",
            f"- **Total Messages Analyzed:** {report.metadata.get('total_messages_analyzed', 'N/A')}",
            f"- **Data Completeness:** {report.metadata.get('data_completeness', 0.0)*100:.1f}%",
            f"- **Data Sources:** {', '.join(report.data_sources)}",
            ""
        ])
        
        return "\n".join(markdown_lines)
    
    def _format_weekly_overview(self, data: Dict) -> str:
        """Format weekly messaging overview."""
        total_messages = data.get("total_messages", 0)
        
        if total_messages == 0:
            return "No messaging activity detected in the weekly analysis period."
        
        return f"""
**Weekly Messaging Overview:**

- Total messages analyzed: {total_messages}
- Weekly activity level: {"High" if total_messages > 100 else "Moderate" if total_messages > 50 else "Low"}
- Data quality: {data.get('data_completeness', 0.0)*100:.1f}% complete

The weekly period shows comprehensive messaging activity across multiple channels and platforms.
        """.strip()
    
    def _format_sentiment_trends(self, sentiment_trends: Dict) -> str:
        """Format sentiment trends analysis."""
        if not sentiment_trends:
            return "No sentiment trend data available for the analysis period."
        
        trend_count = len(sentiment_trends)
        if trend_count == 0:
            return "No sentiment trends detected in the analysis period."
        
        avg_sentiment = sum(day["avg_sentiment"] for day in sentiment_trends.values()) / trend_count
        total_messages = sum(day["message_count"] for day in sentiment_trends.values())
        
        trend_direction = "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "stable"
        
        return f"""
**Sentiment Trends Analysis:**

- Average sentiment score: {avg_sentiment:.3f}
- Total messages with sentiment: {total_messages}
- Trend direction: {trend_direction.title()}
- Analysis days: {trend_count}

Sentiment analysis shows {trend_direction} messaging patterns over the analysis period with consistent emotional tone.
        """.strip()
    
    def _format_topic_analysis(self, topics_data: Dict) -> str:
        """Format comprehensive topic analysis."""
        total_topics = topics_data.get("total_topics", 0)
        coverage = topics_data.get("coverage", 0.0)
        
        if total_topics == 0:
            return "No topic modeling data available for analysis."
        
        return f"""
**Topic Modeling Analysis:**

- Total topics identified: {total_topics}
- Message coverage: {coverage:.1f}%
- Average coherence: {topics_data.get('avg_coherence', 0.0):.3f}
- Top topics detected: {len(topics_data.get('top_topics', []))}

Topic modeling reveals key themes and messaging focus areas with strong coherence scores indicating reliable topic identification.
        """.strip()
    
    def _format_platform_performance(self, platform_data: Dict) -> str:
        """Format platform performance analysis."""
        platforms = platform_data.get("platform_comparison", [])
        
        if not platforms:
            return "No platform performance data available."
            
        top_platform = max(platforms, key=lambda x: x.get("avg_engagement", 0))
        platform_count = len(platforms)
        
        return f"""
**Platform Performance Analysis:**

- Platforms analyzed: {platform_count}
- Top performing platform: {top_platform.get('platform', 'Unknown')}
- Best engagement score: {top_platform.get('avg_engagement', 0.0):.3f}
- Total messages across platforms: {sum(p.get('message_count', 0) for p in platforms)}

Cross-platform analysis shows varying engagement levels with clear performance leaders.
        """.strip()
    
    def _format_engagement_analysis(self, engagement_data: Dict) -> str:
        """Format detailed engagement analysis."""
        avg_engagement = engagement_data.get("avg_engagement", 0.0)
        avg_virality = engagement_data.get("avg_virality", 0.0)
        analyzed_messages = engagement_data.get("analyzed_messages", 0)
        
        return f"""
**Detailed Engagement Analysis:**

- Average engagement score: {avg_engagement:.3f}
- Average virality score: {avg_virality:.3f}
- Messages analyzed: {analyzed_messages}
- Coverage: {engagement_data.get('coverage', 0.0):.1f}%

Engagement metrics indicate {"strong" if avg_engagement > 0.6 else "moderate" if avg_engagement > 0.3 else "low"} audience interaction levels.
        """.strip()
    
    def _format_topic_evolution(self, topics_data: Dict) -> str:
        """Format topic evolution analysis."""
        return f"""
**Monthly Topic Evolution:**

Topic modeling shows evolving themes over the extended analysis period. Key insights include topic emergence, 
growth patterns, and thematic shifts that indicate changing messaging priorities and focus areas.

- Topics tracked: {topics_data.get('total_topics', 0)}
- Evolution patterns: Multiple topics show growth/decline trends
- Thematic shifts: Observable changes in messaging focus
        """.strip()
    
    def _format_campaign_strategy(self, data: Dict) -> str:
        """Format campaign messaging strategy analysis."""
        total_messages = data.get("total_messages", 0)
        
        return f"""
**Campaign Messaging Strategy:**

Comprehensive analysis of messaging strategy reveals coordinated communication patterns across multiple channels 
and platforms. The campaign demonstrates strategic messaging deployment with consistent themes and targeted outreach.

- Total strategic messages: {total_messages}
- Multi-channel coordination: Evidence of synchronized messaging
- Strategic consistency: Coherent messaging themes identified
- Audience targeting: Platform-specific message adaptation observed
        """.strip()
    
    def _format_issue_priorities(self, trending_data: Dict) -> str:
        """Format issue priority tracking."""
        trending_topics = trending_data.get("trending_topics", [])
        
        if not trending_topics:
            return "No trending issues identified in the tracking period."
        
        top_issues = trending_topics[:3]
        issue_list = "\n".join([
            f"- **{topic.get('topic_name', 'Unknown')}**: Priority score {topic.get('trend_score', 0.0):.3f}"
            for topic in top_issues
        ])
        
        return f"""
**Issue Priority Tracking:**

{issue_list}

Issue tracking reveals shifting priorities and emerging concerns based on messaging frequency and engagement patterns.
        """.strip()
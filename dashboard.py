import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from collections import Counter
import os

from src.database import get_session
from src.models import Source, Message, Keyword, Constituency, Candidate, MessageSentiment
from src.dashboard.sentiment_service import SentimentDashboardService
from src.dashboard.sentiment_visualizations import (
    display_sentiment_overview_metrics, create_sentiment_distribution_chart,
    create_political_tone_chart, create_sentiment_trends_chart,
    create_candidate_sentiment_chart, create_regional_sentiment_chart,
    create_emotion_analysis_chart, display_detailed_messages_table,
    create_sentiment_analysis_controls
)
from src.dashboard.topic_service import TopicDashboardService
from src.dashboard.topic_visualizations import (
    display_topic_overview_metrics, create_topic_distribution_chart,
    create_trending_topics_chart, create_topic_trends_chart,
    create_candidate_topics_chart, create_topic_coherence_chart,
    create_regional_topics_chart, display_detailed_topics_table,
    create_topic_analysis_controls
)


st.set_page_config(
    page_title="Reform UK Messaging Analysis",
    page_icon="🏛️",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load data from database with caching."""
    with next(get_session()) as db:
        # Load messages with source information and candidate/constituency data
        messages_query = db.query(Message, Source, Candidate, Constituency)\
            .join(Source)\
            .outerjoin(Candidate, Message.candidate_id == Candidate.id)\
            .outerjoin(Constituency, Candidate.constituency_id == Constituency.id)\
            .all()
        
        messages_data = []
        for message, source, candidate, constituency in messages_query:
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'url': message.url,
                'published_at': message.published_at,
                'scraped_at': message.scraped_at,
                'message_type': message.message_type,
                'geographic_scope': message.geographic_scope,
                'source_name': source.name,
                'source_type': source.source_type,
                'candidate_id': candidate.id if candidate else None,
                'candidate_name': candidate.name if candidate else None,
                'constituency_id': constituency.id if constituency else None,
                'constituency_name': constituency.name if constituency else None,
                'region': constituency.region if constituency else None,
                'metadata': message.message_metadata or {}
            })
        
        # Load keywords
        keywords_query = db.query(Keyword, Message).join(Message).all()
        
        keywords_data = []
        for keyword, message in keywords_query:
            keywords_data.append({
                'keyword': keyword.keyword,
                'confidence': keyword.confidence,
                'extraction_method': keyword.extraction_method,
                'message_id': message.id,
                'published_at': message.published_at,
                'source_type': message.source.source_type
            })
        
        # Load constituency and candidate summary data
        constituencies = db.query(Constituency).all()
        candidates = db.query(Candidate).all()
        
        constituency_data = []
        for const in constituencies:
            constituency_data.append({
                'id': const.id,
                'name': const.name,
                'region': const.region,
                'constituency_type': const.constituency_type,
                'candidate_count': len(const.candidates)
            })
        
        candidate_data = []
        for cand in candidates:
            candidate_data.append({
                'id': cand.id,
                'name': cand.name,
                'constituency_id': cand.constituency_id,
                'constituency_name': cand.constituency.name if cand.constituency else None,
                'candidate_type': cand.candidate_type,
                'message_count': len(cand.messages),
                'social_media_accounts': cand.social_media_accounts or {}
            })
    
    messages_df = pd.DataFrame(messages_data)
    keywords_df = pd.DataFrame(keywords_data)
    constituencies_df = pd.DataFrame(constituency_data)
    candidates_df = pd.DataFrame(candidate_data)
    
    if not messages_df.empty:
        messages_df['published_at'] = pd.to_datetime(messages_df['published_at'])
        messages_df['scraped_at'] = pd.to_datetime(messages_df['scraped_at'])
    
    if not keywords_df.empty:
        keywords_df['published_at'] = pd.to_datetime(keywords_df['published_at'])
    
    return messages_df, keywords_df, constituencies_df, candidates_df


def main():
    st.title("🏛️ Reform UK Digital Footprint Analysis")
    st.markdown("Analysis of Reform UK's digital messaging across platforms and constituencies")
    
    # Add refresh button
    if st.button("🔄 Refresh Data", help="Clear cache and reload data from database"):
        st.cache_data.clear()
        st.rerun()
    
    # Load data
    messages_df, keywords_df, constituencies_df, candidates_df = load_data()
    
    if messages_df.empty:
        st.warning("No data found. Please run the scraper first.")
        st.code("python -m src.scrapers.main")
        return
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🗳️ Constituencies", "👥 Candidates", "🎭 Sentiment Analysis", "📊 Topic Modeling"])
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Date range filter
    if messages_df['published_at'].notna().any():
        min_date = messages_df['published_at'].min().date()
        max_date = messages_df['published_at'].max().date()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            mask = (messages_df['published_at'].dt.date >= start_date) & \
                   (messages_df['published_at'].dt.date <= end_date)
            filtered_messages = messages_df[mask]
            filtered_keywords = keywords_df[
                (keywords_df['published_at'].dt.date >= start_date) & 
                (keywords_df['published_at'].dt.date <= end_date)
            ] if not keywords_df.empty else keywords_df
        else:
            filtered_messages = messages_df
            filtered_keywords = keywords_df
    else:
        filtered_messages = messages_df
        filtered_keywords = keywords_df
    
    # Source type filter
    source_types = st.sidebar.multiselect(
        "Source Types",
        options=messages_df['source_type'].unique(),
        default=messages_df['source_type'].unique()
    )
    
    filtered_messages = filtered_messages[filtered_messages['source_type'].isin(source_types)]
    if not keywords_df.empty:
        filtered_keywords = filtered_keywords[filtered_keywords['source_type'].isin(source_types)]
    
    # Phase 2 filters
    if not constituencies_df.empty:
        # Region filter
        regions = st.sidebar.multiselect(
            "Regions",
            options=constituencies_df['region'].unique(),
            default=constituencies_df['region'].unique()
        )
        
        # Geographic scope filter
        if not filtered_messages['geographic_scope'].isna().all():
            geographic_scopes = st.sidebar.multiselect(
                "Geographic Scope",
                options=filtered_messages['geographic_scope'].dropna().unique(),
                default=filtered_messages['geographic_scope'].dropna().unique()
            )
            filtered_messages = filtered_messages[
                filtered_messages['geographic_scope'].isin(geographic_scopes) | 
                filtered_messages['geographic_scope'].isna()
            ]
        
        # Filter by selected regions
        if regions:
            region_constituencies = constituencies_df[constituencies_df['region'].isin(regions)]['id'].tolist()
            filtered_messages = filtered_messages[
                filtered_messages['constituency_id'].isin(region_constituencies) |
                filtered_messages['constituency_id'].isna()
            ]
    
    with tab1:
        # Overview Dashboard
        st.subheader("📊 Overall Statistics")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Messages", len(filtered_messages))
        
        with col2:
            st.metric("Unique Keywords", len(filtered_keywords['keyword'].unique()) if not filtered_keywords.empty else 0)
        
        with col3:
            st.metric("Sources", len(filtered_messages['source_type'].unique()))
        
        with col4:
            st.metric("Constituencies", len(constituencies_df))
        
        with col5:
            st.metric("Candidates", len(candidates_df))
    
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Messages by Source Type")
            source_counts = filtered_messages['source_type'].value_counts()
            fig_pie = px.pie(
                values=source_counts.values,
                names=source_counts.index,
                title="Distribution of Messages by Source"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("Geographic Scope Distribution")
            if not filtered_messages['geographic_scope'].isna().all():
                scope_counts = filtered_messages['geographic_scope'].value_counts()
                fig_scope = px.bar(
                    x=scope_counts.values,
                    y=scope_counts.index,
                    orientation='h',
                    title="Messages by Geographic Scope"
                )
                st.plotly_chart(fig_scope, use_container_width=True)
            else:
                st.info("No geographic scope data available")
        
        # Timeline chart
        st.subheader("Message Frequency Over Time")
        if filtered_messages['published_at'].notna().any():
            timeline_data = filtered_messages.groupby([
                filtered_messages['published_at'].dt.date,
                'source_type'
            ]).size().reset_index(name='count')
            timeline_data.columns = ['date', 'source_type', 'count']
            
            fig_timeline = px.line(
                timeline_data,
                x='date',
                y='count',
                color='source_type',
                title="Daily Message Count by Source"
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Regional distribution
        if not constituencies_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Messages by Region")
                region_messages = filtered_messages.dropna(subset=['region'])
                if not region_messages.empty:
                    region_counts = region_messages['region'].value_counts()
                    fig_regions = px.bar(
                        x=region_counts.values,
                        y=region_counts.index,
                        orientation='h',
                        title="Messages by UK Region"
                    )
                    st.plotly_chart(fig_regions, use_container_width=True)
                else:
                    st.info("No regional message data available")
            
            with col2:
                st.subheader("Constituencies by Region")
                region_const_counts = constituencies_df['region'].value_counts()
                fig_const_regions = px.pie(
                    values=region_const_counts.values,
                    names=region_const_counts.index,
                    title="Constituency Distribution by Region"
                )
                st.plotly_chart(fig_const_regions, use_container_width=True)
    
        # Keywords analysis
        if not filtered_keywords.empty:
            st.subheader("Top Keywords")
            
            col1, col2 = st.columns(2)
            
            with col1:
                top_keywords = filtered_keywords['keyword'].value_counts().head(20)
                fig_keywords = px.bar(
                    x=top_keywords.values,
                    y=top_keywords.index,
                    orientation='h',
                    title="Most Frequent Keywords"
                )
                fig_keywords.update_layout(height=600)
                st.plotly_chart(fig_keywords, use_container_width=True)
            
            with col2:
                # Keywords by extraction method
                method_counts = filtered_keywords['extraction_method'].value_counts()
                fig_methods = px.pie(
                    values=method_counts.values,
                    names=method_counts.index,
                    title="Keywords by Extraction Method"
                )
                st.plotly_chart(fig_methods, use_container_width=True)
    
    with tab2:
        # Constituencies Dashboard
        st.subheader("🗳️ Constituency Analysis")
        
        if not constituencies_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Constituency Details")
                
                # Constituency selector
                selected_constituency = st.selectbox(
                    "Select Constituency",
                    options=constituencies_df['name'].tolist(),
                    index=0
                )
                
                const_info = constituencies_df[constituencies_df['name'] == selected_constituency].iloc[0]
                
                # Display constituency info
                st.info(f"""
                **{const_info['name']}**
                - Region: {const_info['region']}
                - Type: {const_info['constituency_type']}
                - Candidates: {const_info['candidate_count']}
                """)
                
                # Get candidates for this constituency
                const_candidates = candidates_df[
                    candidates_df['constituency_name'] == selected_constituency
                ]
                
                if not const_candidates.empty:
                    st.subheader("Candidates in this Constituency")
                    for _, candidate in const_candidates.iterrows():
                        with st.expander(f"{candidate['name']} ({candidate['message_count']} messages)"):
                            st.write(f"**Type:** {candidate['candidate_type']}")
                            if candidate['social_media_accounts']:
                                st.write("**Social Media:**")
                                for platform, handle in candidate['social_media_accounts'].items():
                                    st.write(f"- {platform.title()}: {handle}")
            
            with col2:
                st.subheader("Constituency Message Activity")
                
                # Messages by constituency
                const_messages = filtered_messages.dropna(subset=['constituency_name'])
                if not const_messages.empty:
                    const_msg_counts = const_messages['constituency_name'].value_counts().head(15)
                    fig_const_messages = px.bar(
                        x=const_msg_counts.values,
                        y=const_msg_counts.index,
                        orientation='h',
                        title="Top 15 Constituencies by Message Count"
                    )
                    fig_const_messages.update_layout(height=500)
                    st.plotly_chart(fig_const_messages, use_container_width=True)
                
                # Regional breakdown
                st.subheader("Regional Summary")
                region_summary = constituencies_df.groupby('region').agg({
                    'id': 'count',
                    'candidate_count': 'sum'
                }).rename(columns={'id': 'constituencies', 'candidate_count': 'total_candidates'})
                
                # Add message counts by region
                if not const_messages.empty:
                    region_msg_counts = const_messages.groupby('region').size()
                    region_summary['messages'] = region_summary.index.map(region_msg_counts).fillna(0).astype(int)
                else:
                    region_summary['messages'] = 0
                
                st.dataframe(region_summary, use_container_width=True)
        else:
            st.info("No constituency data available")
    
    with tab3:
        # Candidates Dashboard
        st.subheader("👥 Candidate Analysis")
        
        if not candidates_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Top Candidates by Message Volume")
                
                # Top candidates by message count
                top_candidates = candidates_df.nlargest(10, 'message_count')
                fig_top_candidates = px.bar(
                    top_candidates,
                    x='message_count',
                    y='name',
                    orientation='h',
                    title="Top 10 Candidates by Message Count",
                    hover_data=['constituency_name']
                )
                fig_top_candidates.update_layout(height=400)
                st.plotly_chart(fig_top_candidates, use_container_width=True)
                
                # Candidate selector for detailed view
                st.subheader("Candidate Details")
                selected_candidate = st.selectbox(
                    "Select Candidate",
                    options=candidates_df['name'].tolist(),
                    index=0
                )
                
                candidate_info = candidates_df[candidates_df['name'] == selected_candidate].iloc[0]
                
                st.info(f"""
                **{candidate_info['name']}**
                - Constituency: {candidate_info['constituency_name']}
                - Type: {candidate_info['candidate_type']}
                - Messages: {candidate_info['message_count']}
                """)
                
                if candidate_info['social_media_accounts']:
                    st.write("**Social Media Accounts:**")
                    for platform, handle in candidate_info['social_media_accounts'].items():
                        st.write(f"- {platform.title()}: {handle}")
            
            with col2:
                st.subheader("Candidate Message Distribution")
                
                # Messages by candidate (top 15)
                candidate_messages = filtered_messages.dropna(subset=['candidate_name'])
                if not candidate_messages.empty:
                    cand_msg_counts = candidate_messages['candidate_name'].value_counts().head(15)
                    fig_cand_messages = px.bar(
                        x=cand_msg_counts.values,
                        y=cand_msg_counts.index,
                        orientation='h',
                        title="Top 15 Candidates by Message Count"
                    )
                    fig_cand_messages.update_layout(height=500)
                    st.plotly_chart(fig_cand_messages, use_container_width=True)
                
                # Recent messages from selected candidate
                st.subheader(f"Recent Messages from {selected_candidate}")
                candidate_recent = filtered_messages[
                    filtered_messages['candidate_name'] == selected_candidate
                ].sort_values('published_at', ascending=False).head(5)
                
                if not candidate_recent.empty:
                    for _, msg in candidate_recent.iterrows():
                        with st.expander(f"{msg['published_at'].strftime('%Y-%m-%d') if pd.notna(msg['published_at']) else 'No date'}"):
                            st.write(msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content'])
                            if msg['url']:
                                st.write(f"[View Original]({msg['url']})")
                else:
                    st.info("No messages found for this candidate")
        else:
            st.info("No candidate data available")
    
    with tab4:
        # Sentiment Analysis Dashboard
        st.subheader("🎭 Sentiment Analysis Dashboard")
        
        # Initialize sentiment service
        sentiment_service = SentimentDashboardService()
        
        # Get sentiment overview
        with next(get_session()) as db:
            overview_data = sentiment_service.get_sentiment_overview(db)
        
        # Display overview metrics
        display_sentiment_overview_metrics(overview_data)
        
        # Check if we have sentiment data
        if overview_data["needs_analysis"]:
            st.warning("⚠️ No sentiment analysis data found. Generate some test data to explore the dashboard features.")
            
            # Show controls for generating test data
            generate_button, analyze_count = create_sentiment_analysis_controls()
            
            if generate_button:
                with st.spinner("Generating dummy sentiment data..."):
                    with next(get_session()) as db:
                        result = sentiment_service.generate_dummy_sentiment_batch(db, limit=analyze_count)
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()  # Refresh the dashboard
                    else:
                        st.error(result["message"])
        else:
            # We have sentiment data, show visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Sentiment Distribution")
                sentiment_chart = create_sentiment_distribution_chart(overview_data)
                st.plotly_chart(sentiment_chart, use_container_width=True)
            
            with col2:
                st.subheader("🗣️ Political Tone Analysis")
                with next(get_session()) as db:
                    tone_data = sentiment_service.get_political_tone_analysis(db)
                tone_chart = create_political_tone_chart(tone_data)
                st.plotly_chart(tone_chart, use_container_width=True)
            
            # Sentiment trends over time
            st.subheader("📊 Sentiment Trends Over Time")
            
            # Period selector for trends
            col1, col2 = st.columns([3, 1])
            with col2:
                trend_days = st.selectbox(
                    "Time Period",
                    options=[7, 14, 30, 60, 90],
                    index=2,  # Default to 30 days
                    help="Select number of days for trend analysis"
                )
            
            with next(get_session()) as db:
                trends_data = sentiment_service.get_sentiment_trends(db, days=trend_days)
            trends_chart = create_sentiment_trends_chart(trends_data)
            st.plotly_chart(trends_chart, use_container_width=True)
            
            # Candidate and regional analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("👥 Candidate Sentiment Comparison")
                with next(get_session()) as db:
                    candidate_df = sentiment_service.get_candidate_sentiment_comparison(db, limit=15)
                
                if not candidate_df.empty:
                    candidate_chart = create_candidate_sentiment_chart(candidate_df)
                    st.plotly_chart(candidate_chart, use_container_width=True)
                    
                    # Show top candidates table
                    st.write("**Top Candidates by Message Count:**")
                    display_df = candidate_df[['candidate_name', 'message_count', 'avg_sentiment', 'positive_pct']].head(10)
                    display_df.columns = ['Candidate', 'Messages', 'Avg Sentiment', 'Positive %']
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No candidate sentiment data available")
            
            with col2:
                st.subheader("🗺️ Regional Sentiment Analysis")
                with next(get_session()) as db:
                    regional_df = sentiment_service.get_regional_sentiment_analysis(db)
                
                if not regional_df.empty:
                    regional_chart = create_regional_sentiment_chart(regional_df)
                    st.plotly_chart(regional_chart, use_container_width=True)
                    
                    # Show regional summary table
                    st.write("**Regional Summary:**")
                    display_df = regional_df[['region', 'message_count', 'avg_sentiment']].copy()
                    display_df.columns = ['Region', 'Messages', 'Avg Sentiment']
                    display_df['Avg Sentiment'] = display_df['Avg Sentiment'].round(3)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No regional sentiment data available")
            
            # Emotion analysis
            st.subheader("😊 Emotional Content Analysis")
            with next(get_session()) as db:
                emotion_data = sentiment_service.get_emotion_analysis_data(db)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                emotion_chart = create_emotion_analysis_chart(emotion_data)
                st.plotly_chart(emotion_chart, use_container_width=True)
            
            with col2:
                if emotion_data["emotion_totals"]:
                    st.write("**Emotion Summary:**")
                    emotion_summary = []
                    for emotion, avg_score in emotion_data["emotion_averages"].items():
                        if emotion != 'neutral':
                            count = emotion_data["emotion_counts"].get(emotion, 0)
                            emotion_summary.append({
                                'Emotion': emotion.title(),
                                'Avg Intensity': f"{avg_score:.3f}",
                                'Messages': count
                            })
                    
                    if emotion_summary:
                        emotion_df = pd.DataFrame(emotion_summary)
                        st.dataframe(emotion_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("Only neutral emotions detected")
                else:
                    st.info("No emotion data available")
            
            # Detailed messages with sentiment
            st.subheader("📝 Messages with Sentiment Analysis")
            
            # Filters for detailed messages
            col1, col2, col3 = st.columns(3)
            
            with col1:
                sentiment_filter = st.selectbox(
                    "Filter by Sentiment",
                    options=["All", "positive", "negative", "neutral"],
                    help="Filter messages by sentiment classification"
                )
            
            with col2:
                tone_filter = st.selectbox(
                    "Filter by Political Tone",
                    options=["All", "aggressive", "diplomatic", "populist", "nationalist"],
                    help="Filter messages by political tone"
                )
            
            with col3:
                message_limit = st.number_input(
                    "Number of Messages",
                    min_value=5,
                    max_value=50,
                    value=20,
                    help="Number of messages to display"
                )
            
            # Apply filters
            sentiment_filter_val = None if sentiment_filter == "All" else sentiment_filter
            tone_filter_val = None if tone_filter == "All" else tone_filter
            
            with next(get_session()) as db:
                detailed_messages = sentiment_service.get_detailed_messages_with_sentiment(
                    db,
                    limit=message_limit,
                    sentiment_filter=sentiment_filter_val,
                    tone_filter=tone_filter_val
                )
            
            display_detailed_messages_table(detailed_messages, show_sentiment=True)
            
            # Analysis controls at the bottom
            st.markdown("---")
            generate_button, analyze_count = create_sentiment_analysis_controls()
            
            if generate_button:
                with st.spinner("Generating additional sentiment data..."):
                    with next(get_session()) as db:
                        result = sentiment_service.generate_dummy_sentiment_batch(db, limit=analyze_count)
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()  # Refresh the dashboard
                    else:
                        st.error(result["message"])
    
    with tab5:
        # Topic Modeling Dashboard
        st.subheader("📊 Topic Modeling Dashboard")
        
        # Initialize topic service
        topic_service = TopicDashboardService()
        
        # Get topic overview
        with next(get_session()) as db:
            topic_overview_data = topic_service.get_topic_overview(db)
        
        # Display overview metrics
        display_topic_overview_metrics(topic_overview_data)
        
        # Check if we have topic data
        if topic_overview_data["needs_analysis"]:
            st.warning("⚠️ No topic modeling data found. Generate some test data to explore the dashboard features.")
            
            # Show controls for generating test data
            generate_button, analyze_count = create_topic_analysis_controls()
            
            if generate_button:
                with st.spinner("Generating dummy topic data..."):
                    with next(get_session()) as db:
                        result = topic_service.generate_dummy_topic_batch(db, limit=analyze_count)
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()  # Refresh the dashboard
                    else:
                        st.error(result["message"])
        else:
            # We have topic data, show visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🥧 Topic Distribution")
                with next(get_session()) as db:
                    distribution_data = topic_service.get_topic_distribution_data(db)
                distribution_chart = create_topic_distribution_chart(distribution_data)
                st.plotly_chart(distribution_chart, use_container_width=True, key="topic_distribution_chart")
            
            with col2:
                st.subheader("🔥 Trending Topics")
                with next(get_session()) as db:
                    trending_data = topic_service.get_trending_topics(db, days=7, limit=8)
                trending_chart = create_trending_topics_chart(trending_data)
                st.plotly_chart(trending_chart, use_container_width=True, key="trending_topics_chart")
            
            # Topic trends over time
            st.subheader("📈 Topic Activity Over Time")
            
            # Period selector for trends
            col1, col2 = st.columns([3, 1])
            with col2:
                topic_trend_days = st.selectbox(
                    "Time Period",
                    options=[7, 14, 30, 60, 90],
                    index=2,  # Default to 30 days
                    key="topic_trend_days",
                    help="Select number of days for topic trend analysis"
                )
            
            with next(get_session()) as db:
                topic_trends_data = topic_service.get_topic_trends_over_time(db, days=topic_trend_days)
            topic_trends_chart = create_topic_trends_chart(topic_trends_data)
            st.plotly_chart(topic_trends_chart, use_container_width=True, key="topic_trends_chart")
            
            # Candidate and regional analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("👥 Candidate Topic Analysis")
                with next(get_session()) as db:
                    candidate_topics_data = topic_service.get_candidate_topic_analysis(db, limit=10)
                
                if candidate_topics_data["candidate_topic_analysis"]:
                    candidate_topics_chart = create_candidate_topics_chart(candidate_topics_data)
                    st.plotly_chart(candidate_topics_chart, use_container_width=True, key="candidate_topics_chart")
                    
                    # Show top candidates table
                    st.write("**Top Candidates by Topic Diversity:**")
                    candidate_summary = []
                    for candidate in candidate_topics_data["candidate_topic_analysis"][:5]:
                        candidate_summary.append({
                            'Candidate': candidate['candidate_name'],
                            'Messages': candidate['total_messages'],
                            'Topics': candidate['topic_diversity'],
                            'Top Topic': candidate['top_topics'][0]['topic_name'] if candidate['top_topics'] else 'None'
                        })
                    
                    if candidate_summary:
                        candidate_df = pd.DataFrame(candidate_summary)
                        st.dataframe(candidate_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No candidate topic data available")
            
            with col2:
                st.subheader("🗺️ Regional Topic Analysis")
                with next(get_session()) as db:
                    regional_topics_df = topic_service.get_regional_topic_analysis(db)
                
                if not regional_topics_df.empty:
                    regional_topics_chart = create_regional_topics_chart(regional_topics_df)
                    st.plotly_chart(regional_topics_chart, use_container_width=True, key="regional_topics_chart")
                    
                    # Show regional summary table
                    st.write("**Regional Topic Summary:**")
                    regional_summary = regional_topics_df.groupby('region').agg({
                        'message_count': 'sum',
                        'topic_name': 'nunique'
                    }).rename(columns={'topic_name': 'unique_topics'}).reset_index()
                    regional_summary.columns = ['Region', 'Total Messages', 'Unique Topics']
                    st.dataframe(regional_summary, use_container_width=True, hide_index=True)
                else:
                    st.info("No regional topic data available")
            
            # Topic quality analysis
            st.subheader("🎯 Topic Quality Analysis")
            with next(get_session()) as db:
                coherence_data = topic_service.get_topic_coherence_analysis(db)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                coherence_chart = create_topic_coherence_chart(coherence_data)
                st.plotly_chart(coherence_chart, use_container_width=True, key="topic_coherence_chart")
            
            with col2:
                if coherence_data["coherence_data"]:
                    st.write("**Quality Distribution:**")
                    quality_dist = coherence_data["quality_distribution"]
                    quality_summary = pd.DataFrame([
                        {'Quality': 'High (≥0.7)', 'Count': quality_dist['high']},
                        {'Quality': 'Medium (0.5-0.7)', 'Count': quality_dist['medium']},
                        {'Quality': 'Low (<0.5)', 'Count': quality_dist['low']}
                    ])
                    st.dataframe(quality_summary, use_container_width=True, hide_index=True)
                    
                    avg_coherence = coherence_data["avg_coherence"]
                    st.metric(
                        "Average Coherence", 
                        f"{avg_coherence:.3f}",
                        help="Higher scores indicate better topic quality"
                    )
                else:
                    st.info("No coherence data available")
            
            # Topic-sentiment correlation
            st.subheader("🎭 Topic-Sentiment Correlation")
            with next(get_session()) as db:
                topic_sentiment_data = topic_service.get_topic_sentiment_analysis(db)
            
            if topic_sentiment_data["topic_sentiment_analysis"]:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Create a simple correlation chart
                    sentiment_correlation = []
                    for topic in topic_sentiment_data["topic_sentiment_analysis"]:
                        sentiment_correlation.append({
                            'Topic': topic['topic_name'][:30] + "..." if len(topic['topic_name']) > 30 else topic['topic_name'],
                            'Avg Sentiment': topic['avg_sentiment'],
                            'Messages': topic['analyzed_messages']
                        })
                    
                    if sentiment_correlation:
                        corr_df = pd.DataFrame(sentiment_correlation)
                        fig_corr = px.scatter(
                            corr_df,
                            x='Avg Sentiment',
                            y='Topic',
                            size='Messages',
                            title="Topic Sentiment Correlation",
                            labels={'Avg Sentiment': 'Average Sentiment Score'},
                            color='Avg Sentiment',
                            color_continuous_scale='RdYlGn'
                        )
                        fig_corr.update_layout(height=400)
                        st.plotly_chart(fig_corr, use_container_width=True, key="topic_sentiment_correlation_chart")
                
                with col2:
                    st.write("**Topic-Sentiment Summary:**")
                    sentiment_summary = []
                    for topic in topic_sentiment_data["topic_sentiment_analysis"][:5]:
                        sentiment_summary.append({
                            'Topic': topic['topic_name'][:25] + "..." if len(topic['topic_name']) > 25 else topic['topic_name'],
                            'Sentiment': f"{topic['avg_sentiment']:.3f}",
                            'Positive %': f"{topic['positive_pct']:.1f}%"
                        })
                    
                    if sentiment_summary:
                        sentiment_df = pd.DataFrame(sentiment_summary)
                        st.dataframe(sentiment_df, use_container_width=True, hide_index=True)
            else:
                st.info("No topic-sentiment correlation data available. Generate sentiment analysis data first.")
            
            # Detailed messages with topics
            st.subheader("📝 Messages with Topic Classification")
            
            # Filters for detailed messages
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Get available topics for filter
                with next(get_session()) as db:
                    all_topics_data = topic_service.get_topic_distribution_data(db)
                topic_names = ["All"] + [topic["topic_name"] for topic in all_topics_data["topics"]]
                
                topic_filter = st.selectbox(
                    "Filter by Topic",
                    options=topic_names,
                    help="Filter messages by topic classification"
                )
            
            with col2:
                st.write("")  # Spacer
            
            with col3:
                topic_message_limit = st.number_input(
                    "Number of Messages",
                    min_value=5,
                    max_value=50,
                    value=20,
                    key="topic_message_limit",
                    help="Number of messages to display"
                )
            
            # Apply filters
            topic_filter_val = None if topic_filter == "All" else topic_filter
            
            with next(get_session()) as db:
                detailed_topic_messages = topic_service.get_detailed_messages_with_topics(
                    db,
                    limit=topic_message_limit,
                    topic_filter=topic_filter_val
                )
            
            display_detailed_topics_table(detailed_topic_messages, show_topics=True)
            
            # Analysis controls at the bottom
            st.markdown("---")
            generate_button, analyze_count = create_topic_analysis_controls()
            
            if generate_button:
                with st.spinner("Generating additional topic data..."):
                    with next(get_session()) as db:
                        result = topic_service.generate_dummy_topic_batch(db, limit=analyze_count)
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()  # Refresh the dashboard
                    else:
                        st.error(result["message"])
    
    # Recent messages (outside tabs - global view)
    st.subheader("📝 Recent Messages")
    
    # Sort by published date or scraped date
    sort_column = 'published_at' if filtered_messages['published_at'].notna().any() else 'scraped_at'
    recent_messages = filtered_messages.sort_values(sort_column, ascending=False).head(10)
    
    for idx, message in recent_messages.iterrows():
        candidate_info = f" - {message['candidate_name']}" if pd.notna(message['candidate_name']) else ""
        constituency_info = f" ({message['constituency_name']})" if pd.notna(message['constituency_name']) else ""
        
        title = f"{message['source_type'].title()}{candidate_info}{constituency_info} - {message[sort_column].strftime('%Y-%m-%d %H:%M') if pd.notna(message[sort_column]) else 'No date'}"
        
        with st.expander(title):
            st.write(f"**Source:** {message['source_name']}")
            if pd.notna(message['candidate_name']):
                st.write(f"**Candidate:** {message['candidate_name']}")
            if pd.notna(message['constituency_name']):
                st.write(f"**Constituency:** {message['constituency_name']} ({message['region']})")
            if message['url']:
                st.write(f"**URL:** {message['url']}")
            st.write(f"**Type:** {message['message_type'] or 'Unknown'}")
            st.write(f"**Geographic Scope:** {message['geographic_scope'] or 'Unknown'}")
            st.write("**Content:**")
            st.write(message['content'][:500] + "..." if len(message['content']) > 500 else message['content'])
            
            # Show metadata if available
            if message['metadata']:
                st.write("**Metadata:**")
                for key, value in message['metadata'].items():
                    if key not in ['raw_post', 'raw_ad']:  # Skip large raw data
                        st.write(f"- {key}: {value}")
    
    # Export functionality
    st.subheader("📊 Export Data")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Download Messages CSV"):
            csv = filtered_messages.to_csv(index=False)
            st.download_button(
                label="Download Messages",
                data=csv,
                file_name=f"reform_uk_messages_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if not filtered_keywords.empty and st.button("Download Keywords CSV"):
            csv = filtered_keywords.to_csv(index=False)
            st.download_button(
                label="Download Keywords",
                data=csv,
                file_name=f"reform_uk_keywords_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col3:
        if not constituencies_df.empty and st.button("Download Constituencies CSV"):
            csv = constituencies_df.to_csv(index=False)
            st.download_button(
                label="Download Constituencies",
                data=csv,
                file_name=f"reform_uk_constituencies_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col4:
        if not candidates_df.empty and st.button("Download Candidates CSV"):
            csv = candidates_df.to_csv(index=False)
            st.download_button(
                label="Download Candidates",
                data=csv,
                file_name=f"reform_uk_candidates_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )


if __name__ == "__main__":
    main()
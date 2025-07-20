import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from collections import Counter
import os

from src.database import get_session
from src.models import Source, Message, Keyword


st.set_page_config(
    page_title="Reform UK Messaging Analysis",
    page_icon="🏛️",
    layout="wide"
)


@st.cache_data
def load_data():
    """Load data from database with caching."""
    with next(get_session()) as db:
        # Load messages with source information
        messages_query = db.query(Message, Source).join(Source).all()
        
        messages_data = []
        for message, source in messages_query:
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'url': message.url,
                'published_at': message.published_at,
                'scraped_at': message.scraped_at,
                'message_type': message.message_type,
                'source_name': source.name,
                'source_type': source.source_type,
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
    
    messages_df = pd.DataFrame(messages_data)
    keywords_df = pd.DataFrame(keywords_data)
    
    if not messages_df.empty:
        messages_df['published_at'] = pd.to_datetime(messages_df['published_at'])
        messages_df['scraped_at'] = pd.to_datetime(messages_df['scraped_at'])
    
    if not keywords_df.empty:
        keywords_df['published_at'] = pd.to_datetime(keywords_df['published_at'])
    
    return messages_df, keywords_df


def main():
    st.title("🏛️ Reform UK Digital Footprint Analysis")
    st.markdown("Analysis of Reform UK's digital messaging across platforms")
    
    # Add refresh button
    if st.button("🔄 Refresh Data", help="Clear cache and reload data from database"):
        st.cache_data.clear()
        st.rerun()
    
    # Load data
    messages_df, keywords_df = load_data()
    
    if messages_df.empty:
        st.warning("No data found. Please run the scraper first.")
        st.code("python -m src.scrapers.main")
        return
    
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
    
    # Main dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Messages", len(filtered_messages))
    
    with col2:
        st.metric("Unique Keywords", len(filtered_keywords['keyword'].unique()) if not filtered_keywords.empty else 0)
    
    with col3:
        st.metric("Sources", len(filtered_messages['source_type'].unique()))
    
    with col4:
        avg_daily = len(filtered_messages) / max(1, (filtered_messages['published_at'].max() - filtered_messages['published_at'].min()).days)
        st.metric("Avg Daily Messages", f"{avg_daily:.1f}")
    
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
        st.subheader("Message Types")
        if 'message_type' in filtered_messages.columns and not filtered_messages['message_type'].isna().all():
            type_counts = filtered_messages['message_type'].value_counts()
            fig_bar = px.bar(
                x=type_counts.values,
                y=type_counts.index,
                orientation='h',
                title="Messages by Type"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No message type data available")
    
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
    
    # Recent messages
    st.subheader("Recent Messages")
    
    # Sort by published date or scraped date
    sort_column = 'published_at' if filtered_messages['published_at'].notna().any() else 'scraped_at'
    recent_messages = filtered_messages.sort_values(sort_column, ascending=False).head(10)
    
    for idx, message in recent_messages.iterrows():
        with st.expander(f"{message['source_type'].title()} - {message[sort_column].strftime('%Y-%m-%d %H:%M') if pd.notna(message[sort_column]) else 'No date'}"):
            st.write(f"**Source:** {message['source_name']}")
            if message['url']:
                st.write(f"**URL:** {message['url']}")
            st.write(f"**Type:** {message['message_type'] or 'Unknown'}")
            st.write("**Content:**")
            st.write(message['content'][:500] + "..." if len(message['content']) > 500 else message['content'])
            
            # Show metadata if available
            if message['metadata']:
                st.write("**Metadata:**")
                for key, value in message['metadata'].items():
                    if key not in ['raw_post', 'raw_ad']:  # Skip large raw data
                        st.write(f"- {key}: {value}")
    
    # Export functionality
    st.subheader("Export Data")
    
    col1, col2 = st.columns(2)
    
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


if __name__ == "__main__":
    main()
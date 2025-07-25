"""
Streamlit visualization components for topic modeling analysis.

Provides reusable visualization functions for the topic modeling dashboard
with interactive charts, metrics, and data displays.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional
import numpy as np

from .topic_service import TopicDashboardService


def display_topic_overview_metrics(overview_data: Dict):
    """
    Display topic overview metrics in a clean card layout.
    
    Args:
        overview_data: Dictionary from topic_service.get_topic_overview()
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Topics", 
            overview_data["total_topics"],
            help="Total number of political topics identified"
        )
    
    with col2:
        st.metric(
            "Topic Assignments", 
            overview_data["total_assignments"],
            help="Total topic assignments to messages"
        )
    
    with col3:
        coverage = overview_data["coverage"]
        st.metric(
            "Analysis Coverage", 
            f"{coverage:.1f}%",
            help="Percentage of messages with topic assignments"
        )
    
    with col4:
        avg_coherence = overview_data["avg_coherence"]
        coherence_emoji = "🎯" if avg_coherence > 0.7 else "📊" if avg_coherence > 0.5 else "📈"
        st.metric(
            "Avg Coherence", 
            f"{avg_coherence:.3f} {coherence_emoji}",
            help="Average topic coherence score (0-1)"
        )


def create_topic_distribution_chart(distribution_data: Dict) -> go.Figure:
    """
    Create a pie chart showing topic distribution by message count.
    
    Args:
        distribution_data: Dictionary with topic distribution data
        
    Returns:
        Plotly figure object
    """
    topics = distribution_data["topics"]
    
    if not topics:
        # Create empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No topic data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    # Define colors for political topics
    colors = {
        'Immigration and Border Security': '#FF6B6B',  # Red
        'Economic Policy': '#4ECDC4',                  # Teal
        'Healthcare Reform': '#45B7D1',                # Blue
        'Education and Schools': '#96CEB4',            # Green
        'Law and Order': '#FECA57',                    # Yellow
        'European Union Relations': '#FF9FF3',         # Pink
        'Climate and Environment': '#54A0FF',          # Light Blue
        'Housing and Local Issues': '#5F27CD',         # Purple
        'Foreign Policy': '#00D2D3',                   # Cyan
        'Media and Democracy': '#FF7675'               # Light Red
    }
    
    topic_names = [topic["topic_name"] for topic in topics]
    message_counts = [topic["message_count"] for topic in topics]
    chart_colors = [colors.get(name, '#888888') for name in topic_names]
    
    fig = px.pie(
        values=message_counts,
        names=topic_names,
        title="Topic Distribution by Message Count",
        color_discrete_sequence=chart_colors
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>' +
                      'Messages: %{value}<br>' +
                      'Percentage: %{percent}<br>' +
                      '<extra></extra>'
    )
    
    fig.update_layout(
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.01)
    )
    
    return fig


def create_trending_topics_chart(trending_data: Dict) -> go.Figure:
    """
    Create a horizontal bar chart for trending topics.
    
    Args:
        trending_data: Dictionary from topic_service.get_trending_topics()
        
    Returns:
        Plotly figure object
    """
    trending_topics = trending_data["trending_topics"]
    
    if not trending_topics:
        fig = go.Figure()
        fig.add_annotation(
            text="No trending topics data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    # Sort by trend score
    trending_topics = sorted(trending_topics, key=lambda x: x['trend_score'], reverse=True)
    
    topic_names = [topic['topic_name'] for topic in trending_topics]
    trend_scores = [topic['trend_score'] for topic in trending_topics]
    recent_messages = [topic['recent_messages'] for topic in trending_topics]
    
    # Create color scale based on trend score
    colors = px.colors.sequential.Reds
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=topic_names,
        x=trend_scores,
        orientation='h',
        marker_color=trend_scores,
        marker_colorscale='Reds',
        text=[f"Score: {score:.3f}<br>Messages: {msgs}" for score, msgs in zip(trend_scores, recent_messages)],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>' +
                      'Trend Score: %{x:.3f}<br>' +
                      'Recent Messages: %{customdata}<br>' +
                      '<extra></extra>',
        customdata=recent_messages
    ))
    
    fig.update_layout(
        title="Trending Topics by Score",
        xaxis_title="Trend Score",
        yaxis_title="Topic",
        height=max(400, len(topic_names) * 40),
        margin=dict(l=200)
    )
    
    return fig


def create_topic_trends_chart(trends_data: Dict) -> go.Figure:
    """
    Create a line chart showing topic trends over time.
    
    Args:
        trends_data: Dictionary from topic_service.get_topic_trends_over_time()
        
    Returns:
        Plotly figure object
    """
    daily_data = trends_data["daily_data"]
    
    if not daily_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No trend data available for the selected period",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    # Convert daily data to DataFrame for easier plotting
    trend_df_data = []
    for date, topics in daily_data.items():
        for topic_name, topic_data in topics.items():
            trend_df_data.append({
                'date': date,
                'topic_name': topic_name,
                'message_count': topic_data['message_count'],
                'avg_probability': topic_data['avg_probability']
            })
    
    if not trend_df_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No trend data to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    df = pd.DataFrame(trend_df_data)
    df['date'] = pd.to_datetime(df['date'])
    
    # Create line chart with one line per topic
    fig = px.line(
        df,
        x='date',
        y='message_count',
        color='topic_name',
        title="Topic Activity Over Time",
        labels={
            'date': 'Date',
            'message_count': 'Daily Message Count',
            'topic_name': 'Topic'
        }
    )
    
    fig.update_layout(
        height=500,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_candidate_topics_chart(candidate_data: Dict) -> go.Figure:
    """
    Create a stacked bar chart showing candidate topic distributions.
    
    Args:
        candidate_data: Dictionary from topic_service.get_candidate_topic_analysis()
        
    Returns:
        Plotly figure object
    """
    candidates = candidate_data["candidate_topic_analysis"]
    
    if not candidates:
        fig = go.Figure()
        fig.add_annotation(
            text="No candidate topic data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    # Prepare data for stacked bar chart
    candidate_names = []
    topic_data = {}
    
    for candidate in candidates[:10]:  # Top 10 candidates
        candidate_names.append(candidate['candidate_name'])
        
        for topic in candidate['top_topics'][:5]:  # Top 5 topics per candidate
            topic_name = topic['topic_name']
            if topic_name not in topic_data:
                topic_data[topic_name] = []
            topic_data[topic_name].append(topic['message_count'])
        
        # Pad missing topics with zeros
        for topic_name in topic_data:
            if len(topic_data[topic_name]) < len(candidate_names):
                topic_data[topic_name].extend([0] * (len(candidate_names) - len(topic_data[topic_name])))
    
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3
    for i, (topic_name, counts) in enumerate(topic_data.items()):
        fig.add_trace(go.Bar(
            name=topic_name,
            x=candidate_names,
            y=counts,
            marker_color=colors[i % len(colors)],
            hovertemplate='<b>%{x}</b><br>' +
                          f'{topic_name}: %{{y}} messages<br>' +
                          '<extra></extra>'
        ))
    
    fig.update_layout(
        title="Candidate Topic Distribution",
        xaxis_title="Candidate",
        yaxis_title="Message Count",
        barmode='stack',
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_topic_coherence_chart(coherence_data: Dict) -> go.Figure:
    """
    Create a scatter plot showing topic coherence vs message count.
    
    Args:
        coherence_data: Dictionary from topic_service.get_topic_coherence_analysis()
        
    Returns:
        Plotly figure object
    """
    coherence_topics = coherence_data["coherence_data"]
    
    if not coherence_topics:
        fig = go.Figure()
        fig.add_annotation(
            text="No coherence data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    topic_names = [topic['topic_name'] for topic in coherence_topics]
    coherence_scores = [topic['coherence_score'] for topic in coherence_topics]
    message_counts = [topic['message_count'] for topic in coherence_topics]
    trend_scores = [topic['trend_score'] for topic in coherence_topics]
    
    fig = px.scatter(
        x=coherence_scores,
        y=message_counts,
        size=trend_scores,
        hover_name=topic_names,
        color=coherence_scores,
        color_continuous_scale='Viridis',
        title="Topic Quality: Coherence vs Message Count",
        labels={
            'x': 'Coherence Score',
            'y': 'Message Count',
            'color': 'Coherence'
        }
    )
    
    # Add reference lines
    fig.add_vline(x=0.7, line_dash="dash", line_color="green", line_width=1, 
                  annotation_text="High Quality")
    fig.add_vline(x=0.5, line_dash="dash", line_color="orange", line_width=1,
                  annotation_text="Medium Quality")
    
    fig.update_traces(
        hovertemplate='<b>%{hovertext}</b><br>' +
                      'Coherence: %{x:.3f}<br>' +
                      'Messages: %{y}<br>' +
                      'Trend Score: %{marker.size:.3f}<br>' +
                      '<extra></extra>'
    )
    
    fig.update_layout(height=500)
    
    return fig


def create_regional_topics_chart(regional_df: pd.DataFrame) -> go.Figure:
    """
    Create a heatmap showing topic distribution by region.
    
    Args:
        regional_df: DataFrame from topic_service.get_regional_topic_analysis()
        
    Returns:
        Plotly figure object
    """
    if regional_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No regional topic data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    # Pivot data for heatmap
    heatmap_data = regional_df.pivot_table(
        index='region',
        columns='topic_name',
        values='message_count',
        fill_value=0
    )
    
    fig = px.imshow(
        heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        color_continuous_scale='Blues',
        title="Regional Topic Distribution Heatmap"
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Topic",
        yaxis_title="Region"
    )
    
    return fig


def display_detailed_topics_table(messages_df: pd.DataFrame, show_topics: bool = True):
    """
    Display a formatted table of messages with topic assignments.
    
    Args:
        messages_df: DataFrame from topic_service.get_detailed_messages_with_topics()
        show_topics: Whether to display topic columns
    """
    if messages_df.empty:
        st.info("No messages found with the selected filters.")
        return
    
    # Prepare display DataFrame
    display_df = messages_df.copy()
    
    # Format content preview
    display_df['content_preview'] = display_df['content'].apply(
        lambda x: x[:100] + "..." if len(x) > 100 else x
    )
    
    # Format topic probability with indicator
    if show_topics and 'topic_probability' in display_df.columns:
        display_df['topic_display'] = display_df.apply(
            lambda row: f"{row['primary_topic']} ({row['topic_probability']:.2f})", 
            axis=1
        )
    
    # Select columns for display
    if show_topics:
        columns = [
            'candidate_name', 'constituency_name', 'region', 
            'content_preview', 'topic_display', 'published_at'
        ]
        column_config = {
            'candidate_name': st.column_config.TextColumn('Candidate'),
            'constituency_name': st.column_config.TextColumn('Constituency'),
            'region': st.column_config.TextColumn('Region'),
            'content_preview': st.column_config.TextColumn('Content Preview'),
            'topic_display': st.column_config.TextColumn('Primary Topic'),
            'published_at': st.column_config.DatetimeColumn('Published')
        }
    else:
        columns = [
            'candidate_name', 'constituency_name', 'region',
            'content_preview', 'published_at'
        ]
        column_config = {
            'candidate_name': st.column_config.TextColumn('Candidate'),
            'constituency_name': st.column_config.TextColumn('Constituency'),
            'region': st.column_config.TextColumn('Region'),
            'content_preview': st.column_config.TextColumn('Content Preview'),
            'published_at': st.column_config.DatetimeColumn('Published')
        }
    
    # Filter available columns
    available_columns = [col for col in columns if col in display_df.columns]
    available_config = {k: v for k, v in column_config.items() if k in display_df.columns}
    
    st.dataframe(
        display_df[available_columns],
        column_config=available_config,
        use_container_width=True,
        hide_index=True
    )


def create_topic_analysis_controls():
    """
    Create interactive controls for topic analysis operations.
    
    Returns:
        Tuple of (generate_button_clicked, analyze_count)
    """
    st.subheader("🔧 Topic Analysis Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Generate Test Data**")
        analyze_count = st.number_input(
            "Number of messages to analyze",
            min_value=1,
            max_value=100,
            value=20,
            help="Generate dummy topic assignments for testing"
        )
        
        generate_button = st.button(
            "🎲 Generate Dummy Topic Data",
            help="Create realistic test topic assignments for dashboard testing"
        )
    
    with col2:
        st.write("**Analysis Status**")
        st.info("""
        **Dummy Data**: Fast generation for testing and development
        
        **Real Analysis**: Uses LDA topic modeling for actual topic detection
        
        Use dummy data for rapid testing and real analysis for production insights.
        """)
    
    return generate_button, analyze_count
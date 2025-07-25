"""
Streamlit visualization components for engagement analytics.

Provides reusable visualization functions for the engagement analytics dashboard
with interactive charts, metrics, and data displays.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional
import numpy as np

from .engagement_service import EngagementDashboardService


def display_engagement_overview_metrics(overview_data: Dict):
    """
    Display engagement overview metrics in a clean card layout.
    
    Args:
        overview_data: Dictionary from engagement_service.get_engagement_overview()
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Messages", 
            overview_data["total_messages"],
            help="Total number of messages in the system"
        )
    
    with col2:
        st.metric(
            "Analyzed Messages", 
            overview_data["analyzed_messages"],
            help="Messages with engagement analysis"
        )
    
    with col3:
        coverage = overview_data["coverage"]
        st.metric(
            "Analysis Coverage", 
            f"{coverage:.1f}%",
            help="Percentage of messages with engagement analysis"
        )
    
    with col4:
        avg_engagement = overview_data["avg_engagement"]
        engagement_emoji = "🚀" if avg_engagement > 0.7 else "📈" if avg_engagement > 0.4 else "📊"
        st.metric(
            "Avg Engagement", 
            f"{avg_engagement:.3f} {engagement_emoji}",
            help="Average engagement score (0-1)"
        )


def create_engagement_distribution_chart(distribution_data: Dict) -> go.Figure:
    """
    Create a histogram showing engagement score distribution.
    
    Args:
        distribution_data: Dictionary with engagement distribution data
        
    Returns:
        Plotly figure object
    """
    engagement_scores = distribution_data["engagement_scores"]
    
    if not engagement_scores:
        # Create empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No engagement data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    fig = go.Figure()
    
    # Add engagement score histogram
    fig.add_trace(go.Histogram(
        x=engagement_scores,
        nbinsx=20,
        name="Engagement Score",
        marker_color='#1f77b4',
        opacity=0.7
    ))
    
    # Add average line
    avg_score = np.mean(engagement_scores)
    fig.add_vline(
        x=avg_score,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Average: {avg_score:.3f}"
    )
    
    fig.update_layout(
        title="Engagement Score Distribution",
        xaxis_title="Engagement Score",
        yaxis_title="Number of Messages",
        height=400,
        showlegend=False
    )
    
    return fig


def create_platform_performance_chart(platform_data: Dict) -> go.Figure:
    """
    Create a grouped bar chart showing platform performance comparison.
    
    Args:
        platform_data: Dictionary from engagement_service.get_platform_performance_comparison()
        
    Returns:
        Plotly figure object
    """
    platforms = platform_data["platform_comparison"]
    
    if not platforms:
        fig = go.Figure()
        fig.add_annotation(
            text="No platform performance data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    platform_names = [p["platform"] for p in platforms]
    engagement_scores = [p["avg_engagement"] for p in platforms]
    virality_scores = [p["avg_virality"] for p in platforms]
    influence_scores = [p["avg_influence"] for p in platforms]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Engagement',
        x=platform_names,
        y=engagement_scores,
        marker_color='#1f77b4',
        hovertemplate='<b>%{x}</b><br>Engagement: %{y:.3f}<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        name='Virality',
        x=platform_names,
        y=virality_scores,
        marker_color='#ff7f0e',
        hovertemplate='<b>%{x}</b><br>Virality: %{y:.3f}<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        name='Influence',
        x=platform_names,
        y=influence_scores,
        marker_color='#2ca02c',
        hovertemplate='<b>%{x}</b><br>Influence: %{y:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Platform Performance Comparison",
        xaxis_title="Platform",
        yaxis_title="Score",
        barmode='group',
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_viral_content_chart(viral_data: Dict) -> go.Figure:
    """
    Create a bar chart showing viral content by virality score.
    
    Args:
        viral_data: Dictionary from engagement_service.get_viral_content_analysis()
        
    Returns:
        Plotly figure object
    """
    viral_content = viral_data["viral_content"]
    
    if not viral_content:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No viral content found above threshold {viral_data['viral_threshold']}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    # Sort by virality score
    viral_content = sorted(viral_content, key=lambda x: x['virality_score'], reverse=True)
    
    # Take top 10 for readability
    viral_content = viral_content[:10]
    
    content_labels = [content['content_preview'][:50] + "..." for content in viral_content]
    virality_scores = [content['virality_score'] for content in viral_content]
    engagement_scores = [content['engagement_score'] for content in viral_content]
    candidates = [content['candidate_name'] for content in viral_content]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=content_labels,
        x=virality_scores,
        orientation='h',
        marker_color=virality_scores,
        marker_colorscale='Reds',
        text=[f"V:{v:.3f} E:{e:.3f}" for v, e in zip(virality_scores, engagement_scores)],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>' +
                      'Virality: %{x:.3f}<br>' +
                      'Candidate: %{customdata}<br>' +
                      '<extra></extra>',
        customdata=candidates
    ))
    
    fig.update_layout(
        title=f"Top Viral Content (Threshold: {viral_data['viral_threshold']})",
        xaxis_title="Virality Score",
        yaxis_title="Content",
        height=max(400, len(content_labels) * 40),
        margin=dict(l=300)
    )
    
    return fig


def create_engagement_trends_chart(trends_data: Dict) -> go.Figure:
    """
    Create a line chart showing engagement trends over time.
    
    Args:
        trends_data: Dictionary from engagement_service.get_engagement_trends_over_time()
        
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
    
    # Convert to DataFrame for easier plotting
    dates = list(daily_data.keys())
    engagement_scores = [daily_data[date]['avg_engagement'] for date in dates]
    virality_scores = [daily_data[date]['avg_virality'] for date in dates]
    influence_scores = [daily_data[date]['avg_influence'] for date in dates]
    message_counts = [daily_data[date]['message_count'] for date in dates]
    
    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add engagement metrics
    fig.add_trace(
        go.Scatter(x=dates, y=engagement_scores, name="Engagement", line=dict(color='#1f77b4')),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(x=dates, y=virality_scores, name="Virality", line=dict(color='#ff7f0e')),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(x=dates, y=influence_scores, name="Influence", line=dict(color='#2ca02c')),
        secondary_y=False,
    )
    
    # Add message count
    fig.add_trace(
        go.Scatter(x=dates, y=message_counts, name="Message Count", 
                  line=dict(color='rgba(128, 128, 128, 0.5)', dash='dot')),
        secondary_y=True,
    )
    
    # Set y-axes titles
    fig.update_yaxes(title_text="Engagement Scores", secondary_y=False)
    fig.update_yaxes(title_text="Message Count", secondary_y=True)
    
    fig.update_layout(
        title="Engagement Trends Over Time",
        xaxis_title="Date",
        height=500,
        hovermode='x unified'
    )
    
    return fig


def create_candidate_engagement_chart(candidate_df: pd.DataFrame) -> go.Figure:
    """
    Create a scatter plot showing candidate engagement performance.
    
    Args:
        candidate_df: DataFrame from engagement_service.get_candidate_engagement_analysis()
        
    Returns:
        Plotly figure object
    """
    if candidate_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No candidate engagement data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    fig = px.scatter(
        candidate_df,
        x='avg_engagement',
        y='avg_virality',
        size='message_count',
        color='avg_influence',
        hover_name='candidate_name',
        hover_data=['constituency_name', 'region', 'viral_content'],
        color_continuous_scale='Viridis',
        title="Candidate Engagement Performance",
        labels={
            'avg_engagement': 'Average Engagement',
            'avg_virality': 'Average Virality',
            'avg_influence': 'Average Influence'
        }
    )
    
    fig.update_traces(
        hovertemplate='<b>%{hovertext}</b><br>' +
                      'Engagement: %{x:.3f}<br>' +
                      'Virality: %{y:.3f}<br>' +
                      'Messages: %{marker.size}<br>' +
                      'Constituency: %{customdata[0]}<br>' +
                      'Region: %{customdata[1]}<br>' +
                      'Viral Content: %{customdata[2]}<br>' +
                      '<extra></extra>'
    )
    
    fig.update_layout(height=500)
    
    return fig


def create_engagement_metrics_comparison(overview_data: Dict) -> go.Figure:
    """
    Create a radar chart comparing different engagement metrics.
    
    Args:
        overview_data: Dictionary with engagement overview data
        
    Returns:
        Plotly figure object
    """
    categories = ['Engagement', 'Virality', 'Influence']
    values = [
        overview_data.get("avg_engagement", 0),
        overview_data.get("avg_virality", 0),
        overview_data.get("avg_influence", 0)
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Current Performance',
        line_color='rgba(31, 119, 180, 0.8)'
    ))
    
    # Add benchmark line at 0.5
    benchmark_values = [0.5, 0.5, 0.5]
    fig.add_trace(go.Scatterpolar(
        r=benchmark_values,
        theta=categories,
        fill=None,
        name='Benchmark (0.5)',
        line=dict(color='rgba(255, 0, 0, 0.8)', dash='dash')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        title="Engagement Metrics Overview",
        height=400
    )
    
    return fig


def display_top_performing_table(messages_df: pd.DataFrame, metric: str = "engagement"):
    """
    Display a formatted table of top performing messages.
    
    Args:
        messages_df: DataFrame from engagement_service.get_top_performing_messages()
        metric: Metric being displayed
    """
    if messages_df.empty:
        st.info("No top performing messages found.")
        return
    
    # Prepare display DataFrame
    display_df = messages_df.copy()
    
    # Format content preview
    display_df['content_preview'] = display_df['content'].apply(
        lambda x: x[:100] + "..." if len(x) > 100 else x
    )
    
    # Format scores
    display_df['engagement_display'] = display_df['engagement_score'].apply(lambda x: f"{x:.3f}")
    display_df['virality_display'] = display_df['virality_score'].apply(lambda x: f"{x:.3f}")
    display_df['influence_display'] = display_df['influence_score'].apply(lambda x: f"{x:.3f}")
    
    # Select columns for display
    columns = [
        'candidate_name', 'source_type', 'content_preview', 
        'engagement_display', 'virality_display', 'influence_display', 'published_at'
    ]
    
    column_config = {
        'candidate_name': st.column_config.TextColumn('Candidate'),
        'source_type': st.column_config.TextColumn('Platform'),
        'content_preview': st.column_config.TextColumn('Content Preview'),
        'engagement_display': st.column_config.TextColumn('Engagement'),
        'virality_display': st.column_config.TextColumn('Virality'),
        'influence_display': st.column_config.TextColumn('Influence'),
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


def create_engagement_analysis_controls():
    """
    Create interactive controls for engagement analysis operations.
    
    Returns:
        Tuple of (generate_button_clicked, analyze_count)
    """
    st.subheader("🔧 Engagement Analysis Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Generate Test Data**")
        analyze_count = st.number_input(
            "Number of messages to analyze",
            min_value=1,
            max_value=100,
            value=20,
            help="Generate dummy engagement data for testing"
        )
        
        generate_button = st.button(
            "⚡ Generate Dummy Engagement Data",
            help="Create realistic test engagement analysis for dashboard testing"
        )
    
    with col2:
        st.write("**Analysis Status**")
        st.info("""
        **Dummy Data**: Fast generation for testing and development
        
        **Real Analysis**: Uses platform-specific metrics for actual engagement scoring
        
        Use dummy data for rapid testing and real analysis for production insights.
        """)
    
    return generate_button, analyze_count


def create_viral_threshold_selector():
    """
    Create a slider for viral content threshold selection.
    
    Returns:
        Selected threshold value
    """
    threshold = st.slider(
        "Viral Content Threshold",
        min_value=0.1,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Minimum virality score to classify content as viral"
    )
    
    return threshold
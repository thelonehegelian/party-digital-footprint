"""
Streamlit visualization components for sentiment analysis.

Provides reusable visualization functions for the sentiment analysis dashboard
with interactive charts, metrics, and data displays.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional
import numpy as np

from .sentiment_service import SentimentDashboardService


def display_sentiment_overview_metrics(overview_data: Dict):
    """
    Display sentiment overview metrics in a clean card layout.
    
    Args:
        overview_data: Dictionary from sentiment_service.get_sentiment_overview()
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Messages", 
            overview_data["total_messages"],
            help="Total number of messages in the database"
        )
    
    with col2:
        st.metric(
            "Analyzed Messages", 
            overview_data["total_analyzed"],
            help="Messages with sentiment analysis completed"
        )
    
    with col3:
        coverage = overview_data["analysis_coverage"]
        st.metric(
            "Analysis Coverage", 
            f"{coverage:.1f}%",
            help="Percentage of messages with sentiment analysis"
        )
    
    with col4:
        avg_sentiment = overview_data["average_sentiment_score"]
        sentiment_emoji = "😊" if avg_sentiment > 0.1 else "😠" if avg_sentiment < -0.1 else "😐"
        st.metric(
            "Avg Sentiment", 
            f"{avg_sentiment:.3f} {sentiment_emoji}",
            help="Average sentiment score (-1 to 1)"
        )


def create_sentiment_distribution_chart(overview_data: Dict) -> go.Figure:
    """
    Create a pie chart showing sentiment distribution.
    
    Args:
        overview_data: Dictionary with sentiment_distribution data
        
    Returns:
        Plotly figure object
    """
    sentiment_dist = overview_data["sentiment_distribution"]
    
    if not sentiment_dist:
        # Create empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No sentiment data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    # Define colors for sentiment categories
    colors = {
        'positive': '#2E8B57',  # Sea Green
        'negative': '#DC143C',  # Crimson
        'neutral': '#4682B4'    # Steel Blue
    }
    
    labels = list(sentiment_dist.keys())
    values = list(sentiment_dist.values())
    chart_colors = [colors.get(label, '#888888') for label in labels]
    
    fig = px.pie(
        values=values,
        names=labels,
        title="Sentiment Distribution",
        color_discrete_sequence=chart_colors
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>' +
                      'Count: %{value}<br>' +
                      'Percentage: %{percent}<br>' +
                      '<extra></extra>'
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_political_tone_chart(tone_data: Dict) -> go.Figure:
    """
    Create a horizontal bar chart for political tone distribution.
    
    Args:
        tone_data: Dictionary from sentiment_service.get_political_tone_analysis()
        
    Returns:
        Plotly figure object
    """
    tone_dist = tone_data["tone_distribution"]
    tone_conf = tone_data["tone_confidence"]
    
    if not tone_dist:
        fig = go.Figure()
        fig.add_annotation(
            text="No political tone data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    # Define colors for political tones
    colors = {
        'aggressive': '#FF6B6B',    # Red
        'diplomatic': '#4ECDC4',    # Teal
        'populist': '#45B7D1',      # Blue
        'nationalist': '#96CEB4'    # Green
    }
    
    tones = list(tone_dist.keys())
    counts = list(tone_dist.values())
    confidences = [tone_conf.get(tone, 0) for tone in tones]
    chart_colors = [colors.get(tone, '#888888') for tone in tones]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=tones,
        x=counts,
        orientation='h',
        marker_color=chart_colors,
        text=[f"{count} (conf: {conf:.2f})" for count, conf in zip(counts, confidences)],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>' +
                      'Count: %{x}<br>' +
                      'Confidence: %{customdata:.3f}<br>' +
                      '<extra></extra>',
        customdata=confidences
    ))
    
    fig.update_layout(
        title="Political Tone Distribution",
        xaxis_title="Number of Messages",
        yaxis_title="Political Tone",
        height=400,
        margin=dict(l=100)
    )
    
    return fig


def create_sentiment_trends_chart(trends_data: Dict) -> go.Figure:
    """
    Create a line chart showing sentiment trends over time.
    
    Args:
        trends_data: Dictionary from sentiment_service.get_sentiment_trends()
        
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
    
    df = pd.DataFrame(daily_data)
    df['date'] = pd.to_datetime(df['date'])
    
    # Create subplots with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add sentiment line
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['avg_sentiment'],
            mode='lines+markers',
            name='Average Sentiment',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8),
            hovertemplate='<b>Date:</b> %{x}<br>' +
                          '<b>Avg Sentiment:</b> %{y:.3f}<br>' +
                          '<extra></extra>'
        ),
        secondary_y=False,
    )
    
    # Add message count bars
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['message_count'],
            name='Message Count',
            opacity=0.3,
            marker_color='#ff7f0e',
            hovertemplate='<b>Date:</b> %{x}<br>' +
                          '<b>Messages:</b> %{y}<br>' +
                          '<extra></extra>'
        ),
        secondary_y=True,
    )
    
    # Add reference line at zero sentiment
    fig.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1, secondary_y=False)
    
    # Update layout
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Average Sentiment Score", secondary_y=False)
    fig.update_yaxes(title_text="Message Count", secondary_y=True)
    
    fig.update_layout(
        title="Sentiment Trends Over Time",
        height=500,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_candidate_sentiment_chart(candidate_df: pd.DataFrame) -> go.Figure:
    """
    Create a scatter plot showing candidate sentiment comparison.
    
    Args:
        candidate_df: DataFrame from sentiment_service.get_candidate_sentiment_comparison()
        
    Returns:
        Plotly figure object
    """
    if candidate_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No candidate sentiment data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    # Create bubble chart
    fig = px.scatter(
        candidate_df,
        x='avg_sentiment',
        y='avg_confidence',
        size='message_count',
        hover_name='candidate_name',
        color='positive_pct',
        color_continuous_scale='RdYlGn',
        title="Candidate Sentiment Analysis",
        labels={
            'avg_sentiment': 'Average Sentiment Score',
            'avg_confidence': 'Average Confidence',
            'positive_pct': 'Positive %'
        }
    )
    
    # Add reference lines
    fig.add_vline(x=0, line_dash="dash", line_color="gray", line_width=1)
    fig.add_hline(y=0.7, line_dash="dash", line_color="gray", line_width=1)
    
    # Update hover template
    fig.update_traces(
        hovertemplate='<b>%{hovertext}</b><br>' +
                      'Avg Sentiment: %{x:.3f}<br>' +
                      'Avg Confidence: %{y:.3f}<br>' +
                      'Messages: %{marker.size}<br>' +
                      'Positive: %{marker.color:.1f}%<br>' +
                      '<extra></extra>'
    )
    
    fig.update_layout(
        height=500,
        xaxis=dict(range=[-1, 1]),
        yaxis=dict(range=[0, 1])
    )
    
    return fig


def create_regional_sentiment_chart(regional_df: pd.DataFrame) -> go.Figure:
    """
    Create a horizontal bar chart for regional sentiment analysis.
    
    Args:
        regional_df: DataFrame from sentiment_service.get_regional_sentiment_analysis()
        
    Returns:
        Plotly figure object
    """
    if regional_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No regional sentiment data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    # Sort by message count for better visualization
    regional_df = regional_df.sort_values('message_count', ascending=True)
    
    # Create color mapping based on sentiment
    colors = []
    for sentiment in regional_df['avg_sentiment']:
        if sentiment > 0.1:
            colors.append('#2E8B57')  # Green for positive
        elif sentiment < -0.1:
            colors.append('#DC143C')  # Red for negative
        else:
            colors.append('#4682B4')  # Blue for neutral
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=regional_df['region'],
        x=regional_df['message_count'],
        orientation='h',
        marker_color=colors,
        text=[f"Sentiment: {sent:.3f}" for sent in regional_df['avg_sentiment']],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>' +
                      'Messages: %{x}<br>' +
                      'Avg Sentiment: %{customdata:.3f}<br>' +
                      '<extra></extra>',
        customdata=regional_df['avg_sentiment']
    ))
    
    fig.update_layout(
        title="Regional Message Activity & Sentiment",
        xaxis_title="Number of Messages",
        yaxis_title="Region",
        height=400,
        margin=dict(l=150)
    )
    
    return fig


def create_emotion_analysis_chart(emotion_data: Dict) -> go.Figure:
    """
    Create a radar chart for emotion analysis.
    
    Args:
        emotion_data: Dictionary from sentiment_service.get_emotion_analysis_data()
        
    Returns:
        Plotly figure object
    """
    emotion_averages = emotion_data["emotion_averages"]
    emotion_counts = emotion_data["emotion_counts"]
    
    if not emotion_averages or 'neutral' in emotion_averages and len(emotion_averages) == 1:
        fig = go.Figure()
        fig.add_annotation(
            text="No emotion data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    # Filter out neutral emotions for cleaner visualization
    filtered_emotions = {k: v for k, v in emotion_averages.items() if k != 'neutral'}
    
    if not filtered_emotions:
        fig = go.Figure()
        fig.add_annotation(
            text="Only neutral emotions detected",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(height=300)
        return fig
    
    emotions = list(filtered_emotions.keys())
    values = list(filtered_emotions.values())
    counts = [emotion_counts.get(emotion, 0) for emotion in emotions]
    
    # Create radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=emotions,
        fill='toself',
        name='Emotion Intensity',
        marker_color='rgba(66, 165, 245, 0.6)',
        line=dict(color='rgba(66, 165, 245, 1)', width=2),
        hovertemplate='<b>%{theta}</b><br>' +
                      'Intensity: %{r:.3f}<br>' +
                      'Count: %{customdata}<br>' +
                      '<extra></extra>',
        customdata=counts
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(values) * 1.1] if values else [0, 1]
            )),
        title="Emotional Content Analysis",
        height=500
    )
    
    return fig


def display_detailed_messages_table(messages_df: pd.DataFrame, show_sentiment: bool = True):
    """
    Display a formatted table of messages with sentiment data.
    
    Args:
        messages_df: DataFrame from sentiment_service.get_detailed_messages_with_sentiment()
        show_sentiment: Whether to display sentiment columns
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
    
    # Format sentiment score with emoji
    if show_sentiment and 'sentiment_score' in display_df.columns:
        display_df['sentiment_display'] = display_df.apply(
            lambda row: f"{row['sentiment_score']:.3f} " + 
                       ("😊" if row['sentiment_score'] > 0.1 else 
                        "😠" if row['sentiment_score'] < -0.1 else "😐"), 
            axis=1
        )
    
    # Select columns for display
    if show_sentiment:
        columns = [
            'candidate_name', 'constituency_name', 'region', 
            'content_preview', 'sentiment_display', 'political_tone',
            'confidence', 'published_at'
        ]
        column_config = {
            'candidate_name': st.column_config.TextColumn('Candidate'),
            'constituency_name': st.column_config.TextColumn('Constituency'),
            'region': st.column_config.TextColumn('Region'),
            'content_preview': st.column_config.TextColumn('Content Preview'),
            'sentiment_display': st.column_config.TextColumn('Sentiment'),
            'political_tone': st.column_config.TextColumn('Political Tone'),
            'confidence': st.column_config.NumberColumn('Confidence', format="%.3f"),
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


def create_sentiment_analysis_controls():
    """
    Create interactive controls for sentiment analysis operations.
    
    Returns:
        Tuple of (generate_button_clicked, analyze_count)
    """
    st.subheader("🔧 Sentiment Analysis Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Generate Test Data**")
        analyze_count = st.number_input(
            "Number of messages to analyze",
            min_value=1,
            max_value=100,
            value=20,
            help="Generate dummy sentiment data for testing"
        )
        
        generate_button = st.button(
            "🎲 Generate Dummy Sentiment Data",
            help="Create realistic test sentiment data for dashboard testing"
        )
    
    with col2:
        st.write("**Analysis Status**")
        st.info("""
        **Dummy Data**: Fast generation for testing and development
        
        **Real Analysis**: Uses TextBlob for actual sentiment analysis
        
        Use dummy data for rapid testing and real analysis for production insights.
        """)
    
    return generate_button, analyze_count
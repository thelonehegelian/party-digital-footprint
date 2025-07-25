"""
Intelligence reports dashboard visualizations.

Provides visualization components for intelligence reports including
report generation controls, report display, metrics charts, and export functionality.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


def create_report_generation_controls() -> Dict:
    """
    Create controls for generating new intelligence reports.
    
    Returns:
        Dictionary with user selections
    """
    st.subheader("🔧 Generate New Intelligence Report")
    
    with st.expander("Report Generation Settings", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Report type selection
            report_types = [
                ("daily_brief", "📅 Daily Intelligence Brief"),
                ("weekly_summary", "📊 Weekly Analysis Summary"),
                ("monthly_analysis", "📈 Monthly Intelligence Analysis"),
                ("campaign_overview", "🏛️ Campaign Overview Analysis"),
                ("candidate_profile", "👤 Candidate Profile Analysis"),
                ("issue_tracker", "🎯 Issue Tracking Report"),
                ("comparative_analysis", "⚖️ Comparative Analysis Report")
            ]
            
            selected_type = st.selectbox(
                "Report Type",
                options=[t[0] for t in report_types],
                format_func=lambda x: next(t[1] for t in report_types if t[0] == x),
                help="Select the type of intelligence report to generate"
            )
            
            # Time period selection
            time_period = st.slider(
                "Analysis Period (Days)",
                min_value=1,
                max_value=90,
                value=7,
                help="Number of days to include in the analysis"
            )
        
        with col2:
            # Entity filters
            st.write("**Optional Filters:**")
            
            use_source_filter = st.checkbox("Filter by Source Type")
            source_filter = None
            if use_source_filter:
                source_filter = st.selectbox(
                    "Source Type",
                    options=["twitter", "facebook", "website", "meta_ads"],
                    format_func=lambda x: {
                        "twitter": "Twitter/X Posts",
                        "facebook": "Facebook Posts", 
                        "website": "Website Articles",
                        "meta_ads": "Meta Advertisements"
                    }.get(x, x)
                )
            
            use_scope_filter = st.checkbox("Filter by Geographic Scope")
            scope_filter = None
            if use_scope_filter:
                scope_filter = st.selectbox(
                    "Geographic Scope",
                    options=["national", "regional", "local"],
                    format_func=lambda x: x.title()
                )
    
    # Build entity filter
    entity_filter = {}
    if source_filter:
        entity_filter["source_type"] = source_filter
    if scope_filter:
        entity_filter["geographic_scope"] = scope_filter
    
    return {
        "report_type": selected_type,
        "time_period_days": time_period,
        "entity_filter": entity_filter if entity_filter else None
    }


def display_report_overview_metrics(report_data: Dict):
    """
    Display overview metrics for a generated report.
    
    Args:
        report_data: Complete report data
    """
    metadata = report_data.get("metadata", {})
    sections = report_data.get("sections", [])
    recommendations = report_data.get("recommendations", [])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Messages Analyzed",
            value=metadata.get("total_messages_analyzed", 0),
            help="Total number of messages included in the analysis"
        )
    
    with col2:
        st.metric(
            "Data Completeness",
            value=f"{metadata.get('data_completeness', 0.0)*100:.1f}%",
            help="Percentage of analytics data available for comprehensive analysis"
        )
    
    with col3:
        st.metric(
            "Report Sections",
            value=len(sections),
            help="Number of analysis sections in the report"
        )
    
    with col4:
        st.metric(
            "Recommendations",
            value=len(recommendations),
            help="Number of actionable recommendations generated"
        )


def create_section_priority_chart(report_data: Dict):
    """
    Create a chart showing report sections by priority level.
    
    Args:
        report_data: Complete report data
    """
    sections = report_data.get("sections", [])
    
    if not sections:
        st.info("No sections available for priority analysis.")
        return
    
    # Count sections by priority
    priorities = {"high": 0, "medium": 0, "low": 0}
    for section in sections:
        priority = section.get("priority", "medium")
        if priority in priorities:
            priorities[priority] += 1
    
    # Create pie chart
    labels = ["High Priority", "Medium Priority", "Low Priority"]
    values = [priorities["high"], priorities["medium"], priorities["low"]]
    colors = ["#ff4444", "#ffa500", "#90ee90"]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        hole=0.4,
        textinfo='label+percent',
        textposition='outside'
    )])
    
    fig.update_layout(
        title="Report Sections by Priority Level",
        showlegend=True,
        height=400,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    st.plotly_chart(fig, use_container_width=True, key="section_priority_chart")


def create_data_sources_chart(report_data: Dict):
    """
    Create a chart showing data sources used in the report.
    
    Args:
        report_data: Complete report data
    """
    data_sources = report_data.get("data_sources", [])
    
    if not data_sources:
        st.info("No data sources information available.")
        return
    
    # Create simple bar chart for data sources
    source_names = {
        "sentiment_analysis": "Sentiment Analysis",
        "topic_modeling": "Topic Modeling", 
        "engagement_metrics": "Engagement Analytics"
    }
    
    labels = [source_names.get(source, source.title()) for source in data_sources]
    values = [1] * len(data_sources)  # All sources equally weighted
    
    fig = go.Figure(data=[go.Bar(
        x=labels,
        y=values,
        marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'][:len(labels)],
        text=["✓"] * len(labels),
        textposition='inside'
    )])
    
    fig.update_layout(
        title="Analytics Data Sources Used",
        xaxis_title="Data Sources",
        yaxis_title="",
        showlegend=False,
        height=300,
        yaxis=dict(showticklabels=False, showgrid=False),
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    st.plotly_chart(fig, use_container_width=True, key="data_sources_chart")


def display_report_content(report_data: Dict):
    """
    Display the main content of an intelligence report.
    
    Args:
        report_data: Complete report data
    """
    # Report header
    st.header(report_data.get("title", "Intelligence Report"))
    st.caption(f"Generated: {report_data.get('generated_at', 'Unknown')}")
    
    # Executive Summary
    st.subheader("📋 Executive Summary")
    st.write(report_data.get("executive_summary", "No executive summary available."))
    
    # Report Sections
    sections = report_data.get("sections", [])
    if sections:
        st.subheader("📄 Report Sections")
        
        # Sort sections by priority
        priority_order = {"high": 1, "medium": 2, "low": 3}
        sorted_sections = sorted(sections, key=lambda x: priority_order.get(x.get("priority", "medium"), 2))
        
        for i, section in enumerate(sorted_sections):
            priority = section.get("priority", "medium")
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            
            with st.expander(f"{priority_emoji.get(priority, '🟡')} {section.get('title', 'Untitled Section')}", 
                           expanded=(priority == "high")):
                st.write(section.get("content", "No content available."))
                
                # Show visualizations if available
                visualizations = section.get("visualizations", [])
                if visualizations:
                    st.caption(f"**Suggested Visualizations:** {', '.join(visualizations)}")
    
    # Recommendations
    recommendations = report_data.get("recommendations", [])
    if recommendations:
        st.subheader("💡 Recommendations")
        for i, recommendation in enumerate(recommendations, 1):
            st.write(f"{i}. {recommendation}")


def display_reports_list(reports: List[Dict]):
    """
    Display a list of available intelligence reports.
    
    Args:
        reports: List of report summaries
    """
    if not reports:
        st.info("No intelligence reports available. Generate your first report above!")
        return
    
    st.subheader("📚 Available Intelligence Reports")
    
    # Create DataFrame for better display
    reports_data = []
    for report in reports:
        reports_data.append({
            "Report ID": report.get("report_id", ""),
            "Type": report.get("report_type", "").replace("_", " ").title(),
            "Title": report.get("title", ""),
            "Generated": report.get("generated_at", "")[:10] if report.get("generated_at") else "",
            "Period": f"{report.get('time_period_days', 0)} days",
            "Sections": report.get("sections_count", 0)
        })
    
    df = pd.DataFrame(reports_data)
    
    # Display as interactive table
    selected_indices = st.multiselect(
        "Select reports to view:",
        options=range(len(df)),
        format_func=lambda x: f"{df.iloc[x]['Type']} - {df.iloc[x]['Generated']}",
        default=[0] if len(df) > 0 else []
    )
    
    if selected_indices:
        selected_reports = [reports[i] for i in selected_indices]
        return selected_reports
    
    # Show table for reference
    st.dataframe(df, use_container_width=True, hide_index=True)
    return []


def create_export_controls(report_data: Dict, service):
    """
    Create controls for exporting intelligence reports.
    
    Args:
        report_data: Complete report data
        service: Intelligence dashboard service instance
    """
    st.subheader("💾 Export Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox(
            "Export Format",
            options=["json", "markdown"],
            format_func=lambda x: {
                "json": "📄 JSON (API Integration)",
                "markdown": "📝 Markdown (Documentation)"
            }.get(x, x)
        )
    
    with col2:
        if st.button("🔽 Export Report", type="primary"):
            report_id = report_data.get("report_id")
            if report_id:
                with st.spinner(f"Exporting report as {export_format.upper()}..."):
                    export_data = service.export_report(report_id, export_format)
                    
                    if export_data:
                        content = export_data.get("content", "")
                        filename = export_data.get("filename", f"report.{export_format}")
                        
                        # Provide download
                        st.download_button(
                            label=f"📥 Download {filename}",
                            data=content,
                            file_name=filename,
                            mime="application/json" if export_format == "json" else "text/markdown"
                        )
                        st.success(f"Report exported successfully as {export_format.upper()}!")
                    else:
                        st.error("Failed to export report. Please try again.")
            else:
                st.error("No report ID available for export.")


def create_time_period_analysis_chart(reports: List[Dict]):
    """
    Create a chart showing report generation over time.
    
    Args:
        reports: List of report data
    """
    if not reports or len(reports) < 2:
        st.info("Need at least 2 reports to show time period analysis.")
        return
    
    # Extract time data
    report_dates = []
    report_types = []
    
    for report in reports:
        generated_at = report.get("generated_at", "")
        if generated_at:
            try:
                # Parse date (assuming ISO format)
                date = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                report_dates.append(date.date())
                report_types.append(report.get("report_type", "unknown").replace("_", " ").title())
            except:
                continue
    
    if not report_dates:
        return
    
    # Create timeline chart
    df = pd.DataFrame({
        "Date": report_dates,
        "Report Type": report_types,
        "Count": [1] * len(report_dates)
    })
    
    fig = px.scatter(
        df, 
        x="Date", 
        y="Report Type",
        size="Count",
        color="Report Type",
        title="Intelligence Reports Timeline",
        size_max=20
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    st.plotly_chart(fig, use_container_width=True, key="reports_timeline_chart")


def display_report_comparison(reports: List[Dict]):
    """
    Display comparison between multiple reports.
    
    Args:
        reports: List of selected reports for comparison
    """
    if len(reports) < 2:
        st.info("Select at least 2 reports to enable comparison.")
        return
    
    st.subheader("🔀 Report Comparison")
    
    # Create comparison table
    comparison_data = []
    for report in reports:
        metadata = report.get("metadata", {})
        comparison_data.append({
            "Report": report.get("title", "Untitled")[:30] + "...",
            "Type": report.get("report_type", "").replace("_", " ").title(),
            "Messages": metadata.get("total_messages_analyzed", 0),
            "Completeness": f"{metadata.get('data_completeness', 0.0)*100:.1f}%",
            "Sections": len(report.get("sections", [])),
            "Recommendations": len(report.get("recommendations", []))
        })
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Comparison charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Messages analyzed comparison
        fig1 = px.bar(
            df, 
            x="Report", 
            y="Messages",
            title="Messages Analyzed Comparison",
            color="Type"
        )
        fig1.update_layout(height=300, margin=dict(t=50, b=50, l=20, r=20))
        st.plotly_chart(fig1, use_container_width=True, key="messages_comparison_chart")
    
    with col2:
        # Sections and recommendations comparison
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=df["Report"], y=df["Sections"], name="Sections", marker_color='lightblue'))
        fig2.add_trace(go.Bar(x=df["Report"], y=df["Recommendations"], name="Recommendations", marker_color='lightcoral'))
        
        fig2.update_layout(
            title="Sections vs Recommendations",
            barmode='group',
            height=300,
            margin=dict(t=50, b=50, l=20, r=20)
        )
        st.plotly_chart(fig2, use_container_width=True, key="sections_recommendations_chart")
"""
Intelligence reports dashboard service.

Provides data access and business logic for intelligence reports dashboard
including report generation, retrieval, and export functionality.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class IntelligenceReportSummary:
    """Summary information for an intelligence report."""
    report_id: str
    report_type: str
    title: str
    generated_at: str
    time_period_days: int
    sections_count: int
    recommendations_count: int


class IntelligenceDashboardService:
    """Service class for intelligence reports dashboard operations."""
    
    def __init__(self, api_base_url: str = "http://localhost:8000/api/v1"):
        """Initialize the service with API base URL."""
        self.api_base_url = api_base_url
        self.reports_endpoint = f"{api_base_url}/analytics/reports"
    
    def generate_report(
        self, 
        report_type: str, 
        time_period_days: int = 7,
        entity_filter: Optional[Dict] = None
    ) -> Dict:
        """
        Generate a new intelligence report.
        
        Args:
            report_type: Type of report to generate
            time_period_days: Number of days to analyze
            entity_filter: Optional filters for specific entities
            
        Returns:
            Generated report data
        """
        try:
            payload = {
                "report_type": report_type,
                "time_period_days": time_period_days,
                "export_format": "json"
            }
            
            if entity_filter:
                payload["entity_filter"] = entity_filter
            
            response = requests.post(
                f"{self.reports_endpoint}/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Failed to generate report: {response.status_code}",
                    "details": response.text
                }
                
        except requests.RequestException as e:
            return {
                "error": f"Request failed: {str(e)}",
                "details": "Check if the API server is running"
            }
    
    def list_reports(self, report_type: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        List available intelligence reports.
        
        Args:
            report_type: Optional filter by report type
            limit: Maximum number of reports to return
            
        Returns:
            List of report summaries
        """
        try:
            params = {"limit": limit}
            if report_type:
                params["report_type"] = report_type
            
            response = requests.get(
                f"{self.reports_endpoint}/list",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("reports", [])
            else:
                return []
                
        except requests.RequestException:
            return []
    
    def get_report(self, report_id: str) -> Optional[Dict]:
        """
        Retrieve a specific intelligence report.
        
        Args:
            report_id: Unique identifier for the report
            
        Returns:
            Report data or None if not found
        """
        try:
            response = requests.get(
                f"{self.reports_endpoint}/{report_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except requests.RequestException:
            return None
    
    def export_report(self, report_id: str, format: str = "json") -> Optional[Dict]:
        """
        Export a report in specified format.
        
        Args:
            report_id: Unique identifier for the report
            format: Export format (json or markdown)
            
        Returns:
            Export data or None if failed
        """
        try:
            response = requests.get(
                f"{self.reports_endpoint}/{report_id}/export",
                params={"format": format},
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except requests.RequestException:
            return None
    
    def get_report_types(self) -> List[Tuple[str, str]]:
        """
        Get available report types with display names.
        
        Returns:
            List of (value, display_name) tuples
        """
        return [
            ("daily_brief", "📅 Daily Intelligence Brief"),
            ("weekly_summary", "📊 Weekly Analysis Summary"),
            ("monthly_analysis", "📈 Monthly Intelligence Analysis"),
            ("campaign_overview", "🏛️ Campaign Overview Analysis"),
            ("candidate_profile", "👤 Candidate Profile Analysis"),
            ("issue_tracker", "🎯 Issue Tracking Report"),
            ("comparative_analysis", "⚖️ Comparative Analysis Report")
        ]
    
    def get_entity_filters(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Get available entity filter options.
        
        Returns:
            Dictionary of filter categories with options
        """
        return {
            "source_type": [
                ("twitter", "Twitter/X Posts"),
                ("facebook", "Facebook Posts"), 
                ("website", "Website Articles"),
                ("meta_ads", "Meta Advertisements")
            ],
            "geographic_scope": [
                ("national", "National Messages"),
                ("regional", "Regional Messages"),
                ("local", "Local Messages")
            ]
        }
    
    def format_report_summary(self, report_data: Dict) -> IntelligenceReportSummary:
        """
        Format report data into summary object.
        
        Args:
            report_data: Raw report data from API
            
        Returns:
            Formatted report summary
        """
        return IntelligenceReportSummary(
            report_id=report_data.get("report_id", ""),
            report_type=report_data.get("report_type", ""),
            title=report_data.get("title", ""),
            generated_at=report_data.get("generated_at", ""),
            time_period_days=report_data.get("metadata", {}).get("time_period_days", 0),
            sections_count=len(report_data.get("sections", [])),
            recommendations_count=len(report_data.get("recommendations", []))
        )
    
    def extract_key_metrics(self, report_data: Dict) -> Dict:
        """
        Extract key metrics from report for dashboard display.
        
        Args:
            report_data: Complete report data
            
        Returns:
            Dictionary of key metrics
        """
        metadata = report_data.get("metadata", {})
        sections = report_data.get("sections", [])
        recommendations = report_data.get("recommendations", [])
        
        return {
            "total_messages_analyzed": metadata.get("total_messages_analyzed", 0),
            "data_completeness": metadata.get("data_completeness", 0.0) * 100,
            "analysis_period": metadata.get("time_period_days", 0),
            "sections_count": len(sections),
            "recommendations_count": len(recommendations),
            "high_priority_sections": len([s for s in sections if s.get("priority") == "high"]),
            "data_sources": len(report_data.get("data_sources", [])),
            "generated_at": report_data.get("generated_at", "")
        }
    
    def get_section_priorities(self, report_data: Dict) -> Dict[str, int]:
        """
        Get count of sections by priority level.
        
        Args:
            report_data: Complete report data
            
        Returns:
            Dictionary with priority counts
        """
        sections = report_data.get("sections", [])
        priorities = {"high": 0, "medium": 0, "low": 0}
        
        for section in sections:
            priority = section.get("priority", "medium")
            if priority in priorities:
                priorities[priority] += 1
        
        return priorities
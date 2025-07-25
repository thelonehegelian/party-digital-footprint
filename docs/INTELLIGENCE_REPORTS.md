# Intelligence Reports Documentation

This document provides comprehensive guidance for using the Intelligence Reports system, which combines sentiment analysis, topic modeling, and engagement analytics into actionable intelligence reports.

## Overview

The Intelligence Reports system generates comprehensive analytical reports that combine insights from multiple analytics engines:

- **Sentiment Analysis**: Political tone and emotional content analysis
- **Topic Modeling**: Issue identification and trending analysis  
- **Engagement Analytics**: Platform performance and viral content tracking

## Report Types

### 📅 Daily Intelligence Brief
**Purpose**: Focused daily summary for rapid decision-making
**Time Period**: 1-2 days
**Content**:
- Message activity summary
- Sentiment highlights
- Trending topics
- High-engagement content

**Use Case**: Daily campaign briefings, rapid response planning

### 📊 Weekly Analysis Summary  
**Purpose**: Comprehensive weekly analysis for strategic planning
**Time Period**: 7 days
**Content**:
- Weekly messaging overview
- Sentiment trends analysis
- Topic modeling analysis
- Platform performance analysis

**Use Case**: Weekly strategy meetings, performance reviews

### 📈 Monthly Intelligence Analysis
**Purpose**: Extended monthly analysis for long-term strategy
**Time Period**: 30 days
**Content**:
- All weekly summary content
- Monthly topic evolution
- Detailed engagement analysis
- Comprehensive trend analysis

**Use Case**: Monthly strategy planning, campaign retrospectives

### 🏛️ Campaign Overview Analysis
**Purpose**: Complete campaign messaging analysis
**Time Period**: Flexible (14-90 days)
**Content**:
- Campaign messaging strategy analysis
- All comprehensive analysis sections
- Strategic insights and coordination patterns

**Use Case**: Campaign post-mortems, strategic communications review

### 👤 Candidate Profile Analysis
**Purpose**: Individual candidate focus analysis
**Time Period**: Flexible
**Content**:
- Candidate-specific messaging patterns
- Performance vs. other candidates
- Topic focus and sentiment analysis

**Use Case**: Individual candidate performance review

### 🎯 Issue Tracking Report
**Purpose**: Topic-specific messaging tracking
**Time Period**: Flexible
**Content**:
- Issue priority tracking
- Topic emergence and evolution
- Sentiment correlation with issues

**Use Case**: Issue-based campaign planning, crisis response

### ⚖️ Comparative Analysis Report
**Purpose**: Multi-entity comparison analysis
**Time Period**: Flexible
**Content**:
- Cross-platform comparison
- Candidate vs. candidate analysis
- Time period comparisons

**Use Case**: Competitive analysis, performance benchmarking

## API Usage

### Generate Intelligence Report

```bash
curl -X POST "http://localhost:8000/api/v1/analytics/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "weekly_summary",
    "time_period_days": 7,
    "entity_filter": {
      "source_type": "twitter"
    },
    "export_format": "json"
  }'
```

**Parameters**:
- `report_type`: One of the report types listed above
- `time_period_days`: Number of days to analyze (1-365)
- `entity_filter` (optional): Filter by source_type, candidate_id, etc.
- `export_format`: "json" or "markdown"

**Response**:
```json
{
  "report_id": "weekly_summary_20250725_155133",
  "report_type": "weekly_summary", 
  "title": "Weekly Analysis Summary (7-Day)",
  "executive_summary": "Analysis of 246 messages shows high messaging activity...",
  "generated_at": "2025-07-25T15:51:33.280081",
  "time_period": {
    "start": "2025-07-18T15:51:33.280081",
    "end": "2025-07-25T15:51:33.280081"
  },
  "sections": [...],
  "metadata": {...},
  "recommendations": [...],
  "data_sources": ["sentiment_analysis", "topic_modeling", "engagement_metrics"]
}
```

### List Available Reports

```bash
curl "http://localhost:8000/api/v1/analytics/reports/list?limit=20"
```

### Retrieve Specific Report

```bash
curl "http://localhost:8000/api/v1/analytics/reports/{report_id}"
```

### Export Report

```bash
# Export as JSON
curl "http://localhost:8000/api/v1/analytics/reports/{report_id}/export?format=json"

# Export as Markdown
curl "http://localhost:8000/api/v1/analytics/reports/{report_id}/export?format=markdown"
```

## Dashboard Usage

### Accessing Intelligence Reports

1. **Open Dashboard**: Navigate to the "📈 Intelligence Reports" tab
2. **Generate Report**: Use the report generation controls to select:
   - Report type from dropdown
   - Analysis period (1-90 days)
   - Optional filters (source type, geographic scope)
3. **Click Generate**: Process takes 10-30 seconds depending on data volume

### Viewing Reports

**Report Overview Metrics**:
- Messages Analyzed: Total message count in analysis
- Data Completeness: Percentage of analytics data available
- Report Sections: Number of analysis sections generated
- Recommendations: Number of actionable recommendations

**Visual Analysis**:
- Section Priority Chart: Distribution of high/medium/low priority sections
- Data Sources Chart: Analytics engines used in the report

**Report Content**:
- Executive Summary: High-level insights and trends
- Report Sections: Detailed analysis organized by priority
- Recommendations: Actionable insights for strategy

### Report Management

**Loading Existing Reports**:
1. Click "📚 Load Existing Reports"
2. Select one or more reports from the list
3. Single selection: View full report
4. Multiple selection: Compare reports side-by-side

**Exporting Reports**:
1. View any generated report
2. Use export controls at bottom
3. Select JSON or Markdown format
4. Download file for external use

## Entity Filtering

### Source Type Filters
- `twitter`: Twitter/X posts only
- `facebook`: Facebook posts only
- `website`: Website articles only
- `meta_ads`: Meta advertisements only

### Geographic Scope Filters
- `national`: National-level messaging
- `regional`: Regional-level messaging
- `local`: Local constituency messaging

### Example Filtered Report
```json
{
  "report_type": "daily_brief",
  "time_period_days": 1,
  "entity_filter": {
    "source_type": "twitter",
    "geographic_scope": "national"
  }
}
```

## Report Structure

### Executive Summary
Automated summary including:
- Activity level assessment
- Sentiment insights
- Topic focus identification
- Engagement highlights
- Data quality notes

### Report Sections
Each section includes:
- **Title**: Descriptive section name
- **Content**: Formatted analysis content
- **Data**: Structured data for the section
- **Visualizations**: Suggested chart types
- **Priority**: High/Medium/Low importance

### Recommendations
Actionable insights including:
- Data collection improvements
- Sentiment-based messaging guidance
- Engagement optimization suggestions
- Platform-specific recommendations
- Topic diversity guidance

## Best Practices

### Report Generation
1. **Regular Cadence**: Generate daily briefs for active periods, weekly summaries for ongoing analysis
2. **Appropriate Time Periods**: Match report type to time period (daily=1-2 days, weekly=7 days, monthly=30 days)
3. **Strategic Filtering**: Use entity filters for focused analysis
4. **Export for Sharing**: Use Markdown export for stakeholder reports

### Analysis Workflow
1. **Start with Overview**: Review executive summary first
2. **Prioritize High-Priority Sections**: Focus on red-flagged items
3. **Follow Recommendations**: Implement actionable insights
4. **Track Over Time**: Compare reports to identify trends

### Data Quality
- **Minimum 50 messages** recommended for meaningful analysis
- **70%+ data completeness** ideal for comprehensive insights
- **Multiple data sources** provide richer analysis
- **Regular analytics processing** ensures fresh insights

## Integration Examples

### Python API Client
```python
import requests

# Generate report
response = requests.post(
    "http://localhost:8000/api/v1/analytics/reports/generate",
    json={
        "report_type": "weekly_summary",
        "time_period_days": 7,
        "export_format": "json"
    }
)

report = response.json()
print(f"Generated report: {report['title']}")
print(f"Executive summary: {report['executive_summary']}")

# Export as markdown
export_response = requests.get(
    f"http://localhost:8000/api/v1/analytics/reports/{report['report_id']}/export",
    params={"format": "markdown"}
)

markdown_content = export_response.json()["content"]
with open("weekly_report.md", "w") as f:
    f.write(markdown_content)
```

### Automated Reporting
```bash
#!/bin/bash
# Daily report generation script

# Generate daily brief
REPORT_ID=$(curl -s -X POST "http://localhost:8000/api/v1/analytics/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{"report_type": "daily_brief", "time_period_days": 1}' | \
  jq -r '.report_id')

# Export as markdown
curl -s "http://localhost:8000/api/v1/analytics/reports/$REPORT_ID/export?format=markdown" | \
  jq -r '.content' > "reports/daily_brief_$(date +%Y%m%d).md"

echo "Daily report generated: daily_brief_$(date +%Y%m%d).md"
```

## Troubleshooting

### Common Issues

**Report Generation Fails**:
- Verify API server is running on port 8000
- Check database has sufficient message data
- Ensure analytics engines have processed data

**Empty or Minimal Reports**:
- Run analytics batch processing first
- Verify messages exist in time period
- Check data completeness percentage

**Dashboard Connection Issues**:
- Confirm API server accessibility
- Check network connectivity
- Verify correct API base URL in service

### Error Messages

**"No messaging activity detected"**: No messages in time period
**"Limited analytics data available"**: Data completeness < 50%
**"Failed to generate report"**: API server error or database issue

### Support

For additional support:
1. Check system logs for detailed error messages
2. Verify all dependencies are installed
3. Ensure database migrations are current
4. Review API documentation for parameter validation
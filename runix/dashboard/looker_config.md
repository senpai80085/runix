# Runix Looker Studio Dashboard Configuration

## Overview

This document provides step-by-step instructions for creating the Runix workload intelligence dashboard in Looker Studio.

## Prerequisites

- BigQuery dataset `runix` deployed with all tables
- At least one workload analysis completed (use `/analyze/mock` endpoint for testing)
- Looker Studio access with your Google account

## Data Source Setup

### Step 1: Create BigQuery Connection

1. Go to [Looker Studio](https://lookerstudio.google.com/)
2. Click **Create** → **Data Source**
3. Select **BigQuery** connector
4. Choose:
   - **Project**: `warm-ring-483118-v9`
   - **Dataset**: `runix`
   - **Table**: Start with `dashboard_summary` (view)
5. Click **CONNECT**

### Step 2: Configure Fields

Ensure these fields are available (auto-detected from view):

| Field Name | Type | Description |
|------------|------|-------------|
| `resource_id` | Text | Workload identifier |
| `project_id` | Text | GCP project |
| `workload_type` | Text | Classification result |
| `confidence` | Number (0-1) | Classification confidence |
| `cpu_mean` | Number | Average CPU utilization % |
| `cpu_p95` | Number | 95th percentile CPU % |
| `memory_mean` | Number | Average memory utilization % |
| `idle_ratio` | Number (0-1) | Percentage of idle time |
| `burstiness_score` | Number | Traffic burstiness metric |
| `efficiency_score` | Number | Cost efficiency 0-100 |
| `cost_impact` | JSON | Current vs optimized costs |
| `risk_level` | Text | Low/Medium/High |
| `recommended_at` | Datetime | Analysis timestamp |

### Step 3: Add Calculated Fields

**Confidence Percentage**:
```
confidence * 100
```

**Idle Percentage**:
```
idle_ratio * 100
```

**Current Cost** (extract from JSON):
```
CAST(REGEXP_EXTRACT(cost_impact, r'"current_monthly_usd":\s*([0-9.]+)') AS NUMBER)
```

**Optimized Cost**:
```
CAST(REGEXP_EXTRACT(cost_impact, r'"optimized_monthly_usd":\s*([0-9.]+)') AS NUMBER)
```

**Savings USD**:
```
CAST(REGEXP_EXTRACT(cost_impact, r'"savings_usd":\s*([0-9.]+)') AS NUMBER)
```

**Savings Percentage**:
```
CAST(REGEXP_EXTRACT(cost_impact, r'"savings_percentage":\s*([0-9.]+)') AS NUMBER)
```

---

## Dashboard Layout

### Page 1: Workload Overview

**Title**: "Runix Workload Intelligence"

#### 1. Workload Type (Scorecard)
- **Type**: Scorecard
- **Metric**: `workload_type`
- **Comparison**: None
- **Style**: Large text, center-aligned
- **Background**: Gradient blue

#### 2. Classification Confidence (Gauge)
- **Type**: Gauge  
- **Metric**: `Confidence Percentage` (calculated field)
- **Min**: 0
- **Max**: 100
- **Ranges**:
  - 0-59%: Red (Low confidence)
  - 60-79%: Yellow (Medium confidence)
  - 80-100%: Green (High confidence)

#### 3. CPU Utilization (Time Series)
- **Type**: Time series chart
- **Dimension**: `recommended_at` (aggregated by hour)
- **Metrics**: 
  - `cpu_mean` (line, blue)
  - `cpu_p95` (line, red, dashed)
- **Y-axis**: 0-100%
- **X-axis**: Last 30 days

#### 4. Memory Utilization (Time Series)
- **Type**: Area chart
- **Dimension**: `recommended_at`
- **Metric**: `memory_mean`
- **Fill**: Gradient purple
- **Y-axis**: 0-100%

---

### Page 2: Traffic Patterns

#### 5. Request Rate (Area Chart)
- **Type**: Area chart  
- **Data Source**: Create new from `runix.engineered_features` table
- **Dimension**: `window_start`
- **Metric**: `request_rate_mean`
- **Fill**: Gradient green

#### 6. Idle Window Heatmap
- **Type**: Pivot table with heatmap
- **Data Source**: `runix.engineered_features`
- **Row**: Hour of day (extract from `window_start`)
- **Column**: Day of week (extract from `window_start`)
- **Metric**: AVG(`idle_ratio`)
- **Heatmap colors**:
  - High idle (>70%): Dark red
  - Medium (30-70%): Yellow
  - Low idle (<30%): Green

---

### Page 3: Cost Analysis

#### 7. Idle vs Active Cost (Donut Chart)
- **Type**: Donut chart
- **Dimension**: Create calculated dimension:
  ```
  CASE
    WHEN idle_ratio > 0.5 THEN "Idle Cost"
    ELSE "Active Cost"
  END
  ```
- **Metric**: Count of records
- **Colors**: 
  - Idle: Red
  - Active: Green

#### 8. Current vs Optimized Cost (Bar Chart)
- **Type**: Column chart
- **Dimension**: `resource_id`
- **Metrics**:
  - `Current Cost` (calculated)
  - `Optimized Cost` (calculated)
- **Colors**:
  - Current: Red
  - Optimized: Green
- **Sort**: By savings (descending)

#### 9. Runix Recommendation (Text Panel)
- **Type**: Scorecard with custom text
- **Data**: Connect to `runix.optimization_recommendations` table
- **Fields to display**:
  - Workload Type
  - Confidence score
  - Current architecture (formatted JSON)
  - Recommended architecture (formatted JSON)
  - Savings: `$X.XX (Y%)`
  - Risk level
  - Top 3 explanation points (ARRAY elements)
- **Template**:
   ```
   🎯 WORKLOAD: {workload_type}
   📊 CONFIDENCE: {confidence}%
   
   💰 SAVINGS: ${savings_usd} ({savings_percentage}%)
   ⚠️  RISK: {risk_level}
   
   📝 RECOMMENDATION:
   {explanation[0]}
   {explanation[1]}
   {explanation[2]}
   ```

---

## Filters & Interactivity

### Global Filters

Add these controls to allow users to filter data:

1. **Date Range Selector**
   - Default: Last 30 days
   - Options: 7d, 30d, 90d, Custom

2. **Resource Filter** 
   - Multi-select dropdown
   - Dimension: `resource_id`

3. **Workload Type Filter**
   - Multi-select dropdown
   - Dimension: `workload_type`

4. **Project ID Filter** (for multi-tenant)
   - Single-select dropdown
   - Dimension: `project_id`
   - Default: Current user's project

### Dashboard Actions

- **Click on resource_id** → Navigate to detail page
- **Click on workload type** → Filter to show all of that type
- **Hover over charts** → Show tooltip with details

---

## Styling & Branding

**Theme**: Modern, Google Cloud-inspired

- **Primary Color**: `#4285F4` (Google Blue)
- **Secondary Color**: `#EA4335` (Warning Red)
- **Success Color**: `#34A853` (Google Green)
- **Background**: White `#FFFFFF`
- **Text**: Dark gray `#202124`
- **Font**: Google Sans

**Logo**: Add "Runix" text logo in top-left
**Tagline**: "Workload Intelligence Platform"

---

## Testing the Dashboard

After setup:

1. Generate test data:
   ```bash
   curl -X POST https://YOUR-CLOUD-RUN-URL/analyze/mock \
     -H "Content-Type: application/json" \
     -d '{"workload_type": "bursty"}'
   ```

2. Refresh Looker Studio data source

3. Verify all 9 visualizations display data

4. Test filters and interactivity

5. Share dashboard with stakeholders

---

## Sharing & Permissions

**Viewer Access**:
- Share dashboard link
- Set to "Anyone with link can view"
- No BigQuery permissions needed (Looker Studio handles auth)

**Editor Access**:
- Invite specific users
- Requires BigQuery dataset permissions

---

## Troubleshooting

**No data showing**:
- Verify BigQuery tables have data: `SELECT COUNT(*) FROM runix.dashboard_summary`
- Check data source connection
- Refresh fields schema

**JSON parsing errors**:
- Ensure calculated fields for `cost_impact` use correct regex
- Test regex in BigQuery first

**Performance issues**:
- Add date range filter (default last 30 days)
- Use `dashboard_summary` view instead of raw tables
- Enable query caching in Looker Studio settings

---

## Next Steps

After dashboard is live:

1. Schedule email reports (weekly summary)
2. Set up alerts for high-cost workloads
3. Create drill-down pages for each workload type
4. Add comparison charts (month-over-month)
5. Integrate with Slack/Teams for notifications

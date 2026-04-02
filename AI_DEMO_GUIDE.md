# AI Procurement System - Demo Guide

This guide shows you how to see the AI system in action.

## Quick Start

### 1. Access the AI Interface

Open your browser to: **http://localhost:8000/ai/login/**

Login credentials:
- Username: `admin`
- Password: `admin123`

You'll be redirected to the AI Dashboard.

---

## What You'll See

### AI Dashboard (`/ai/dashboard/`)

The dashboard shows:
- **Active Pipelines**: Number of AI procurement pipelines currently running
- **Pending Approvals**: Decisions waiting for human review
- **Recent Decisions**: AI decisions made in the last 7 days
- **Forecast Accuracy**: How accurate the AI predictions have been (last 30 days)
- **Recent Pipeline Executions**: Timeline of recent AI activities

---

### Parts Management (`/ai/parts/`)

Browse your inventory with AI insights:
- **Stock Levels**: Current stock vs minimum stock
- **AI Forecasts**: Predicted demand for next 30 days
- **Trend Direction**: Whether demand is increasing/decreasing/stable
- **Days Until Stockout**: How long until you run out
- **Reorder Recommendations**: Parts highlighted in red/orange need attention

**Try this:**
1. Find a part with low stock (highlighted in red/orange)
2. Click "Trigger AI Procurement"
3. Watch the AI pipeline start

---

### Pipeline Status (`/ai/procurement/pipeline/{id}/`)

Watch the AI work through 7 nodes:
1. **Data Collection**: Gathering historical data
2. **Forecasting**: Predicting future demand
3. **Supplier Evaluation**: Scoring suppliers with AI
4. **Decision Making**: Deciding whether to procure
5. **Approval (HITL)**: Waiting for human approval
6. **Execution**: Creating purchase order
7. **Outcome Recording**: Logging results

Each node shows:
- Status (pending/running/completed/failed)
- Output data from AI agents
- Timestamps

---

### Approval Queue (`/ai/approvals/`)

Review AI decisions that need human oversight:

**What the AI shows you:**
- **Decision**: "Procure" or "Defer" with reasoning
- **Recommended Quantity**: Based on demand forecast
- **Recommended Supplier**: Ranked by AI scores
- **Confidence Level**: How confident the AI is
- **Risk Factors**: Potential issues identified
- **Forecast Data**: Predicted demand with confidence intervals
- **Supplier Rankings**: Top 3 suppliers with scores

**Your options:**
- **Approve**: Accept AI recommendation, create PO
- **Reject**: Decline the recommendation
- **Modify**: Change quantity or supplier, then proceed

---

### Supplier Management (`/ai/suppliers/`)

View suppliers with AI-powered scoring:
- **AI Overall Score**: Composite score (0-1)
- **Price Score**: How competitive their pricing is
- **Lead Time Score**: How fast they deliver
- **Reliability Score**: Historical performance
- **Reliability Metrics**: On-time delivery, quality acceptance, lead time accuracy

**Try this:**
1. Select multiple suppliers (checkboxes)
2. Click "Compare Suppliers"
3. See side-by-side AI scores and metrics

---

### Inventory Management (`/ai/inventory/`)

AI-optimized inventory levels:
- **Current Stock**: Across all locations
- **AI Recommendations**: Optimized reorder points
- **Stockout Risk**: High/Medium/Low based on forecast
- **Alerts**: Low stock warnings, stockout risk alerts

---

### Analytics Dashboard (`/ai/analytics/`)

AI performance metrics:
- **Forecast Accuracy**: Overall and by category
- **Procurement Metrics**: Success rate, execution time
- **Supplier Performance**: Rankings with AI scores
- **Demand Trends**: Historical and forecasted (Chart.js visualizations)

---

## How to Trigger the AI Pipeline

### Method 1: Via Web Interface (Recommended)

1. Go to `/ai/parts/`
2. Find a part with low stock (red/orange highlight)
3. Click "Trigger AI Procurement"
4. Follow the pipeline status page
5. When it pauses at "Approval", go to `/ai/approvals/`
6. Review the AI decision and approve/reject/modify

### Method 2: Via API (for testing)

Run the test script:
```bash
./test_ai_pipeline.sh
```

Or manually via curl:
```bash
# Get CSRF token
curl -c /tmp/cookies.txt http://localhost:8000/ai/login/
CSRF_TOKEN=$(grep csrftoken /tmp/cookies.txt | awk '{print $7}')

# Login
curl -b /tmp/cookies.txt -c /tmp/cookies.txt -X POST \
  http://localhost:8000/ai/login/ \
  -d "username=admin&password=admin123&csrfmiddlewaretoken=$CSRF_TOKEN"

# Trigger pipeline (replace PART_ID with actual part ID)
curl -b /tmp/cookies.txt -X POST \
  http://localhost:8000/api/ai/procurement/pipeline/trigger/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF_TOKEN" \
  -d '{"part_id": 1}'
```

---

## What the AI Does

### 1. Demand Forecasting Agent
- Analyzes historical demand patterns
- Detects seasonality and trends
- Generates 30-day demand forecast
- Provides confidence intervals

### 2. Supplier Evaluation Agent
- Scores suppliers on price, lead time, reliability
- Ranks suppliers for the specific part
- Considers historical performance
- Provides recommendation reasoning

### 3. Decision Making Agent
- Decides: Procure vs Defer
- Calculates optimal quantity
- Selects best supplier
- Identifies risk factors
- Provides confidence level

### 4. Outcome Recording Agent
- Logs all decisions and outcomes
- Tracks forecast accuracy
- Updates supplier reliability scores
- Enables continuous learning

---

## Verifying AI is Working

### Check 1: Dashboard Metrics
- Go to `/ai/dashboard/`
- Should see non-zero values for:
  - Recent Decisions
  - Forecast Accuracy (if demo data has accuracy scores)

### Check 2: Parts with Forecasts
- Go to `/ai/parts/`
- Parts should show:
  - "Forecasted Demand: X units"
  - "Days until stockout: Y days"
  - Trend direction (↑ increasing, ↓ decreasing, → stable)

### Check 3: Trigger New Pipeline
- Click "Trigger AI Procurement" on any part
- Should redirect to pipeline status page
- Should see nodes executing one by one
- Should pause at "Approval" node

### Check 4: Review AI Decision
- Go to `/ai/approvals/`
- Should see pending approval with:
  - AI reasoning
  - Recommended quantity
  - Recommended supplier
  - Confidence level
  - Risk factors

### Check 5: Supplier AI Scores
- Go to `/ai/suppliers/`
- Suppliers should show AI scores (0.0 - 1.0)
- Scores should be based on recent evaluations

### Check 6: Analytics
- Go to `/ai/analytics/`
- Should see:
  - Forecast accuracy percentage
  - Procurement success rate
  - Supplier performance rankings
  - Demand trend charts

---

## Troubleshooting

**No parts showing?**
```bash
cd src/backend/InvenTree
python manage.py create_demo_data
```

**Pipeline not starting?**
- Check that the part has linked suppliers
- Check server logs for errors
- Verify AI models are loaded (check `ai_procurement/TESTING.md`)

**No AI scores showing?**
- Demo data creates some evaluations
- Trigger a few pipelines to generate more AI data
- Scores are calculated from recent evaluations (last 10)

**Pipeline stuck?**
- Check if it's waiting at "Approval" node
- Go to `/ai/approvals/` to review and approve
- Check server logs for errors

---

## Demo Data Overview

The `create_demo_data` command created:
- 9 parts across 5 categories
- 5 suppliers with reliability scores
- 14 pipeline executions (some completed, some pending approval)
- Forecasts for all parts
- Supplier evaluations with AI scores
- 1 pending approval request

This gives you a realistic dataset to explore the AI features.

---

## Next Steps

After verifying the AI is working:
1. Trigger more pipelines to see the AI learn
2. Approve/reject decisions to complete workflows
3. Check analytics to see AI performance improve
4. Compare suppliers to see AI scoring in action
5. Monitor inventory to see AI optimization recommendations

The AI system is fully functional and ready to demonstrate!

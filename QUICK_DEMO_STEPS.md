# Quick Demo Steps - AI Procurement System

## Prerequisites
- Server is running: `./run_dev.sh python manage.py runserver` (in `src/backend/InvenTree/`)
- Demo data has been created: `python manage.py create_demo_data --clear`

## Step-by-Step Demo

### 1. Login to AI Interface

1. Open your browser to: **http://localhost:8000/ai/login/**
2. Enter credentials:
   - Username: `admin`
   - Password: `admin123`
3. Click "Login"
4. You'll be redirected to the AI Dashboard

### 2. View AI Dashboard

**URL**: http://localhost:8000/ai/dashboard/

You should see:
- **Active Pipelines**: Number of AI pipelines currently running
- **Pending Approvals**: Decisions waiting for human review  
- **Recent Decisions**: AI decisions made in last 7 days
- **Forecast Accuracy**: How accurate the AI predictions have been
- **Recent Pipeline Executions**: Timeline showing recent AI activities

### 3. Browse Parts with AI Insights

**URL**: http://localhost:8000/ai/parts/

You should see a grid of parts showing:
- Part name, IPN, and category
- Current stock vs minimum stock
- **AI Forecast** section with:
  - Predicted demand for next 30 days
  - Confidence range
  - Trend direction (↑ increasing, ↓ decreasing, → stable)
  - Days until stockout

**Try this**:
- Look for parts highlighted in red/orange (low stock)
- Click "View Details" on any part to see more information
- Click "Trigger Procurement" to start an AI pipeline for that part

### 4. Review Pending Approvals

**URL**: http://localhost:8000/ai/approvals/

You should see approval requests showing:
- Part name and current stock level
- **AI Decision**: ORDER, DEFER, or ESCALATE
- **Recommended Quantity**: Based on demand forecast
- **Recommended Supplier**: Ranked by AI scores
- **Confidence Level**: high, medium, or low
- **Risk Factors**: Issues the AI identified
- **Forecast Data**: Predicted demand with confidence intervals
- **Supplier Rankings**: Top 3 suppliers with scores

**Try this**:
- Click "View Details" on any approval
- Review the AI's reasoning
- You can approve, reject, or modify the decision

### 5. View Suppliers with AI Scores

**URL**: http://localhost:8000/ai/suppliers/

You should see suppliers with:
- **AI Overall Score**: Composite score (0-1)
- **Price Score**: How competitive their pricing is
- **Lead Time Score**: How fast they deliver
- **Reliability Score**: Historical performance
- **Reliability Metrics**: On-time delivery rate, quality acceptance rate

**Try this**:
- Select multiple suppliers (checkboxes)
- Click "Compare Suppliers" to see side-by-side comparison

### 6. Check Inventory with AI Optimization

**URL**: http://localhost:8000/ai/inventory/

You should see:
- Parts with current stock across all locations
- **AI Recommendations**: Optimized reorder points
- **Stockout Risk**: High/Medium/Low based on forecast
- **Alerts**: Low stock warnings, stockout risk alerts

**Try this**:
- Filter by "Low Stock" or "Stockout Risk"
- See which parts need immediate attention

### 7. View Analytics Dashboard

**URL**: http://localhost:8000/ai/analytics/

You should see:
- **Forecast Accuracy**: Overall and by category
- **Procurement Metrics**: Success rate, execution time
- **Supplier Performance**: Rankings with AI scores
- **Demand Trends**: Historical and forecasted (charts)

## Troubleshooting

### No data showing up?

1. **Check if demo data was created**:
   ```bash
   cd src/backend/InvenTree
   python manage.py shell -c "from part.models import Part; from ai_procurement.models import PipelineExecution; print(f'Parts: {Part.objects.count()}'); print(f'Pipelines: {PipelineExecution.objects.count()}')"
   ```
   
   Should show: `Parts: 20` and `Pipelines: 10`

2. **Recreate demo data**:
   ```bash
   cd src/backend/InvenTree
   python manage.py create_demo_data --clear
   ```

3. **Check if you're logged in**:
   - If you see a redirect or login page, go to http://localhost:8000/ai/login/
   - Login with admin/admin123

### Parts page shows "No parts found"?

1. **Check the search box** - Make sure it's empty
2. **Check pagination** - Look for "Page 1 of X" at the bottom
3. **Try the test script**:
   ```bash
   ./test_ai_frontend.sh
   ```

### Server not running?

```bash
cd src/backend/InvenTree
./run_dev.sh python manage.py runserver
```

## What the Demo Shows

### AI Capabilities

1. **Demand Forecasting**:
   - Predicts future demand based on historical patterns
   - Detects seasonality and trends
   - Provides confidence intervals

2. **Supplier Evaluation**:
   - Scores suppliers on price, lead time, reliability
   - Ranks suppliers for each part
   - Provides recommendation reasoning

3. **Procurement Decisions**:
   - Decides whether to procure or defer
   - Calculates optimal quantity
   - Selects best supplier
   - Identifies risk factors

4. **Human-in-the-Loop**:
   - AI escalates uncertain decisions for human review
   - Humans can approve, reject, or modify AI recommendations
   - System learns from human feedback

### Realistic Data

- **15 parts** across 5 categories (Electronics, Mechanical, Raw Materials, Fasteners, Packaging)
- **Varied stock levels**: Some critical (20% of minimum), some low (70%), some adequate (150%)
- **10 pipeline executions**: In different states (completed, running, interrupted, failed)
- **Multiple suppliers**: With different prices, lead times, and reliability scores
- **Pending approvals**: Waiting for human review

## Next Steps

After exploring the demo:

1. **Trigger a new pipeline**: Click "Trigger Procurement" on any part
2. **Watch it progress**: Go to the pipeline status page
3. **Review the decision**: When it pauses at "Approval", review and approve/reject
4. **Check analytics**: See how the AI performance improves over time

The AI system is fully functional and ready to demonstrate!

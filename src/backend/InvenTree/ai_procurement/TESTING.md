# Testing Guide: Agentic AI Procurement System

This guide walks you through testing the complete agentic AI procurement system end-to-end.

## Prerequisites

### 1. Install Python Dependencies

```bash
cd src/backend/InvenTree
pip install langgraph langgraph-checkpoint-postgres prophet xgboost pandas numpy requests
```

Or install from requirements file:
```bash
pip install -r ai_procurement/requirements.txt
```

### 2. Set Up Ollama with llama3

```bash
# Install Ollama (if not already installed)
# Visit: https://ollama.ai/download

# Pull llama3 model
ollama pull llama3

# Verify Ollama is running
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "Hello",
  "stream": false
}'
```

### 3. Run Database Migrations

```bash
cd src/backend/InvenTree
python manage.py makemigrations ai_procurement
python manage.py migrate ai_procurement
```

### 4. Start InvenTree Development Server

```bash
# Activate virtual environment if needed
source dev/venv/bin/activate  # or your venv path

# Start Django development server
python manage.py runserver
```

## Testing Scenarios

### Scenario 1: Manual Pipeline Trigger (Quick Test)

This tests the basic pipeline without waiting for stock changes.

**Steps:**

1. **Open InvenTree UI**
   - Navigate to: http://localhost:8000
   - Log in with your admin credentials

2. **Go to a Part Detail Page**
   - Navigate to: Parts → Select any part
   - Scroll down to the "Agentic AI Procurement" panel

3. **Trigger Pipeline**
   - Click "Trigger Pipeline" button
   - Watch the "Recent Pipelines" section appear
   - Pipeline status should show: `running` → `interrupted`

4. **Wait for Approval Request**
   - After ~10-30 seconds, an approval card should appear
   - The card shows:
     - 📊 Demand forecast (30-day prediction)
     - 🤖 AI recommendation with reasoning
     - 🏭 Top 3 suppliers ranked by score

5. **Review the Recommendation**
   - Check the AI's reasoning
   - Review supplier scores and prices
   - Note any risk factors

6. **Approve the Order**
   - Click "Approve" button
   - Pipeline should resume and create a PurchaseOrder
   - Check: Orders → Purchase Orders for the new PO

**Expected Result:**
✅ Pipeline completes successfully
✅ PurchaseOrder created with status "Pending"
✅ Pipeline status shows "completed"

---

### Scenario 2: Event-Driven Trigger (Full Test)

This tests the automatic pipeline triggering via stock changes.

**Steps:**

1. **Set Up a Part with Reorder Point**
   - Go to: Parts → Select a part
   - Edit the part
   - Set "Minimum Stock" to 100 (this is the reorder point)
   - Save

2. **Add Suppliers**
   - Go to: Part → Suppliers tab
   - Add 2-3 suppliers with different prices and lead times
   - Example:
     - Supplier A: $10/unit, 5 days lead time
     - Supplier B: $12/unit, 2 days lead time
     - Supplier C: $9/unit, 10 days lead time

3. **Set Current Stock Above Reorder Point**
   - Go to: Stock → Add Stock Item
   - Set quantity to 150 (above minimum of 100)

4. **Trigger Stock Change Event**
   - Go to: Stock → Select the stock item
   - Click "Remove Stock"
   - Remove 60 units (brings stock to 90, below reorder point of 100)
   - Add note: "Testing AI procurement trigger"

5. **Wait for Pipeline to Start**
   - Within 60 seconds, the pipeline should auto-trigger
   - Go back to the Part detail page
   - Check the "Agentic AI Procurement" panel
   - You should see a new pipeline in "Recent Pipelines"

6. **Process the Approval**
   - Wait for the approval card to appear
   - Review the AI's analysis
   - Choose an action:
     - **Approve**: Accept as-is
     - **Modify**: Change quantity or supplier
     - **Reject**: Decline the recommendation

**Expected Result:**
✅ Pipeline auto-triggers when stock falls below reorder point
✅ No duplicate pipelines (event deduplication works)
✅ Approval request appears automatically
✅ PO created after approval

---

### Scenario 3: Modify Before Approval

This tests the human-in-the-loop modification capability.

**Steps:**

1. **Trigger a Pipeline** (use Scenario 1 or 2)

2. **When Approval Card Appears:**
   - Click "Modify" button
   - Change the quantity (e.g., from 50 to 75)
   - Select a different supplier from dropdown
   - Add notes: "Increased quantity for safety stock"

3. **Confirm Changes**
   - Click "Confirm Changes"
   - Pipeline resumes with your modifications

4. **Verify PurchaseOrder**
   - Go to: Orders → Purchase Orders
   - Open the newly created PO
   - Verify:
     - Quantity matches your modified value
     - Supplier matches your selection
     - Notes are included

**Expected Result:**
✅ Modified values are used instead of AI recommendation
✅ PO reflects human modifications
✅ Pipeline completes successfully

---

### Scenario 4: Reject Recommendation

This tests the rejection workflow.

**Steps:**

1. **Trigger a Pipeline**

2. **When Approval Card Appears:**
   - Click "Reject" button
   - Optionally add notes explaining why

3. **Verify Rejection**
   - Pipeline status should change to "rejected"
   - No PurchaseOrder should be created
   - Rejection is logged in the system

**Expected Result:**
✅ Pipeline marked as rejected
✅ No PO created
✅ System ready for next pipeline

---

### Scenario 5: Multiple Parts Simultaneously

This tests concurrent pipeline execution.

**Steps:**

1. **Set Up Multiple Parts**
   - Create/select 3 different parts
   - Set reorder points for each
   - Add suppliers to each

2. **Trigger All Pipelines**
   - Manually trigger pipelines for all 3 parts
   - Or adjust stock levels to trigger automatically

3. **Verify Concurrent Execution**
   - Each part should have its own pipeline
   - Pipelines should not interfere with each other
   - Each should generate separate approval requests

4. **Process Approvals**
   - Approve/reject each independently
   - Verify each creates its own PO

**Expected Result:**
✅ Multiple pipelines run concurrently
✅ No state interference between pipelines
✅ Each pipeline completes independently

---

## Debugging & Troubleshooting

### Check Pipeline Status via API

```bash
# Get pipeline status by part_id
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/ai/procurement/pipeline/status/?part_id=1

# Get specific pipeline
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/ai/procurement/pipeline/status/PIPELINE_ID/
```

### Check Pending Approvals

```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/ai/procurement/approvals/?part_id=1&status=pending
```

### Check Django Logs

```bash
# In your Django console, you should see:
# - "Triggering procurement pipeline for part X"
# - "Pipeline PIPELINE_ID started for part X"
# - "Created approval request REQUEST_ID for pipeline PIPELINE_ID"
# - "Approval request REQUEST_ID processed: approve by user X"
# - "Created PurchaseOrder PO_ID for X units of PART from SUPPLIER"
```

### Check Database Directly

```sql
-- Check pipeline executions
SELECT id, part_id, status, current_node, created_at 
FROM ai_procurement_pipelineexecution 
ORDER BY created_at DESC LIMIT 10;

-- Check approval requests
SELECT id, part_id, status, created_at, expires_at
FROM ai_procurement_approvalrequest
WHERE status = 'pending';

-- Check procurement outcomes
SELECT id, part_id, decision_made, quantity_ordered, po_id
FROM ai_procurement_procurementoutcome
ORDER BY outcome_timestamp DESC LIMIT 10;
```

### Common Issues

**Issue: Pipeline doesn't trigger automatically**
- Check: Is minimum_stock set on the part?
- Check: Is stock actually below minimum_stock?
- Check: Are Django signals registered? (Check apps.py ready() method)
- Check: Django logs for signal handler errors

**Issue: Ollama connection fails**
- Check: Is Ollama running? `curl http://localhost:11434/api/tags`
- Check: Is llama3 model pulled? `ollama list`
- Check: Docker network if running in container (use host.docker.internal)

**Issue: Prophet forecasting fails**
- Check: Is there historical data? (Needs at least 14 days)
- Check: Prophet installed correctly? `pip show prophet`
- Check: Logs for Prophet errors

**Issue: No suppliers found error**
- Check: Are suppliers linked to the part?
- Go to: Part → Suppliers tab → Add suppliers

**Issue: Permission denied on approval**
- Check: User has "purchase_order.add" permission
- Go to: Admin → Users → Select user → Permissions

---

## Performance Testing

### Test Prophet Model Caching

```python
# In Django shell
from ai_procurement.agents.demand_agent import DemandAgent
from ai_procurement.models import ProphetModelCache

agent = DemandAgent()

# First forecast (trains model)
result1 = agent.forecast_demand(part_id=1, forecast_days=30)
print(f"First forecast: {result1['model_used']}")

# Check cache
cache = ProphetModelCache.objects.filter(part_id=1).first()
print(f"Model cached: {cache is not None}")

# Second forecast (uses cache)
result2 = agent.forecast_demand(part_id=1, forecast_days=30)
print(f"Second forecast: {result2['model_used']}")
print(f"Cache hit: {cache.last_used}")
```

### Test Event Deduplication

```python
# In Django shell
from ai_procurement.signals import EventDeduplicator

# First trigger
should_trigger1 = EventDeduplicator.should_trigger(part_id=1)
print(f"First trigger: {should_trigger1}")  # Should be True

# Immediate second trigger (within 60 seconds)
should_trigger2 = EventDeduplicator.should_trigger(part_id=1)
print(f"Second trigger: {should_trigger2}")  # Should be False (deduplicated)
```

---

## Success Criteria

Your system is working correctly if:

✅ Pipelines trigger automatically when stock falls below reorder point
✅ Demand forecasts are generated using Prophet
✅ Suppliers are ranked with scores
✅ Ollama llama3 provides reasoning for decisions
✅ Approval requests appear in the UI
✅ Humans can approve/reject/modify recommendations
✅ PurchaseOrders are created after approval
✅ Pipeline state persists across restarts
✅ Multiple pipelines can run concurrently
✅ Learning layer logs outcomes for future improvement

---

## Next Steps After Testing

Once basic testing is complete:

1. **Add Real Historical Data**
   - Import actual stock movement history
   - This improves Prophet forecast accuracy

2. **Configure Supplier Reliability**
   - Add historical delivery data
   - System will learn supplier performance

3. **Tune Configuration**
   - Adjust supplier ranking weights in `config.py`
   - Modify forecast horizon, approval timeout, etc.

4. **Set Up Production**
   - Configure Celery/Django-Q for async tasks
   - Set up email notifications (SMTP)
   - Configure proper authentication

5. **Monitor & Improve**
   - Review forecast accuracy over time
   - Check reorder point adjustments
   - Analyze supplier reliability scores
   - Review few-shot memory examples

---

## Support

If you encounter issues:

1. Check Django logs for errors
2. Verify all dependencies are installed
3. Ensure Ollama is running and accessible
4. Check database migrations are applied
5. Review the design document for architecture details

For detailed implementation, see:
- `.kiro/specs/agentic-ai-inventory/design.md`
- `.kiro/specs/agentic-ai-inventory/requirements.md`
- `.kiro/specs/agentic-ai-inventory/tasks.md`

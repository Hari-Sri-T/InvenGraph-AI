# AI Procurement - Testing Checklist

Use this checklist to verify the implementation works correctly in your devcontainer.

## Pre-Testing Setup

- [ ] Docker Desktop is running
- [ ] VS Code with Remote-Containers extension installed
- [ ] At least 8GB RAM available for Docker
- [ ] At least 10GB free disk space

## DevContainer Setup

- [ ] Opened project in VS Code
- [ ] Reopened in devcontainer (F1 → "Dev Containers: Reopen in Container")
- [ ] Container built successfully (check for errors in terminal)
- [ ] All services started (db, redis, ollama, inventree)

## AI Procurement Setup

- [ ] Ran setup script: `bash .devcontainer/setup_ai_procurement.sh`
- [ ] Python dependencies installed without errors
- [ ] Django migrations ran successfully
- [ ] Ollama service is accessible
- [ ] llama3 model pulled successfully (check with `curl http://ollama:11434/api/tags`)

## Server Startup

- [ ] Navigated to backend: `cd src/backend/InvenTree`
- [ ] Started server: `invoke server`
- [ ] Server running on http://localhost:8000
- [ ] No errors in server logs
- [ ] Can access admin interface at http://localhost:8000/admin

## Database Verification

- [ ] Can log into Django admin
- [ ] See ai_procurement app in admin
- [ ] See all 10 models:
  - [ ] PipelineExecution
  - [ ] DemandForecast
  - [ ] SupplierEvaluation
  - [ ] ProcurementDecisionLog
  - [ ] ApprovalRequest
  - [ ] ProcurementOutcome
  - [ ] ProphetModelCache
  - [ ] ReorderPointHistory
  - [ ] SupplierReliabilityScore
  - [ ] FewShotMemory

## Test Data Creation

- [ ] Created a test part:
  - [ ] Name: "Test Widget"
  - [ ] Minimum Stock: 10
  - [ ] Active: Yes
- [ ] Created 2-3 supplier companies
- [ ] Added SupplierPart for each supplier:
  - [ ] Linked to test part
  - [ ] Set unit prices (different for each)
  - [ ] Set lead times (different for each)
- [ ] Created stock item:
  - [ ] Linked to test part
  - [ ] Quantity above minimum (e.g., 15)

## API Testing

### Get API Token
- [ ] Created API token in admin or via: `python manage.py drf_create_token <username>`
- [ ] Token saved for testing

### Test Pipeline Trigger
```bash
curl -X POST http://localhost:8000/api/ai/procurement/pipeline/trigger/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{"part_id": 1}'
```
- [ ] Request successful (200 OK)
- [ ] Received pipeline_id in response
- [ ] No errors in server logs

### Test Pipeline Status
```bash
curl http://localhost:8000/api/ai/procurement/pipeline/status/?part_id=1 \
  -H "Authorization: Token YOUR_TOKEN"
```
- [ ] Request successful (200 OK)
- [ ] Received pipeline status
- [ ] Status shows "interrupted" (waiting for approval)

### Test Approval List
```bash
curl http://localhost:8000/api/ai/procurement/approvals/ \
  -H "Authorization: Token YOUR_TOKEN"
```
- [ ] Request successful (200 OK)
- [ ] See pending approval request
- [ ] Forecast data present
- [ ] Supplier rankings present
- [ ] AI reasoning present

## Pipeline Execution Verification

### Check Database Records
In Django shell (`python manage.py shell`):
```python
from ai_procurement.models import PipelineExecution, ApprovalRequest
# Check pipeline
p = PipelineExecution.objects.last()
print(f"Status: {p.status}")
print(f"Current Node: {p.current_node}")
print(f"State Data: {p.state_data}")

# Check approval
a = ApprovalRequest.objects.last()
print(f"Status: {a.status}")
print(f"Decision: {a.decision_log.decision}")
```
- [ ] Pipeline exists
- [ ] Status is "interrupted"
- [ ] Current node is "human_approval"
- [ ] State data contains forecast, suppliers, decision
- [ ] Approval request exists
- [ ] Approval status is "pending"

### Check Agent Outputs
- [ ] Forecast data:
  - [ ] predicted_demand > 0
  - [ ] confidence_lower and confidence_upper present
  - [ ] model_used is "prophet" or "simple_average"
  - [ ] trend_direction present
- [ ] Supplier rankings:
  - [ ] At least 1 supplier ranked
  - [ ] overall_score between 0 and 1
  - [ ] price_score, lead_time_score, reliability_score present
  - [ ] recommendation_reason present
- [ ] Decision data:
  - [ ] decision is "ORDER" or "WAIT"
  - [ ] recommended_quantity > 0
  - [ ] recommended_supplier_id present
  - [ ] reasoning present
  - [ ] confidence_level present

## UI Testing

- [ ] Opened http://localhost:8000 in browser
- [ ] Navigated to AI Procurement Panel
- [ ] See pending approval card
- [ ] Approval card shows:
  - [ ] Part name
  - [ ] Forecasted demand
  - [ ] Trend direction with icon
  - [ ] AI reasoning
  - [ ] Confidence level
  - [ ] Risk factors
  - [ ] Supplier comparison table
  - [ ] Top 3 suppliers with scores
  - [ ] Recommended supplier highlighted
- [ ] Action buttons present:
  - [ ] Approve (green)
  - [ ] Reject (red)
  - [ ] Modify (blue)

## Approval Testing

### Test Approve Action
- [ ] Clicked "Approve" button in UI
- [ ] Success notification shown
- [ ] Approval card disappears
- [ ] Pipeline status changes to "completed"
- [ ] Purchase order created
- [ ] PO linked to correct supplier
- [ ] PO has correct quantity
- [ ] PO status is "Pending"

### Verify Learning Layer
In Django shell:
```python
from ai_procurement.models import ProcurementOutcome
o = ProcurementOutcome.objects.last()
print(f"Decision: {o.decision_made}")
print(f"Quantity: {o.quantity_ordered}")
print(f"Supplier: {o.supplier_used}")
print(f"Forecast: {o.forecast_demand}")
```
- [ ] Outcome logged
- [ ] Decision is "ORDER"
- [ ] Quantity matches approved amount
- [ ] Supplier matches approved supplier
- [ ] Forecast demand recorded

## Event-Driven Testing

### Test Stock Change Trigger
- [ ] Edited stock item quantity to below minimum (e.g., 5)
- [ ] Saved stock item
- [ ] Checked server logs for "Triggering procurement pipeline"
- [ ] New pipeline created automatically
- [ ] Pipeline progressed to approval gate

### Test Event Deduplication
- [ ] Edited stock item again within 60 seconds
- [ ] Saved stock item
- [ ] Checked server logs for deduplication message
- [ ] No new pipeline created

## Error Handling Testing

### Test No Suppliers
- [ ] Created new part without suppliers
- [ ] Triggered pipeline for that part
- [ ] Pipeline failed with clear error message
- [ ] Error message says "No suppliers found"

### Test Ollama Unavailable
- [ ] Stopped Ollama container: `docker stop inventree-ollama-1`
- [ ] Triggered pipeline
- [ ] Pipeline used rule-based fallback
- [ ] Decision made without LLM
- [ ] Restarted Ollama: `docker start inventree-ollama-1`

## Performance Testing

- [ ] Measured first pipeline execution time (should be 15-25 seconds)
- [ ] Triggered second pipeline for same part
- [ ] Measured cached pipeline execution time (should be 8-12 seconds)
- [ ] Verified Prophet model cached (check ProphetModelCache table)

## Logging Verification

- [ ] Checked server logs for structured logging
- [ ] Logs include pipeline_id and part_id
- [ ] Logs include agent outputs
- [ ] Logs include timing information
- [ ] No sensitive data in logs (passwords, tokens)

## Configuration Testing

- [ ] Verified environment variables loaded:
```python
import os
print(os.getenv('AI_PROCUREMENT_OLLAMA_URL'))
print(os.getenv('AI_PROCUREMENT_PRICE_WEIGHT'))
```
- [ ] All environment variables present
- [ ] Values match docker-compose.yml

## Cleanup

- [ ] Stopped server (Ctrl+C)
- [ ] Exited devcontainer
- [ ] Optionally: Removed containers and volumes

## Issues Found

Document any issues encountered:

1. Issue: _______________
   - Expected: _______________
   - Actual: _______________
   - Error message: _______________
   - Resolution: _______________

2. Issue: _______________
   - Expected: _______________
   - Actual: _______________
   - Error message: _______________
   - Resolution: _______________

## Overall Assessment

- [ ] All critical features working
- [ ] No blocking errors
- [ ] Performance acceptable
- [ ] UI functional
- [ ] API endpoints working
- [ ] Database models correct
- [ ] Logging adequate

## Sign-Off

- Tester Name: _______________
- Date: _______________
- Overall Status: ☐ Pass ☐ Pass with Issues ☐ Fail
- Notes: _______________

---

## Quick Reference Commands

### Check Services
```bash
docker ps | grep -E "ollama|postgres|redis"
curl http://ollama:11434/api/tags
```

### Check Logs
```bash
# Server logs
tail -f /home/inventree/dev/logs/inventree.log

# Ollama logs
docker logs inventree-ollama-1
```

### Django Shell
```bash
cd src/backend/InvenTree
python manage.py shell
```

### Reset Database (if needed)
```bash
python manage.py migrate ai_procurement zero
python manage.py migrate ai_procurement
```

### Pull llama3 Model
```bash
curl -X POST http://ollama:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "llama3"}'
```

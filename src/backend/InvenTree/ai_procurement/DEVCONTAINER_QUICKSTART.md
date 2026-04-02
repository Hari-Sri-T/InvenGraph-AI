# AI Procurement - DevContainer Quick Start Guide

This guide will help you set up and test the AI Procurement system in the InvenTree devcontainer.

## Prerequisites

- Docker Desktop installed and running
- VS Code with Remote-Containers extension
- At least 8GB RAM available for Docker
- At least 10GB free disk space (for Ollama models)

## Step 1: Open in DevContainer

1. Open the InvenTree project in VS Code
2. Press `F1` and select "Dev Containers: Reopen in Container"
3. Wait for the container to build and start (first time may take 10-15 minutes)

## Step 2: Run AI Procurement Setup

Once inside the devcontainer:

```bash
# Run the setup script
bash .devcontainer/setup_ai_procurement.sh
```

This script will:
- Install Python dependencies (Prophet, LangGraph, etc.)
- Run Django migrations for AI procurement models
- Check Ollama service connectivity
- Pull the llama3 model (this takes 5-10 minutes)

## Step 3: Start InvenTree Server

```bash
# Navigate to backend directory
cd src/backend/InvenTree

# Start the development server
invoke server
```

The server will be available at http://localhost:8000

## Step 4: Access the Admin Interface

1. Open http://localhost:8000/admin in your browser
2. Log in with your admin credentials
3. If you don't have an admin user, create one:

```bash
python manage.py createsuperuser
```

## Step 5: Configure Test Data

### Create a Test Part

1. Go to Parts → Add Part
2. Fill in:
   - Name: "Test Widget"
   - Category: Create a new category if needed
   - Minimum Stock: 10 (this is the reorder point)
   - Active: Yes

### Add Suppliers

1. Go to Companies → Add Company
2. Create 2-3 supplier companies
3. For each supplier, add a SupplierPart:
   - Link to your test part
   - Set unit price (e.g., $5.00, $4.50, $6.00)
   - Set lead time (e.g., 7, 14, 21 days)
   - Set MOQ if desired

### Add Stock Items

1. Go to Stock → Add Stock Item
2. Link to your test part
3. Set quantity above minimum stock (e.g., 15)

## Step 6: Test the Pipeline

### Method 1: Manual Trigger (Quick Test)

```bash
# In the devcontainer terminal
cd src/backend/InvenTree

# Trigger pipeline for part ID 1
curl -X POST http://localhost:8000/api/ai/procurement/pipeline/trigger/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_API_TOKEN" \
  -d '{"part_id": 1}'
```

### Method 2: Event-Driven Trigger (Full Test)

1. Go to Stock → Your test stock item
2. Edit the quantity to be below the minimum stock (e.g., change from 15 to 5)
3. Save the stock item
4. The pipeline should trigger automatically!

### Check Pipeline Status

```bash
# Get pipeline status
curl http://localhost:8000/api/ai/procurement/pipeline/status/?part_id=1 \
  -H "Authorization: Token YOUR_API_TOKEN"
```

## Step 7: Approve the Recommendation

### Via API

```bash
# Get pending approvals
curl http://localhost:8000/api/ai/procurement/approvals/ \
  -H "Authorization: Token YOUR_API_TOKEN"

# Approve the request
curl -X POST http://localhost:8000/api/ai/procurement/approvals/REQUEST_ID/action/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_API_TOKEN" \
  -d '{"action": "approve"}'
```

### Via UI

1. Go to the AI Procurement Panel in the InvenTree UI
2. You should see a pending approval request
3. Review the forecast, supplier rankings, and AI reasoning
4. Click "Approve", "Reject", or "Modify"

## Step 8: Verify Purchase Order Creation

1. Go to Purchase Orders
2. You should see a new PO created for the approved recommendation
3. The PO will be in "Pending" status
4. It will be linked to the recommended supplier

## Troubleshooting

### Ollama Not Accessible

```bash
# Check if Ollama container is running
docker ps | grep ollama

# Check Ollama logs
docker logs inventree-ollama-1

# Test Ollama API
curl http://ollama:11434/api/tags
```

### llama3 Model Not Found

```bash
# Pull the model manually
curl -X POST http://ollama:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "llama3"}'
```

### Database Errors

```bash
# Reset migrations (WARNING: This will delete data!)
cd src/backend/InvenTree
python manage.py migrate ai_procurement zero
python manage.py migrate ai_procurement
```

### Check Logs

```bash
# View Django logs
tail -f /home/inventree/dev/logs/inventree.log

# View pipeline execution logs
python manage.py shell
>>> from ai_procurement.models import PipelineExecution
>>> for p in PipelineExecution.objects.all():
...     print(f"{p.id}: {p.status} - {p.error_message}")
```

## Environment Variables

The following environment variables are pre-configured in the devcontainer:

```bash
AI_PROCUREMENT_OLLAMA_URL=http://ollama:11434/api/generate
AI_PROCUREMENT_PRICE_WEIGHT=0.4
AI_PROCUREMENT_LEAD_TIME_WEIGHT=0.3
AI_PROCUREMENT_RELIABILITY_WEIGHT=0.3
AI_PROCUREMENT_FORECAST_DAYS=30
AI_PROCUREMENT_APPROVAL_TIMEOUT_DAYS=7
AI_PROCUREMENT_EMA_ALPHA=0.3
AI_PROCUREMENT_PROPHET_CACHE_TTL_DAYS=7
```

You can override these in `.devcontainer/docker-compose.yml` if needed.

## Next Steps

- Read the full [TESTING.md](./TESTING.md) for more test scenarios
- Review the [README.md](./README.md) for architecture details
- Check [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) for feature status
- Explore the code in `agents/`, `learning/`, and `graph.py`

## Getting Help

If you encounter issues:

1. Check the logs (see Troubleshooting section)
2. Review the error messages in the Django admin
3. Check the PipelineExecution table for error details
4. Verify all services are running: `docker ps`
5. Ensure you have sufficient resources (RAM, disk space)

## Performance Notes

- First pipeline execution will be slow (Prophet model training)
- Subsequent executions use cached models (7-day TTL)
- LLM calls take 2-5 seconds depending on your hardware
- Prophet forecasting takes 1-3 seconds for 180 days of data
- Overall pipeline execution: 10-20 seconds until approval gate

## Development Tips

- Use `invoke server` for hot-reloading during development
- Run `python manage.py shell` to test agents interactively
- Check `logging_config.py` to adjust log levels
- Use the Django admin to inspect database tables
- Monitor Ollama with `curl http://ollama:11434/api/ps`

Happy testing! 🚀

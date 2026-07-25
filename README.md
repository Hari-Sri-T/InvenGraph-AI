<div align="center">
 <h1> InvenGraph-AI</h1>
 <p><strong>Agentic AI Procurement System built on top of InvenTree</strong></p>
 <p>Autonomous inventory management powered by LangGraph, Prophet, and local LLMs (Ollama)</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/license/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.x-green.svg)](https://www.djangoproject.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-purple.svg)](https://github.com/langchain-ai/langgraph)

</div>

---

## What is InvenGraph-AI?

**InvenGraph-AI** extends the open-source [InvenTree](https://inventree.org/) inventory management platform with a fully autonomous, event-driven AI procurement system (`ai_procurement` plugin).

When stock levels fall below a reorder threshold, the system **automatically**:
1. Forecasts demand using **Prophet** (time-series ML)
2. Ranks suppliers using **multi-criteria scoring** (price, lead time, reliability)
3. Makes a procurement decision using a **local LLM** (Ollama llama3)
4. Pauses for **human approval** before creating any purchase order
5. Creates the purchase order in InvenTree upon approval
6. **Learns** from outcomes to continuously improve future decisions

---

## Architecture

```
Stock Change / Sales Order


 Django Signal (event trigger)



 LangGraph Pipeline 

 1. Data Collection 
 2. Demand Forecasting Prophet 
 3. Supplier Ranking MCDA 
 4. Decision Making Ollama LLM 
 5. Human Approval Gate (HITL) 
 6. PO Execution InvenTree 
 7. Learning Update Feedback 

```

### Multi-Agent System

| Agent | Role | Technology |
|---|---|---|
| **Demand Agent** | 30-day demand forecasting | Prophet + XGBoost fallback |
| **Supplier Agent** | Multi-criteria supplier ranking | Weighted scoring (price 40%, lead time 30%, reliability 30%) |
| **Decision Agent** | Intelligent procurement decisions with reasoning | Ollama llama3 + rule-based fallback |
| **Execution Agent** | Atomic purchase order creation | Django ORM + InvenTree API |

### Tech Stack

- **Backend**: Python 3.10+, Django, Django REST Framework
- **AI Orchestration**: LangGraph (multi-agent state machine)
- **Forecasting**: Prophet, XGBoost, Pandas
- **LLM**: Ollama (llama3, runs locally — no OpenAI API needed)
- **Task Queue**: django-q2 (async background tasks)
- **Frontend**: React + TypeScript (Mantine UI)
- **Database**: SQLite (dev) / PostgreSQL (production)

---

## Key Features

- ** Autonomous Triggering** — Pipeline fires automatically on stock changes or sales orders via Django signals, with 60-second deduplication
- ** Prophet Forecasting** — 180-day historical data analysis with seasonality detection, confidence intervals, and 7-day model caching
- ** Smart Supplier Ranking** — Configurable multi-criteria scoring with MOQ constraint checking and reliability tracking
- ** LLM-Powered Decisions** — Ollama llama3 with few-shot learning and JSON-structured output; rule-based fallback when LLM is unavailable
- ** Human-in-the-Loop** — Approval gate with approve / reject / modify actions and 7-day timeout
- ** Continuous Learning** — Logs outcomes, retrains Prophet models, adjusts reorder points, updates supplier reliability scores
- ** Real-time UI** — React panel with 10-second auto-refresh, supplier comparison tables, and pipeline status timeline
- ** REST API** — 5 endpoints for programmatic pipeline management

---

## Performance

| Operation | Time |
|---|---|
| First pipeline run (Prophet training) | 15–25 seconds |
| Cached pipeline run | 8–12 seconds |
| LLM decision (llama3) | 2–5 seconds |
| Supplier ranking | < 1 second |

**Resource Requirements**: ~2 GB RAM for InvenTree, ~4 GB RAM for Ollama (llama3 model is ~5 GB on disk).

---

## Getting Started

### Prerequisites

- Python 3.10 or 3.11
- [Ollama](https://ollama.ai/) installed and running
- Docker + VS Code (for the DevContainer method)

### Method 1: DevContainer — Quickest (Recommended for Testing)

All services (InvenTree, Ollama) are pre-configured in Docker.

1. **Open the project in VS Code**
2. Press `F1` → **"Dev Containers: Reopen in Container"** (first build takes ~10–15 min)
3. Inside the container, run the setup script:
 ```bash
 bash .devcontainer/setup_ai_procurement.sh
 ```
 This installs dependencies and pulls the llama3 model (~5–10 min).
4. Start the server:
 ```bash
 cd src/backend/InvenTree
 invoke server
 ```
5. Open **http://localhost:8000/admin** and create a superuser if prompted.

---

### Method 2: Native Installation

#### 1. Install Prerequisites

```bash
# Install Ollama and pull the llama3 model
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull llama3
```

#### 2. Set Up Python Environment

```bash
cd src/backend/InvenTree
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r ai_procurement/requirements.txt
```

#### 3. Configure Environment Variables

Source the setup script (no secrets — all values are defaults you can change):
```bash
# From the project root
source scripts/setup_env.sh
```

Or set them manually:
```bash
export INVENTREE_DB_ENGINE=sqlite3
export INVENTREE_DB_NAME=./dev/database.sqlite3
export INVENTREE_MEDIA_ROOT=./dev/media
export INVENTREE_STATIC_ROOT=./dev/static
export INVENTREE_BACKUP_DIR=./dev/backup
export INVENTREE_PLUGIN_DIR=./dev/plugins
export INVENTREE_CONFIG_FILE=./dev/config.yaml
export INVENTREE_SECRET_KEY_FILE=./dev/secret_key.txt
export INVENTREE_DEBUG=True
export INVENTREE_PLUGINS_ENABLED=True

# AI Procurement
export AI_PROCUREMENT_OLLAMA_URL=http://localhost:11434/api/generate
export AI_PROCUREMENT_PRICE_WEIGHT=0.4
export AI_PROCUREMENT_LEAD_TIME_WEIGHT=0.3
export AI_PROCUREMENT_RELIABILITY_WEIGHT=0.3
```

#### 4. Run Migrations & Start

```bash
cd src/backend/InvenTree

# Create required directories
mkdir -p ../../../dev/{media,static,backup,plugins}

# Run migrations
python manage.py migrate
python manage.py makemigrations ai_procurement
python manage.py migrate ai_procurement

# Create admin user
python manage.py createsuperuser

# Start server
python manage.py runserver 0.0.0.0:8000
```

---

## Quick Test (5 minutes)

Once the server is running at **http://localhost:8000**:

**1. Create test data in the admin panel:**
- Create a Part (Name: "Test Widget", Minimum Stock: 10)
- Create 2–3 Supplier companies, each with a SupplierPart linked to the test part
- Add a Stock Item for the part with quantity 15

**2. Get an API token:**
```bash
python manage.py drf_create_token <your_username>
```

**3. Trigger the pipeline:**
```bash
curl -X POST http://localhost:8000/api/ai/procurement/pipeline/trigger/ \
 -H "Content-Type: application/json" \
 -H "Authorization: Token YOUR_TOKEN" \
 -d '{"part_id": 1}'
```

**4. Check pending approvals:**
```bash
curl http://localhost:8000/api/ai/procurement/approvals/ \
 -H "Authorization: Token YOUR_TOKEN"
```

**5. Approve the recommendation:**
```bash
curl -X POST http://localhost:8000/api/ai/procurement/approvals/<REQUEST_ID>/action/ \
 -H "Content-Type: application/json" \
 -H "Authorization: Token YOUR_TOKEN" \
 -d '{"action": "approve"}'
```

**6. Check Purchase Orders** — a new PO should appear in the InvenTree UI linked to the recommended supplier.

You can also trigger the pipeline naturally by reducing a stock item's quantity below its minimum stock level in the admin panel.

---

## Project Structure

The AI procurement system lives entirely in one plugin directory:

```
src/backend/InvenTree/ai_procurement/
 agents/
 demand_agent.py # Prophet demand forecasting
 supplier_agent.py # Multi-criteria supplier ranking
 decision_agent.py # Ollama LLM integration
 execution_agent.py # Purchase order creation
 learning/
 learning_layer.py # Continuous improvement feedback loop
 management/commands/
 update_actual_demand.py
 migrations/
 0001_initial.py
 models.py # 10 Django models
 graph.py # LangGraph 7-node workflow
 state_manager.py # LangGraph state & checkpointing
 signals.py # Django event triggers
 tasks.py # Async background tasks (django-q2)
 approval_gate.py # Human-in-the-loop logic
 notifications.py # In-app and email notifications
 views.py # REST API endpoints
 urls.py # URL routing
 config.py # All configuration parameters
 requirements.txt # AI-specific Python dependencies
 setup.sh # Setup helper script

src/frontend/src/pages/part/
 AIProcurementPanel.tsx # React UI panel

scripts/
 setup_env.sh # Environment variable setup script
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/ai/procurement/pipeline/trigger/` | Manually trigger pipeline for a part |
| `GET` | `/api/ai/procurement/pipeline/status/<id>/` | Get pipeline execution status |
| `GET` | `/api/ai/procurement/approvals/` | List pending approval requests |
| `POST` | `/api/ai/procurement/approvals/<id>/action/` | Approve / reject / modify a recommendation |

---

## Configuration Reference

All settings can be overridden via environment variables:

| Variable | Default | Description |
|---|---|---|
| `AI_PROCUREMENT_OLLAMA_URL` | `http://localhost:11434/api/generate` | Ollama API endpoint |
| `AI_PROCUREMENT_OLLAMA_MODEL` | `llama3` | LLM model to use |
| `AI_PROCUREMENT_PRICE_WEIGHT` | `0.4` | Supplier scoring weight for price |
| `AI_PROCUREMENT_LEAD_TIME_WEIGHT` | `0.3` | Supplier scoring weight for lead time |
| `AI_PROCUREMENT_RELIABILITY_WEIGHT` | `0.3` | Supplier scoring weight for reliability |
| `AI_PROCUREMENT_FORECAST_DAYS` | `30` | Days to forecast ahead |
| `AI_PROCUREMENT_APPROVAL_TIMEOUT_DAYS` | `7` | Days before approval request expires |
| `AI_PROCUREMENT_EMA_ALPHA` | `0.3` | Learning rate for EMA updates |
| `AI_PROCUREMENT_PROPHET_CACHE_TTL_DAYS` | `7` | How long to cache trained Prophet models |

---

## Troubleshooting

**Pipeline doesn't trigger automatically**
- Check that `minimum_stock` is set on the part
- Verify the stock quantity is below `minimum_stock`
- Check Django server logs for signal errors

**Ollama connection error**
```bash
# Verify Ollama is running and model is available
curl http://localhost:11434/api/tags
ollama list # should show llama3
```

**Migration errors**
```bash
# Reset and reapply ai_procurement migrations
python manage.py migrate ai_procurement zero
python manage.py migrate ai_procurement
```

**"No suppliers found" in pipeline**
- Go to the Part's Suppliers tab in InvenTree and add at least one SupplierPart with a price

---

## Further Documentation

- **Testing Guide**: [`docs/TESTING_CHECKLIST.md`](docs/TESTING_CHECKLIST.md)
- **AI Module README**: [`src/backend/InvenTree/ai_procurement/README.md`](src/backend/InvenTree/ai_procurement/README.md)
- **DevContainer Guide**: [`src/backend/InvenTree/ai_procurement/DEVCONTAINER_QUICKSTART.md`](src/backend/InvenTree/ai_procurement/DEVCONTAINER_QUICKSTART.md)
- **Native Installation**: [`src/backend/InvenTree/ai_procurement/NATIVE_INSTALLATION.md`](src/backend/InvenTree/ai_procurement/NATIVE_INSTALLATION.md)

---

## Acknowledgements

Built on top of:
- [InvenTree](https://inventree.org/) — Open-source inventory management
- [LangGraph](https://github.com/langchain-ai/langgraph) — Multi-agent orchestration
- [Prophet](https://facebook.github.io/prophet/) — Time-series forecasting
- [Ollama](https://ollama.ai/) — Local LLM inference

## License

Distributed under the [MIT License](LICENSE).

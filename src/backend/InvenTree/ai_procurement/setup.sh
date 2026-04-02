#!/bin/bash

# Setup script for Agentic AI Procurement System
# Run this from the InvenTree backend directory

set -e

echo "🤖 Setting up Agentic AI Procurement System..."
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Please run this script from the InvenTree backend directory (where manage.py is located)"
    exit 1
fi

# Step 1: Install Python dependencies
echo "📦 Step 1: Installing Python dependencies..."
pip install langgraph langgraph-checkpoint-postgres prophet xgboost pandas numpy requests
echo "✅ Dependencies installed"
echo ""

# Step 2: Check Ollama
echo "🦙 Step 2: Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is installed"
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is running"
        
        # Check if llama3 is available
        if ollama list | grep -q "llama3"; then
            echo "✅ llama3 model is available"
        else
            echo "⚠️  llama3 model not found. Pulling now..."
            ollama pull llama3
            echo "✅ llama3 model pulled"
        fi
    else
        echo "⚠️  Ollama is not running. Please start it with: ollama serve"
        echo "   Or it will start automatically when you run: ollama pull llama3"
    fi
else
    echo "⚠️  Ollama is not installed"
    echo "   Please install from: https://ollama.ai/download"
    echo "   Then run: ollama pull llama3"
fi
echo ""

# Step 3: Run migrations
echo "🗄️  Step 3: Running database migrations..."
python manage.py makemigrations ai_procurement
python manage.py migrate ai_procurement
echo "✅ Migrations applied"
echo ""

# Step 4: Verify setup
echo "🔍 Step 4: Verifying setup..."

# Check if models are created
python manage.py shell -c "
from ai_procurement.models import PipelineExecution, ApprovalRequest
print('✅ Database models are accessible')
"

# Check if agents are importable
python manage.py shell -c "
from ai_procurement.agents.demand_agent import DemandAgent
from ai_procurement.agents.supplier_agent import SupplierAgent
from ai_procurement.agents.decision_agent import DecisionAgent
from ai_procurement.agents.execution_agent import ExecutionAgent
print('✅ All agents are importable')
"

# Check if LangGraph components are importable
python manage.py shell -c "
from ai_procurement.state_manager import StateManager
from ai_procurement.graph import compile_procurement_graph
print('✅ LangGraph components are accessible')
"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start the Django development server:"
echo "   python manage.py runserver"
echo ""
echo "2. Open InvenTree in your browser:"
echo "   http://localhost:8000"
echo ""
echo "3. Navigate to a Part detail page and look for the 'Agentic AI Procurement' panel"
echo ""
echo "4. Click 'Trigger Pipeline' to test the system"
echo ""
echo "📖 For detailed testing instructions, see:"
echo "   ai_procurement/TESTING.md"
echo ""

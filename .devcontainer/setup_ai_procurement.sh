#!/bin/bash
# Setup script for AI Procurement in devcontainer

set -e

echo "========================================="
echo "AI Procurement Setup Script"
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the devcontainer
if [ "$INVENTREE_DEVCONTAINER" != "True" ]; then
    echo -e "${YELLOW}Warning: Not running in devcontainer${NC}"
fi

echo ""
echo "Step 1: Installing Python dependencies..."
cd /home/inventree/src/backend/InvenTree/ai_procurement
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}! requirements.txt not found, skipping${NC}"
fi

echo ""
echo "Step 2: Running Django migrations..."
cd /home/inventree/src/backend/InvenTree
python manage.py makemigrations ai_procurement
python manage.py migrate ai_procurement
echo -e "${GREEN}✓ Migrations completed${NC}"

echo ""
echo "Step 3: Checking Ollama service..."
if curl -s http://ollama:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama service is running${NC}"
    
    echo ""
    echo "Step 4: Pulling llama3 model..."
    echo -e "${YELLOW}This may take several minutes...${NC}"
    
    # Pull llama3 model
    curl -X POST http://ollama:11434/api/pull \
        -H "Content-Type: application/json" \
        -d '{"name": "llama3"}' \
        --max-time 600
    
    echo -e "${GREEN}✓ llama3 model pulled${NC}"
else
    echo -e "${RED}✗ Ollama service is not accessible${NC}"
    echo "Please ensure the ollama container is running"
    exit 1
fi

echo ""
echo "Step 5: Creating test data (optional)..."
read -p "Do you want to create test data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # TODO: Add test data creation script
    echo -e "${YELLOW}Test data creation not yet implemented${NC}"
fi

echo ""
echo "========================================="
echo -e "${GREEN}AI Procurement Setup Complete!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Start the InvenTree server: invoke server"
echo "2. Access the UI at http://localhost:8000"
echo "3. Configure parts and suppliers"
echo "4. Test the AI procurement pipeline"
echo ""
echo "For testing instructions, see:"
echo "  src/backend/InvenTree/ai_procurement/TESTING.md"
echo ""

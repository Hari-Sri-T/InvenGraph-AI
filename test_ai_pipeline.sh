#!/bin/bash
# Test script to demonstrate AI procurement pipeline

echo "=== Testing AI Procurement Pipeline ==="
echo ""

# Get CSRF token and session
echo "1. Getting CSRF token..."
curl -c /tmp/test_cookies.txt -s http://localhost:8000/ai/login/ > /dev/null
CSRF_TOKEN=$(grep csrftoken /tmp/test_cookies.txt | awk '{print $7}')
echo "   CSRF Token: ${CSRF_TOKEN:0:20}..."

# Login
echo ""
echo "2. Logging in as admin..."
curl -b /tmp/test_cookies.txt -c /tmp/test_cookies.txt -s \
  -X POST http://localhost:8000/ai/login/ \
  -d "username=admin&password=admin123&csrfmiddlewaretoken=$CSRF_TOKEN" \
  -H "Referer: http://localhost:8000/ai/login/" > /dev/null
echo "   ✓ Logged in"

# Get a part that needs procurement
echo ""
echo "3. Finding parts that need procurement..."
PARTS_HTML=$(curl -b /tmp/test_cookies.txt -s http://localhost:8000/ai/parts/)
# Extract first part ID from the HTML (this is a simple grep, might need adjustment)
PART_ID=$(echo "$PARTS_HTML" | grep -o 'data-part-id="[0-9]*"' | head -1 | grep -o '[0-9]*')

if [ -z "$PART_ID" ]; then
  echo "   ✗ No parts found. Run: python manage.py create_demo_data"
  exit 1
fi

echo "   Found part ID: $PART_ID"

# Trigger AI procurement pipeline
echo ""
echo "4. Triggering AI procurement pipeline for part $PART_ID..."
RESPONSE=$(curl -b /tmp/test_cookies.txt -s \
  -X POST http://localhost:8000/api/ai/procurement/pipeline/trigger/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF_TOKEN" \
  -d "{\"part_id\": $PART_ID}")

echo "   Response: $RESPONSE"

PIPELINE_ID=$(echo "$RESPONSE" | grep -o '"pipeline_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$PIPELINE_ID" ]; then
  echo "   ✗ Failed to start pipeline"
  exit 1
fi

echo "   ✓ Pipeline started: $PIPELINE_ID"

# Check pipeline status
echo ""
echo "5. Checking pipeline status..."
sleep 2
STATUS=$(curl -b /tmp/test_cookies.txt -s \
  "http://localhost:8000/api/ai/procurement/pipeline/status/$PIPELINE_ID/")

echo "$STATUS" | python3 -m json.tool 2>/dev/null || echo "$STATUS"

echo ""
echo "=== Test Complete ==="
echo ""
echo "Next steps:"
echo "  1. Open browser to: http://localhost:8000/ai/login/"
echo "  2. Login with: admin / admin123"
echo "  3. View pipeline at: http://localhost:8000/ai/procurement/pipeline/$PIPELINE_ID/"
echo "  4. Check approvals at: http://localhost:8000/ai/approvals/"
echo ""

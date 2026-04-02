#!/bin/bash

# Test script to demonstrate AI frontend access

echo "=== AI Procurement Frontend Test ==="
echo ""

# Step 1: Get login page and extract CSRF token
echo "Step 1: Getting login page..."
COOKIES_FILE="/tmp/ai_cookies.txt"
rm -f $COOKIES_FILE

curl -s -c $COOKIES_FILE http://localhost:8000/ai/login/ > /tmp/login_page.html
CSRF_TOKEN=$(grep csrftoken $COOKIES_FILE | awk '{print $7}')

if [ -z "$CSRF_TOKEN" ]; then
    echo "ERROR: Could not get CSRF token"
    exit 1
fi

echo "✓ Got CSRF token: ${CSRF_TOKEN:0:20}..."
echo ""

# Step 2: Login
echo "Step 2: Logging in as admin..."
LOGIN_RESPONSE=$(curl -s -b $COOKIES_FILE -c $COOKIES_FILE \
    -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "Referer: http://localhost:8000/ai/login/" \
    --data-urlencode "username=admin" \
    --data-urlencode "password=admin123" \
    --data-urlencode "csrfmiddlewaretoken=$CSRF_TOKEN" \
    -w "\n%{http_code}" \
    http://localhost:8000/ai/login/?next=/ai/dashboard/)

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Login successful (HTTP $HTTP_CODE)"
else
    echo "ERROR: Login failed (HTTP $HTTP_CODE)"
    exit 1
fi
echo ""

# Step 3: Access Dashboard
echo "Step 3: Accessing AI Dashboard..."
DASHBOARD_RESPONSE=$(curl -s -b $COOKIES_FILE -w "\n%{http_code}" http://localhost:8000/ai/dashboard/)
HTTP_CODE=$(echo "$DASHBOARD_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Dashboard accessible (HTTP $HTTP_CODE)"
    # Check if we got HTML
    if echo "$DASHBOARD_RESPONSE" | grep -q "AI Dashboard"; then
        echo "✓ Dashboard contains expected content"
    else
        echo "⚠ Dashboard might not have expected content"
    fi
else
    echo "ERROR: Dashboard not accessible (HTTP $HTTP_CODE)"
fi
echo ""

# Step 4: Access Parts List
echo "Step 4: Accessing Parts List..."
PARTS_RESPONSE=$(curl -s -b $COOKIES_FILE -w "\n%{http_code}" http://localhost:8000/ai/parts/)
HTTP_CODE=$(echo "$PARTS_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Parts list accessible (HTTP $HTTP_CODE)"
    
    # Count how many parts are displayed
    PART_COUNT=$(echo "$PARTS_RESPONSE" | grep -o "View Details" | wc -l)
    echo "✓ Found $PART_COUNT parts displayed"
    
    # Check for specific parts
    if echo "$PARTS_RESPONSE" | grep -q "Resistor 10K Ohm"; then
        echo "✓ Demo part 'Resistor 10K Ohm' found"
    fi
    
    if echo "$PARTS_RESPONSE" | grep -q "AI Forecast"; then
        echo "✓ AI Forecast data is displayed"
    fi
else
    echo "ERROR: Parts list not accessible (HTTP $HTTP_CODE)"
fi
echo ""

# Step 5: Access Approvals
echo "Step 5: Accessing Approval Queue..."
APPROVALS_RESPONSE=$(curl -s -b $COOKIES_FILE -w "\n%{http_code}" http://localhost:8000/ai/approvals/)
HTTP_CODE=$(echo "$APPROVALS_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Approval queue accessible (HTTP $HTTP_CODE)"
    
    # Check for pending approvals
    if echo "$APPROVALS_RESPONSE" | grep -q "pending"; then
        echo "✓ Pending approvals found"
    else
        echo "⚠ No pending approvals (this is normal if none exist)"
    fi
else
    echo "ERROR: Approval queue not accessible (HTTP $HTTP_CODE)"
fi
echo ""

# Step 6: Access Suppliers
echo "Step 6: Accessing Suppliers List..."
SUPPLIERS_RESPONSE=$(curl -s -b $COOKIES_FILE -w "\n%{http_code}" http://localhost:8000/ai/suppliers/)
HTTP_CODE=$(echo "$SUPPLIERS_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Suppliers list accessible (HTTP $HTTP_CODE)"
    
    # Check for demo suppliers
    if echo "$SUPPLIERS_RESPONSE" | grep -q "TechSupply Inc"; then
        echo "✓ Demo supplier 'TechSupply Inc' found"
    fi
    
    if echo "$SUPPLIERS_RESPONSE" | grep -q "AI Score"; then
        echo "✓ AI scores are displayed"
    fi
else
    echo "ERROR: Suppliers list not accessible (HTTP $HTTP_CODE)"
fi
echo ""

echo "=== Test Complete ==="
echo ""
echo "To access the AI interface manually:"
echo "1. Open your browser to: http://localhost:8000/ai/login/"
echo "2. Login with username: admin, password: admin123"
echo "3. You'll be redirected to the AI Dashboard"
echo ""
echo "Available pages:"
echo "- Dashboard: http://localhost:8000/ai/dashboard/"
echo "- Parts: http://localhost:8000/ai/parts/"
echo "- Approvals: http://localhost:8000/ai/approvals/"
echo "- Suppliers: http://localhost:8000/ai/suppliers/"
echo "- Inventory: http://localhost:8000/ai/inventory/"
echo "- Analytics: http://localhost:8000/ai/analytics/"

# Cleanup
rm -f $COOKIES_FILE /tmp/login_page.html

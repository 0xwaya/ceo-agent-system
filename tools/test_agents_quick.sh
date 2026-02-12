#!/bin/bash

# Quick test for all agent execute buttons
echo "🧪 Testing All Agent Execute Buttons..."
echo "========================================"

agents=("branding" "web_development" "legal" "martech" "content" "campaigns")
passed=0
failed=0

for agent in "${agents[@]}"; do
    echo ""
    echo "🧪 Testing $agent..."
    
    response=$(curl -s -X POST "http://localhost:5001/api/agent/execute/$agent" \
        -H "Content-Type: application/json" \
        -d '{
            "task": "Test execution",
            "company_info": {
                "company_name": "Test Company",
                "industry": "Tech",
                "location": "SF"
            }
        }')
    
    # Check if response has success=true
    if echo "$response" | grep -q '"success": true'; then
        budget=$(echo "$response" | grep -o '"budget_used": [0-9.]*' | grep -o '[0-9.]*')
        deliverables=$(echo "$response" | grep -o '"deliverables"' | wc -l)
        echo "✅ $agent Execute Success! Budget: \$$budget"
        ((passed++))
    else
        error=$(echo "$response" | grep -o '"error": "[^"]*"' || echo "Unknown error")
        echo "❌ $agent Execute Failed: $error"
        ((failed++))
    fi
done

echo ""
echo "========================================"
echo "📊 Test Summary: $passed/6 agents passed"
echo "========================================"

if [ $failed -eq 0 ]; then
    echo "✅ All agents working!"
    exit 0
else
    echo "❌ $failed agents failed"
    exit 1
fi

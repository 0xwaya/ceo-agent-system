#!/bin/bash

echo "🔍 Verifying All Agent Endpoints..."
echo "======================================"

agents=("branding" "web_development" "legal" "martech" "content" "campaigns")
pass=0
fail=0

for agent in "${agents[@]}"; do
    echo ""
    echo "Testing: $agent"

    response=$(curl -s -X POST "http://localhost:5001/api/agent/execute/$agent" \
        -H "Content-Type: application/json" \
        -d "{\"task\":\"Test execution\",\"company_info\":{\"company_name\":\"Test Co\",\"industry\":\"Technology\",\"location\":\"San Francisco\"}}")

    success=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
    deliverables=$(echo "$response" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('result',{}).get('deliverables',[])))" 2>/dev/null)
    budget=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('result',{}).get('budget_used',0))" 2>/dev/null)

    if [ "$success" = "True" ] && [ ! -z "$deliverables" ] && [ "$deliverables" -gt 0 ]; then
        echo "  ✅ SUCCESS - Deliverables: $deliverables, Budget: \$$budget"
        ((pass++))
    else
        echo "  ❌ FAILED - Success: $success, Deliverables: $deliverables"
        ((fail++))
    fi
done

echo ""
echo "======================================"
echo "📊 Final Results: $pass/$((pass + fail)) agents working"
echo "======================================"

if [ $fail -eq 0 ]; then
    echo "✅ ALL AGENTS OPERATIONAL!"
    exit 0
else
    echo "❌ $fail agents need attention"
    exit 1
fi

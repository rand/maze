#!/bin/bash
# Test Modal deployment
# Based on lift-sys testing patterns

set -e

echo "============================================================"
echo "Testing Maze Modal Deployment"
echo "============================================================"

if [ -z "$MODAL_ENDPOINT_URL" ]; then
    echo "❌ MODAL_ENDPOINT_URL not set"
    echo "Set to your Modal endpoint URL:"
    echo "  export MODAL_ENDPOINT_URL=https://<user>--maze-inference-fastapi-app.modal.run"
    exit 1
fi

echo "Testing endpoint: $MODAL_ENDPOINT_URL"
echo ""

# Test 1: Health check
echo "Test 1: Health Check"
echo "-----------------------------------------------------------"
curl -s "$MODAL_ENDPOINT_URL/health" | python -m json.tool
echo ""

# Test 2: Simple generation
echo ""
echo "Test 2: Simple Python Generation"
echo "-----------------------------------------------------------"
curl -s -X POST "$MODAL_ENDPOINT_URL/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "def add(a: int, b: int) -> int:",
    "language": "python",
    "max_tokens": 256,
    "temperature": 0.7
  }' | python -m json.tool | head -20

echo ""
echo "✅ Tests complete!"
echo ""
echo "To test with Maze CLI:"
echo "  maze config set generation.provider modal"
echo "  maze generate \"Create a Python function\""
echo ""

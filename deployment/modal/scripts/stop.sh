#!/bin/bash
# Stop Modal deployment to save costs
# Based on lift-sys cost optimization patterns

set -e

echo "============================================================"
echo "Stopping Maze Inference Server on Modal"
echo "============================================================"

# Stop the app
echo "Stopping maze-inference app..."
modal app stop maze-inference

echo ""
echo "✅ App stopped"
echo ""
echo "Cost savings:"
echo "  - No more idle time charges"
echo "  - Restart with: ./deployment/modal/scripts/deploy.sh"
echo ""

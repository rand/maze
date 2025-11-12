#!/bin/bash
# Deploy Maze inference server to Modal
# Based on lift-sys deployment patterns

set -e

echo "============================================================"
echo "Deploying Maze Inference Server to Modal"
echo "============================================================"

# Check Modal is installed
if ! command -v modal &> /dev/null; then
    echo "❌ Modal CLI not found"
    echo "Install with: pip install modal"
    exit 1
fi

# Check Modal is authenticated
if ! modal token show &> /dev/null; then
    echo "❌ Modal not authenticated"
    echo "Run: modal setup"
    exit 1
fi

# Check for HuggingFace secret
echo "Checking Modal secrets..."
if ! modal secret list | grep -q "huggingface-secret"; then
    echo "⚠️  HuggingFace secret not found"
    echo "Create with:"
    echo "  modal secret create huggingface-secret HF_TOKEN=hf_your_token"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set mode (default: dev)
MODE=${MODAL_MODE:-dev}
echo "Deployment mode: $MODE"
echo "Scaledown window: $([ "$MODE" = "dev" ] && echo "2 min" || [ "$MODE" = "demo" ] && echo "10 min" || echo "5 min")"

# Deploy
echo ""
echo "Deploying to Modal..."
export MODAL_MODE=$MODE

cd "$(dirname "$0")/../../.."  # Go to maze root
modal deploy deployment/modal/modal_app.py

echo ""
echo "============================================================"
echo "✅ Deployment Complete!"
echo "============================================================"
echo ""
echo "Your endpoints:"
echo "  Generate: https://<user>--maze-inference-fastapi-app.modal.run/generate"
echo "  Health: https://<user>--maze-inference-fastapi-app.modal.run/health"
echo "  Docs: https://<user>--maze-inference-fastapi-app.modal.run/docs"
echo ""
echo "Configure Maze:"
echo "  export MODAL_ENDPOINT_URL=https://<user>--maze-inference-fastapi-app.modal.run"
echo "  maze config set generation.provider modal"
echo ""
echo "Test:"
echo "  maze generate \"Create a Python function\""
echo ""
echo "To stop (save costs):"
echo "  ./deployment/modal/scripts/stop.sh"
echo ""

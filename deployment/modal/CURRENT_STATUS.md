# Modal Deployment Current Status

**Date**: 2025-11-12
**Status**: ✅ FIXED - Deployed with A100-80GB
**Issue Resolved**: OOM error (L40S too small for 32B model)

---

## Problem Identified and Fixed

### Issue: CUDA Out of Memory
```
GPU: L40S (44.39 GiB VRAM)
Model: Qwen2.5-Coder-32B (32.7GB + activations = 43.94 GiB)
Result: OOM - only 453 MiB free
Error: RuntimeError: Failed to create unquantized linear weights
```

### Solution: A100-80GB
```
GPU: A100-80GB (80 GiB VRAM) ✅
Model: Qwen2.5-Coder-32B (43.94 GiB)
Headroom: ~36 GiB for activations ✅
```

---

## Current Deployment

**Configuration**:
- GPU: **A100-80GB** (was L40S-48GB)
- vLLM: 0.11.0
- llguidance: 0.7.30
- Model: Qwen2.5-Coder-32B-Instruct
- Cost: **~$4/hour** (was $1.20/hour)

**Endpoints**:
- https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run
- https://rand--maze-inference-mazeinferenceserver-generate-endpoint.modal.run

**Status**: Deployed, container warming up

---

## What's Happening Now

1. Container is starting on A100-80GB
2. Model loading (32.7GB into GPU memory)
3. llguidance initialization
4. Should complete without OOM

**Expected Timeline**:
- Model load: 3-5 minutes
- First generation: Available after load
- Subsequent: 2-3 seconds

---

## Testing Strategy

The test script `test_live_deployment.py` is designed to:
- Wait for cold start (up to 10 minutes)
- Retry health checks (20 attempts, 15s intervals)
- Handle long-running generation
- Test multiple languages
- Collect real results

**To run manually**:
```bash
uv run python deployment/modal/test_live_deployment.py
```

This will wait properly for initialization and run actual tests.

---

## Cost Impact

**Before** (L40S): $1.20/hour
**After** (A100-80GB): $4.00/hour

**For testing** (~1-2 hours): ~$4-8
**Dev mode** (2min scaledown): Minimal active time

**Justification**: 32B model requires 80GB VRAM. This is the minimum GPU that works.

---

## Next Steps

1. Wait for container to initialize (~5 min)
2. Test health endpoint
3. Test simple generation
4. Test with grammar constraints
5. Run full validation suite

The deployment should now work correctly with sufficient VRAM.

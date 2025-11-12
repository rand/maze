# Modal Deployment Status

**Date**: 2025-11-12
**Status**: ✅ DEPLOYED with vLLM 0.11.0 + llguidance
**State**: Cold start in progress

---

## Deployment Confirmed

### Final Configuration (Correct)

**Versions** (Research-verified):
- vLLM: **0.11.0** (latest stable, llguidance merged in 0.8.2)
- llguidance: **0.7.30** (compatible range: >=0.7.11,<0.8.0)
- transformers: **4.55.2** (required by vLLM 0.11.0)
- Model: Qwen2.5-Coder-32B-Instruct

**Backend**: llguidance (NOT outlines, NOT xgrammar)
- Supports Lark grammars ✅
- Maze's native format ✅

### Deployment Output

```
✓ App deployed in 239s
✓ Created web endpoint MazeInferenceServer.fastapi_app
✓ Created web endpoint MazeInferenceServer.generate_endpoint

Endpoint: https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run
```

---

## Current State

**Container**: Cold start in progress
- First request triggers model loading
- Qwen2.5-Coder-32B (32.7GB) loading into GPU
- Expected duration: 3-5 minutes
- Subsequent requests: 2-3 seconds

**Why Long Cold Start**:
- 32B parameter model (large)
- llguidance initialization
- GPU memory allocation
- First-time compilation

---

## Configuration Applied

### Maze Defaults

**Changed defaults to Modal**:
```python
# config.py
provider: str = "modal"  # Was: openai
model: str = "qwen2.5-coder-32b"  # Was: gpt-4
```

**Endpoint**:
```python
# modal.py
default = "https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run"
```

---

## How to Test (After Warmup)

### 1. Wait for Container Ready (~3-5 min from first request)

```bash
# Check health (triggers warmup if not already started)
curl https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run/health
```

### 2. Test Generation

```bash
export MODAL_ENDPOINT_URL=https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run

curl -X POST $MODAL_ENDPOINT_URL/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "def fibonacci(n: int) -> int:",
    "language": "python",
    "max_tokens": 128
  }'
```

### 3. Test with Maze CLI

```bash
cd /Users/rand/src/maze
maze init --language python
maze generate "Create async function with error handling"
```

### 4. Run Validation Suite

```bash
export MODAL_ENDPOINT_URL=https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run
pytest tests/validation/test_suite_comprehensive.py -v -k "python_simple"
```

---

## What's Deployed

### Image Contents ✅
- NVIDIA CUDA 12.4.1 devel
- Python 3.12
- vLLM 0.11.0
- llguidance 0.7.30 (compatible version)
- transformers 4.55.2
- FastAPI
- All optimizations (flashinfer, hf-transfer)

### Runtime Config ✅
- GPU: L40S (48GB VRAM, $1.20/hour)
- Scaledown: 2 minutes (dev mode)
- Model caching: Persistent volumes
- guided_decoding_backend: "llguidance"

---

## Verification Needed

Once container is warm:

1. ✅ Health endpoint responds
2. ⏳ Generation works
3. ⏳ Grammar constraints enforced
4. ⏳ All 5 languages functional
5. ⏳ Validation suite passes

---

## Expected Results

**When Working**:
- Health: `{"status": "healthy", "backend": "vLLM 0.11.0 + llguidance"}`
- Generation: Real Python/TypeScript/Rust/Go/Zig code
- Grammar: Syntax constraints enforced
- Speed: 2-3s per generation (warm)
- Quality: High (32B parameter model)

---

**Next**: Wait for cold start completion, then run actual validation tests

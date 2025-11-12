# Modal Deployment for Maze

Deploy Maze inference server on Modal.com with vLLM + llguidance.

## Prerequisites

1. **Modal Account**
```bash
pip install modal
modal setup
```

2. **Hugging Face Token** (for model download)
```bash
# Create secret in Modal dashboard
modal secret create huggingface-secret HF_TOKEN=hf_your_token_here
```

## Deployment

### 1. Deploy the Service

```bash
# From maze root directory
modal deploy deployment/modal/modal_app.py
```

This will:
- Build custom image with vLLM and llguidance
- Download Qwen2.5-Coder-32B-Instruct (32.7GB)
- Start vLLM server on L40S GPU
- Expose FastAPI endpoints
- Keep 1 container warm

Expected output:
```
✓ Created web function MazeInferenceServer.fastapi_app
✓ App deployed! 🎉

View endpoints at: https://modal.com/apps/...

Endpoints:
  https://<user>--maze-inference-fastapi-app.modal.run
```

### 2. Test the Deployment

```bash
# Run built-in tests
modal run deployment/modal/modal_app.py
```

Or test via HTTP:

```bash
curl -X POST https://<user>--maze-inference-fastapi-app.modal.run/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "def fibonacci(n: int) -> int:",
    "language": "python",
    "max_tokens": 512,
    "temperature": 0.7
  }'
```

### 3. Test with Grammar Constraints

```bash
curl -X POST https://<user>--maze-inference-fastapi-app.modal.run/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "def add(a: int, b: int) -> int:",
    "grammar": "?start: function_def\nfunction_def: \"def\" IDENT \"(\" params \")\" \":\" statement\nparams: IDENT (\":\" IDENT)? (\",\" IDENT (\":\" IDENT)?)*\nstatement: \"return\" IDENT \"+\" IDENT\nIDENT: /[a-zA-Z_][a-zA-Z0-9_]*/\n%ignore /\\s+/",
    "max_tokens": 256
  }'
```

## Integration with Maze

### 1. Add Modal Provider to Maze

Create `src/maze/orchestrator/providers/modal.py`:

```python
from maze.orchestrator.providers import ProviderAdapter, GenerationRequest, GenerationResponse
import requests
import os

class ModalProviderAdapter(ProviderAdapter):
    def __init__(self, model: str = "qwen2.5-coder-32b", api_key: Optional[str] = None):
        super().__init__(model, api_key)
        self.api_base = os.getenv("MODAL_ENDPOINT_URL")
        
    def supports_grammar(self) -> bool:
        return True
    
    def supports_json_schema(self) -> bool:
        return True
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        response = requests.post(
            f"{self.api_base}/generate",
            json={
                "prompt": request.prompt,
                "grammar": request.grammar,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            },
            timeout=60,
        )
        response.raise_for_status()
        
        data = response.json()
        return GenerationResponse(
            text=data["code"],
            finish_reason="stop",
            tokens_generated=data["metadata"]["tokens_generated"],
            metadata=data["metadata"],
        )
```

### 2. Configure Maze to Use Modal

```bash
# Set Modal endpoint URL
export MODAL_ENDPOINT_URL=https://<user>--maze-inference-fastapi-app.modal.run

# Configure Maze
maze config set generation.provider modal
maze config set generation.model qwen2.5-coder-32b

# Test
maze generate "Create a Python function to validate email addresses"
```

## Monitoring

### Check Service Health

```bash
curl https://<user>--maze-inference-fastapi-app.modal.run/health
```

### View Logs

```bash
modal app logs maze-inference
```

### Check Costs

```bash
modal profile
```

## Performance

Expected performance:
- **Cold start**: ~60s (model loading)
- **Warm inference**: 2-3s per generation
- **Throughput**: ~10-15 tokens/second
- **Grammar overhead**: <50μs per token (negligible)

## Cost Estimates

**With keep_warm=1**:
- Always-on cost: ~$30/day (~$900/month)
- Per-generation cost: $0.001-0.002

**With idle timeout (300s)**:
- Development usage: ~$5-10/day
- Per-generation cost: $0.001-0.002 + cold start

**Recommendation**: Use keep_warm=1 for testing, idle timeout for development.

## Troubleshooting

### Model Download Timeout

If model download times out:
```bash
# Increase timeout
modal deploy deployment/modal/modal_app.py --timeout 1800
```

### Out of Memory

If OOM errors:
```bash
# Reduce gpu_memory_utilization
# Edit modal_app.py: gpu_memory_utilization=0.85
# Or use 4-bit quantization
```

### llguidance Not Working

Verify llguidance installation:
```bash
modal run deployment/modal/modal_app.py::test_llguidance
```

## Next Steps

1. Deploy: `modal deploy deployment/modal/modal_app.py`
2. Get endpoint URL from output
3. Set `MODAL_ENDPOINT_URL` environment variable
4. Test with Maze: `maze generate "test"`
5. Run full validation benchmarks

## Related Files

- `modal_app.py` - Main Modal deployment
- `../modal-deployment-plan.md` - Detailed planning document
- `../../src/maze/orchestrator/providers/modal.py` - Provider adapter (to be created)

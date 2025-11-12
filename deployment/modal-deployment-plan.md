# Modal Deployment Plan: Maze with llguidance + Qwen2.5-Coder-32B

**Objective**: Deploy Maze on Modal.com for end-to-end constrained code generation testing

---

## Executive Summary

Deploy Qwen2.5-Coder-32B-Instruct on Modal with llguidance integration for grammar-constrained generation. This enables testing Maze's full capabilities in a production-like environment.

---

## Architecture Overview

```
┌─────────────┐
│   Client    │ (Maze CLI/API)
└──────┬──────┘
       │ HTTP POST /generate
       ▼
┌─────────────────────────────────┐
│  Modal Web Endpoint (FastAPI)   │
├─────────────────────────────────┤
│ - Parse request (prompt + grammar)
│ - Forward to vLLM instance      │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  vLLM + llguidance on L40S GPU  │
├─────────────────────────────────┤
│ - Qwen2.5-Coder-32B-Instruct    │
│ - llguidance token masking       │
│ - Grammar constraint enforcement │
└──────┬──────────────────────────┘
       │ Generated code
       ▼
┌─────────────┐
│   Response  │ (Constrained code)
└─────────────┘
```

---

## Model Specifications

**Qwen2.5-Coder-32B-Instruct**:
- **Size**: 32.7 GB (BF16 format)
- **Parameters**: 32.5B total
- **Memory Required**: ~40GB VRAM minimum
- **Recommended GPU**: L40S (48GB) or A100 (40GB/80GB)
- **Quantization**: Can use 4-bit for 24GB GPUs (L4)
- **Inference Server**: vLLM recommended
- **Context Length**: 32K tokens

**llguidance Integration**:
- **Compatible**: vLLM (merged support)
- **Also Compatible**: SGLang (use `--grammar-backend llguidance`)
- **Performance**: 50μs per token (negligible overhead)
- **Format**: Lark grammars (what Maze uses!)

---

## Deployment Strategy

### Option A: Full Model on L40S (Recommended)
**Best for**: Production testing, best quality

```python
# GPU: L40S (48GB VRAM, ~$1-2/hour)
# Model: Full BF16 (32.7GB)
# Fits comfortably with 15GB headroom
```

**Pros**:
- Full model quality
- Fast inference
- Plenty of memory for activations
- Good cost/performance

**Cons**:
- Higher cost (~$1-2/hour)

### Option B: Quantized Model on L4
**Best for**: Budget testing, experimentation

```python
# GPU: L4 (24GB VRAM, ~$0.60/hour)
# Model: 4-bit quantized (~8GB)
# Fits easily with 16GB headroom
```

**Pros**:
- Lower cost (60% cheaper)
- Still good quality
- Faster cold starts

**Cons**:
- Slightly lower quality
- Quantization overhead

---

## Modal Implementation

### 1. Custom Image with llguidance + vLLM

```python
import modal

# Build custom image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    # System dependencies
    .apt_install("git", "build-essential")
    # vLLM with llguidance support
    .uv_pip_install(
        "vllm==0.8.5",  # Version with llguidance support
        "torch==2.6.0",
        "transformers==4.47.1",
    )
    # llguidance Python bindings
    .run_commands(
        "git clone https://github.com/guidance-ai/llguidance.git /tmp/llguidance",
        "cd /tmp/llguidance && ./scripts/install-deps.sh",
        "cd /tmp/llguidance/python && pip install -e .",
    )
    # Maze dependencies
    .copy_local_dir("./src", "/app/maze/src")
    .uv_pip_install_from_requirements("requirements.txt")
    # Environment
    .env({
        "HF_HOME": "/cache/huggingface",
        "VLLM_CACHE": "/cache/vllm",
    })
)
```

### 2. vLLM Server with llguidance

```python
app = modal.App("maze-inference")

@app.cls(
    gpu="l40s",  # 48GB VRAM
    image=image,
    timeout=3600,  # 1 hour max
    container_idle_timeout=300,  # 5 min idle shutdown
    secrets=[modal.Secret.from_name("huggingface-secret")],
)
class MazeInferenceServer:
    """vLLM server with llguidance for Maze code generation."""

    @modal.enter()
    def start_vllm(self):
        """Load model with vLLM and llguidance support."""
        from vllm import LLM, SamplingParams
        import torch
        
        print("Loading Qwen2.5-Coder-32B-Instruct...")
        
        self.llm = LLM(
            model="Qwen/Qwen2.5-Coder-32B-Instruct",
            tensor_parallel_size=1,  # Single GPU
            gpu_memory_utilization=0.9,
            max_model_len=8192,  # Limit context for faster inference
            dtype="bfloat16",
            trust_remote_code=True,
            # Enable llguidance
            guided_decoding_backend="llguidance",
        )
        
        print("Model loaded successfully")
        print(f"GPU memory allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")

    @modal.method()
    def generate(
        self,
        prompt: str,
        grammar: str = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> dict:
        """Generate code with grammar constraints.

        Args:
            prompt: Code generation prompt
            grammar: Lark grammar for constraints (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated code and metadata
        """
        from vllm import SamplingParams
        import time
        
        start = time.time()
        
        # Configure sampling with grammar if provided
        sampling_params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95,
        )
        
        # Add grammar constraint (llguidance integration)
        if grammar:
            # Format grammar for llguidance in vLLM
            sampling_params.guided_decoding = {
                "backend": "llguidance",
                "grammar": grammar,
            }
        
        # Generate
        outputs = self.llm.generate([prompt], sampling_params)
        
        generated_text = outputs[0].outputs[0].text
        duration = time.time() - start
        
        return {
            "text": generated_text,
            "tokens_generated": len(outputs[0].outputs[0].token_ids),
            "duration_seconds": duration,
            "finish_reason": outputs[0].outputs[0].finish_reason,
            "grammar_applied": grammar is not None,
        }

    @modal.web_endpoint(method="POST")
    def web_generate(self, request: dict):
        """HTTP endpoint for code generation.

        POST /web_generate
        Body: {
            "prompt": "Create a function...",
            "grammar": "optional Lark grammar",
            "language": "python|typescript|rust|go|zig",
            "max_tokens": 2048,
            "temperature": 0.7
        }
        """
        result = self.generate(
            prompt=request.get("prompt"),
            grammar=request.get("grammar"),
            max_tokens=request.get("max_tokens", 2048),
            temperature=request.get("temperature", 0.7),
        )
        
        return {
            "success": True,
            "code": result["text"],
            "metadata": {
                "tokens": result["tokens_generated"],
                "duration_seconds": result["duration_seconds"],
                "grammar_constrained": result["grammar_applied"],
            }
        }
```

### 3. Maze Client Integration

```python
# In maze/orchestrator/providers/modal.py (NEW)

from maze.orchestrator.providers import ProviderAdapter, GenerationRequest, GenerationResponse
import requests

class ModalProviderAdapter(ProviderAdapter):
    """Adapter for Modal-deployed Maze inference server."""

    def __init__(
        self,
        model: str = "qwen2.5-coder-32b",
        api_key: Optional[str] = None,
        api_base: str = None,  # e.g., "https://username--maze-inference-web-generate.modal.run"
    ):
        super().__init__(model, api_key)
        self.api_base = api_base or os.getenv("MODAL_ENDPOINT_URL")

    def supports_grammar(self) -> bool:
        return True

    def supports_json_schema(self) -> bool:
        return True  # Can convert via grammar

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate using Modal endpoint."""
        
        payload = {
            "prompt": request.prompt,
            "grammar": request.grammar,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        response = requests.post(
            self.api_base,
            json=payload,
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
        
        data = response.json()
        
        return GenerationResponse(
            text=data["code"],
            finish_reason="stop",
            tokens_generated=data["metadata"]["tokens"],
            metadata=data["metadata"],
        )
```

---

## Performance Optimizations

### 1. Fast Cold Starts

```python
# Keep 1 container warm for instant response
@app.cls(
    gpu="l40s",
    image=image,
    keep_warm=1,  # Always 1 container ready
)
class MazeInferenceServer:
    pass
```

### 2. Model Caching

```python
# Cache model weights in Modal volume
volume = modal.Volume.from_name("model-cache", create_if_missing=True)

@app.cls(
    gpu="l40s",
    image=image,
    volumes={"/cache": volume},  # Persistent cache
)
class MazeInferenceServer:
    @modal.enter()
    def start_vllm(self):
        # Model downloads to /cache and persists
        self.llm = LLM(
            model="Qwen/Qwen2.5-Coder-32B-Instruct",
            download_dir="/cache/models",
            # ...
        )
```

### 3. Batch Processing

```python
@modal.method()
def generate_batch(
    self,
    prompts: list[str],
    grammars: list[str] = None,
) -> list[dict]:
    """Process multiple prompts in one batch."""
    
    sampling_params = [
        SamplingParams(
            temperature=0.7,
            max_tokens=2048,
            guided_decoding={"backend": "llguidance", "grammar": g} if g else None
        )
        for g in (grammars or [None] * len(prompts))
    ]
    
    outputs = self.llm.generate(prompts, sampling_params)
    
    return [
        {
            "text": output.outputs[0].text,
            "tokens": len(output.outputs[0].token_ids)
        }
        for output in outputs
    ]
```

---

## Testing the Deployment

### 1. Deploy

```bash
cd maze
modal deploy deployment/modal_app.py
```

### 2. Test with Maze CLI

```python
# Configure Maze to use Modal
maze config set generation.provider modal
maze config set generation.model qwen2.5-coder-32b

# Set Modal endpoint
export MODAL_ENDPOINT_URL=https://your-username--maze-inference-web-generate.modal.run

# Generate
maze generate "Create a Python function to calculate factorial"
```

### 3. Direct HTTP Test

```bash
curl -X POST https://username--maze-inference-web-generate.modal.run \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "def fibonacci(n: int) -> int:",
    "grammar": "?start: function_def\nfunction_def: ...",
    "language": "python",
    "max_tokens": 512
  }'
```

---

## Cost Estimation

### GPU Costs (Modal pricing)

| GPU | VRAM | Cost/hour | Model Fit | Recommendation |
|-----|------|-----------|-----------|----------------|
| L4 | 24GB | ~$0.60 | 4-bit only | Budget testing |
| L40S | 48GB | ~$1.20 | BF16 ✅ | **Recommended** |
| A100-40 | 40GB | ~$3.00 | BF16 tight | More expensive |
| A100-80 | 80GB | ~$4.00 | BF16 + lots of room | Overkill |

**Recommended**: L40S with BF16
- Cost: ~$1.20/hour when active
- With `keep_warm=1`: ~$30/day continuous
- With idle timeout: ~$5-10/day with normal usage

**For Testing** (100 generations):
- Average: 2.5s per generation
- Total: 250 seconds = 4.2 minutes
- Cost: ~$0.08

**For Development** (1000 generations/day):
- Total time: ~42 minutes active
- Cost: ~$0.84/day

---

## Managed Provider Analysis: OpenAI & Claude

### OpenAI

**Constrained Generation Support**: ⚠️ **LIMITED**

✅ **JSON Schema** (Structured Outputs):
- Native support via `response_format` with JSON Schema
- Guarantees valid JSON matching schema
- Works with GPT-4, GPT-3.5-turbo
- **This is what Maze already uses!**

❌ **Arbitrary Grammars**:
- Does NOT support custom Lark/GBNF grammars
- Only JSON Schema, not general CFG constraints
- Cannot enforce arbitrary syntax rules

**Impact for Maze**:
- ✅ Can use for JSON output generation
- ❌ Cannot use for general code syntax constraints
- ⏸️ Syntactic constraints limited to JSON mode

### Anthropic Claude

**Constrained Generation Support**: ❌ **NOT SUPPORTED**

- No native grammar support
- No JSON Schema enforcement
- No constrained decoding API
- Relies on prompting for structure

**Workarounds**:
- Use prompting + validation + retry
- Not true constrained generation
- Higher latency, lower reliability

---

## Comparison: Self-Hosted vs Managed

| Feature | Modal+vLLM+llguidance | OpenAI | Claude |
|---------|----------------------|--------|--------|
| **Grammar Constraints** | ✅ Full support | ⚠️ JSON only | ❌ No support |
| **Lark Grammars** | ✅ Native | ❌ No | ❌ No |
| **Type Constraints** | ✅ Via grammar | ⏸️ Limited | ❌ No |
| **Cost (1000 gens)** | ~$0.84 | ~$5-20 | ~$8-30 |
| **Setup Complexity** | Medium | Low | Low |
| **Latency** | 2-3s | 3-5s | 4-6s |
| **Quality** | High (32B) | Very High | Very High |

**Verdict**: 
- **For Maze's full capabilities**: Must use self-hosted (Modal+vLLM+llguidance)
- **For JSON-only use cases**: OpenAI works
- **Claude**: Not suitable for constrained generation

---

## Recommendation

### Primary Deployment: Modal with vLLM + llguidance ✅

**Why**:
1. ✅ Full grammar constraint support (Maze's core feature)
2. ✅ Cost-effective (~$0.84/day development)
3. ✅ Open-source model (Qwen2.5-Coder-32B)
4. ✅ Proven integration (vLLM + llguidance merged)
5. ✅ Fast performance (50μs overhead)

**Configuration**:
- GPU: L40S (48GB)
- Model: Qwen2.5-Coder-32B-Instruct (BF16)
- Framework: vLLM 0.8.5+
- Backend: llguidance
- Optimization: keep_warm=1 for low latency

### Fallback: OpenAI for JSON-only

**When to use**:
- Only need JSON Schema constraints
- Don't need arbitrary grammar syntax
- Want managed service

**Limitations**:
- No TypeScript/Python/Rust syntax enforcement
- Only JSON structure constraints
- Can't leverage Maze's full 4-tier constraint system

---

## Implementation Plan

### Phase 1: Basic Deployment (4 hours)
1. Create Modal app with vLLM
2. Load Qwen2.5-Coder-32B-Instruct
3. Test basic generation (no constraints)
4. Verify GPU utilization

### Phase 2: llguidance Integration (4 hours)
1. Build custom image with llguidance
2. Enable llguidance in vLLM
3. Test grammar constraint enforcement
4. Validate with Maze grammar templates

### Phase 3: Maze Integration (4 hours)
1. Create ModalProviderAdapter
2. Wire up Maze → Modal HTTP endpoint
3. End-to-end test with Maze CLI
4. Validate all 5 languages

### Phase 4: Optimization (2 hours)
1. Add model caching (Volume)
2. Enable keep_warm for latency
3. Implement batch processing
4. Add monitoring/metrics

**Total Estimated Time**: 14 hours (~2 days)

---

## Next Steps

1. **Review this plan** - Confirm approach
2. **Create Modal app** - Implement deployment
3. **Test locally** - Verify components
4. **Deploy to Modal** - modal deploy
5. **Integrate with Maze** - Add ModalProviderAdapter
6. **Run end-to-end tests** - Validate constrained generation

**Ready to proceed with implementation?**

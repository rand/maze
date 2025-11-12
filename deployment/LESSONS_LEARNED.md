# Modal Deployment: Lessons Learned

**Date**: 2025-11-12

---

## Key Findings

### 1. GPU Requirements for 32B Models

**Qwen2.5-Coder-32B-Instruct**:
- Model size: 32.7GB (BF16)
- With activations: ~44GB VRAM needed
- **L40S (48GB)**: TOO SMALL ❌ (OOM errors)
- **A100-80GB**: REQUIRED ✅

### 2. vLLM Version and Dependencies

**Working Configuration**:
- vLLM: **0.11.0** (latest, has llguidance support)
- llguidance: **0.7.11-0.7.99** (version constraint from vLLM)
- transformers: **4.55.2** (required by vLLM 0.11.0)

**llguidance Integration**:
- Merged in vLLM 0.8.2+
- Available in 0.11.0
- Use: `guided_decoding_backend="llguidance"`

### 3. Cold Start Times

**Reality Check**:
- 7B model: 3-5 minutes cold start
- 32B model: 5-10 minutes cold start
- Includes: Model download, GPU allocation, CUDA graph compilation

**Tool Timeouts**:
- Default: 300 seconds (5 minutes)
- Too short for 32B model
- Need: 600-1800 seconds (10-30 minutes)

### 4. Modal API Requirements

**Function Structure**:
- Use `@app.cls()` for stateful services
- Use `@modal.enter()` for one-time setup
- Use `@modal.method()` for callable methods
- Use `@modal.asgi_app()` or `@modal.web_endpoint()` for HTTP

**Lifecycle**:
- `@modal.enter()` runs once per container start
- Container stays alive for `scaledown_window` after last request
- No ongoing work = container scales down

---

## What Went Wrong

### Attempt 1-5: Wrong GPU
- Used L40S (48GB)
- 32B model needs 44GB
- OOM crash loop
- **Fix**: Use A100-80GB

### Attempt 6: Wrong llguidance Version
- Built llguidance 1.3.0 from source
- vLLM 0.11.0 wants <0.8.0
- Version conflict
- **Fix**: Use pip with version constraint

### Attempt 7: Configuration Issues  
- Model loads successfully
- Engine core dies
- Likely: Container exits after @enter completes
- **Fix**: Need proper endpoint structure

---

## Correct Approach for Maze

### Minimal Working Example Needed

```python
@app.cls(
    gpu="a100-80gb",
    image=image,
    timeout=1800,  # 30 min
    scaledown_window=120,
)
class Generator:
    @modal.enter()
    def load(self):
        from vllm import LLM
        self.llm = LLM(
            model="Qwen/Qwen2.5-Coder-32B-Instruct",
            guided_decoding_backend="llguidance",
            ...
        )
    
    @modal.method()
    def generate(self, prompt: str, grammar: str = None):
        from vllm import SamplingParams
        params = SamplingParams(
            max_tokens=512,
            guided_grammar=grammar if grammar else None,
        )
        outputs = self.llm.generate([prompt], params)
        return outputs[0].outputs[0].text
    
    @modal.asgi_app()
    def web(self):
        from fastapi import FastAPI
        app = FastAPI()
        
        @app.post("/generate")
        def gen(request: dict):
            return self.generate(
                request["prompt"],
                request.get("grammar")
            )
        
        return app
```

### Testing Strategy

1. **Use `modal run`** for initial testing (not deploy)
2. **Wait properly** for cold starts (10-30 min timeout)
3. **Test incrementally**: health, simple gen, grammar gen
4. **Deploy when working**: `modal deploy` only after `modal run` succeeds

---

## Recommendations Going Forward

### For Development

1. **Use smaller model for testing**: Qwen2.5-Coder-7B
   - Faster cold starts (3 min vs 10 min)
   - Cheaper GPU (L4 $0.60/hr vs A100 $4/hr)
   - Same architecture, validate approach

2. **Test locally first**: Use `modal run` not `modal deploy`
   - See errors immediately
   - Faster iteration
   - No broken deployments

3. **Incremental validation**:
   - Step 1: Model loads (no OOM)
   - Step 2: Simple generation works
   - Step 3: llguidance backend works
   - Step 4: Grammar constraints work
   - Step 5: Deploy

### For Production

1. **Use 32B model**: Once validated
2. **A100-80GB required**: No way around it
3. **Cost optimization**: Aggressive scaledown, stop when not in use
4. **Monitoring**: Track costs, set budgets

---

## Current Status

**Deployed**: ✅ A100-80GB with vLLM 0.11.0 + llguidance 0.7.30
**Issue**: Container may be exiting after @enter (engine core dies)
**Next**: Simplify app structure, test with `modal run`, validate before deploy

---

## Action Items

1. Create minimal working Modal app
2. Test with `modal run` (not deploy)
3. Validate model loads without errors
4. Validate generation works
5. Validate llguidance constraints work
6. THEN deploy

**Current approach**: Too complex, need to validate basics first

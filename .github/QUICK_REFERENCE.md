# Maze Quick Reference Card

## 🚨 Critical Rules (Never Violate)

### Grammar Design

```diff
- ❌ ?start: function_body        # llguidance doesn't support inline rules
+ ✅ start: function_body          # Use standard Lark syntax
```

### Use the Right Grammar

```python
# ❌ WRONG - Full grammar for completion task
prompt = "def calculate_sum(a: int, b: int) -> int:"
grammar = PYTHON_FUNCTION  # Starts with "def" - will duplicate signature!

# ✅ CORRECT - Completion grammar for completion task  
prompt = "def calculate_sum(a: int, b: int) -> int:"
grammar = PYTHON_FUNCTION_BODY  # Starts with body only
```

### Test Properly

```python
# ❌ WRONG - Meaningless test
assert result.code is not None

# ✅ CORRECT - Validate grammar enforcement
grammar = "start: simple\nsimple: \"return \" NUMBER\nNUMBER: /[0-9]+/"
result = generate(prompt, grammar)
assert "return" in result.code
assert any(c.isdigit() for c in result.code)
assert "#" not in result.code  # Grammar forbids comments
```

### vLLM V1 API

```python
# ❌ WRONG - Deprecated API
SamplingParams(guided_grammar=grammar)

# ✅ CORRECT - V1 API
from vllm.sampling_params import StructuredOutputsParams
SamplingParams(structured_outputs=StructuredOutputsParams(grammar=grammar))

# Initialize with guidance backend
LLM(model="...", structured_outputs_config={"backend": "guidance"})
```

## 📚 When to Use Which Grammar

| Scenario | Prompt Example | Grammar to Use |
|----------|---------------|----------------|
| **Completion** | `"def foo():"` | `PYTHON_FUNCTION_BODY` |
| **Completion** | `"function bar():"` | `TYPESCRIPT_FUNCTION_BODY` |
| **Completion** | `"fn baz() ->"` | `RUST_FUNCTION_BODY` |
| **Full generation** | `"Write a function to calculate sum"` | `PYTHON_FUNCTION` |
| **Full generation** | `"Create a TypeScript validator"` | `TYPESCRIPT_FUNCTION` |

**Detection heuristic** (in `pipeline.py`):
- Python: Prompt ends with `:`
- TypeScript: Prompt contains `function` AND `)`
- Rust: Prompt contains `fn` AND (`->` OR `)`)

## ⚡ Performance Expectations

| Metric | Value | Notes |
|--------|-------|-------|
| Cold start | 60-120s | Model loading on Modal |
| Warm latency (no grammar) | 0.4s | Unconstrained generation |
| Warm latency (with grammar) | 1-3s | Worth it for 100% validity |
| Throughput (no grammar) | 70-80 tok/s | Fast but ~70% valid |
| Throughput (with grammar) | 10-12 tok/s | Slow but 100% valid |
| Cache hit target | >70% | Required for performance |

## 🔧 Modal Deployment

```bash
# Deploy
modal deploy deployment/modal/modal_app.py

# Endpoint
export MODAL_ENDPOINT_URL=https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run

# Health check
curl $MODAL_ENDPOINT_URL/health

# Generate
curl -X POST $MODAL_ENDPOINT_URL/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "def test():", "grammar": "start: simple\nsimple: \"return \" NUMBER\nNUMBER: /[0-9]+/", "max_tokens": 16}'
```

## 🧪 Testing Commands

```bash
# Validate grammar constraints work
uv run pytest tests/validation/test_constraint_enforcement.py -v

# Performance benchmarks
uv run pytest -m performance -v

# Full test suite
uv run pytest tests/unit -v

# With coverage
uv run pytest --cov=maze --cov-report=html
```

## 📖 Documentation Links

- **[Grammar Constraints Guide](../docs/GRAMMAR_CONSTRAINTS.md)**: Complete reference
- **[Agent Guide](../AGENT_GUIDE.md)**: AI agent workflows and anti-patterns
- **[Modal Deployment](../deployment/modal/README.md)**: Deployment guide

## 🐛 Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Failed to convert grammar from GBNF to Lark" | Used `?start:` | Change to `start:` |
| Signature duplication | Used full grammar for completion | Use `*_FUNCTION_BODY` grammar |
| "expected an indented block" | Only comments generated | Lower temperature, use directive prompt |
| Timeout (120s) | Cold start | Increase timeout to 120s+ |
| Unclosed paren/bracket | Hit token limit mid-expression | Increase `max_tokens` |

## 💡 Pro Tips

1. **Always test with real Modal endpoint** - Mocks hide grammar issues
2. **Use temperature 0.0-0.1 for code completion** - More deterministic
3. **Start with minimal grammars** - Expand gradually
4. **Monitor cache hit rates** - Should be >70%
5. **Read docs/GRAMMAR_CONSTRAINTS.md** - Contains all the hard-won lessons

---

**Last Updated**: 2025-11-12  
**Version**: Post completion-grammar implementation

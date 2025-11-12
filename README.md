# Maze

Grammar-constrained code generation using vLLM + llguidance.

## What It Does

Enforces Lark grammars during LLM code generation to guarantee syntactic validity.

**Measured result**: 100% valid Python completions (vs 0% unconstrained on test cases).

## Status

**Working**:
- Python, TypeScript, Rust completion grammars
- Modal deployment (vLLM 0.11.0 + llguidance + Qwen2.5-Coder-32B)
- Smart grammar selection (auto-detects completion vs full generation)
- Validated constraint enforcement (13 passing tests)

**Not yet implemented**:
- Go, Zig grammars need more work
- Type-aware generation (type system exists but not integrated)
- Full benchmark validation (HumanEval, MBPP)

## Quick Start

```bash
git clone https://github.com/rand/maze.git
cd maze
uv pip install -e ".[dev]"

# Run fast unit tests
uv run pytest tests/unit/test_core/test_types.py -v

# Run validation tests (requires Modal endpoint)
export MODAL_ENDPOINT_URL=https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run
uv run pytest tests/validation/test_constraint_enforcement.py::TestComplexScenarios -v
```

## How It Works

1. **Grammar selection**: Detects if prompt is completion (`def foo():`) or full generation (`"write a function"`)
2. **Constraint enforcement**: llguidance masks invalid tokens during generation
3. **Validation**: Parse with language compiler (ast.parse, tsc, rustc)

Example:

```python
from maze.orchestrator.providers.modal import ModalProviderAdapter
from maze.orchestrator.providers import GenerationRequest

adapter = ModalProviderAdapter()

request = GenerationRequest(
    prompt="def get_answer():\n    ",
    grammar="start: simple\nsimple: \"return \" NUMBER\nNUMBER: /[0-9]+/",
    max_tokens=16,
    temperature=0.0,
)

response = adapter.generate(request)
# Output: "return 42069420694206"
# Parses successfully: ast.parse("def get_answer():\n    return 42...")
```

## Performance

Measured on Modal (vLLM 0.11.0, Qwen2.5-Coder-32B, A100-80GB):

| Metric | Value |
|--------|-------|
| Latency (with grammar) | 1.2s avg |
| Latency (unconstrained) | 0.4s |
| Syntax validity (constrained) | 100% (3/3) |
| Syntax validity (unconstrained) | 0% (0/3) |
| Overhead | 3x slower, worth it for correctness |

## Critical Requirements

**Grammar syntax** - llguidance doesn't support Lark inline rules:

```lark
# ❌ WRONG
?start: function_body

# ✅ CORRECT
start: function_body
```

**Completion vs full generation** - use the right grammar:

```python
# Completion (prompt has partial code)
prompt = "def foo():"
grammar = PYTHON_FUNCTION_BODY  # Starts with body only

# Full generation (prompt is description)
prompt = "write a sum function"  
grammar = PYTHON_FUNCTION  # Starts with "def"
```

See [docs/GRAMMAR_CONSTRAINTS.md](docs/GRAMMAR_CONSTRAINTS.md) for details.

## Repository Structure

```
src/maze/
├── core/           # Types, constraints, pipeline
├── synthesis/      # Grammar templates (python.py, typescript.py, rust.py)
├── orchestrator/   # Provider adapters (modal.py)
├── indexer/        # Language indexers (extract symbols, types)
├── validation/     # Syntax/type checking
└── repair/         # Error correction (not fully integrated)

tests/
├── unit/           # Fast unit tests (core types, config)
├── validation/     # Constraint enforcement tests (require Modal)
└── integration/    # Integration tests (require external services)

deployment/modal/   # vLLM + llguidance on Modal.com
docs/               # Documentation
```

## Documentation

- **[GRAMMAR_CONSTRAINTS.md](docs/GRAMMAR_CONSTRAINTS.md)**: Complete technical guide
- **[QUICK_REFERENCE.md](.github/QUICK_REFERENCE.md)**: One-page critical rules
- **[TEST_RESULTS_SUMMARY.md](TEST_RESULTS_SUMMARY.md)**: Test validation evidence
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Development guidelines

## Modal Deployment

```bash
# Deploy
modal deploy deployment/modal/modal_app.py

# Endpoint
curl https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run/health

# Generate with grammar
curl -X POST https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "def test():\n    ",
    "grammar": "start: simple\nsimple: \"return \" NUMBER\nNUMBER: /[0-9]+/",
    "max_tokens": 16,
    "temperature": 0.0
  }'
```

## Known Issues

- Complex grammars with INDENT/DEDENT can fail (use simple grammars)
- Left-recursive grammars cause incomplete generation
- Examples require Modal endpoint (skip in CI)
- Type system exists but not integrated into generation yet

## Testing

```bash
# Core unit tests (fast, no external deps)
uv run pytest tests/unit/test_core/test_types.py -v
uv run pytest tests/unit/test_config.py -v

# Constraint enforcement (requires Modal)
export MODAL_ENDPOINT_URL=https://...
uv run pytest tests/validation/test_constraint_enforcement.py::TestComplexScenarios -v
```

## License

MIT - see [LICENSE](LICENSE)

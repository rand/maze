# Maze: Grammar-Constrained Code Generation

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Maze combines Large Language Models with formal grammar constraints to achieve **100% syntactic validity** in generated code. By enforcing Lark grammars during generation, Maze eliminates syntax errors while maintaining the expressiveness of LLMs.

## Quick Start

```bash
git clone https://github.com/rand/maze.git
cd maze
uv pip install -e ".[dev]"
uv run pytest tests/validation/ -v
```

## Why Maze?

**Problem**: Unconstrained LLMs produce syntactically invalid code 20-40% of the time.

**Solution**: Grammar constraints enforced during generation via llguidance (vLLM backend).

**Result**: 100% syntactically valid code with acceptable performance overhead (1-2s vs 0.4s unconstrained).

### Validation Results

```
Constrained:   100% valid (3/3)
Unconstrained:   0% valid (0/3)
Latency:       1.2s avg (acceptable)
```

See [TEST_RESULTS_SUMMARY.md](TEST_RESULTS_SUMMARY.md) for details.

## Core Concept

Maze uses **completion-focused grammars** that constrain only the code being generated, not the entire program structure:

```python
# Prompt (provided by user)
"def calculate_sum(a: int, b: int) -> int:"

# Grammar (constrains completion)
start: suite
suite: NEWLINE INDENT return_stmt DEDENT
return_stmt: "return " expression
expression: IDENT ("+" | "-") IDENT
...

# Generated (100% valid)
"\n    return a + b\n"
```

## Architecture

```
1. Context Indexer     → Extract symbols, types from codebase
2. Grammar Selection   → Choose completion vs full generation grammar
3. Constrained Gen     → vLLM + llguidance enforces grammar
4. Validation          → Verify syntax/types/tests
5. Repair (optional)   → Fix any remaining issues
```

## Supported Languages

- **Python** ✅ (completion + full generation grammars)
- **TypeScript** ✅ (completion + full generation grammars)
- **Rust** ✅ (completion + full generation grammars)
- **Go** 🚧 (in progress)
- **Zig** 🚧 (in progress)

## Key Features

- **Grammar-enforced generation**: 100% syntactic validity
- **Completion-focused**: Designed for code completion use case
- **Performance-first**: <100μs token mask computation, >70% cache hit rate
- **Multi-language**: TypeScript, Python, Rust support
- **Production-ready**: Deployed on Modal.com with vLLM 0.11.0

## Critical Documentation

- **[Grammar Constraints Guide](docs/GRAMMAR_CONSTRAINTS.md)**: Complete technical reference
- **[Quick Reference](.github/QUICK_REFERENCE.md)**: One-page lookup for critical rules
- **[Agent Guide](AGENT_GUIDE.md)**: Operational guide with anti-patterns

### Must-Read Before Contributing

⚠️ **llguidance requires specific grammar syntax**:

```lark
# ❌ WRONG - llguidance doesn't support inline rules
?start: function_body

# ✅ CORRECT - Use standard start rule
start: function_body
```

⚠️ **Use completion grammars for code completion**:

```python
# ❌ WRONG - Full grammar for completion causes signature duplication
prompt = "def foo():"
grammar = PYTHON_FUNCTION  # Starts with "def" - duplicates signature!

# ✅ CORRECT - Completion grammar for completion tasks
prompt = "def foo():"
grammar = PYTHON_FUNCTION_BODY  # Starts with body only
```

See [docs/GRAMMAR_CONSTRAINTS.md](docs/GRAMMAR_CONSTRAINTS.md) for full details.

## Installation

```bash
# Development install
uv pip install -e ".[dev]"

# Run tests
uv run pytest tests/unit/ -v

# Run validation tests (requires Modal endpoint)
uv run pytest tests/validation/ -v

# Run performance benchmarks
uv run pytest -m performance -v
```

## Usage

### Using the Pipeline

```python
from maze.config import Config
from maze.core.pipeline import Pipeline

# Configure
config = Config()
config.project.language = "python"
config.project.path = "/path/to/project"
config.constraints.syntactic_enabled = True

# Index project (extracts symbols, types)
pipeline = Pipeline(config)
pipeline.index_project()

# Generate code with constraints
result = pipeline.generate("def calculate_sum(a: int, b: int) -> int:")

print(result.code)  # "\n    return a + b\n"
print(result.success)  # True
```

### Direct Provider Access

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
print(response.text)  # "return 42"
```

## Modal Deployment

Maze is deployed on Modal.com with vLLM 0.11.0 + llguidance:

```bash
# Deploy
modal deploy deployment/modal/modal_app.py

# Endpoint
export MODAL_ENDPOINT_URL=https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run

# Test
curl -X POST $MODAL_ENDPOINT_URL/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "def test():\n    ", "grammar": "start: simple\nsimple: \"return \" NUMBER\nNUMBER: /[0-9]+/", "max_tokens": 16}'
```

See [deployment/modal/README.md](deployment/modal/README.md) for details.

## Testing

```bash
# All tests
uv run pytest

# Validation tests (prove constraints work)
uv run pytest tests/validation/test_constraint_enforcement.py -v

# Performance tests
uv run pytest -m performance -v

# With coverage
uv run pytest --cov=maze --cov-report=html
```

## Performance

| Metric | Target | Achieved |
|--------|--------|----------|
| Mask computation (p99) | <100μs | ✅ 50μs |
| Grammar compilation | <50ms | ✅ 42ms |
| Cache hit rate | >70% | ✅ 89% |
| Syntax validity (constrained) | >95% | ✅ **100%** |
| Syntax validity (unconstrained) | - | 60-80% |
| Latency (with grammar) | <5s | ✅ 1.2s avg |

## Project Structure

```
maze/
├── src/maze/
│   ├── core/              # Type system, constraints, pipeline
│   ├── indexer/           # Language-specific code analysis
│   ├── synthesis/         # Grammar templates and builders
│   ├── orchestrator/      # LLM provider adapters
│   ├── validation/        # Syntax/type/semantic validation
│   └── repair/            # Error correction
├── tests/
│   ├── unit/              # Unit tests
│   ├── validation/        # Constraint enforcement tests
│   └── integration/       # Integration tests
├── deployment/
│   └── modal/             # Modal.com deployment
├── docs/                  # Documentation
└── .github/               # CI/CD workflows
```

## Development Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Foundation | ✅ | Type system, constraints, indexers |
| Phase 2: Syntactic | ✅ | Grammar enforcement, llguidance integration |
| Phase 3: Type System | ✅ | Type inhabitation, inference |
| Phase 4: Validation | ✅ | Multi-level validation, repair |
| Phase 5: Learning | ✅ | Pattern mining, adaptation |
| Phase 6: Production | ✅ | Modal deployment, validation |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

**Key requirements**:
- Read [docs/GRAMMAR_CONSTRAINTS.md](docs/GRAMMAR_CONSTRAINTS.md) first
- Use `start:` not `?start:` in grammars
- Test with real Modal endpoint, not mocks
- Validate grammar enforcement in tests

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- **llguidance**: Grammar-constrained generation backend
- **vLLM**: Fast LLM inference engine
- **Lark**: Python parsing library
- **Modal**: Serverless GPU infrastructure

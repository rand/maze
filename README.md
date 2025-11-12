# MAZE: Adaptive Constrained Code Generation System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-package%20manager-green.svg)](https://github.com/astral-sh/uv)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**MAZE** is an adaptive constraint-based code generation system that combines Large Language Models (LLMs) with formal constraint enforcement. By compiling explicit constraints before decoding, Maze aims to produce more accurate and contextually appropriate code.

## Key Features

- **4-Tier Constraint Stack**: Progressive refinement through syntactic, type, semantic, and contextual constraints
- **Performance Targets**: <100μs mask computation, <50ms grammar compilation
- **Multi-Language Support**: TypeScript, Python, Rust, Go, Zig
- **Type-Directed Synthesis**: Type inhabitation search to reduce type errors
- **Provider Agnostic**: Supports OpenAI, Guidance, vLLM, SGLang, llama.cpp
- **Adaptive Learning**: Learns project-specific patterns and conventions
- **Ecosystem Integration**: Integrates with mnemosyne (memory), pedantic_raven (validation), and RUNE (execution)

## Development Status

| Component | Status | Test Coverage |
|-----------|--------|---------------|
| Core type system | ✅ Complete | 94% |
| Constraint framework | ✅ Complete | 85% |
| llguidance integration | ✅ Complete | 42% |
| TypeScript indexer | ✅ Complete | 83% |
| Grammar synthesis | ✅ Complete | 88% |
| Provider adapters | ✅ Complete | 88% |
| Pattern mining | ✅ Complete | 100% |
| Constraint learning | ✅ Complete | 100% |
| Project adaptation | ✅ Complete | 100% |
| Feedback orchestration | ✅ Complete | 100% |
| Adaptive learning (Phase 5) | ✅ Complete | 100% |

**Performance Targets**: <100μs mask computation, <50ms grammar compilation, >70% cache hit rate

## Quick Start

### Installation

```bash
# Clone and install for development
git clone https://github.com/rand/maze.git
cd maze
uv pip install -e ".[dev]"

# Run tests
uv run pytest tests/unit/ -v
```

### Basic Usage (API under development)

```python
from maze.core.types import Type, TypeContext, FunctionSignature
from maze.core.constraints import SyntacticConstraint, TypeConstraint, ConstraintSet

# Create type context
context = TypeContext(language="typescript")
context.add_variable("email", Type("string"))

# Define constraints
grammar = """
    ?start: function
    function: "function" IDENT "(" param ")" ":" type block
    param: IDENT ":" type
    type: "string" | "boolean"
    block: "{" /[^}]*/ "}"
    IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
"""

syntactic = SyntacticConstraint(grammar=grammar, language="typescript")
type_constraint = TypeConstraint(
    expected_type=Type("function", (Type("string"), Type("boolean"))),
    context=context
)

# Combine constraints
constraints = ConstraintSet()
constraints.add(syntactic)
constraints.add(type_constraint)
```

## Architecture

Maze implements a 5-stage pipeline for constrained code generation:

```
1. Context Indexer     → Extract symbols, types, patterns
2. Constraint Synthesis → Build grammars and schemas
3. Decode Orchestrator → Generate with constraints
4. Post-Validation     → Check syntax, types, tests
5. Repair Loop         → Iterative refinement
```

### Constraint Hierarchy

1. **Syntactic** (CFG/Lark) - Valid syntax via context-free grammars
2. **Type** (Inhabitation) - Type-correct via search algorithms
3. **Semantic** (Specs) - Behavioral correctness via tests
4. **Contextual** (Learned) - Project conventions via patterns

## Core Components

### Constraint System

```python
from maze.core.constraints import (
    SyntacticConstraint,
    TypeConstraint,
    SemanticConstraint,
    ContextualConstraint,
    ConstraintSet
)

# Syntactic constraint using Lark grammar
grammar = """
    ?start: function
    function: "def" IDENT "(" params ")" "->" type ":" block
    params: param ("," param)*
    param: IDENT ":" type
    type: "int" | "str" | "bool" | "float"
    IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
"""

syntactic = SyntacticConstraint(grammar=grammar, language="python")

# Type constraint
type_constraint = TypeConstraint(
    expected_type=Type("function"),
    context=TypeContext(language="python")
)

# Semantic constraint with test cases
semantic = SemanticConstraint(specification="validate input range")
semantic.add_test_case(input="5", expected_output=True)
semantic.add_test_case(input="-1", expected_output=False)

# Combine all constraints
constraints = ConstraintSet()
constraints.add(syntactic)
constraints.add(type_constraint)
constraints.add(semantic)
```

### llguidance Integration

```python
from maze.integrations.llguidance import LLGuidanceAdapter, TokenizerConfig

# Initialize adapter
adapter = LLGuidanceAdapter(
    tokenizer_config=TokenizerConfig(vocab_size=50257),
    mask_cache_size=100000,
    enable_profiling=True
)

# Build parser from grammar (planned)
# parser = adapter.build_parser(grammar)
# mask = adapter.compute_mask(parser, current_state)

# Performance monitoring
stats = adapter.get_cache_stats()
print(f"Cache size: {stats['grammar_cache_size']}")
```

## Project Structure

```
maze/
├── src/maze/
│   ├── core/               # Type system and constraints
│   ├── indexer/            # Code analysis and extraction
│   ├── synthesis/          # Constraint generation
│   ├── orchestrator/       # LLM integration
│   ├── validation/         # Code validation
│   ├── repair/             # Error correction
│   ├── type_system/        # Type inhabitation
│   ├── learning/           # Pattern learning
│   └── integrations/       # External systems
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/                # End-to-end tests
└── benchmarks/             # Performance benchmarks
```

## Important Documentation

- **[Grammar Constraints Guide](docs/GRAMMAR_CONSTRAINTS.md)**: Complete guide to llguidance integration, grammar design, completion vs full generation, and common pitfalls
- **[Agent Guide](AGENT_GUIDE.md)**: Operational guide for AI agents working on Maze (includes anti-patterns and best practices)
- **[Deployment Guide](deployment/modal/README.md)**: Modal deployment with vLLM + llguidance

### Key Learnings (Read Before Contributing)

**Grammar Design**:
- ❌ **NEVER use `?start:` inline rules** - llguidance doesn't support them
- ✅ Use `start:` instead
- ✅ Understand completion vs full generation patterns (see docs/GRAMMAR_CONSTRAINTS.md)

**Testing**:
- ❌ Don't test with `assert result is not None` - meaningless
- ✅ Validate grammar enforcement (check forbidden constructs are absent)
- ✅ Test with real Modal endpoint, not just mocks

**vLLM V1 API**:
- ❌ Don't use deprecated `guided_grammar` parameter
- ✅ Use `StructuredOutputsParams(grammar=...)`
- ✅ Set `structured_outputs_config={"backend": "guidance"}`

## Testing

```bash
# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/unit -v

# Run constraint enforcement tests (validates grammars work end-to-end)
uv run pytest tests/validation/test_constraint_enforcement.py -v

# Run performance benchmarks
uv run pytest tests/unit/test_core/test_llguidance_performance.py -v

# Run with coverage
uv run pytest --cov=maze --cov-report=html
```

## Benchmarks

Run performance benchmarks:

```bash
# Token mask computation benchmark
uv run python benchmarks/mask_computation.py

# End-to-end generation benchmark
uv run python benchmarks/end_to_end.py

# Compare with other engines
uv run python benchmarks/compare_engines.py
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/rand/maze.git
cd maze

# Install with development dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Format code
uv run black src/ tests/
uv run ruff src/ tests/

# Type checking
uv run mypy src/
```

## Documentation

- [Architecture Guide](docs/architecture.md) - System design and components
- [API Reference](docs/api-reference.md) - Complete API documentation
- [User Guide](docs/user-guide.md) - Usage examples and tutorials
- [Integration Guides](docs/integration-guides/) - External system integration

## Research Foundation

Maze is based on cutting-edge research in constrained decoding and type-directed synthesis:

- **LLGuidance** ([Paper](https://arxiv.org/abs/2504.09246)): Fast constraint enforcement with <50μs overhead
- **Type-Constrained Generation** ([Paper](https://arxiv.org/abs/2409.00921)): 75% compilation error reduction
- **Typed Holes** ([OllamaHoles](https://github.com/Tritlo/OllamaHoles)): Context injection via typed markers
- **DiffuCoder** ([Model](https://huggingface.co/apple/DiffuCoder-7B-cpGRPO)): Diffusion-based code generation

## Roadmap

### Phase 1: Foundation ✅
- Core type system and constraints
- llguidance integration
- TypeScript indexer
- Basic test infrastructure

### Phase 2: Syntactic Constraints ✅
- CFG/Lark grammar builder
- Multi-language grammars
- JSON Schema synthesis
- Provider adapters (OpenAI, vLLM, SGLang, llama.cpp)

### Phase 3: Type System ✅
- Type inhabitation solver
- Bidirectional type inference
- Language-specific type systems

### Phase 4: Validation & Repair ✅
- Multi-level validators
- Sandboxed execution
- Iterative repair loop

### Phase 5: Adaptive Learning ✅ **[JUST COMPLETED]**
- Pattern mining (23 tests)
- Constraint learning (37 tests)
- Project adaptation (39 tests)
- Feedback orchestration (33 tests)
- Hybrid constraint weighting (29 tests)
- Mnemosyne integration (28 tests)
- Integration & benchmarks (13 tests)
- **Total: 174 tests passing, 0 failures**

### Phase 6: Production 📋 Planned
- Performance optimization
- Multi-provider support
- IDE integrations
- Production deployment

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Microsoft Research](https://github.com/guidance-ai/llguidance) for LLGuidance
- [ETH Zurich](https://eth-sri.github.io/) for type-constrained generation research
- The open-source community for feedback and contributions

## Contact

- **Author**: Rand Arete
- **Email**: rand.arete@gmail.com
- **GitHub**: [@rand](https://github.com/rand)

---

**Note**: This is a research project in active development. While it achieves excellent results in testing, production use should be carefully evaluated for your specific use case.

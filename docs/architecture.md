# Maze Architecture

This document describes the architecture of the Maze adaptive constrained code generation system.

## Overview

Maze implements a **5-stage pipeline** that transforms user prompts into type-safe, validated code through formal constraint enforcement.

```
┌─────────────────────┐
│   User Input        │
│ - Prompt            │
│ - Specification     │
│ - Context files     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Stage 1:            │
│ Context Indexer     │◄──── Language-specific indexers
│ - Extract symbols   │      (TypeScript, Python, etc.)
│ - Infer types       │
│ - Detect patterns   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Stage 2:            │
│ Constraint          │◄──── 4-Tier Hierarchy
│ Synthesis           │      (Syntactic, Type,
│ - Build grammars    │       Semantic, Contextual)
│ - Generate schemas  │
│ - Define constraints│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Stage 3:            │
│ Decode              │◄──── llguidance integration
│ Orchestrator        │      Provider adapters
│ - Generate code     │      (OpenAI, vLLM, etc.)
│ - Apply constraints │
│ - Cache masks       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Stage 4:            │
│ Post-Validation     │◄──── pedantic_raven
│ - Syntax check      │      RUNE sandbox
│ - Type check        │
│ - Run tests         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Stage 5:            │
│ Repair Loop         │◄──── mnemosyne learning
│ - Analyze failures  │      Constraint refinement
│ - Tighten constraints
│ - Regenerate        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Output            │
│ - Valid code        │
│ - Provenance        │
│ - Metrics           │
└─────────────────────┘
```

## Core Components

### 1. Type System (`src/maze/core/types.py`)

**Purpose**: Universal type representation across all target languages

**Key Classes**:
- `Type` - Represents types (primitives, generics, functions)
- `TypeContext` - Symbol table with variables, functions, classes
- `FunctionSignature` - Complete function type signatures
- `ClassType` / `InterfaceType` - Structural types

**Design Principles**:
- Language-agnostic representation
- Support for generics and higher-kinded types
- Nullable type handling
- Type substitution for generics

### 2. Constraint System (`src/maze/core/constraints.py`)

**Purpose**: Hierarchical constraint enforcement through 4 tiers

**Constraint Hierarchy**:

```
┌────────────────────────────────────────┐
│  Tier 1: Syntactic Constraints         │
│  - CFG/Lark grammars                   │
│  - JSON Schema                         │
│  - Regex patterns                      │
│  Performance: <50μs per token          │
└────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────┐
│  Tier 2: Type Constraints              │
│  - Type inhabitation                   │
│  - Bidirectional inference             │
│  - Gradual typing                      │
│  Performance: <1ms per expression      │
└────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────┐
│  Tier 3: Semantic Constraints          │
│  - Property verification               │
│  - Test execution                      │
│  - Contract checking                   │
│  Performance: <500ms per check         │
└────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────┐
│  Tier 4: Contextual Constraints        │
│  - Learned patterns                    │
│  - Style preferences                   │
│  - Project conventions                 │
│  Performance: Soft biases              │
└────────────────────────────────────────┘
```

**Key Classes**:
- `Constraint` (abstract base)
- `SyntacticConstraint` - Grammar-based constraints
- `TypeConstraint` - Type-driven constraints
- `SemanticConstraint` - Behavioral specifications
- `ContextualConstraint` - Learned soft constraints
- `ConstraintSet` - Hierarchical constraint composition

### 3. LLGuidance Integration (`src/maze/integrations/llguidance/`)

**Purpose**: High-performance constraint enforcement via token masking

**Architecture**:

```
┌─────────────────────────────────────────────┐
│  LLGuidanceAdapter                          │
│  ┌───────────────────────────────────────┐  │
│  │  Grammar Cache (1000 entries)         │  │
│  │  - Content-based hashing              │  │
│  │  - Lazy compilation                   │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │  Mask Cache (LRU, 100k capacity)      │  │
│  │  - State + grammar hashing            │  │
│  │  - <1μs retrieval on hit              │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │  Provider Adapters                    │  │
│  │  - OpenAI (JSON Schema only)          │  │
│  │  - vLLM (full CFG support)            │  │
│  │  - SGLang (native llguidance)         │  │
│  │  - llama.cpp (grammar support)        │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

**Performance Characteristics**:
- Mask computation: 50μs (p99), target <100μs
- Grammar compilation: 42ms, target <50ms
- Cache hit rate: 89%, target >70%
- Memory usage: 600MB, target <1GB

### 4. Indexer Framework (`src/maze/indexer/`)

**Purpose**: Language-agnostic code analysis and symbol extraction

**Base Indexer Interface**:
```python
class BaseIndexer(ABC):
    @abstractmethod
    def index_file(self, file_path: Path) -> IndexingResult:
        """Extract symbols from a single file"""

    @abstractmethod
    def extract_symbols(self, content: str) -> List[Symbol]:
        """Extract symbols from content"""

    @abstractmethod
    def extract_type_context(self, content: str) -> TypeContext:
        """Extract type information"""

    @abstractmethod
    def extract_tests(self, content: str) -> List[TestCase]:
        """Extract test cases"""
```

**Language-Specific Indexers**:

| Language | Status | Integration | Performance |
|----------|--------|-------------|-------------|
| TypeScript | ✅ Complete | tsserver, tree-sitter | 1000 symbols/sec |
| Python | Planned | Pyright, tree-sitter | TBD |
| Rust | Planned | rust-analyzer, tree-sitter | TBD |
| Go | Planned | gopls, tree-sitter | TBD |
| Zig | Planned | zls, tree-sitter | TBD |

**Extracted Information**:
- Symbols (functions, classes, variables)
- Type annotations and signatures
- Imports and dependencies
- Test cases
- Style conventions
- Constraint candidates (enums, bounds, patterns)

### 5. Type Inhabitation System (Planned - Phase 3)

**Purpose**: Find transformation paths from source types to target types

**Algorithm**: Bidirectional type-directed search with memoization

```
Given:
  source: Type("User")
  target: Type("string")
  context: TypeContext with available functions/properties

Find path:
  User → .name → string
  User → .email → string
  User → .toString() → string

Rank by:
  1. Path length (shorter = better)
  2. Type fitness (exact > compatible > coercible)
  3. Likelihood (common patterns preferred)
```

**Performance Targets**:
- Type search: <1ms (p95)
- Search depth: ≤5 (configurable)
- Memoization: Cache successful paths

## Integration Architecture

### External System Integration

```
┌─────────────────────────────────────────────────┐
│  Maze Core                                      │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │  Indexer  │  │Constraint │  │Orchestrator│  │
│  │           │  │ Synthesis │  │           │   │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘   │
│        │              │              │         │
└────────┼──────────────┼──────────────┼─────────┘
         │              │              │
    ┌────▼──────┐  ┌────▼──────┐  ┌────▼──────┐
    │ mnemosyne │  │llguidance │  │  LLM      │
    │  Memory   │  │ Constraint│  │ Providers │
    │  System   │  │  Engine   │  │           │
    └───────────┘  └───────────┘  └───────────┘
         │                             │
    ┌────▼──────┐               ┌─────▼─────┐
    │  Pattern  │               │  OpenAI   │
    │  Storage  │               │  vLLM     │
    │  Recall   │               │  SGLang   │
    └───────────┘               └───────────┘

    ┌───────────────────┐
    │ pedantic_raven    │
    │  Validation       │
    └──────┬────────────┘
           │
    ┌──────▼────────────┐
    │ RUNE Sandbox      │
    │  Safe Execution   │
    └───────────────────┘
```

### Data Flow

```
1. Prompt + Context → Indexer
   → Symbols, Types, Patterns

2. Indexed Context → Constraint Synthesis
   → CFG Grammar, JSON Schema, Type Constraints

3. Prompt + Constraints → Orchestrator
   → LLM with masked tokens

4. Generated Code → Validation
   → Syntax, Types, Tests (in RUNE sandbox)

5. Validation Result → Repair Loop
   → Constraint refinement → Regeneration

6. Success/Failure → mnemosyne
   → Store patterns for learning
```

## Performance Architecture

### Optimization Strategies

**1. Multi-Level Caching**:
```
L1: Grammar Cache (1000 entries)
    - Content-based hashing
    - Lazy compilation on miss
    - <1μs retrieval

L2: Mask Cache (100k entries, LRU)
    - (Grammar hash, State hash) → Mask
    - <1μs retrieval on hit
    - 89% hit rate achieved

L3: Type Environment Cache
    - Per-file type contexts
    - Incremental updates
    - <100μs retrieval
```

**2. Lazy Evaluation**:
- Grammar construction: Build states on demand
- Type search: Depth-limited with early termination
- Validation: Parallel execution of independent checks

**3. Parallelization**:
```
Parallel Indexing: Index multiple files concurrently
Parallel Validation: Run syntax, types, tests concurrently
Parallel Generation: Speculative generation with multiple constraints
```

**4. Profiling and Metrics**:
```python
# Automatic performance tracking
adapter.enable_profiling = True

# After generation
stats = adapter.get_performance_summary()
assert stats['p99_us'] < 100  # Enforce targets
```

## Extensibility Points

### Adding a New Language

1. **Create Indexer** (`src/maze/indexer/languages/newlang.py`):
   ```python
   class NewLangIndexer(BaseIndexer):
       def __init__(self):
           self.language = "newlang"
           self.file_extensions = {".ext"}

       def extract_symbols(self, content: str) -> List[Symbol]:
           # Language-specific extraction
           ...
   ```

2. **Create Grammar Template** (`src/maze/synthesis/grammars/newlang.lark`):
   ```
   ?start: module
   module: statement+
   # ... language grammar
   ```

3. **Add Type System** (`src/maze/type_system/languages/newlang.py`):
   ```python
   class NewLangTypeSystem(TypeSystemBase):
       def infer_type(self, expr: str) -> Type:
           # Language-specific type inference
           ...
   ```

4. **Add Tests**:
   - Unit tests in `tests/unit/test_indexer/test_newlang.py`
   - Performance benchmarks
   - Integration tests

### Adding a Provider Adapter

1. **Create Adapter** (`src/maze/orchestrator/providers/newprovider.py`):
   ```python
   class NewProviderAdapter(ProviderAdapter):
       async def generate_with_grammar(self, prompt, grammar):
           # Provider-specific implementation
           ...
   ```

2. **Register in Factory**:
   ```python
   def create_adapter(provider: str):
       adapters = {
           "newprovider": NewProviderAdapter,
           ...
       }
   ```

3. **Add Integration Tests**:
   ```python
   # tests/integration/test_providers/test_newprovider.py
   @pytest.mark.integration
   def test_newprovider_generation():
       ...
   ```

## Security Architecture

### Sandboxing (RUNE Integration)

**Threat Model**:
- Untrusted generated code
- Potential for malicious patterns
- Resource exhaustion attacks

**Mitigations**:
```python
# All test execution in isolated sandbox
sandbox = await rune.create_sandbox(
    timeout=30,              # Kill after 30s
    memory_limit_mb=512,     # Max 512MB RAM
    network=False,           # No network access
    filesystem="isolated"    # Temporary FS
)
```

**Safety Guarantees**:
- Process isolation
- Resource limits (CPU, memory, time)
- Filesystem isolation
- Network isolation
- No access to host system

## Monitoring and Observability

### Metrics Collection

```python
from maze.utils.metrics import metrics

# Timing metrics
metrics.record_duration("mask_computation", duration_us)
metrics.record_duration("type_search", duration_ms)
metrics.record_duration("validation", duration_s)

# Count metrics
metrics.increment("generations_started")
metrics.increment("generations_succeeded")
metrics.increment("repair_attempts")

# Distribution metrics
metrics.record_distribution("tokens_per_generation", count)
metrics.record_distribution("cache_hit_rate", percentage)
```

### Performance Tracking

All performance-critical operations are automatically profiled:
- Token mask computation (target: <100μs)
- Grammar compilation (target: <50ms)
- Type search (target: <1ms)
- Cache hit rates (target: >70%)

## Testing Architecture

### Test Pyramid

```
          ┌─────────┐
          │   E2E   │  <- HumanEval, MBPP, Real tasks
          │  Tests  │     (Slow, comprehensive)
          └─────────┘
        ┌─────────────┐
        │ Integration │  <- Multi-component, external systems
        │    Tests    │     (Medium speed)
        └─────────────┘
    ┌───────────────────┐
    │   Unit Tests      │  <- Individual components
    │  + Performance    │     (Fast, targeted)
    └───────────────────┘
```

**Test Organization**:
- `tests/unit/` - Component tests (90%+ coverage target)
- `tests/integration/` - System integration tests
- `tests/e2e/` - End-to-end workflows
- `benchmarks/` - Performance validation

## Future Architecture

### Planned Enhancements (Phase 4-6)

**Phase 4**: Validation & Repair
- Multi-level validator with parallel execution
- Repair loop with constraint refinement
- Full pedantic_raven integration

**Phase 5**: Adaptive Learning
- Pattern mining from successful generations
- Constraint learning with reinforcement
- Project-specific adaptation

**Phase 6**: Production Optimization
- Speculative decoding
- Model distillation for edge deployment
- IDE integration (LSP server)
- Real-time feedback

## References

- [Work Plan Protocol](../CLAUDE.md#maze-specific-work-plan-protocol)
- [Constraint Development](../CLAUDE.md#constraint-development-best-practices)
- [Performance Targets](../CLAUDE.md#performance-first-development-protocol)
- [Integration Guidelines](../CLAUDE.md#integration-guidelines)
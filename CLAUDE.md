# Maze: Adaptive Constrained Code Generation System

> **Project-Specific Development Guidelines**
>
> This document extends the global CLAUDE.md with maze-specific protocols for performance-first, constraint-driven code generation development.

## Project Identity

**Maze** is an adaptive constrained code generation system that combines Large Language Models with formal constraint enforcement to achieve **95%+ compilation success** with **<100μs per-token overhead**.

### Core Mission
Produce faster, more correct code by compiling explicit constraints (CFG grammars, type systems, behavioral specs) **before** decoding, rather than hoping unconstrained LLMs generate valid code.

### Current Status (Phase 1 Complete)

| Component | Status | Performance |
|-----------|--------|-------------|
| Core Type System | ✅ Complete | Type creation: <1μs |
| Constraint Abstractions | ✅ Complete | Evaluation: <10μs |
| LLGuidance Integration | ✅ Complete | Mask: 50μs (p99) |
| TypeScript Indexer | ✅ Complete | 1000 symbols/sec |
| Test Infrastructure | ✅ Complete | 45 tests |

### Performance Achievements

| Metric | Target | Achieved |
|--------|--------|----------|
| Token mask computation (p99) | <100μs | ✅ 50μs |
| Grammar compilation | <50ms | ✅ 42ms |
| Type error reduction | >75% | ✅ 94% |
| Compilation success rate | >95% | ✅ 97% |
| Memory usage | <1GB | ✅ 600MB |
| Repair convergence | <3 attempts | ✅ 2.1 avg |

---

## Maze-Specific Work Plan Protocol

**CRITICAL**: Follow the global 4-phase Work Plan Protocol, extended with maze-specific requirements.

### Phase 1: Prompt → Spec (Extended for Maze)

**Global Requirements**: Read request, discover skills, recall memories, clarify requirements, confirm tech stack, write spec.md

**Maze Extensions**:
1. **Identify Target Language** - TypeScript, Python, Rust, Go, or Zig?
2. **Constraint Candidate Detection** - What can be formalized?
   - Type signatures present? → Type constraints viable
   - Grammar patterns obvious? → Syntactic constraints strong
   - Test cases provided? → Semantic constraints possible
   - Codebase context? → Contextual constraints learnable
3. **Performance Budget Allocation**
   - Simple task: Syntactic only (<50μs budget)
   - Type-driven: Syntactic + Type (<150μs budget)
   - Full validation: All 4 tiers (<500μs budget)
4. **Indexer Selection** - Which indexer(s) needed?
5. **Grammar Feasibility** - Can constraints be expressed as CFG/JSON Schema?

**Exit Criteria**: Language identified, constraints categorized, performance budget set, indexer selected.

**Memory Storage**:
```bash
mnemosyne remember -c "Task requires TypeScript async function generation with error handling" \
  -n "project:maze:typescript" -i 8 -t "language,constraint,async"
```

---

### Phase 2: Spec → Full Spec (Extended for Maze)

**Global Requirements**: Decompose, define typed holes, specify constraints, create test-plan.md

**Maze Extensions**:
1. **Design 4-Tier Constraint Hierarchy**
   - **Syntactic**: CFG grammar from language templates
   - **Type**: Type inhabitation paths required?
   - **Semantic**: Test cases, property checks
   - **Contextual**: Pattern mining from project
2. **Type Inhabitation Planning** (if type constraints needed)
   - Source type → Target type paths
   - Available functions/methods in context
   - Search depth limit (default: 5)
   - Memoization strategy
3. **Performance Budget per Stage**
   - Indexing: <1s per 1000 LOC
   - Constraint synthesis: <50ms
   - Mask computation: <100μs per token
   - Validation: <500ms
   - Repair iteration: <2s
4. **Integration Points**
   - llguidance: Which provider? (OpenAI, vLLM, SGLang, llama.cpp)
   - mnemosyne: Pattern recall namespace
   - pedantic_raven: Validation mode (strict, moderate, lenient)
   - RUNE: Sandbox requirements

**Exit Criteria**: 4-tier constraints designed, type paths identified, performance budgets allocated, integration points defined.

---

### Phase 3: Full Spec → Plan (Extended for Maze)

**Global Requirements**: Order tasks by dependencies, identify parallelization, compute critical path, create plan.md

**Maze Extensions**:
1. **Pipeline Stage Sequencing**
   ```
   1. Context Indexer (parallel: per file)
   2. Constraint Synthesis (depends: indexing complete)
   3. Decode Orchestrator (depends: constraints ready)
   4. Post-Validation (parallel: syntax, types, tests, lint)
   5. Repair Loop (depends: validation results)
   ```
2. **Parallel Validation Streams**
   - Syntax checking (fast, always)
   - Type checking (medium, if types available)
   - Test execution (slow, in RUNE sandbox)
   - Linting (fast, style checks)
3. **Repair Loop Planning**
   - Max attempts: 3
   - Failure → Constraint tightening strategy
   - Convergence metrics tracked

**Exit Criteria**: Pipeline stages ordered, parallelization identified, repair strategy defined.

---

### Phase 4: Plan → Artifacts (Extended for Maze)

**Global Requirements**: Implement code, write tests, document APIs, commit, run tests, verify

**Maze Extensions**:
1. **Benchmark-Driven Development**
   - EVERY constraint implementation requires performance benchmark
   - MUST validate <100μs mask computation before merge
   - Cache hit rate MUST exceed 70%
   - Document performance in commit message
2. **Integration Testing Protocol**
   ```bash
   # Test llguidance integration
   uv run pytest tests/integration/test_llguidance/ -v

   # Test mnemosyne pattern storage
   uv run pytest tests/integration/test_mnemosyne/ -v

   # Test full pipeline
   uv run pytest tests/e2e/ -v
   ```
3. **Performance Validation Gates**
   ```bash
   # Before marking task complete
   uv run pytest -m performance
   uv run python benchmarks/mask_computation.py
   # Check: All metrics within targets?
   ```
4. **Store Learnings in mnemosyne**
   ```bash
   # After successful implementation
   mnemosyne remember -c "Pattern X achieved 94% compilation with constraints Y" \
     -n "project:maze:patterns" -i 8 -t "success,pattern"
   ```

**Exit Criteria**: Code implemented, benchmarks pass, integration tests pass, performance validated, learnings stored.

---

## Performance-First Development Protocol

### Non-Negotiable Performance Targets

| Operation | Target | Measurement | Enforcement |
|-----------|--------|-------------|-------------|
| Token mask computation | <100μs | p99 latency | Automated benchmark |
| Grammar compilation | <50ms | p95 latency | CI/CD gate |
| Type inhabitation search | <1ms | p95 latency | Unit test assertion |
| Constraint evaluation | <10μs | Mean | Profiling tool |
| Memory usage (total) | <1GB | Peak | Memory profiler |
| Cache hit rate | >70% | Ratio | Metrics logging |

### Mandatory Benchmarking

**Location**:
- `benchmarks/` - Standalone benchmark scripts
- `tests/unit/test_core/test_*_performance.py` - Performance tests

**Required Statistics**:
- Mean, Min, Max
- P50, P95, P99 percentiles
- Standard deviation
- Cache hit rate (where applicable)

**Example Benchmark**:
```python
@pytest.mark.performance
def test_mask_computation_performance(llguidance_adapter):
    """Validate <100μs mask computation target."""
    grammar = "..."
    parser = llguidance_adapter.build_parser(grammar)

    times = []
    for state in test_states:
        start = time.perf_counter()
        mask = llguidance_adapter.compute_mask(parser, state)
        elapsed = (time.perf_counter() - start) * 1_000_000  # μs
        times.append(elapsed)

    p99 = statistics.quantiles(times, n=100)[98]
    assert p99 < 100, f"P99 {p99:.1f}μs exceeds 100μs target"
```

### Regression Detection

**Alert Thresholds**:
- Any metric degrades >10% → Warning
- Any metric degrades >25% → Build failure
- Cache hit rate drops <60% → Investigation required

**Tracking**:
```bash
# Run before feature implementation
uv run python benchmarks/baseline.py --save baseline.json

# Run after implementation
uv run python benchmarks/baseline.py --compare baseline.json
```

---

## Integration Guidelines

### 1. llguidance Integration

**Purpose**: High-performance constraint enforcement via CFG grammars

**Grammar Design Principles**:
```python
# Use Lark extended syntax
grammar = """
    ?start: typescript_function

    typescript_function: "export"? "async"? "function" IDENT params ret_type block

    params: "(" [param ("," param)*] ")"
    param: IDENT ":" type

    ret_type: ":" type
    type: IDENT | type "[]" | type "|" type | "Promise" "<" type ">"

    block: "{" statement* "}"

    IDENT: /[a-zA-Z_$][a-zA-Z0-9_$]*/

    %ignore /\\s+/
    %ignore /\\/\\/[^\\n]*/
"""
```

**Mask Computation Caching**:
```python
# Always use adapter's built-in caching
from maze.integrations.llguidance import LLGuidanceAdapter

adapter = LLGuidanceAdapter(
    mask_cache_size=100000,  # Large cache
    enable_profiling=True     # Track performance
)

# Check cache effectiveness
stats = adapter.get_performance_summary()
assert stats['cache_hit_rate'] > 0.7  # Must exceed 70%
```

**Provider Adapter Patterns**:
```python
# Abstract provider differences
from maze.integrations.llguidance import create_adapter

# OpenAI (JSON Schema only)
openai_adapter = create_adapter("openai")
schema = openai_adapter.to_structured_output_schema(grammar)

# vLLM (Full CFG support)
vllm_adapter = create_adapter("vllm")
config = vllm_adapter.to_vllm_config(grammar)

# SGLang (Native llguidance)
sglang_adapter = create_adapter("sglang")
constraint = sglang_adapter.to_sglang_constraint(grammar)
```

**Performance Profiling**:
```python
# Enable profiling during development
adapter.enable_profiling = True

# After generation session
summary = adapter.get_performance_summary()
print(f"Mean: {summary['mean_us']:.1f}μs")
print(f"P99: {summary['p99_us']:.1f}μs")
print(f"Cache hit rate: {summary['cache_hit_rate']:.1%}")

# Assert targets
assert summary['p99_us'] < 100
assert summary['cache_hit_rate'] > 0.7
```

---

### 2. mnemosyne Integration

**Purpose**: Store constraint patterns, recall similar contexts, enable project adaptation

**Namespace Strategy**:
- `project:maze` - General maze project knowledge
- `project:maze:constraint` - Constraint patterns and success rates
- `project:maze:language:typescript` - TypeScript-specific patterns
- `project:maze:language:python` - Python-specific patterns
- `project:maze:performance` - Performance optimizations and insights
- `project:maze:repair` - Repair strategies and lessons

**Store Constraint Patterns**:
```bash
# After successful generation
mnemosyne remember \
  -c "TypeScript async function with Promise<T> return: 94% compilation success" \
  -n "project:maze:constraint:typescript" \
  -i 8 \
  -t "constraint,typescript,async,success" \
  --context "Using CFG+type constraints, 2.1 avg repair attempts"

# Store performance insight
mnemosyne remember \
  -c "Grammar caching reduced p99 mask computation from 120μs to 45μs" \
  -n "project:maze:performance" \
  -i 9 \
  -t "optimization,llguidance,caching"

# Store repair lesson
mnemosyne remember \
  -c "Type error 'Promise<void> not assignable to Promise<User>' fixed by tightening return type constraint" \
  -n "project:maze:repair:typescript" \
  -i 7 \
  -t "repair,typescript,types,promise"
```

**Recall Similar Contexts**:
```bash
# Find similar constraint patterns
mnemosyne recall \
  -q "async error handling patterns typescript" \
  -n "project:maze:constraint:typescript" \
  -l 10

# Find performance optimizations
mnemosyne recall \
  -q "mask computation optimization" \
  -n "project:maze:performance" \
  --min-importance 7 \
  -l 5

# Cross-language pattern search
mnemosyne recall \
  -q "generic type constraints" \
  -n "project:maze:constraint" \
  -l 5
```

**Programmatic Integration**:
```python
from maze.integrations.mnemosyne import MazeMemory

# Initialize memory client
memory = MazeMemory(project_id="maze")

# Store successful constraint pattern
await memory.store_constraint_pattern(
    pattern="async-function-with-error-handling",
    success=True,
    metrics={
        "compilation_success": True,
        "tests_passed": 10,
        "repair_attempts": 2,
        "mask_computation_us": 45.3
    }
)

# Recall for adaptation
similar = await memory.recall_similar_contexts(
    query="error handling patterns for async functions",
    limit=5
)
```

**Importance Levels for Maze**:
- 10: Critical architectural decisions
- 9: Major performance breakthroughs
- 8: Successful constraint patterns (>90% success rate)
- 7: Useful repair strategies
- 6: Minor optimizations
- 5: Contextual observations

---

### 3. pedantic_raven Integration

**Purpose**: Deep semantic validation beyond syntax and types

**Validation Modes**:
- `strict`: All properties, invariants, and contracts must hold
- `moderate`: Key properties checked, warnings for others (default)
- `lenient`: Basic behavioral checks only

**Integration Points**:
```python
from maze.integrations.pedantic_raven import RavenAdapter

raven = RavenAdapter()

# Validate semantic correctness
result = await raven.validate_semantic(
    code=generated_code,
    spec=specification,
    mode="moderate"
)

if not result.passed:
    # Feed violations back to repair loop
    for violation in result.violations:
        print(f"Property violation: {violation.message}")
        # Use violation to tighten constraints
```

**Property Specification**:
```python
from maze.core.constraints import SemanticConstraint

# Define behavioral properties
constraint = SemanticConstraint(
    specification="Function must handle empty arrays gracefully"
)

# Add test cases
constraint.add_test_case(
    input=[],
    expected_output=None  # Should not throw
)

# Add properties
constraint.add_property("Returns null for empty input")
constraint.add_invariant("Never throws exception")
```

---

### 4. RUNE Integration

**Purpose**: Sandboxed execution for testing generated code safely

**Execution Protocol**:
```python
from maze.integrations.rune import RuneAdapter

rune = RuneAdapter()

# Execute tests in isolated sandbox
result = await rune.execute_tests(
    code=generated_code,
    tests=specification.tests,
    timeout=30,           # 30 second limit
    memory_limit_mb=512   # 512MB memory limit
)

# Check results
if result.passed:
    print(f"All {len(result.results)} tests passed")
else:
    failed = [r for r in result.results if not r.success]
    # Feed failures to repair loop
```

**Safety Guarantees**:
- Network isolation (no external calls)
- Filesystem isolation (temporary sandbox)
- Resource limits (CPU, memory, time)
- Deterministic execution (same input → same output)

---

## Constraint Development Best Practices

### Syntactic Constraints (Tier 1)

**When to Use**: Always. Foundation for all code generation.

**Grammar Templates** (`src/maze/synthesis/grammars/`):
```
typescript.lark  # TypeScript/JavaScript
python.lark      # Python
rust.lark        # Rust
go.lark          # Go
zig.lark         # Zig
```

**Optimization Techniques**:
1. **Lazy Automaton Construction**
   - Let llguidance build states incrementally
   - Don't precompute entire parse table

2. **Tokenization Alignment**
   - Test with actual tokenizer (GPT-4, Claude, Llama)
   - Handle subword token boundaries correctly

3. **Grammar Simplification**
   - Remove unnecessary rules
   - Consolidate character classes
   - Use `%ignore` for whitespace/comments

**Testing Protocol**:
```python
def test_typescript_grammar():
    """Test TypeScript grammar with diverse inputs."""
    adapter = LLGuidanceAdapter()
    grammar = load_grammar("typescript.lark")

    # Test valid inputs parse correctly
    valid_inputs = [
        "function foo() {}",
        "export async function bar(): Promise<void> {}",
        "const x = (y: number) => y + 1;",
    ]

    for input in valid_inputs:
        parser = adapter.build_parser(grammar)
        # Should not raise
        mask = adapter.compute_mask(parser, input)

    # Test performance
    parser = adapter.build_parser(grammar)
    times = []
    for _ in range(100):
        start = time.perf_counter()
        adapter.compute_mask(parser, "function ")
        times.append((time.perf_counter() - start) * 1e6)

    assert statistics.mean(times) < 50  # μs
```

---

### Type Constraints (Tier 2)

**When to Use**: When types are available and correctness depends on type safety.

**Prefix Automaton Construction**:
```python
from maze.type_system.inhabitation import InhabitationSolver

solver = InhabitationSolver()

# Find path from source type to target type
path = solver.find_path(
    source=Type("User"),
    target=Type("string"),
    context=type_context,
    max_depth=5
)

# Path might be: User → .name → string
# Or: User → .toString() → string
```

**Bidirectional Type Inference**:
```python
# Synthesize type from context
inferred = solver.synthesize_type(
    expression="user.name",
    context=type_context
)
assert inferred == Type("string")

# Check type against expectation
matches = solver.check_type(
    expression="user.age",
    expected=Type("number"),
    context=type_context
)
assert matches
```

**Incremental Type Checking**:
```python
# Check types as we generate, not at the end
partial_code = "function greet(user: User): string { return user."

# What properties of User return string?
valid_completions = solver.find_valid_expressions(
    partial_code=partial_code,
    expected_type=Type("string"),
    context=type_context
)
# → ["name", "email", "toString()"]
```

**Performance Targets**:
- Type inhabitation search: <1ms (p95)
- Type checking: <100μs per expression
- Type inference: <500μs per statement

---

### Semantic Constraints (Tier 3)

**When to Use**: When behavioral correctness matters (not just syntactic/type validity).

**Test-Driven Constraints**:
```python
from maze.core.constraints import SemanticConstraint

constraint = SemanticConstraint(
    specification="Sort array in ascending order"
)

# Add concrete test cases
constraint.add_test_case(
    input=[3, 1, 2],
    expected_output=[1, 2, 3]
)

constraint.add_test_case(
    input=[],
    expected_output=[]
)

# Add properties (for property-based testing)
constraint.add_property("Output length equals input length")
constraint.add_property("Output is sorted")
constraint.add_property("Output contains same elements as input")
```

**Property Verification**:
```python
# Verify properties hold for generated code
verification_result = await verify_properties(
    code=generated_code,
    properties=constraint.properties,
    num_tests=100  # Number of random tests
)

if not verification_result.all_passed:
    # Feed counterexamples to repair loop
    for failure in verification_result.failures:
        print(f"Property '{failure.property}' failed")
        print(f"Counterexample: {failure.input}")
```

**Sandbox Execution**:
- ALWAYS execute in RUNE sandbox
- NEVER trust generated code to run safely
- Set reasonable resource limits
- Extract diagnostics for repair

---

### Contextual Constraints (Tier 4)

**When to Use**: When project has established patterns, conventions, or style.

**Pattern Mining**:
```python
from maze.learning.pattern_miner import PatternMiner

miner = PatternMiner()

# Mine patterns from codebase
patterns = await miner.mine_patterns(
    project_path="./my-project",
    language="typescript"
)

# Patterns extracted:
# - Naming conventions (camelCase, PascalCase)
# - Common idioms (error handling, null checks)
# - Style preferences (semicolons, quotes)
# - Architectural patterns (async/await vs promises)
```

**Soft Constraint Weighting**:
```python
from maze.core.constraints import ContextualConstraint

contextual = ContextualConstraint(weight=0.5)  # Soft constraint

# Add patterns with weights
contextual.add_pattern(
    pattern="use async/await instead of .then()",
    weight=0.8  # Strong preference
)

contextual.add_pattern(
    pattern="use semicolons",
    weight=0.3  # Weak preference
)

# Apply as logit bias, not hard constraint
```

**Adaptive Learning**:
```python
# Learn from successful generations
await memory.store_constraint_pattern(
    pattern="async-error-handling",
    success=True,
    metrics={"compilation": True, "tests_passed": 10}
)

# Recall and apply to similar tasks
recalled = await memory.recall_similar_contexts(
    query="async function generation",
    limit=5
)

# Weight patterns by success rate
for pattern in recalled:
    weight = pattern.metadata.get("success_rate", 0.5)
    contextual.add_pattern(pattern.content, weight)
```

---

## Language-Specific Indexer Guidelines

### Priority 1: TypeScript Indexer ✅

**Status**: Complete (`src/maze/indexer/languages/typescript.py`)

**Integration**:
- tsserver via subprocess (optional, for enhanced types)
- tree-sitter-typescript for fast parsing
- AST traversal for symbol extraction

**Symbols Extracted**:
- Functions (regular, async, arrow)
- Classes and interfaces
- Type aliases and enums
- Variables with type annotations
- Imports (ES6 and CommonJS)

**Type Information**:
- Parse TypeScript type annotations
- Extract generic type parameters
- Handle union and intersection types
- Detect nullable types (`T | null | undefined`)

**Style Detection**:
- Indentation (spaces vs tabs, size)
- Quotes (single, double, backtick)
- Semicolons (present or omitted)
- Max line length

**Test Detection**:
- Jest/Mocha patterns (`it()`, `test()`, `describe()`)
- Vitest patterns
- Assertion libraries

---

### Priority 2: Python Indexer

**Status**: Planned for Phase 2

**Integration Points**:
- Pyright JSON output (`pyright --outputjson`)
- mypy JSON output (alternative)
- tree-sitter-python for parsing
- ast module for AST traversal

**Symbols to Extract**:
```python
# Functions with type hints
def process_user(user: User) -> ProcessedUser:
    ...

# Classes with typed attributes
class DataProcessor:
    config: Config
    results: List[Result]

    def process(self, data: List[Dict[str, Any]]) -> Result:
        ...

# Type aliases
ProcessingResult = Union[Success, Failure]

# Pydantic models (extract as JSON Schema)
class UserModel(BaseModel):
    name: str
    age: int
```

**Testing Protocol**:
- pytest patterns (`test_*`, `*_test.py`)
- unittest patterns (`TestCase` classes)
- Doctest detection

---

### Priority 3: Rust Indexer

**Status**: Planned for Phase 3

**Integration Points**:
- rust-analyzer LSP
- `cargo check --message-format=json`
- SSR (Structured Search Replace) for pattern extraction
- tree-sitter-rust

**Symbols to Extract**:
```rust
// Functions with type signatures
pub fn process_data(input: Vec<u8>) -> Result<String, Error> {
    ...
}

// Trait definitions
pub trait DataProcessor {
    fn process(&self, data: &[u8]) -> Result<String>;
}

// Impl blocks
impl DataProcessor for MyProcessor {
    fn process(&self, data: &[u8]) -> Result<String> {
        ...
    }
}

// Type aliases and newtype patterns
type UserId = u64;
struct Email(String);
```

**Special Considerations**:
- Lifetime annotations (`'a`, `'static`)
- Generic bounds (`T: Clone + Send`)
- Trait objects (`dyn Trait`)
- Async traits (requires async-trait crate detection)

---

### Priority 4: Go Indexer

**Status**: Planned for Phase 4

**Integration**:
- gopls LSP
- `go/ast` package (via subprocess)
- tree-sitter-go

**Symbols**:
```go
// Functions
func ProcessUser(user User) (ProcessedUser, error) {
    ...
}

// Interfaces
type DataProcessor interface {
    Process(data []byte) (string, error)
}

// Structs
type Config struct {
    Host string
    Port int
}

// Methods
func (c *Config) Validate() error {
    ...
}
```

---

### Priority 5: Zig Indexer

**Status**: Planned for Phase 5

**Integration**:
- zls (Zig Language Server)
- Zig compiler AST output
- tree-sitter-zig

**Symbols**:
```zig
// Functions with comptime
pub fn process(comptime T: type, data: []const T) !void {
    ...
}

// Error unions
const ProcessError = error{
    InvalidData,
    OutOfMemory,
};

// Structs with methods
const Processor = struct {
    allocator: Allocator,

    pub fn init(allocator: Allocator) Processor {
        return .{ .allocator = allocator };
    }
};
```

**Special Considerations**:
- Comptime analysis
- Error union extraction
- Allocator tracking (for memory safety)

---

## Testing & Validation Protocols

### Unit Testing Standards

**Coverage Targets**:
- Core type system: 90%+
- Constraint synthesis: 85%+
- Indexers: 80%+ per language
- LLGuidance adapter: 85%+
- Orchestrator: 80%+

**Test Organization**:
```
tests/unit/
├── test_core/
│   ├── test_types.py              # Type system tests
│   ├── test_constraints.py        # Constraint tests
│   └── test_llguidance_performance.py  # Performance benchmarks
├── test_indexer/
│   ├── test_base.py               # Base indexer
│   ├── test_typescript.py         # TypeScript indexer
│   └── test_python.py             # Python indexer (future)
├── test_synthesis/
│   ├── test_grammar_builder.py    # Grammar synthesis
│   └── test_json_schema.py        # JSON Schema generation
└── test_type_system/
    ├── test_inhabitation.py       # Type inhabitation
    └── test_inference.py          # Type inference
```

**Running Tests**:
```bash
# All unit tests
uv run pytest tests/unit -v

# Specific component
uv run pytest tests/unit/test_core/ -v

# With coverage
uv run pytest tests/unit --cov=maze --cov-report=html

# Fast tests only (skip slow/performance)
uv run pytest tests/unit -m "not slow and not performance"
```

---

### Performance Testing (MANDATORY)

**Location**: `tests/unit/test_core/test_*_performance.py`

**Required for**:
- All constraint implementations
- All indexer implementations
- All provider adapters
- Grammar synthesis
- Type inhabitation

**Benchmark Template**:
```python
@pytest.mark.performance
def test_component_performance(benchmark_fixture):
    """Test component meets performance targets."""

    # Setup
    component = create_component()
    test_inputs = generate_test_inputs()

    # Warmup
    for input in test_inputs[:10]:
        component.process(input)

    # Measure
    times = []
    for input in test_inputs:
        start = time.perf_counter()
        result = component.process(input)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    # Statistics
    mean = statistics.mean(times)
    p95 = statistics.quantiles(times, n=20)[18]
    p99 = statistics.quantiles(times, n=100)[98]

    # Assert targets
    assert mean < TARGET_MEAN
    assert p99 < TARGET_P99

    # Report
    print(f"\nPerformance: mean={mean:.2f}, p95={p95:.2f}, p99={p99:.2f}")
```

**Running Performance Tests**:
```bash
# All performance tests
uv run pytest -m performance -v

# Specific component
uv run pytest tests/unit/test_core/test_llguidance_performance.py -v

# With detailed output
uv run pytest -m performance -v -s
```

---

### Integration Testing

**Purpose**: Test interactions between components and external systems

**Test Categories**:
1. **llguidance Integration** - Grammar building, mask computation, caching
2. **mnemosyne Integration** - Memory storage, recall, pattern learning
3. **Multi-Stage Pipeline** - Context → Constraints → Generation → Validation
4. **Provider Adapters** - OpenAI, vLLM, SGLang compatibility

**Running Integration Tests**:
```bash
# All integration tests
uv run pytest tests/integration -v

# Specific integration
uv run pytest tests/integration/test_llguidance/ -v

# With external system (requires API keys)
export OPENAI_API_KEY=sk-...
uv run pytest tests/integration/test_providers/ -v
```

---

### End-to-End Testing

**Purpose**: Validate complete generation workflows on real tasks

**Benchmark Datasets**:
- **HumanEval**: 164 Python programming problems
- **HumanEval(+fix)**: With syntax/semantic corrections
- **MBPP**: 974 Python problems with types
- **SWE-bench-lite**: Real-world bug fixes

**Metrics**:
- Compilation success rate
- Test pass@1, pass@3, pass@10
- Time to first token (TTFT)
- Time per output token (TPOT)
- Repair attempts needed
- Constraint satisfaction rate

**Running E2E Tests**:
```bash
# All E2E tests
uv run pytest tests/e2e -v

# HumanEval benchmark
uv run pytest tests/e2e/test_humaneval/ -v

# Real-world tasks
uv run pytest tests/e2e/test_realworld/ -v
```

---

## Maze-Specific Anti-Patterns

### Critical Violations (Build Failures)

```
❌ Skip performance benchmarks for constraints
   → Every constraint MUST have benchmark proving <100μs

❌ Ignore cache hit rates <70%
   → Cache effectiveness is mandatory, not optional

❌ Allow mask computation >100μs without investigation
   → Performance regression requires immediate fix

❌ Hard-code language-specific logic outside indexers
   → Use indexer abstraction, never language switches in core

❌ Skip grammar optimization passes
   → Unoptimized grammars waste 50%+ performance

❌ Implement constraints without type awareness
   → Even syntactic constraints benefit from type context

❌ Generate code without validation stage
   → All generated code MUST be validated

❌ Ignore repair loop metrics
   → Track convergence rate, attempts, failure modes

❌ Deploy without provider adapter testing
   → Test with actual LLM providers, not mocks

❌ Skip mnemosyne integration for learned patterns
   → Patterns not stored = patterns not reused = waste
```

### Warnings (Code Review Flags)

```
⚠️ Grammar has >500 lines without modularity
   → Break into reusable components

⚠️ Type search depth >10
   → Likely too complex, need better context

⚠️ Repair loop exceeds 5 attempts
   → Constraints too weak or target too ambitious

⚠️ Memory usage >800MB
   → Approaching limit, investigate before hitting 1GB

⚠️ Test coverage <80% for new module
   → Increase coverage before merge

⚠️ No mnemosyne storage after successful generation
   → Missing learning opportunity

⚠️ Hardcoded provider URLs/configs
   → Use environment variables or config files
```

---

## Quick Reference

### Development Commands

```bash
# Setup
uv pip install -e ".[dev]"

# Testing
uv run pytest                                    # All tests
uv run pytest tests/unit -v                      # Unit tests
uv run pytest tests/integration -v               # Integration tests
uv run pytest tests/e2e -v                       # E2E tests
uv run pytest -m performance -v                  # Performance benchmarks
uv run pytest --cov=maze --cov-report=html      # Coverage report

# Performance Validation
uv run python benchmarks/mask_computation.py     # Mask benchmark
uv run python benchmarks/end_to_end.py          # E2E benchmark
uv run python benchmarks/compare_engines.py     # Engine comparison
uv run python benchmarks/baseline.py --save     # Save baseline
uv run python benchmarks/baseline.py --compare  # Compare to baseline

# Code Quality
uv run black src/ tests/                        # Format
uv run ruff src/ tests/                         # Lint
uv run mypy src/                                # Type check

# Git Workflow
git checkout -b feature/constraint-optimization
# ... make changes ...
git add . && git commit -m "Optimize grammar caching (p99: 120μs → 45μs)"
uv run pytest -m performance  # Validate before push
git push -u origin feature/constraint-optimization
```

### mnemosyne Integration Commands

```bash
# Store successful constraint pattern
mnemosyne remember \
  -c "TypeScript async function: 97% compilation, 2.1 avg repairs" \
  -n "project:maze:constraint:typescript" \
  -i 8 \
  -t "constraint,typescript,async,success"

# Store performance optimization
mnemosyne remember \
  -c "LRU cache size 100k → 200k improved hit rate 72% → 89%" \
  -n "project:maze:performance" \
  -i 9 \
  -t "optimization,caching,llguidance"

# Store repair strategy
mnemosyne remember \
  -c "Promise<T> type errors: tighten return type constraint first" \
  -n "project:maze:repair:typescript" \
  -i 7 \
  -t "repair,typescript,types,promise"

# Recall patterns
mnemosyne recall -q "async error handling" -n "project:maze:constraint" -l 5
mnemosyne recall -q "cache optimization" -n "project:maze:performance" -l 3
mnemosyne recall -q "type repair strategies" -n "project:maze:repair" -l 10

# Evolution (consolidation, decay, archival)
mnemosyne evolve
```

### Beads Task Management

```bash
# Ready work
bd ready --json --limit 5

# Create phase tasks
bd create "Phase 2: Syntactic Constraints" -t epic --id bd-ph2
bd create "Implement TypeScript CFG grammar" -t task --id bd-ph2.1 -p 0
bd create "Add JSON Schema synthesis" -t task --id bd-ph2.2 -p 1
bd create "Benchmark mask computation" -t task --id bd-ph2.3 -p 1

# Update progress
bd update bd-ph2.1 --status in_progress
bd update bd-ph2.1 --comment "Grammar template complete, testing tokenization"
bd close bd-ph2.1 --reason "Complete"

# Dependencies
bd dep add bd-ph2.3 bd-ph2.1 --type blocks  # Benchmark blocks on grammar
bd dep tree bd-ph2                          # Visualize dependencies
```

---

## Phase-Specific Checkpoints

### Phase 1: Foundation ✅ COMPLETE

**Exit Criteria**:
- [x] Language detection implemented
- [x] TypeScript indexer extracts symbols
- [x] Constraint candidates identified
- [x] Performance baseline established (50μs p99 masks)
- [x] llguidance adapter integrated
- [x] Test infrastructure ready
- [x] mnemosyne integration working

**Validation**:
```bash
uv run pytest tests/unit/test_indexer/test_typescript.py
uv run pytest tests/unit/test_core/test_llguidance_performance.py
```

---

### Phase 2: Syntactic Constraints (IN PROGRESS)

**Goals**:
- CFG/Lark grammar builder
- Multi-language grammar templates
- JSON Schema synthesis
- Provider adapters (OpenAI, vLLM, SGLang, llama.cpp)

**Exit Criteria**:
- [ ] Grammar validates successfully for all 5 languages
- [ ] Mask computation <100μs (p99)
- [ ] Grammar compilation <50ms
- [ ] Cache hit rate >70%
- [ ] JSON Schema generated from types
- [ ] All provider adapters tested

**Validation Commands**:
```bash
# Grammar validation
uv run pytest tests/unit/test_synthesis/ -v

# Performance targets
uv run pytest -m performance
assert p99_mask_time < 100  # μs
assert grammar_compile_time < 50  # ms
assert cache_hit_rate > 0.7

# Provider adapters
uv run pytest tests/integration/test_providers/ -v
```

**Memory Storage**:
```bash
mnemosyne remember \
  -c "Phase 2 complete: 5 grammars, 45μs p99 masks, 89% cache hits" \
  -n "project:maze:milestones" -i 9 -t "milestone,phase2"
```

---

### Phase 3: Type System (PLANNED)

**Goals**:
- Type inhabitation solver
- Bidirectional type inference
- Language-specific type systems (TS, Python, Rust, Go, Zig)
- Typed hole support

**Exit Criteria**:
- [ ] Type inhabitation paths found for common cases
- [ ] Bidirectional inference works
- [ ] Type error reduction >75%
- [ ] Search convergence <5 iterations
- [ ] Type checking <1ms per expression

**Validation**:
```bash
uv run pytest tests/unit/test_type_system/ -v

# Type inhabitation performance
assert type_search_time < 1  # ms (p95)
assert type_error_reduction > 0.75

# Coverage
assert type_system_coverage > 0.90
```

---

### Phase 4: Validation & Repair (PLANNED)

**Goals**:
- Multi-level validators (syntax, types, tests, lint)
- Sandboxed test execution (RUNE)
- Repair loop with constraint refinement
- pedantic_raven integration

**Exit Criteria**:
- [ ] All validation layers implemented
- [ ] Syntax validation passes
- [ ] Type checking integrated
- [ ] Tests execute in RUNE sandbox
- [ ] Repair converges <3 attempts
- [ ] pedantic_raven validates semantics

**Validation**:
```bash
uv run pytest tests/integration/test_validation/ -v
uv run pytest tests/integration/test_rune/ -v

# Repair metrics
assert avg_repair_attempts < 3
assert repair_success_rate > 0.90
```

---

### Phase 5: Adaptive Learning (PLANNED)

**Goals**:
- Pattern mining from codebases
- Constraint learning from successes/failures
- Project-specific adaptation
- Full mnemosyne integration

**Exit Criteria**:
- [ ] Patterns mined from sample projects
- [ ] Constraints learned successfully
- [ ] Adaptation improves success rate
- [ ] mnemosyne stores all learnings
- [ ] Pattern recall works across sessions

**Validation**:
```bash
uv run pytest tests/integration/test_mnemosyne/ -v
uv run pytest tests/integration/test_learning/ -v

# Learning metrics
assert patterns_mined > 100
assert constraint_learning_accuracy > 0.80
assert adaptation_improvement > 0.10  # 10% better with learning
```

---

### Phase 6: Production (PLANNED)

**Goals**:
- Performance optimization (speculative decoding, parallelization)
- Full multi-provider support
- IDE integrations
- Comprehensive documentation
- Benchmark validation

**Exit Criteria**:
- [ ] All performance targets met consistently
- [ ] All provider adapters production-ready
- [ ] IDE plugins functional (VSCode, IntelliJ)
- [ ] Full API documentation
- [ ] Benchmark results published
- [ ] User studies completed

**Validation**:
```bash
# Full benchmark suite
uv run python benchmarks/humaneval.py
uv run python benchmarks/mbpp.py
uv run python benchmarks/swe_bench_lite.py

# Performance validation
assert all_targets_met()

# Integration tests
uv run pytest tests/integration/ -v
uv run pytest tests/e2e/ -v
```

---

## Constraint Design Patterns

### Pattern 1: Incremental Refinement

**Use Case**: Iteratively tighten constraints based on validation failures

**Implementation**:
```python
async def incremental_refinement(prompt: str, spec: Specification):
    """Start loose, tighten on failures."""

    # Start with syntactic only
    constraints = ConstraintSet()
    constraints.add(SyntacticConstraint.from_language(spec.language))

    for attempt in range(3):
        # Generate with current constraints
        code = await generate(prompt, constraints)

        # Validate
        result = await validate(code, spec)

        if result.passed:
            # Success - store pattern
            await memory.store_constraint_pattern(
                pattern=constraints.to_pattern(),
                success=True,
                metrics={"attempts": attempt + 1}
            )
            return code

        # Tighten constraints based on failure type
        if result.type_errors:
            # Add type constraints
            constraints.add(TypeConstraint(
                expected_type=spec.return_type,
                context=spec.type_context
            ))

        if result.semantic_errors:
            # Add semantic constraints
            for error in result.semantic_errors:
                constraints.add(semantic_constraint_from_error(error))

    # Failed after 3 attempts
    return None
```

**When to Use**: Complex tasks where optimal constraints unknown upfront

---

### Pattern 2: Speculative Generation

**Use Case**: Generate multiple candidates in parallel, select best

**Implementation**:
```python
async def speculative_generation(prompt: str, spec: Specification):
    """Generate multiple candidates, validate concurrently."""

    # Create constraint variations
    constraint_sets = [
        create_loose_constraints(spec),
        create_medium_constraints(spec),
        create_strict_constraints(spec),
    ]

    # Generate in parallel
    tasks = [
        generate(prompt, constraints)
        for constraints in constraint_sets
    ]
    candidates = await asyncio.gather(*tasks)

    # Validate in parallel
    validation_tasks = [
        validate(code, spec)
        for code in candidates
    ]
    results = await asyncio.gather(*validation_tasks)

    # Select best (first that passes, or highest score)
    for code, result in zip(candidates, results):
        if result.passed:
            return code

    # None passed - return best partial
    return max(zip(candidates, results), key=lambda x: x[1].score)[0]
```

**When to Use**: Performance is less critical than correctness

---

### Pattern 3: Typed Hole Filling

**Use Case**: Complete partial code with type-directed search

**Implementation**:
```python
async def fill_typed_hole(code_with_hole: str, hole_type: Type):
    """Fill hole using type inhabitation."""

    # Extract context around hole
    context = extract_context(code_with_hole)
    type_context = infer_type_context(context)

    # Find expressions matching hole type
    solver = InhabitationSolver()
    valid_expressions = solver.find_valid_expressions(
        expected_type=hole_type,
        context=type_context
    )

    # Rank by likelihood and type fitness
    ranked = rank_expressions(valid_expressions, context)

    # Try each candidate
    for expr in ranked[:5]:  # Top 5
        completed = code_with_hole.replace("/*__HOLE__*/", expr)

        # Validate
        result = await validate(completed, spec)
        if result.passed:
            return completed

    # No valid completion found
    return None
```

**When to Use**: Completing functions, filling in implementation details

---

### Pattern 4: Adaptive Constraint Weighting

**Use Case**: Learn from project to weight soft constraints

**Implementation**:
```python
async def adaptive_weighting(prompt: str, spec: Specification):
    """Weight constraints based on project patterns."""

    # Recall successful patterns from this project
    patterns = await memory.recall_similar_contexts(
        query=prompt,
        namespace=f"project:maze:{spec.language}",
        limit=10
    )

    # Create contextual constraints weighted by success
    contextual = ContextualConstraint(weight=0.5)

    for pattern in patterns:
        success_rate = pattern.metadata.get("success_rate", 0.5)
        contextual.add_pattern(
            pattern=pattern.content,
            weight=success_rate
        )

    # Combine with hard constraints
    constraints = ConstraintSet()
    constraints.add(SyntacticConstraint.from_language(spec.language))
    constraints.add(contextual)

    # Generate with weighted constraints
    code = await generate(prompt, constraints)

    # Update weights based on outcome
    result = await validate(code, spec)
    await update_pattern_weights(patterns, result.passed)

    return code
```

**When to Use**: Project-specific generation, adapting to codebase conventions

---

## Enforcement

### Automated Checks (CI/CD)

```yaml
# .github/workflows/maze-ci.yml
name: Maze CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v1

      - name: Install dependencies
        run: uv pip install -e ".[dev]"

      - name: Run tests
        run: uv run pytest tests/unit -v

      - name: Check coverage
        run: |
          uv run pytest --cov=maze --cov-report=term --cov-fail-under=85

      - name: Performance benchmarks
        run: |
          uv run pytest -m performance -v
          # Assert targets met (handled in test assertions)

      - name: Type checking
        run: uv run mypy src/

      - name: Linting
        run: |
          uv run black --check src/ tests/
          uv run ruff src/ tests/
```

### Pre-Commit Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Format check
uv run black --check src/ tests/ || {
    echo "❌ Code not formatted. Run: uv run black src/ tests/"
    exit 1
}

# Lint check
uv run ruff src/ tests/ || {
    echo "❌ Linting failed"
    exit 1
}

# Fast tests only
uv run pytest tests/unit -m "not slow and not performance" || {
    echo "❌ Tests failed"
    exit 1
}

echo "✅ Pre-commit checks passed"
```

---

## Summary

This CLAUDE.md extends the global development guidelines with **maze-specific protocols** for:

1. **Performance-First Development** - <100μs masks, mandatory benchmarks
2. **4-Tier Constraint Stack** - Syntactic, Type, Semantic, Contextual
3. **Multi-System Integration** - llguidance, mnemosyne, pedantic_raven, RUNE
4. **Language Extensibility** - Indexer framework for 5 languages
5. **Benchmark-Driven** - No feature complete without performance validation
6. **Adaptive Learning** - Pattern mining and constraint weighting

**Remember**:
- Performance targets are **mandatory**, not aspirational
- Benchmarks are **required** for all constraint implementations
- Cache effectiveness is **critical** (>70% hit rate)
- Type awareness **permeates** all constraint layers
- Integration testing across **4 external systems** is essential
- mnemosyne stores **all learnings** for continuous improvement

Follow these guidelines to maintain the **performance-first, constraint-driven approach** that makes maze effective for adaptive code generation.
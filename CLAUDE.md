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

## Quick Guide: CLAUDE.md vs AGENT_GUIDE.md

**Use CLAUDE.md when you need**:
- **Performance targets and rationale** - What metrics to achieve and why
- **Constraint design principles** - How to architect the 4-tier constraint system
- **Integration philosophy** - When and why to use llguidance, mnemosyne, pedantic_raven, RUNE
- **Language indexer guidelines** - What symbols to extract per language
- **Testing philosophy** - Coverage targets and testing requirements
- **Anti-patterns to avoid** - Critical violations and warnings
- **Phase exit criteria** - What must be achieved before advancing phases

**Use AGENT_GUIDE.md when you need**:
- **Step-by-step commands** - Exact bash/python commands to run
- **Code examples** - Implementation patterns and detailed examples
- **Decision trees** - Task classification and routing logic
- **Templates** - Commit messages, PR descriptions, mnemosyne storage
- **Workflows** - Sequential steps for code changes, releases, tidying
- **Checklists** - Quality gates, enforcement matrices
- **Reference tables** - Quick command lookups and mappings

**Mental Model**:
- **CLAUDE.md** = Strategic principles (WHAT to do and WHY)
- **AGENT_GUIDE.md** = Tactical operations (HOW to do it and WHEN)

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

**Key Principles**:
- Use Lark extended syntax for CFG grammar definitions
- Enable caching with large cache size (100k+ entries)
- Profile performance to ensure targets met
- Abstract provider differences (OpenAI, vLLM, SGLang, llama.cpp)

**Critical Requirements**:
- Cache hit rate MUST exceed 70%
- P99 mask computation MUST be <100μs
- Enable profiling during development
- Test with actual LLM providers (not just mocks)

**When to Use**:
- All constraint enforcement (syntactic, type-aware, contextual)
- Grammar-based generation control
- Provider-agnostic constraint application

**→ See AGENT_GUIDE.md §5.5 for detailed code examples and implementation patterns**

---

### 2. mnemosyne Integration

**Purpose**: Store constraint patterns, recall similar contexts, enable project adaptation

**Namespace Strategy**:
- `project:maze` - General maze project knowledge
- `project:maze:constraint` - Constraint patterns and success rates
- `project:maze:language:{lang}` - Language-specific patterns (typescript, python, rust, go, zig)
- `project:maze:performance` - Performance optimizations and insights
- `project:maze:repair` - Repair strategies and lessons

**Importance Levels**:
- 10: Critical architectural decisions
- 9: Major performance breakthroughs, releases
- 8: Successful constraint patterns (>90% success rate)
- 7: Useful repair strategies, performance insights
- 6: Minor optimizations
- 5: Contextual observations (don't store below 5)

**Key Storage Triggers** (WHEN to store):
- After successful constraint pattern application
- After performance optimization (with metrics)
- After discovering bug root cause
- After phase milestone completion
- After learning integration pattern

**→ See AGENT_GUIDE.md §5.2 for storage/recall commands and §3.6 for templates**

---

### 3. pedantic_raven Integration

**Purpose**: Deep semantic validation beyond syntax and types

**Validation Modes**:
- `strict`: All properties, invariants, and contracts must hold
- `moderate`: Key properties checked, warnings for others (default)
- `lenient`: Basic behavioral checks only

**When to Use**:
- Behavioral correctness validation (not just syntax/types)
- Property-based testing integration
- Semantic constraint violation detection
- Feeding repair loop with specific violations

**→ See AGENT_GUIDE.md §5.6 for validation code examples and property specification**

---

### 4. RUNE Integration

**Purpose**: Sandboxed execution for testing generated code safely

**Safety Guarantees** (NON-NEGOTIABLE):
- Network isolation (no external calls)
- Filesystem isolation (temporary sandbox)
- Resource limits (CPU, memory, time)
- Deterministic execution (same input → same output)

**Critical Rule**: NEVER execute generated code outside RUNE sandbox

**When to Use**:
- All test execution for generated code
- Semantic validation requiring execution
- Extract diagnostics for repair loop
- Verify code behavior safely

**→ See AGENT_GUIDE.md §5.7 for sandbox configuration and execution patterns**

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

**→ See AGENT_GUIDE.md §10 for all command references**:
- §10.1: Workflow Commands (feature development, commits, PRs)
- §10.2: Quality Check Commands (tests, coverage, performance, linting)
- §10.3: Beads Commands (discovery, creation, updates, dependencies)
- §10.4: Git Commands (branching, commits, releases)
- §10.5: mnemosyne Commands (storage, recall, evolution)
- §10.6: Documentation Commands (verification, cross-reference checking)
- §10.7: Repository Tidying Commands (file movement, verification)

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

Maze uses four proven constraint design patterns for adaptive code generation:

1. **Incremental Refinement**: Start with loose constraints, tighten based on validation failures
   - Use when: Optimal constraints unknown upfront
   - Max attempts: 3
   - Stores successful patterns in mnemosyne

2. **Speculative Generation**: Generate multiple candidates in parallel, select best
   - Use when: Correctness more critical than latency
   - Creates loose, medium, strict constraint variations
   - Selects first passing or highest-scoring partial

3. **Typed Hole Filling**: Complete partial code with type-directed search
   - Use when: Completing functions or implementation details
   - Leverages type inhabitation solver
   - Ranks candidates by type fitness

4. **Adaptive Constraint Weighting**: Learn from project to weight soft constraints
   - Use when: Project-specific style or conventions matter
   - Recalls successful patterns from mnemosyne
   - Updates weights based on outcomes

**→ See AGENT_GUIDE.md §11 for complete implementations, code examples, and pattern selection guide**

---

## Enforcement

Quality gates are enforced through automated CI/CD and pre-commit hooks.

**Automated Gates**:
- Tests (all must pass)
- Performance benchmarks (all targets must be met)
- Coverage (≥70% required, CI enforces)
- Type checking (mypy, no errors)
- Formatting (black, no changes needed)
- Linting (ruff, no errors)

**Enforcement Levels**:
- ✅ **CI Required**: Tests, performance, coverage, types, format, lint
- ⚠️ **PR Review**: Documentation updates, changelog entries
- ❌ **Never Bypass**: Tests, performance benchmarks

**Emergency Bypass Protocol** (critical production issues only):
1. Use `git commit --no-verify` for emergency fix
2. Create priority-0 follow-up Beads issue immediately
3. Store incident in mnemosyne (importance 9)

**→ See AGENT_GUIDE.md §12 for CI/CD workflows, pre-commit hooks, and quality gate matrix**

---

## 12. Agent Operations Guide

For detailed operational workflows, decision trees, templates, and repository management guidelines, see **[AGENT_GUIDE.md](AGENT_GUIDE.md)**.

### What AGENT_GUIDE.md Provides

AGENT_GUIDE.md complements this CLAUDE.md with **operational details**:

**This CLAUDE.md**: High-level protocols, principles, and targets (WHAT and WHY)
- Work Plan Protocol phases and requirements
- Performance targets and rationale
- Integration principles
- Anti-patterns to avoid

**AGENT_GUIDE.md**: Step-by-step workflows and execution (HOW and WHEN)
- Decision trees for task classification and routing
- Detailed checklists for code changes, documentation, releases
- Templates for commits, PRs, Beads issues, mnemosyne storage
- Repository tidying workflows (non-destructive)
- Common scenarios with complete workflows
- Integration patterns with Beads, mnemosyne, Git
- Observability and health monitoring

### When to Consult AGENT_GUIDE.md

**Consult AGENT_GUIDE.md when you need**:
- Task classification: What type of work is this? (§1.1)
- Documentation triggers: Which docs need updates? (§1.2)
- Release decisions: Should we release? What version? (§1.3)
- Repository organization: Where does this file belong? (§1.4)
- Step-by-step workflows: How do I execute this? (§2)
- Templates: How should I format this commit/PR/issue? (§3)
- Tidying: How do I reorganize without breaking things? (§4)
- Common scenarios: Similar situation examples (§6)
- Observability: How do I check project health? (§8)

**Consult CLAUDE.md when you need**:
- Phase requirements: What must be done in each phase?
- Performance targets: What are the benchmarks?
- Integration principles: How should I integrate with external systems?
- Constraint development: How do I design constraints?
- Language indexers: What are the guidelines for new languages?
- Anti-patterns: What should I avoid?

### Key Cross-References

| CLAUDE.md Section | AGENT_GUIDE.md Section | What's There |
|-------------------|------------------------|--------------|
| §Work Plan Protocol | §2.1 Code Change Workflow | Step-by-step execution |
| §Performance-First | §6.2 Performance Optimization | Example scenario |
| §Integration Guidelines | §5 Integration Points | Conceptual overview |
| → llguidance | §5.5 llguidance Code Patterns | Grammar design, caching, profiling code |
| → mnemosyne | §5.2 + §3.6 + §5.2 | Commands, templates, patterns |
| → pedantic_raven | §5.6 pedantic_raven Patterns | Validation code examples |
| → RUNE | §5.7 RUNE Execution Patterns | Sandbox configuration code |
| §Constraint Development | §11 Implementation Patterns | 4 patterns with full code |
| §Language Indexers | §6.1 Adding New Indexer | Complete workflow |
| §Testing Protocols | §2.1 steps 7-10 + §10.2 | Workflow + commands |
| §Quick Reference | §10 Quick Command Reference | All commands organized |
| §Constraint Patterns | §11 Implementation Patterns | Incremental, Speculative, Typed Hole, Adaptive |
| §Enforcement | §12 Enforcement and CI/CD | CI workflow, hooks, gates |
| §Anti-Patterns | §7 Anti-Patterns for Agents | Agent-specific violations |
| §Phase Checkpoints | §2 Workflows | Phase execution steps |

**Quick Lookup by Need**:
- **Need code examples?** → AGENT_GUIDE.md §5, §11
- **Need commands?** → AGENT_GUIDE.md §10
- **Need workflows?** → AGENT_GUIDE.md §2
- **Need templates?** → AGENT_GUIDE.md §3
- **Need principles?** → CLAUDE.md (this file)
- **Need targets?** → CLAUDE.md Performance sections
- **Need decision tree?** → AGENT_GUIDE.md §1

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
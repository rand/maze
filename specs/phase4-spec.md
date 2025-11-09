# Phase 4: Validation & Repair System

## Overview

Phase 4 implements the validation and repair loop that turns generated code into production-ready artifacts. This phase builds multi-level validators, integrates RUNE sandbox for safe execution, implements adaptive repair loops with constraint refinement, and integrates pedantic_raven for code quality enforcement.

## Goals

**Primary Objectives**:
- Multi-level validation pipeline (syntax → types → tests → lint)
- Safe sandboxed execution environment (RUNE integration)
- Adaptive repair loop with constraint learning
- pedantic_raven integration for quality gates
- Fast validation (<500ms per check)
- High repair success rate (>90%)
- Low repair iterations (<3 avg attempts)

**Success Metrics**:
- Validation pipeline: <500ms total latency
- Repair success rate: >90% within 3 attempts
- Syntax errors: 0% after repair
- Type errors: <5% after repair
- Test pass rate: >85% after repair
- Lint compliance: >90% after repair

## Architecture

```
Generated Code
      │
      ▼
┌─────────────────────────┐
│  Validation Pipeline    │
│  - Syntax validator     │  → Parse errors, malformed code
│  - Type validator       │  → Type errors, compatibility
│  - Test validator       │  → Unit/integration test failures
│  - Lint validator       │  → Style violations, anti-patterns
└──────────┬──────────────┘
           │ Diagnostics
           ▼
┌─────────────────────────┐
│  RUNE Sandbox           │  Safe execution environment
│  - Isolated filesystem  │  - Resource limits
│  - Network isolation    │  - Timeout enforcement
│  - Memory limits        │  - Process isolation
└──────────┬──────────────┘
           │ Execution results
           ▼
┌─────────────────────────┐
│  Repair Orchestrator    │
│  - Diagnostic analysis  │  → Extract root causes
│  - Constraint refiner   │  → Tighten grammars
│  - Repair strategy      │  → Select fix approach
│  - Regeneration         │  → Apply constraints
└──────────┬──────────────┘
           │ Repair attempts
           ▼
┌─────────────────────────┐
│  pedantic_raven         │  Quality enforcement
│  - Code review rules    │  - Security checks
│  - Best practices       │  - Performance patterns
│  - Documentation check  │  - Test coverage
└─────────────────────────┘
```

## Components

### 1. Validation Pipeline

**Purpose**: Multi-level validation with early exit on success, comprehensive diagnostics on failure.

**Validators**:
- **SyntaxValidator**: Language-specific parsers (tree-sitter, pyright, tsc, rust-analyzer)
- **TypeValidator**: Type checking via language services
- **TestValidator**: Unit/integration test execution in sandbox
- **LintValidator**: Style and quality checks (ruff, clippy, eslint)

**Flow**:
1. Syntax check (fastest, catches parse errors)
2. Type check (catches type mismatches)
3. Test execution (catches logic errors)
4. Lint check (catches style/quality issues)

Each level produces structured diagnostics with line numbers, error codes, and suggested fixes.

### 2. RUNE Sandbox Integration

**Purpose**: Safe, isolated execution of generated code and tests.

**Features**:
- Filesystem isolation (temporary directories, no write to project)
- Network isolation (no external connections)
- Resource limits (CPU, memory, time)
- Process isolation (no fork bombs, no privilege escalation)

**Integration**:
```python
from maze.integrations.rune import RuneExecutor

executor = RuneExecutor(
    timeout_ms=5000,
    memory_limit_mb=512,
    network_enabled=False
)
result = executor.execute(code, tests, language="python")
```

### 3. Repair Orchestrator

**Purpose**: Adaptive repair loop that learns from failures and refines constraints.

**Repair Strategies**:
- **Constraint Tightening**: Add regex/grammar rules to prevent specific errors
- **Type Narrowing**: Refine type constraints based on type errors
- **Example-Based**: Add positive examples to guide generation
- **Template Fallback**: Use more structured templates for complex cases

**Adaptive Learning**:
- Track common failure patterns
- Build constraint refinement rules
- Learn project-specific patterns
- Store successful repairs for reuse

### 4. pedantic_raven Integration

**Purpose**: Enforce code quality, security, and best practices.

**Checks**:
- Code review rules (complexity, duplication, naming)
- Security patterns (SQL injection, XSS, auth issues)
- Performance anti-patterns (N+1 queries, inefficient loops)
- Documentation completeness (docstrings, type hints)
- Test coverage thresholds

**Integration Point**: Final quality gate before accepting repaired code.

## Interfaces

### ValidationPipeline

```python
class ValidationPipeline:
    def validate(self, code: str, language: str, context: ValidationContext) -> ValidationResult:
        """Run all validators, return combined diagnostics."""

    def validate_syntax(self, code: str, language: str) -> list[Diagnostic]:
        """Syntax-only validation (fast)."""

    def validate_types(self, code: str, language: str, context: TypeContext) -> list[Diagnostic]:
        """Type checking validation."""

    def validate_tests(self, code: str, tests: str, language: str) -> TestResult:
        """Run tests in sandbox."""

    def validate_lint(self, code: str, language: str, rules: LintRules) -> list[Diagnostic]:
        """Style and quality validation."""
```

### RepairOrchestrator

```python
class RepairOrchestrator:
    def repair(self, code: str, diagnostics: list[Diagnostic], context: RepairContext, max_attempts: int = 3) -> RepairResult:
        """Attempt to repair code with adaptive strategy."""

    def analyze_diagnostics(self, diagnostics: list[Diagnostic]) -> FailureAnalysis:
        """Extract root causes and patterns."""

    def refine_constraints(self, analysis: FailureAnalysis, grammar: str) -> str:
        """Tighten grammar based on failures."""

    def select_strategy(self, analysis: FailureAnalysis) -> RepairStrategy:
        """Choose repair approach (constraint/template/example)."""
```

### RuneExecutor

```python
class RuneExecutor:
    def execute(self, code: str, tests: str, language: str, timeout_ms: int = 5000) -> ExecutionResult:
        """Execute code and tests in isolated sandbox."""

    def validate_security(self, code: str, language: str) -> list[SecurityIssue]:
        """Check for security vulnerabilities."""
```

### PedanticRavenIntegration

```python
class PedanticRavenIntegration:
    def review(self, code: str, language: str, rules: ReviewRules) -> ReviewResult:
        """Comprehensive code review."""

    def check_security(self, code: str, language: str) -> list[SecurityFinding]:
        """Security-focused review."""

    def check_quality(self, code: str, language: str) -> QualityReport:
        """Code quality metrics."""
```

## Data Structures

```python
@dataclass
class Diagnostic:
    level: Literal["error", "warning", "info"]
    message: str
    line: int
    column: int
    code: Optional[str]
    source: str  # "syntax", "type", "test", "lint"
    suggested_fix: Optional[str]

@dataclass
class ValidationResult:
    success: bool
    diagnostics: list[Diagnostic]
    validation_time_ms: float
    stages_passed: list[str]  # ["syntax", "types", ...]

@dataclass
class RepairResult:
    success: bool
    repaired_code: Optional[str]
    attempts: int
    strategy_used: str
    diagnostics_resolved: list[Diagnostic]
    diagnostics_remaining: list[Diagnostic]
    repair_time_ms: float
    constraint_refinements: list[str]

@dataclass
class ExecutionResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: float
    resource_usage: ResourceUsage
    security_violations: list[str]
```

## Testing Strategy

**Unit Tests**: 80+ tests
- 20 tests: SyntaxValidator (all supported languages)
- 20 tests: TypeValidator (complex type scenarios)
- 15 tests: TestValidator (various failure modes)
- 10 tests: LintValidator (rule enforcement)
- 15 tests: RepairOrchestrator (strategy selection, constraint refinement)
- 10 tests: RuneExecutor (isolation, limits, security)

**Integration Tests**: 25+ tests
- End-to-end validation pipeline
- Complete repair loops
- RUNE sandbox integration
- pedantic_raven integration
- Cross-language validation

**Property Tests**: 10+ tests
- Repair idempotence (repaired code should validate)
- Constraint monotonicity (refinements should be stricter)
- Resource bound compliance (always within limits)

## Dependencies

**Phase Dependencies**:
- Phase 1 (Context Indexer): Type and API context for validation
- Phase 2 (Constraint Synthesis): Grammar refinement for repair
- Phase 3 (Type System): Type validation and checking

**External Dependencies**:
- RUNE: Sandbox execution (maze.integrations.rune)
- pedantic_raven: Code review (maze.integrations.pedantic_raven)
- tree-sitter: Fast syntax parsing
- Language tools: pyright, tsc, rust-analyzer, clippy, ruff, eslint

## Performance Targets

- Syntax validation: <50ms
- Type validation: <200ms
- Test execution: <3s (with timeout)
- Lint validation: <100ms
- Total pipeline: <500ms (excluding tests)
- Repair iteration: <2s per attempt
- Total repair time: <10s for 3 attempts

## Risk Mitigation

**Over-constraint Risk**:
- Solution: Progressive constraint tightening, not all-at-once
- Fallback to looser grammar if repair fails after max attempts

**Sandbox Escape**:
- Solution: RUNE's proven isolation, regular security audits
- Multiple layers: filesystem, network, process, resource limits

**Slow Validation**:
- Solution: Parallel validation where safe (syntax + lint)
- Caching of validation results (hash-based)
- Early exit on success

**Repair Loops**:
- Solution: Max attempts limit (default 3)
- Exponential backoff on repeated failures
- Circuit breaker for systematic issues

## Next Steps

After Phase 4 completion:
- Phase 5: Adaptive Learning (pattern mining, constraint learning)
- Phase 6: Production (performance optimization, benchmarking)

# Maze Phase 4: Validation & Repair System

Complete validation and adaptive repair system with multi-level validation, sandboxed execution, and constraint learning.

## Overview

The validation system provides:
- **Multi-stage validation**: syntax → types → tests → lint → security
- **Sandboxed execution**: Safe test execution with resource limits
- **Adaptive repair**: 5 strategies with pattern learning
- **Security enforcement**: OWASP Top 10 detection
- **Multi-language support**: Python, TypeScript, Rust, Go, Zig

## Quick Start

```python
from maze.validation.pipeline import ValidationPipeline, ValidationContext
from maze.validation.lint import LintRules

# Create pipeline
pipeline = ValidationPipeline()

# Validate code
code = '''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
'''

context = ValidationContext(
    lint_rules=LintRules.default(),
    tests="def test_add(): assert add(2, 3) == 5"
)

result = pipeline.validate(code, "python", context)

if result.success:
    print(f"✓ Validation passed in {result.validation_time_ms:.2f}ms")
else:
    print(f"✗ Validation failed with {len(result.diagnostics)} issues")
    for diag in result.diagnostics:
        print(f"  {diag.source}:{diag.line} - {diag.message}")
```

## Components

### 1. ValidationPipeline

Orchestrates multi-level validation with early exit and parallel execution.

```python
from maze.validation.pipeline import ValidationPipeline

pipeline = ValidationPipeline(
    parallel_validation=True,  # Run syntax + lint in parallel
)

# Run specific stages
result = pipeline.validate(
    code,
    "python",
    context,
    stages=["syntax", "types", "lint"]
)

# Get statistics
stats = pipeline.get_pipeline_stats()
print(f"Success rate: {stats['success_rate']:.1%}")
```

**Performance**: <500ms for syntax + types + lint (excluding tests)

### 2. SyntaxValidator

Fast syntax validation using native parsers.

```python
from maze.validation.syntax import SyntaxValidator

validator = SyntaxValidator()
result = validator.validate(code, "python")

if not result.success:
    for diag in result.diagnostics:
        print(f"Line {diag.line}: {diag.message}")
        if diag.suggested_fix:
            print(f"  Fix: {diag.suggested_fix}")
```

**Performance**: <50ms for typical files

**Supported**: Python (ast), TypeScript (tsc), Rust (cargo), Go (go build), Zig (zig ast-check)

### 3. TypeValidator

Type checking integration with language-specific tools.

```python
from maze.validation.types import TypeValidator
from maze.validation.pipeline import TypeContext

validator = TypeValidator()
context = TypeContext()  # Type environment

result = validator.validate(code, "python", context)
```

**Performance**: <200ms for typical files

**Tools**: pyright (Python), tsc (TypeScript), cargo check (Rust), go build (Go), zig build-obj (Zig)

### 4. TestValidator

Safe test execution in sandboxed environment.

```python
from maze.validation.tests import TestValidator
from maze.integrations.rune import RuneExecutor

sandbox = RuneExecutor(
    timeout_ms=5000,
    memory_limit_mb=512,
)

validator = TestValidator(sandbox=sandbox)

result = validator.validate(
    code="def add(a, b): return a + b",
    tests="def test_add(): assert add(2, 3) == 5",
    language="python",
    timeout_ms=5000
)

if result.success:
    print(f"✓ {result.test_results.passed} tests passed")
else:
    print(f"✗ {result.test_results.failed} tests failed")
```

**Security**: Filesystem isolation, network blocking, resource limits

**Frameworks**: pytest, jest/vitest, cargo test, go test, zig test

### 5. LintValidator

Style and quality enforcement with auto-fix.

```python
from maze.validation.lint import LintValidator, LintRules

# Strict rules for production
validator = LintValidator(rules=LintRules.strict())

result = validator.validate(code, "python")

# Auto-fix issues
if result.auto_fixable:
    fixed_code = validator.auto_fix(code, "python")
```

**Rules**:
- `LintRules.default()`: Lenient (120 chars, no docstrings required)
- `LintRules.strict()`: Production (100 chars, docstrings + type hints required)

**Linters**: ruff (Python), eslint (TypeScript), clippy (Rust), golangci-lint (Go), zig fmt (Zig)

### 6. PedanticRavenIntegration

Comprehensive code review and security enforcement.

```python
from maze.integrations.pedantic_raven import (
    PedanticRavenIntegration,
    ReviewRules
)

raven = PedanticRavenIntegration(ReviewRules.strict())

result = raven.review(
    code=code,
    language="python",
    tests=tests  # Optional for coverage
)

# Security findings
for finding in result.security_findings:
    if finding.severity == "critical":
        print(f"🔴 {finding.message} (CWE-{finding.cwe_id})")

# Quality metrics
print(f"Quality score: {result.quality_report.quality_score:.1f}/100")
print(f"Complexity: {result.quality_report.cyclomatic_complexity}")
print(f"Documentation: {result.documentation_report.completeness_score:.1f}%")
```

**Security Checks**:
- SQL injection (CWE-89)
- XSS vulnerabilities (CWE-79)
- Command injection (CWE-78)
- Code injection - eval/exec (CWE-95)
- Hardcoded credentials (CWE-798)

**Quality Metrics**:
- Cyclomatic complexity
- Function length
- Nesting depth
- Comment ratio
- Overall score (0-100)

### 7. RepairOrchestrator

Adaptive repair with constraint learning.

```python
from maze.repair.orchestrator import RepairOrchestrator, RepairContext

orchestrator = RepairOrchestrator(
    validator=pipeline,
    max_attempts=3,
    learning_enabled=True
)

result = orchestrator.repair(
    code="def broken(",
    prompt="Create add function",
    grammar="",
    language="python",
    context=RepairContext(max_attempts=3)
)

if result.success:
    print(f"✓ Repaired in {result.attempts} attempts")
    print(f"Strategies: {', '.join(result.strategies_used)}")
    print(result.repaired_code)
else:
    print(f"✗ Failed after {result.attempts} attempts")
    for diag in result.diagnostics_remaining:
        print(f"  {diag.source}: {diag.message}")
```

**Strategies** (progressive):
1. **Constraint Tightening**: Add structure requirements
2. **Type Narrowing**: Refine type constraints
3. **Example-Based**: Add positive examples
4. **Template Fallback**: Use conservative template
5. **Simplify**: Reduce complexity

**Learning**: Successful patterns stored and reused automatically

## Complete Workflow

```python
from maze.validation.pipeline import ValidationPipeline, ValidationContext
from maze.validation.lint import LintRules
from maze.integrations.pedantic_raven import PedanticRavenIntegration, ReviewRules
from maze.repair.orchestrator import RepairOrchestrator, RepairContext

# 1. Setup
raven = PedanticRavenIntegration(ReviewRules.strict())
pipeline = ValidationPipeline(pedantic_raven=raven)
orchestrator = RepairOrchestrator(validator=pipeline)

# 2. Validate
code = '''
def process(data):
    eval(data)  # Security issue!
'''

val_context = ValidationContext(
    lint_rules=LintRules.strict(),
    tests="def test(): assert process('42') == 42"
)

result = pipeline.validate(code, "python", val_context)

# 3. Repair if needed
if not result.success:
    repair_result = orchestrator.repair(
        code=code,
        prompt="Create process function",
        grammar="",
        language="python",
        context=RepairContext(validation_context=val_context)
    )

    if repair_result.success:
        code = repair_result.repaired_code

# 4. Final review
review = raven.review(code, "python")
if review.overall_score < 70:
    print("Code needs improvement")
```

## Performance Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| Syntax validation | <50ms | ✓ |
| Type validation | <200ms | ✓ |
| Lint validation | <100ms | ✓ |
| Full pipeline (no tests) | <500ms | ✓ |
| Test execution | <5s | ✓ |
| Repair iteration | <2s | ✓ |

## Error Handling

All validators return structured diagnostics:

```python
@dataclass
class Diagnostic:
    level: Literal["error", "warning", "info"]
    message: str
    line: int
    column: int
    code: Optional[str] = None
    source: str = ""  # "syntax", "type", "test", "lint", "security"
    suggested_fix: Optional[str] = None
    context: Optional[str] = None
```

## Testing

```bash
# Unit tests
uv run pytest tests/unit/test_validation/ -v

# Integration tests
uv run pytest tests/integration/ -v

# All Phase 4 tests
uv run pytest tests/unit/test_validation/ tests/unit/test_integrations/ tests/unit/test_repair/ tests/integration/ -v

# Performance benchmarks
uv run python benchmarks/validation_benchmark.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ValidationPipeline                       │
│  Orchestrates: syntax → types → tests → lint → security     │
└─────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐
   │   Syntax    │  │   Type    │  │    Test     │
   │  Validator  │  │ Validator │  │  Validator  │
   └─────────────┘  └───────────┘  └─────────────┘
                                           │
                                    ┌──────▼──────┐
                                    │    RUNE     │
                                    │   Sandbox   │
                                    └─────────────┘
          │                │                │
   ┌──────▼──────┐  ┌─────▼─────────┐
   │    Lint     │  │  Pedantic     │
   │  Validator  │  │     Raven     │
   └─────────────┘  └───────────────┘
                           │
                    ┌──────▼──────┐
                    │   Repair    │
                    │ Orchestrator│
                    └─────────────┘
```

## Best Practices

1. **Use ValidationContext**: Group related validation parameters
2. **Enable parallel validation**: For faster syntax + lint checks
3. **Set appropriate timeouts**: Match to expected execution time
4. **Cache validation results**: Built-in LRU caching in validators
5. **Learn from repairs**: Enable learning_enabled for better results
6. **Use strict rules in CI**: Lenient for development, strict for production
7. **Handle diagnostics gracefully**: All validators return structured errors

## Examples

See `tests/integration/test_validation_integration.py` for complete examples of:
- End-to-end validation workflows
- Repair loop integration
- Cross-language validation
- Performance optimization
- Error handling patterns

## API Reference

Full API documentation: [API.md](./API.md)

## License

Part of the Maze adaptive constrained code generation system.

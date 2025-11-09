# Maze Phase 4: Validation & Repair API Reference

Complete API documentation for all Phase 4 components.

## Table of Contents

1. [Data Types](#data-types)
2. [RuneExecutor](#runeexecutor)
3. [SyntaxValidator](#syntaxvalidator)
4. [TypeValidator](#typevalidator)
5. [TestValidator](#testvalidator)
6. [LintValidator](#lintvalidator)
7. [ValidationPipeline](#validationpipeline)
8. [RepairOrchestrator](#repairorchestrator)
9. [PedanticRavenIntegration](#pedanticravenintegration)
10. [Exceptions](#exceptions)

---

## Data Types

### Core Validation Types

#### `Diagnostic`

Structured diagnostic message from any validation stage.

```python
@dataclass
class Diagnostic:
    level: Literal["error", "warning", "info"]
    message: str
    line: int
    column: int = 0
    code: Optional[str] = None
    source: str = ""  # "syntax", "type", "test", "lint", "security"
    suggested_fix: Optional[str] = None
    context: Optional[str] = None
```

**Fields:**
- `level`: Severity level
- `message`: Human-readable error message
- `line`: Line number (1-indexed)
- `column`: Column number (0-indexed)
- `code`: Error code (e.g., "E501" for line too long)
- `source`: Which validation stage produced this diagnostic
- `suggested_fix`: Auto-fix suggestion if available
- `context`: Additional context (e.g., surrounding code)

#### `ValidationContext`

Configuration for validation pipeline.

```python
@dataclass
class ValidationContext:
    type_context: Optional[TypeContext] = None
    tests: Optional[str] = None
    lint_rules: Optional[LintRules] = None
    timeout_ms: int = 5000
    parallel_validation: bool = True
```

**Fields:**
- `type_context`: Type environment for type checking
- `tests`: Test code to execute
- `lint_rules`: Linting rules configuration
- `timeout_ms`: Test execution timeout
- `parallel_validation`: Enable parallel syntax + lint validation

#### `TypeContext`

Type environment for type checking (placeholder for Phase 3 integration).

```python
@dataclass
class TypeContext:
    symbols: dict[str, str] = field(default_factory=dict)
    imports: list[str] = field(default_factory=list)
    globals_dict: dict[str, Any] = field(default_factory=dict)
```

**Fields:**
- `symbols`: Symbol table mapping names to types
- `imports`: Available imports
- `globals_dict`: Global namespace bindings

---

## RuneExecutor

Sandboxed code execution with resource limits and security enforcement.

### Constructor

```python
def __init__(
    self,
    timeout_ms: int = 5000,
    memory_limit_mb: int = 512,
    cpu_limit_percent: int = 100,
    network_enabled: bool = False,
    allowed_syscalls: Optional[list[str]] = None
)
```

**Parameters:**
- `timeout_ms`: Maximum execution time in milliseconds (default: 5000)
- `memory_limit_mb`: Maximum memory usage in megabytes (default: 512)
- `cpu_limit_percent`: CPU usage limit as percentage (default: 100)
- `network_enabled`: Allow network access (default: False)
- `allowed_syscalls`: Whitelist of allowed system calls (default: None = all allowed)

**Example:**
```python
from maze.integrations.rune import RuneExecutor

sandbox = RuneExecutor(
    timeout_ms=10000,
    memory_limit_mb=256,
    network_enabled=False
)
```

### Methods

#### `execute()`

Execute code and tests in sandboxed environment.

```python
def execute(
    self,
    code: str,
    tests: str,
    language: str,
    timeout_ms: Optional[int] = None
) -> ExecutionResult
```

**Parameters:**
- `code`: Source code to execute
- `tests`: Test code to run
- `language`: Programming language ("python", "typescript", "rust", "go", "zig")
- `timeout_ms`: Override default timeout (optional)

**Returns:** `ExecutionResult`

**Raises:**
- `ValueError`: If language is unsupported
- `RuntimeError`: If sandbox setup fails

**Example:**
```python
result = sandbox.execute(
    code='def add(a, b): return a + b',
    tests='assert add(2, 3) == 5',
    language='python',
    timeout_ms=5000
)

if result.success:
    print(f"Tests passed in {result.execution_time_ms}ms")
else:
    print(f"Exit code: {result.exit_code}")
    print(f"Stderr: {result.stderr}")
```

#### `validate_security()`

Check code for security vulnerabilities.

```python
def validate_security(
    self,
    code: str,
    language: str
) -> list[SecurityIssue]
```

**Parameters:**
- `code`: Source code to analyze
- `language`: Programming language

**Returns:** List of `SecurityIssue` objects

**Example:**
```python
issues = sandbox.validate_security(
    code='eval(user_input)',
    language='python'
)

for issue in issues:
    print(f"{issue.severity}: {issue.message}")
```

#### `cleanup()`

Clean up temporary resources.

```python
def cleanup(self) -> None
```

**Example:**
```python
try:
    result = sandbox.execute(code, tests, 'python')
finally:
    sandbox.cleanup()
```

### Return Types

#### `ExecutionResult`

```python
@dataclass
class ExecutionResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: float
    memory_used_mb: float
    timeout: bool
    security_violations: list[SecurityIssue]
```

#### `SecurityIssue`

```python
@dataclass
class SecurityIssue:
    severity: Literal["low", "medium", "high", "critical"]
    category: str  # "injection", "unsafe_eval", "hardcoded_secret", etc.
    message: str
    line: int
    code_snippet: str
    suggested_fix: Optional[str] = None
```

---

## SyntaxValidator

Fast syntax validation using native language parsers.

### Constructor

```python
def __init__(self, cache_size: int = 1000)
```

**Parameters:**
- `cache_size`: LRU cache size for parse results (default: 1000)

### Methods

#### `validate()`

Validate code syntax.

```python
def validate(
    self,
    code: str,
    language: str
) -> SyntaxValidationResult
```

**Parameters:**
- `code`: Source code to validate
- `language`: Programming language ("python", "typescript", "rust", "go", "zig")

**Returns:** `SyntaxValidationResult`

**Raises:**
- `ValueError`: If language is unsupported

**Performance:** <50ms for typical files (uses LRU cache)

**Example:**
```python
from maze.validation.syntax import SyntaxValidator

validator = SyntaxValidator()
result = validator.validate(
    code='def foo(: pass',  # Invalid syntax
    language='python'
)

if not result.success:
    for diag in result.diagnostics:
        print(f"Line {diag.line}: {diag.message}")
        if diag.suggested_fix:
            print(f"  Fix: {diag.suggested_fix}")
```

#### `clear_cache()`

Clear parse result cache.

```python
def clear_cache(self) -> None
```

### Return Types

#### `SyntaxValidationResult`

```python
@dataclass
class SyntaxValidationResult:
    success: bool
    diagnostics: list[Diagnostic]
    parse_tree: Optional[Any] = None
    validation_time_ms: float = 0.0
```

---

## TypeValidator

Type checking integration with language-specific tools.

### Constructor

```python
def __init__(self)
```

### Methods

#### `validate()`

Validate code types.

```python
def validate(
    self,
    code: str,
    language: str,
    context: Optional[TypeContext] = None
) -> TypeValidationResult
```

**Parameters:**
- `code`: Source code to type-check
- `language`: Programming language ("python", "typescript", "rust", "go", "zig")
- `context`: Type environment (optional)

**Returns:** `TypeValidationResult`

**Raises:**
- `ValueError`: If language is unsupported
- `RuntimeError`: If type checker is not installed

**Performance:** <200ms for typical files

**Tools Used:**
- Python: pyright
- TypeScript: tsc
- Rust: cargo check
- Go: go build
- Zig: zig build-obj

**Example:**
```python
from maze.validation.types import TypeValidator
from maze.validation.pipeline import TypeContext

validator = TypeValidator()
context = TypeContext()

result = validator.validate(
    code='def add(a: int, b: str) -> int: return a + b',
    language='python',
    context=context
)

if not result.success:
    for error in result.type_errors:
        print(f"Type error: {error}")
```

### Return Types

#### `TypeValidationResult`

```python
@dataclass
class TypeValidationResult:
    success: bool
    diagnostics: list[Diagnostic]
    type_errors: list[str]
    inferred_types: dict[str, str]
    validation_time_ms: float = 0.0
```

---

## TestValidator

Safe test execution with result parsing.

### Constructor

```python
def __init__(self, sandbox: RuneExecutor)
```

**Parameters:**
- `sandbox`: RuneExecutor instance for sandboxed execution

### Methods

#### `validate()`

Run tests and validate results.

```python
def validate(
    self,
    code: str,
    tests: str,
    language: str,
    timeout_ms: int = 5000
) -> TestValidationResult
```

**Parameters:**
- `code`: Source code under test
- `tests`: Test code to execute
- `language`: Programming language ("python", "typescript", "rust", "go", "zig")
- `timeout_ms`: Test execution timeout (default: 5000)

**Returns:** `TestValidationResult`

**Raises:**
- `ValueError`: If language is unsupported

**Performance:** <5s for typical test suites

**Frameworks:**
- Python: pytest
- TypeScript: jest/vitest
- Rust: cargo test
- Go: go test
- Zig: zig test

**Example:**
```python
from maze.validation.tests import TestValidator
from maze.integrations.rune import RuneExecutor

sandbox = RuneExecutor(timeout_ms=10000)
validator = TestValidator(sandbox=sandbox)

result = validator.validate(
    code='def add(a, b): return a + b',
    tests='''
def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
''',
    language='python',
    timeout_ms=5000
)

if result.success:
    print(f"✓ {result.test_results.passed} tests passed")
else:
    print(f"✗ {result.test_results.failed} tests failed")
    for diag in result.diagnostics:
        print(f"  {diag.message}")
```

### Return Types

#### `TestValidationResult`

```python
@dataclass
class TestValidationResult:
    success: bool
    diagnostics: list[Diagnostic]
    test_results: TestResults
    execution_time_ms: float
    timeout: bool = False
```

#### `TestResults`

```python
@dataclass
class TestResults:
    passed: int
    failed: int
    errors: int
    skipped: int
    total: int
    details: list[TestDetail]
```

#### `TestDetail`

```python
@dataclass
class TestDetail:
    name: str
    status: Literal["passed", "failed", "error", "skipped"]
    message: Optional[str] = None
    duration_ms: float = 0.0
```

---

## LintValidator

Style and quality validation with auto-fix support.

### Constructor

```python
def __init__(
    self,
    rules: Optional[LintRules] = None,
    cache_size: int = 500
)
```

**Parameters:**
- `rules`: Linting rules configuration (default: LintRules.default())
- `cache_size`: LRU cache size for lint results (default: 500)

### Methods

#### `validate()`

Validate code style and quality.

```python
def validate(
    self,
    code: str,
    language: str,
    rules: Optional[LintRules] = None
) -> LintValidationResult
```

**Parameters:**
- `code`: Source code to lint
- `language`: Programming language ("python", "typescript", "rust", "go", "zig")
- `rules`: Override default linting rules (optional)

**Returns:** `LintValidationResult`

**Raises:**
- `ValueError`: If language is unsupported
- `RuntimeError`: If linter is not installed

**Performance:** <100ms for typical files (uses LRU cache)

**Linters:**
- Python: ruff
- TypeScript: eslint
- Rust: clippy
- Go: golangci-lint
- Zig: zig fmt

**Example:**
```python
from maze.validation.lint import LintValidator, LintRules

validator = LintValidator(rules=LintRules.strict())

result = validator.validate(
    code='def very_long_function_name_that_exceeds_maximum_line_length_limit(): pass',
    language='python'
)

if not result.success:
    print(f"Found {len(result.diagnostics)} issues")
    if result.auto_fixable:
        fixed_code = validator.auto_fix(code, 'python')
        print("Auto-fixed code:")
        print(fixed_code)
```

#### `auto_fix()`

Automatically fix lint issues.

```python
def auto_fix(
    self,
    code: str,
    language: str
) -> str
```

**Parameters:**
- `code`: Source code to fix
- `language`: Programming language

**Returns:** Fixed code (or original if auto-fix not available)

**Example:**
```python
fixed_code = validator.auto_fix(
    code='x=1+2',  # Missing spaces
    language='python'
)
# Returns: 'x = 1 + 2'
```

### Configuration Types

#### `LintRules`

```python
@dataclass
class LintRules:
    max_line_length: int = 100
    max_complexity: int = 10
    require_docstrings: bool = True
    require_type_hints: bool = True

    @staticmethod
    def default() -> "LintRules":
        """Lenient rules for development."""
        return LintRules(
            max_line_length=120,
            max_complexity=15,
            require_docstrings=False,
            require_type_hints=False
        )

    @staticmethod
    def strict() -> "LintRules":
        """Strict rules for production."""
        return LintRules(
            max_line_length=100,
            max_complexity=10,
            require_docstrings=True,
            require_type_hints=True
        )
```

### Return Types

#### `LintValidationResult`

```python
@dataclass
class LintValidationResult:
    success: bool
    diagnostics: list[Diagnostic]
    auto_fixable: bool
    validation_time_ms: float = 0.0
```

---

## ValidationPipeline

Multi-level validation orchestration with early exit and parallel execution.

### Constructor

```python
def __init__(
    self,
    syntax_validator: Optional[SyntaxValidator] = None,
    type_validator: Optional[TypeValidator] = None,
    test_validator: Optional[TestValidator] = None,
    lint_validator: Optional[LintValidator] = None,
    pedantic_raven: Optional[PedanticRavenIntegration] = None,
    parallel_validation: bool = True
)
```

**Parameters:**
- `syntax_validator`: Custom syntax validator (default: creates new instance)
- `type_validator`: Custom type validator (default: creates new instance)
- `test_validator`: Custom test validator (default: creates with RuneExecutor)
- `lint_validator`: Custom lint validator (default: creates new instance)
- `pedantic_raven`: Code review integration (default: None)
- `parallel_validation`: Enable parallel syntax + lint (default: True)

### Methods

#### `validate()`

Run multi-stage validation pipeline.

```python
def validate(
    self,
    code: str,
    language: str,
    context: Optional[ValidationContext] = None,
    stages: Optional[list[str]] = None
) -> ValidationResult
```

**Parameters:**
- `code`: Source code to validate
- `language`: Programming language
- `context`: Validation configuration (optional)
- `stages`: Which stages to run (default: ["syntax", "types", "tests", "lint"])

**Returns:** `ValidationResult`

**Performance:** <500ms for syntax + types + lint (excluding tests)

**Stage Order:**
1. **syntax**: Parse and validate syntax
2. **types**: Type checking
3. **tests**: Run test suite
4. **lint**: Style and quality checks
5. **security**: Code review (if pedantic_raven enabled)

**Early Exit:** Pipeline stops at first failure unless all stages requested

**Example:**
```python
from maze.validation.pipeline import ValidationPipeline, ValidationContext
from maze.validation.lint import LintRules

pipeline = ValidationPipeline(parallel_validation=True)

code = '''
def calculate(x: int, y: int) -> int:
    """Calculate result."""
    return x + y
'''

context = ValidationContext(
    lint_rules=LintRules.strict(),
    tests='def test(): assert calculate(2, 3) == 5'
)

result = pipeline.validate(code, 'python', context)

if result.success:
    print(f"✓ All {len(result.stages_passed)} stages passed")
    print(f"  Validation time: {result.validation_time_ms:.2f}ms")
else:
    print(f"✗ Failed stages: {', '.join(result.stages_failed)}")
    for diag in result.diagnostics:
        print(f"  [{diag.source}] {diag.message}")
```

#### `get_pipeline_stats()`

Get pipeline performance statistics.

```python
def get_pipeline_stats(self) -> dict
```

**Returns:** Dictionary with statistics:
- `total_validations`: Total validation calls
- `average_validation_time_ms`: Mean validation time
- `success_rate`: Validation success rate (0-1)
- `stage_success_rates`: Per-stage success rates

**Example:**
```python
stats = pipeline.get_pipeline_stats()
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Average time: {stats['average_validation_time_ms']:.2f}ms")
```

### Return Types

#### `ValidationResult`

```python
@dataclass
class ValidationResult:
    success: bool
    diagnostics: list[Diagnostic]
    stages_passed: list[str]
    stages_failed: list[str]
    validation_time_ms: float
    stage_results: dict[str, Any]
```

---

## RepairOrchestrator

Adaptive repair loop with constraint learning and strategy selection.

### Constructor

```python
def __init__(
    self,
    validator: ValidationPipeline,
    synthesizer: Optional[ConstraintSynthesizer] = None,
    generator: Optional[CodeGenerator] = None,
    max_attempts: int = 3,
    learning_enabled: bool = True
)
```

**Parameters:**
- `validator`: ValidationPipeline for checking repairs
- `synthesizer`: Constraint synthesis (Phase 2 integration, optional)
- `generator`: Code generator (Phase 3 integration, optional)
- `max_attempts`: Maximum repair attempts (default: 3)
- `learning_enabled`: Enable pattern learning (default: True)

### Methods

#### `repair()`

Attempt to repair invalid code.

```python
def repair(
    self,
    code: str,
    prompt: str,
    grammar: str,
    language: str,
    context: Optional[RepairContext] = None,
    max_attempts: Optional[int] = None
) -> RepairResult
```

**Parameters:**
- `code`: Code to repair
- `prompt`: Original generation prompt
- `grammar`: Current constraint grammar
- `language`: Programming language
- `context`: Repair configuration (optional)
- `max_attempts`: Override default max attempts (optional)

**Returns:** `RepairResult`

**Performance:** <2s per repair iteration

**Strategies** (progressive):
1. **CONSTRAINT_TIGHTENING**: Add structural requirements
2. **TYPE_NARROWING**: Refine type constraints
3. **EXAMPLE_BASED**: Add positive examples
4. **TEMPLATE_FALLBACK**: Use conservative template
5. **SIMPLIFY**: Reduce complexity

**Pattern Learning:** Successful repairs are stored (MD5-hashed) and reused

**Example:**
```python
from maze.repair.orchestrator import RepairOrchestrator, RepairContext

orchestrator = RepairOrchestrator(
    validator=pipeline,
    max_attempts=3,
    learning_enabled=True
)

result = orchestrator.repair(
    code='def broken(',
    prompt='Create function to add numbers',
    grammar='',
    language='python',
    context=RepairContext(max_attempts=3)
)

if result.success:
    print(f"✓ Repaired in {result.attempts} attempts")
    print(f"  Strategies used: {', '.join(result.strategies_used)}")
    print(f"  Time: {result.total_repair_time_ms:.2f}ms")
    print("\nRepaired code:")
    print(result.repaired_code)
else:
    print(f"✗ Failed after {result.attempts} attempts")
    print(f"Remaining issues: {len(result.diagnostics_remaining)}")
```

#### `analyze_diagnostics()`

Analyze failure patterns.

```python
def analyze_diagnostics(
    self,
    diagnostics: list[Diagnostic]
) -> FailureAnalysis
```

**Parameters:**
- `diagnostics`: Validation diagnostics

**Returns:** `FailureAnalysis` with categorized errors

#### `select_strategy()`

Choose repair strategy.

```python
def select_strategy(
    self,
    analysis: FailureAnalysis,
    attempt: int,
    previous_strategies: list[str]
) -> RepairStrategy
```

**Parameters:**
- `analysis`: Failure analysis
- `attempt`: Current attempt number
- `previous_strategies`: Previously tried strategies

**Returns:** `RepairStrategy` enum value

#### `get_repair_stats()`

Get repair performance statistics.

```python
def get_repair_stats(self) -> dict
```

**Returns:** Dictionary with statistics:
- `total_repairs`: Total repair attempts
- `success_rate`: Repair success rate (0-1)
- `avg_attempts`: Average attempts per repair
- `patterns_learned`: Number of learned patterns
- `patterns_reused`: Pattern reuse count

**Example:**
```python
stats = orchestrator.get_repair_stats()
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Patterns learned: {stats['patterns_learned']}")
print(f"Patterns reused: {stats['patterns_reused']}")
```

### Configuration Types

#### `RepairContext`

```python
@dataclass
class RepairContext:
    max_attempts: int = 3
    validation_context: Optional[ValidationContext] = None
    allow_simplification: bool = True
    preserve_structure: bool = False
```

#### `RepairStrategy`

```python
class RepairStrategy(Enum):
    CONSTRAINT_TIGHTENING = "constraint_tightening"
    TYPE_NARROWING = "type_narrowing"
    EXAMPLE_BASED = "example_based"
    TEMPLATE_FALLBACK = "template_fallback"
    SIMPLIFY = "simplify"
```

### Return Types

#### `RepairResult`

```python
@dataclass
class RepairResult:
    success: bool
    repaired_code: str
    attempts: int
    strategies_used: list[str]
    diagnostics_resolved: list[Diagnostic]
    diagnostics_remaining: list[Diagnostic]
    total_repair_time_ms: float
    refinement_trace: list[ConstraintRefinement]
```

#### `FailureAnalysis`

```python
@dataclass
class FailureAnalysis:
    syntax_errors: list[Diagnostic]
    type_errors: list[Diagnostic]
    test_errors: list[Diagnostic]
    lint_errors: list[Diagnostic]
    security_errors: list[Diagnostic]
    error_patterns: list[str]
    severity: Literal["low", "medium", "high"]
```

#### `ConstraintRefinement`

```python
@dataclass
class ConstraintRefinement:
    strategy: RepairStrategy
    grammar_delta: str
    schema_delta: Optional[dict] = None
    rationale: str = ""
```

---

## PedanticRavenIntegration

Comprehensive code review with security, quality, and documentation checks.

### Constructor

```python
def __init__(self, rules: Optional[ReviewRules] = None)
```

**Parameters:**
- `rules`: Review rules configuration (default: ReviewRules.default())

### Methods

#### `review()`

Perform comprehensive code review.

```python
def review(
    self,
    code: str,
    language: str,
    tests: Optional[str] = None,
    rules: Optional[ReviewRules] = None
) -> ReviewResult
```

**Parameters:**
- `code`: Source code to review
- `language`: Programming language
- `tests`: Test code for coverage analysis (optional)
- `rules`: Override default review rules (optional)

**Returns:** `ReviewResult`

**Checks:**
- **Security**: OWASP Top 10 vulnerabilities
- **Quality**: Complexity, function length, nesting depth
- **Documentation**: Docstrings, comments, coverage
- **Test Coverage**: If tests provided

**Example:**
```python
from maze.integrations.pedantic_raven import (
    PedanticRavenIntegration,
    ReviewRules
)

raven = PedanticRavenIntegration(ReviewRules.strict())

result = raven.review(
    code='''
def process(data):
    eval(data)  # Security issue!
    return data
''',
    language='python',
    tests='def test(): assert process("42") == 42'
)

# Security findings
for finding in result.security_findings:
    if finding.severity == "critical":
        print(f"🔴 {finding.message} (CWE-{finding.cwe_id})")
        print(f"   Fix: {finding.suggested_fix}")

# Quality metrics
print(f"\nQuality score: {result.quality_report.quality_score:.1f}/100")
print(f"Complexity: {result.quality_report.cyclomatic_complexity}")

# Overall
print(f"\nOverall score: {result.overall_score:.1f}/100")
print(f"Status: {'✓ PASS' if result.success else '✗ FAIL'}")
```

### Configuration Types

#### `ReviewRules`

```python
@dataclass
class ReviewRules:
    check_security: bool = True
    check_quality: bool = True
    check_documentation: bool = True
    check_test_coverage: bool = True
    block_on_critical_security: bool = True
    min_quality_score: int = 70
    min_documentation_coverage: int = 50

    @staticmethod
    def default() -> "ReviewRules":
        """Lenient rules for development."""
        return ReviewRules(
            block_on_critical_security=True,
            min_quality_score=50,
            min_documentation_coverage=30
        )

    @staticmethod
    def strict() -> "ReviewRules":
        """Strict rules for production."""
        return ReviewRules(
            block_on_critical_security=True,
            min_quality_score=70,
            min_documentation_coverage=80
        )
```

### Return Types

#### `ReviewResult`

```python
@dataclass
class ReviewResult:
    success: bool
    security_findings: list[SecurityFinding]
    quality_report: QualityReport
    documentation_report: DocumentationReport
    test_coverage_report: Optional[TestCoverageReport]
    overall_score: float  # 0-100
```

#### `SecurityFinding`

```python
@dataclass
class SecurityFinding:
    category: str  # "injection", "xss", "crypto", "auth", etc.
    severity: Literal["low", "medium", "high", "critical"]
    message: str
    line: int
    code_snippet: str
    cwe_id: str  # "CWE-89", "CWE-79", etc.
    suggested_fix: Optional[str] = None
```

**Security Categories:**
- `injection`: SQL injection (CWE-89)
- `xss`: Cross-site scripting (CWE-79)
- `command_injection`: OS command injection (CWE-78)
- `code_injection`: Code injection - eval/exec (CWE-95)
- `hardcoded_secrets`: Hardcoded credentials (CWE-798)

#### `QualityReport`

```python
@dataclass
class QualityReport:
    cyclomatic_complexity: int
    max_function_length: int
    max_nesting_depth: int
    comment_ratio: float  # 0-1
    quality_score: float  # 0-100
```

#### `DocumentationReport`

```python
@dataclass
class DocumentationReport:
    docstring_coverage: float  # 0-1
    comment_coverage: float  # 0-1
    completeness_score: float  # 0-100
    missing_docs: list[str]  # Function/class names
```

#### `TestCoverageReport`

```python
@dataclass
class TestCoverageReport:
    line_coverage: float  # 0-1
    branch_coverage: float  # 0-1
    function_coverage: float  # 0-1
    overall_coverage: float  # 0-1
    uncovered_lines: list[int]
```

---

## Exceptions

### `ValidationError`

Raised when validation fails unexpectedly.

```python
class ValidationError(Exception):
    def __init__(
        self,
        message: str,
        diagnostics: Optional[list[Diagnostic]] = None
    ):
        super().__init__(message)
        self.diagnostics = diagnostics or []
```

**Example:**
```python
try:
    result = validator.validate(code, language)
except ValidationError as e:
    print(f"Validation failed: {e}")
    for diag in e.diagnostics:
        print(f"  {diag.source}: {diag.message}")
```

### `RepairError`

Raised when repair fails after all attempts.

```python
class RepairError(Exception):
    def __init__(
        self,
        message: str,
        result: RepairResult
    ):
        super().__init__(message)
        self.result = result
```

**Example:**
```python
try:
    result = orchestrator.repair(code, prompt, grammar, language)
    if not result.success:
        raise RepairError("All repair attempts failed", result)
except RepairError as e:
    print(f"Repair failed: {e}")
    print(f"Attempts: {e.result.attempts}")
    print(f"Remaining issues: {len(e.result.diagnostics_remaining)}")
```

### `SandboxError`

Raised when sandbox execution fails.

```python
class SandboxError(Exception):
    def __init__(
        self,
        message: str,
        execution_result: Optional[ExecutionResult] = None
    ):
        super().__init__(message)
        self.execution_result = execution_result
```

---

## Usage Patterns

### Basic Validation Workflow

```python
from maze.validation.pipeline import ValidationPipeline, ValidationContext
from maze.validation.lint import LintRules

# Setup
pipeline = ValidationPipeline()
context = ValidationContext(
    lint_rules=LintRules.default(),
    tests='def test(): pass'
)

# Validate
result = pipeline.validate(code, 'python', context)

# Handle results
if result.success:
    print(f"✓ Validation passed ({result.validation_time_ms:.2f}ms)")
else:
    for diag in result.diagnostics:
        print(f"[{diag.source}] Line {diag.line}: {diag.message}")
```

### Repair Loop Workflow

```python
from maze.repair.orchestrator import RepairOrchestrator, RepairContext

# Setup
orchestrator = RepairOrchestrator(
    validator=pipeline,
    learning_enabled=True
)

# Repair
result = orchestrator.repair(
    code=broken_code,
    prompt=original_prompt,
    grammar=constraint_grammar,
    language='python',
    context=RepairContext(max_attempts=3)
)

# Handle results
if result.success:
    print(f"Fixed in {result.attempts} attempts")
    use_code(result.repaired_code)
else:
    print(f"Failed after {result.attempts} attempts")
    for diag in result.diagnostics_remaining:
        print(f"  {diag.message}")
```

### Security Review Workflow

```python
from maze.integrations.pedantic_raven import (
    PedanticRavenIntegration,
    ReviewRules
)

# Setup
raven = PedanticRavenIntegration(ReviewRules.strict())

# Review
result = raven.review(code, 'python', tests)

# Handle critical security issues
critical = [f for f in result.security_findings if f.severity == "critical"]
if critical:
    print("Critical security issues found:")
    for finding in critical:
        print(f"  {finding.message} (CWE-{finding.cwe_id})")
        print(f"  Fix: {finding.suggested_fix}")
    raise SecurityError("Critical vulnerabilities detected")

# Check quality
if result.quality_report.quality_score < 70:
    print("Code quality below threshold")
```

### Complete Validation + Repair Pipeline

```python
# Validate
val_result = pipeline.validate(code, language, context)

# Repair if needed
if not val_result.success:
    repair_result = orchestrator.repair(
        code=code,
        prompt=prompt,
        grammar=grammar,
        language=language,
        context=RepairContext(validation_context=context)
    )

    if repair_result.success:
        code = repair_result.repaired_code
        print(f"Repaired in {repair_result.attempts} attempts")
    else:
        raise RepairError("All repair attempts failed", repair_result)

# Final security review
review = raven.review(code, language, context.tests)
if not review.success:
    raise SecurityError("Security review failed")

# Use validated code
print("Code is validated and secure")
return code
```

---

## Performance Characteristics

| Component | Target | Typical | Notes |
|-----------|--------|---------|-------|
| SyntaxValidator | <50ms | 0-5ms | LRU cached |
| TypeValidator | <200ms | 100-200ms | External tool |
| TestValidator | <5s | 1-3s | Depends on tests |
| LintValidator | <100ms | 0-10ms | LRU cached |
| ValidationPipeline | <500ms | 200-450ms | Excludes tests |
| RepairOrchestrator | <2s/iteration | 400-1500ms | Includes validation |
| PedanticRaven | <1s | 100-500ms | Pattern matching |

**Cache Performance:**
- Cold cache: First run (slower)
- Warm cache: 2-10x faster for repeated validations

**Parallel Validation:**
- Syntax + Lint: Up to 2x faster when both needed
- Requires `parallel_validation=True`

---

## Language Support

### Fully Supported

All components support these languages:

- **Python** (3.8+)
- **TypeScript** (5.0+)
- **Rust** (1.70+)
- **Go** (1.20+)
- **Zig** (0.11+)

### Tool Requirements

| Language | Syntax | Types | Tests | Lint |
|----------|--------|-------|-------|------|
| Python | ast (built-in) | pyright | pytest | ruff |
| TypeScript | tsc | tsc | jest/vitest | eslint |
| Rust | cargo | cargo | cargo | clippy |
| Go | go | go | go | golangci-lint |
| Zig | zig | zig | zig | zig fmt |

---

## Integration with Phase 2 & 3

Phase 4 components include protocol-based integration points:

### ConstraintSynthesizer Protocol (Phase 2)

```python
class ConstraintSynthesizer(Protocol):
    def synthesize_from_diagnostics(
        self,
        diagnostics: list[Diagnostic],
        language: str
    ) -> ConstraintRefinement:
        ...
```

**Usage in RepairOrchestrator:**
```python
if self.synthesizer:
    refinement = self.synthesizer.synthesize_from_diagnostics(
        diagnostics, language
    )
```

### CodeGenerator Protocol (Phase 3)

```python
class CodeGenerator(Protocol):
    def generate(
        self,
        prompt: str,
        grammar: str,
        language: str,
        constraints: Optional[dict] = None
    ) -> str:
        ...
```

**Usage in RepairOrchestrator:**
```python
if self.generator:
    repaired = self.generator.generate(
        prompt, refined_grammar, language
    )
```

---

## Best Practices

### 1. Use ValidationContext for Configuration

```python
# Good
context = ValidationContext(
    lint_rules=LintRules.strict(),
    tests=test_code,
    timeout_ms=10000
)
result = pipeline.validate(code, 'python', context)

# Avoid
result = pipeline.validate(code, 'python')  # Uses defaults
```

### 2. Enable Parallel Validation

```python
# Good
pipeline = ValidationPipeline(parallel_validation=True)

# Slower
pipeline = ValidationPipeline(parallel_validation=False)
```

### 3. Set Appropriate Timeouts

```python
# Good - match to expected execution time
sandbox = RuneExecutor(timeout_ms=10000)  # 10s for integration tests

# Bad - too short for integration tests
sandbox = RuneExecutor(timeout_ms=1000)  # 1s
```

### 4. Handle Diagnostics Gracefully

```python
# Good
if not result.success:
    for diag in result.diagnostics:
        if diag.level == "error":
            log_error(f"{diag.source}:{diag.line} - {diag.message}")
        if diag.suggested_fix:
            apply_fix(diag.suggested_fix)

# Avoid
if not result.success:
    raise Exception("Validation failed")  # Loses diagnostic info
```

### 5. Use Strict Rules in CI

```python
# Development
dev_rules = LintRules.default()

# Production/CI
prod_rules = LintRules.strict()
raven_rules = ReviewRules.strict()
```

### 6. Enable Learning for Repeated Repairs

```python
# Good
orchestrator = RepairOrchestrator(
    validator=pipeline,
    learning_enabled=True  # Learns patterns
)

# Slower for repeated repairs
orchestrator = RepairOrchestrator(
    validator=pipeline,
    learning_enabled=False
)
```

### 7. Clean Up Resources

```python
# Good
sandbox = RuneExecutor()
try:
    result = sandbox.execute(code, tests, 'python')
finally:
    sandbox.cleanup()

# Or use context manager (if available)
with RuneExecutor() as sandbox:
    result = sandbox.execute(code, tests, 'python')
```

---

## See Also

- [README.md](./README.md) - Usage guide and examples
- [Phase 4 Spec](../../specs/phase4-full-spec.md) - Complete specification
- [Benchmarks](../../benchmarks/validation_benchmark.py) - Performance tests
- [Integration Tests](../../tests/integration/test_validation_integration.py) - E2E examples

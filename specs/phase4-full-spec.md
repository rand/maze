# Phase 4: Validation & Repair - Full Specification

## Table of Contents

1. [Component Decomposition](#component-decomposition)
2. [Detailed Interfaces](#detailed-interfaces)
3. [Data Structures](#data-structures)
4. [Test Plan](#test-plan)
5. [Dependencies](#dependencies)
6. [Traceability Matrix](#traceability-matrix)

## Component Decomposition

### Component 4.1: Syntax Validator

**Purpose**: Fast syntax validation using language-specific parsers.

**Responsibilities**:
- Parse code using tree-sitter or native parsers
- Extract syntax errors with line/column precision
- Provide suggested fixes for common errors
- Cache parse trees for reuse
- Support TypeScript, Python, Rust, Go, Zig

**Interface**:
```python
class SyntaxValidator:
    """Fast syntax validation using tree-sitter and native parsers."""

    def __init__(self, cache_size: int = 1000):
        """
        Initialize syntax validator.

        Args:
            cache_size: Maximum parse tree cache size
        """
        self.parsers: dict[str, Any] = {}
        self.parse_cache: dict[str, tuple[bool, list[Diagnostic]]] = {}
        self.cache_size = cache_size

    def validate(self, code: str, language: str) -> SyntaxValidationResult:
        """
        Validate syntax of code.

        Args:
            code: Source code to validate
            language: Programming language

        Returns:
            Validation result with diagnostics

        Example:
            >>> validator = SyntaxValidator()
            >>> result = validator.validate("const x = ", "typescript")
            >>> assert not result.success
            >>> assert len(result.diagnostics) > 0
        """

    def parse(self, code: str, language: str) -> Optional[Any]:
        """
        Parse code and return AST.

        Args:
            code: Source code
            language: Programming language

        Returns:
            Parsed AST or None if parse fails
        """

    def extract_errors(self, tree: Any, code: str, language: str) -> list[Diagnostic]:
        """
        Extract syntax errors from parse tree.

        Args:
            tree: Parse tree
            code: Original source code
            language: Programming language

        Returns:
            List of syntax diagnostics
        """

    def suggest_fix(self, error: Diagnostic, code: str, language: str) -> Optional[str]:
        """
        Suggest fix for syntax error.

        Args:
            error: Syntax error diagnostic
            code: Original source code
            language: Programming language

        Returns:
            Suggested fix or None
        """

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics."""

    def clear_cache(self) -> None:
        """Clear parse cache."""
```

**Implementation Details**:
- **Tree-sitter**: Primary parser (fast, error-tolerant)
- **Native parsers**: Fallback for language-specific features
  - TypeScript: `tsc --noEmit --pretty false`
  - Python: `ast.parse()` + pyright
  - Rust: `cargo check --message-format json`
  - Go: `go build -o /dev/null`
  - Zig: `zig ast-check`
- **Error extraction**: Map tree-sitter error nodes to diagnostics
- **Caching**: Hash code → (success, diagnostics)
- **Suggested fixes**: Pattern-based for common errors (missing semicolon, unmatched braces, etc.)

**Test Coverage**: 20 tests
- Parse valid code (5 languages)
- Detect syntax errors (missing semicolon, unmatched braces, etc.)
- Extract error locations
- Suggest fixes for common errors
- Cache hit/miss behavior
- Performance (parse 1000 lines <50ms)

---

### Component 4.2: Type Validator

**Purpose**: Type checking using language-specific type systems and services.

**Responsibilities**:
- Run type checkers (pyright, tsc, rust-analyzer)
- Parse type error output
- Map errors to source locations
- Integrate with Phase 3 type system for TypeScript
- Provide type-aware suggested fixes

**Interface**:
```python
class TypeValidator:
    """Type validation using language-specific type checkers."""

    def __init__(self, type_system: Optional[TypeSystemOrchestrator] = None):
        """
        Initialize type validator.

        Args:
            type_system: Optional type system from Phase 3
        """
        self.type_system = type_system
        self.checkers: dict[str, Callable] = {}

    def validate(self, code: str, language: str, context: TypeContext) -> TypeValidationResult:
        """
        Validate types in code.

        Args:
            code: Source code to validate
            language: Programming language
            context: Type context

        Returns:
            Validation result with type diagnostics

        Example:
            >>> validator = TypeValidator()
            >>> context = TypeContext(variables={"x": Type("number")})
            >>> result = validator.validate('const y: string = x;', "typescript", context)
            >>> assert not result.success
            >>> assert "string" in result.diagnostics[0].message
        """

    def check_typescript(self, code: str, context: TypeContext) -> list[Diagnostic]:
        """TypeScript type checking using Phase 3 type system."""

    def check_python(self, code: str, context: TypeContext) -> list[Diagnostic]:
        """Python type checking using pyright."""

    def check_rust(self, code: str, context: TypeContext) -> list[Diagnostic]:
        """Rust type checking using rust-analyzer."""

    def check_go(self, code: str, context: TypeContext) -> list[Diagnostic]:
        """Go type checking using go build."""

    def check_zig(self, code: str, context: TypeContext) -> list[Diagnostic]:
        """Zig type checking using zig build-obj."""

    def parse_type_errors(self, output: str, language: str) -> list[Diagnostic]:
        """
        Parse type checker output into diagnostics.

        Args:
            output: Raw type checker output
            language: Programming language

        Returns:
            List of type diagnostics
        """

    def suggest_type_fix(self, error: Diagnostic, code: str, context: TypeContext) -> Optional[str]:
        """
        Suggest fix for type error.

        Args:
            error: Type error diagnostic
            code: Original source code
            context: Type context

        Returns:
            Suggested type annotation or cast
        """
```

**Implementation Details**:
- **TypeScript**: Use Phase 3 type system for fast checking, fallback to `tsc`
- **Python**: Run `pyright --outputjson`
- **Rust**: Run `cargo check --message-format json`
- **Go**: Run `go build` and parse errors
- **Zig**: Run `zig build-obj` and parse errors
- **Error parsing**: Language-specific regex/JSON parsers
- **Suggested fixes**:
  - Missing type annotations
  - Type casts for assignability
  - Generic type parameters

**Test Coverage**: 20 tests
- Detect type mismatches (5 languages)
- Detect missing type annotations
- Detect invalid generic instantiations
- Parse type checker output correctly
- Suggest type fixes
- Integration with Phase 3 type system
- Performance (<200ms for 500 lines)

---

### Component 4.3: Test Validator

**Purpose**: Execute tests in sandboxed environment and report failures.

**Responsibilities**:
- Execute unit and integration tests
- Capture test output (stdout, stderr)
- Parse test results (pass/fail, error messages)
- Enforce timeouts and resource limits
- Support multiple test frameworks (pytest, jest, cargo test, go test, zig test)

**Interface**:
```python
class TestValidator:
    """Test execution and validation in sandboxed environment."""

    def __init__(self, sandbox: RuneExecutor):
        """
        Initialize test validator.

        Args:
            sandbox: RUNE sandbox executor
        """
        self.sandbox = sandbox
        self.test_parsers: dict[str, Callable] = {}

    def validate(self, code: str, tests: str, language: str, timeout_ms: int = 5000) -> TestValidationResult:
        """
        Run tests and validate results.

        Args:
            code: Source code
            tests: Test code
            language: Programming language
            timeout_ms: Maximum execution time

        Returns:
            Test results with diagnostics

        Example:
            >>> sandbox = RuneExecutor()
            >>> validator = TestValidator(sandbox)
            >>> result = validator.validate(
            ...     code="def add(a, b): return a - b",
            ...     tests="def test_add(): assert add(2, 3) == 5",
            ...     language="python"
            ... )
            >>> assert not result.success
        """

    def run_tests(self, code: str, tests: str, language: str, timeout_ms: int) -> ExecutionResult:
        """
        Execute tests in sandbox.

        Args:
            code: Source code
            tests: Test code
            language: Programming language
            timeout_ms: Timeout in milliseconds

        Returns:
            Execution result from sandbox
        """

    def parse_test_results(self, output: str, language: str) -> TestResults:
        """
        Parse test framework output.

        Args:
            output: Test output
            language: Programming language

        Returns:
            Parsed test results
        """

    def extract_test_failures(self, results: TestResults) -> list[Diagnostic]:
        """
        Convert test failures to diagnostics.

        Args:
            results: Parsed test results

        Returns:
            List of test failure diagnostics
        """
```

**Implementation Details**:
- **Sandbox execution**: Use RUNE for all test runs
- **Test frameworks**:
  - Python: pytest
  - TypeScript: jest, vitest
  - Rust: cargo test
  - Go: go test
  - Zig: zig test
- **Output parsing**: Framework-specific parsers
  - pytest: JSON output (`--json-report`)
  - jest: JSON output (`--json`)
  - cargo test: JSON output (`--message-format json`)
- **Timeout enforcement**: Kill tests after timeout
- **Resource limits**: Memory and CPU limits from sandbox

**Test Coverage**: 15 tests
- Run passing tests (5 languages)
- Detect failing tests
- Parse test output correctly
- Enforce timeouts
- Enforce resource limits
- Multiple test cases
- Integration tests

---

### Component 4.4: Lint Validator

**Purpose**: Style and quality validation using linters.

**Responsibilities**:
- Run language-specific linters
- Parse linter output
- Support configurable rules
- Provide auto-fix suggestions
- Cache lint results

**Interface**:
```python
class LintValidator:
    """Style and quality validation using linters."""

    def __init__(self, rules: Optional[LintRules] = None, cache_size: int = 500):
        """
        Initialize lint validator.

        Args:
            rules: Linting rules configuration
            cache_size: Maximum cache size
        """
        self.rules = rules or LintRules.default()
        self.linters: dict[str, str] = {
            "python": "ruff",
            "typescript": "eslint",
            "rust": "clippy",
            "go": "golangci-lint",
            "zig": "zig fmt --check"
        }
        self.cache: dict[str, list[Diagnostic]] = {}

    def validate(self, code: str, language: str, rules: Optional[LintRules] = None) -> LintValidationResult:
        """
        Lint code for style and quality issues.

        Args:
            code: Source code
            language: Programming language
            rules: Optional override rules

        Returns:
            Lint validation result

        Example:
            >>> validator = LintValidator()
            >>> result = validator.validate("x=1+2", "python")
            >>> assert any("whitespace" in d.message.lower() for d in result.diagnostics)
        """

    def run_linter(self, code: str, language: str, rules: LintRules) -> str:
        """
        Run linter and return output.

        Args:
            code: Source code
            language: Programming language
            rules: Linting rules

        Returns:
            Raw linter output
        """

    def parse_lint_output(self, output: str, language: str) -> list[Diagnostic]:
        """
        Parse linter output to diagnostics.

        Args:
            output: Linter output
            language: Programming language

        Returns:
            List of lint diagnostics
        """

    def auto_fix(self, code: str, language: str) -> str:
        """
        Apply auto-fixable lint suggestions.

        Args:
            code: Source code
            language: Programming language

        Returns:
            Auto-fixed code
        """
```

**Implementation Details**:
- **Linters**:
  - Python: ruff (fast, comprehensive)
  - TypeScript: eslint with TypeScript plugin
  - Rust: clippy
  - Go: golangci-lint
  - Zig: zig fmt
- **Output parsing**: JSON output where available
- **Auto-fix**: Use linter's built-in auto-fix when available
- **Caching**: Hash code + rules → diagnostics
- **Rule configuration**: Per-language rule sets

**Test Coverage**: 10 tests
- Detect style violations (5 languages)
- Parse linter output
- Apply auto-fixes
- Custom rule configuration
- Cache behavior

---

### Component 4.5: RUNE Sandbox Integration

**Purpose**: Safe, isolated execution environment for tests and validation.

**Responsibilities**:
- Filesystem isolation (tmpfs, no project writes)
- Network isolation (no external connections)
- Resource limits (CPU, memory, time)
- Process isolation (cgroups, namespaces)
- Security violation detection

**Interface**:
```python
class RuneExecutor:
    """Sandboxed code execution using RUNE."""

    def __init__(
        self,
        timeout_ms: int = 5000,
        memory_limit_mb: int = 512,
        cpu_limit_percent: int = 100,
        network_enabled: bool = False,
        allowed_syscalls: Optional[list[str]] = None
    ):
        """
        Initialize RUNE executor.

        Args:
            timeout_ms: Maximum execution time
            memory_limit_mb: Maximum memory usage
            cpu_limit_percent: CPU usage limit (0-100)
            network_enabled: Allow network access
            allowed_syscalls: Whitelist of allowed syscalls
        """
        self.config = RuneConfig(
            timeout_ms=timeout_ms,
            memory_limit_mb=memory_limit_mb,
            cpu_limit_percent=cpu_limit_percent,
            network_enabled=network_enabled,
            allowed_syscalls=allowed_syscalls or self._default_syscalls()
        )

    def execute(
        self,
        code: str,
        tests: str,
        language: str,
        timeout_ms: Optional[int] = None
    ) -> ExecutionResult:
        """
        Execute code and tests in sandbox.

        Args:
            code: Source code to execute
            tests: Test code
            language: Programming language
            timeout_ms: Override timeout

        Returns:
            Execution result with output and resource usage

        Example:
            >>> executor = RuneExecutor(timeout_ms=1000)
            >>> result = executor.execute(
            ...     code="def add(a, b): return a + b",
            ...     tests="assert add(2, 3) == 5",
            ...     language="python"
            ... )
            >>> assert result.success
        """

    def validate_security(self, code: str, language: str) -> list[SecurityIssue]:
        """
        Check for security vulnerabilities.

        Args:
            code: Source code
            language: Programming language

        Returns:
            List of security issues found
        """

    def check_resource_limits(self, result: ExecutionResult) -> list[str]:
        """
        Check if execution exceeded resource limits.

        Args:
            result: Execution result

        Returns:
            List of limit violations
        """

    def _default_syscalls(self) -> list[str]:
        """Get default allowed syscalls for safe execution."""
```

**Implementation Details**:
- **RUNE integration**: Use maze.integrations.rune package
- **Filesystem**: Mount tmpfs for /tmp, bind mount code read-only
- **Network**: Use network namespaces to block external access
- **Resources**: cgroups v2 for CPU/memory limits
- **Process**: PID namespaces to prevent fork bombs
- **Security**: seccomp-bpf syscall filtering
- **Monitoring**: Track CPU time, memory usage, syscalls
- **Cleanup**: Always cleanup temp dirs and kill processes

**Test Coverage**: 10 tests
- Basic execution (successful)
- Timeout enforcement
- Memory limit enforcement
- CPU limit enforcement
- Network isolation
- Filesystem isolation
- Security violation detection
- Process cleanup
- Multiple languages

---

### Component 4.6: Repair Orchestrator

**Purpose**: Adaptive repair loop with constraint learning and strategy selection.

**Responsibilities**:
- Analyze validation diagnostics
- Select repair strategy
- Refine constraints based on failures
- Regenerate code with tighter constraints
- Track repair patterns for learning
- Limit repair attempts

**Interface**:
```python
class RepairOrchestrator:
    """Adaptive repair loop with constraint learning."""

    def __init__(
        self,
        validator: ValidationPipeline,
        synthesizer: ConstraintSynthesizer,
        generator: ProviderAdapter,
        max_attempts: int = 3,
        learning_enabled: bool = True
    ):
        """
        Initialize repair orchestrator.

        Args:
            validator: Validation pipeline
            synthesizer: Constraint synthesizer from Phase 2
            generator: Provider adapter for regeneration
            max_attempts: Maximum repair attempts
            learning_enabled: Enable pattern learning
        """
        self.validator = validator
        self.synthesizer = synthesizer
        self.generator = generator
        self.max_attempts = max_attempts
        self.learning_enabled = learning_enabled
        self.repair_patterns: dict[str, ConstraintRefinement] = {}

    def repair(
        self,
        code: str,
        prompt: str,
        grammar: str,
        language: str,
        context: RepairContext,
        max_attempts: Optional[int] = None
    ) -> RepairResult:
        """
        Attempt to repair code with adaptive strategy.

        Args:
            code: Generated code with errors
            prompt: Original generation prompt
            grammar: Grammar used for generation
            language: Programming language
            context: Repair context (type context, test context, etc.)
            max_attempts: Override max attempts

        Returns:
            Repair result with final code or diagnostics

        Example:
            >>> orchestrator = RepairOrchestrator(validator, synthesizer, generator)
            >>> result = orchestrator.repair(
            ...     code="const x: number = 'hello';",
            ...     prompt="Create number variable",
            ...     grammar="...",
            ...     language="typescript",
            ...     context=RepairContext()
            ... )
            >>> assert result.success
        """

    def analyze_diagnostics(self, diagnostics: list[Diagnostic]) -> FailureAnalysis:
        """
        Extract root causes and patterns from diagnostics.

        Args:
            diagnostics: Validation diagnostics

        Returns:
            Failure analysis with categorized issues

        Analysis categories:
        - Syntax errors: missing tokens, malformed structure
        - Type errors: mismatches, missing annotations
        - Test errors: assertion failures, exceptions
        - Lint errors: style violations, complexity
        """

    def select_strategy(
        self,
        analysis: FailureAnalysis,
        attempt: int,
        previous_strategies: list[str]
    ) -> RepairStrategy:
        """
        Choose repair approach based on failures and attempt number.

        Args:
            analysis: Failure analysis
            attempt: Current attempt number
            previous_strategies: Previously tried strategies

        Returns:
            Selected repair strategy

        Strategies:
        - CONSTRAINT_TIGHTENING: Add regex/grammar rules
        - TYPE_NARROWING: Refine type constraints
        - EXAMPLE_BASED: Add positive examples
        - TEMPLATE_FALLBACK: Use structured template
        - SIMPLIFY: Reduce complexity
        """

    def refine_constraints(
        self,
        analysis: FailureAnalysis,
        strategy: RepairStrategy,
        grammar: str,
        context: RepairContext
    ) -> str:
        """
        Tighten grammar based on failures and strategy.

        Args:
            analysis: Failure analysis
            strategy: Selected repair strategy
            grammar: Current grammar
            context: Repair context

        Returns:
            Refined grammar

        Refinements:
        - Add forbidden patterns (for repeated errors)
        - Narrow type constraints
        - Add mandatory structure
        - Include positive examples
        """

    def learn_pattern(
        self,
        failure: FailureAnalysis,
        successful_refinement: ConstraintRefinement
    ) -> None:
        """
        Store successful repair pattern for reuse.

        Args:
            failure: Original failure analysis
            successful_refinement: Constraint refinement that fixed the issue
        """

    def get_repair_stats(self) -> dict[str, Any]:
        """Get repair statistics and learned patterns."""
```

**Implementation Details**:
- **Diagnostic analysis**: Group by type, extract common patterns
- **Strategy selection**:
  - Attempt 1: Constraint tightening (fastest)
  - Attempt 2: Type narrowing or example-based
  - Attempt 3: Template fallback (most conservative)
- **Constraint refinement**:
  - Syntax errors → Add structure requirements
  - Type errors → Narrow type constraints
  - Test errors → Add example constraints
  - Lint errors → Add style rules
- **Pattern learning**: Store (failure_pattern → refinement) mappings
- **Reuse**: Check learned patterns before analysis
- **Limits**: Fail after max_attempts with diagnostics

**Test Coverage**: 15 tests
- Analyze various diagnostic types
- Select appropriate strategies
- Refine constraints effectively
- Learn and reuse patterns
- Respect max attempts
- Integration with validation pipeline
- Integration with constraint synthesis

---

### Component 4.7: pedantic_raven Integration

**Purpose**: Final quality gate with comprehensive code review.

**Responsibilities**:
- Code review rules enforcement
- Security vulnerability scanning
- Performance anti-pattern detection
- Documentation completeness checking
- Test coverage validation

**Interface**:
```python
class PedanticRavenIntegration:
    """Code quality and security enforcement using pedantic_raven."""

    def __init__(self, rules: Optional[ReviewRules] = None):
        """
        Initialize pedantic_raven integration.

        Args:
            rules: Custom review rules (defaults to strict)
        """
        self.rules = rules or ReviewRules.strict()

    def review(
        self,
        code: str,
        language: str,
        rules: Optional[ReviewRules] = None
    ) -> ReviewResult:
        """
        Comprehensive code review.

        Args:
            code: Source code to review
            language: Programming language
            rules: Optional override rules

        Returns:
            Review result with findings and quality metrics

        Example:
            >>> raven = PedanticRavenIntegration()
            >>> result = raven.review(
            ...     code="def process(data): eval(data)",
            ...     language="python"
            ... )
            >>> assert any(f.category == "security" for f in result.findings)
        """

    def check_security(self, code: str, language: str) -> list[SecurityFinding]:
        """
        Security-focused review.

        Checks:
        - SQL injection vulnerabilities
        - XSS vulnerabilities
        - Command injection
        - Path traversal
        - Hardcoded credentials
        - Unsafe deserialization
        - Insecure random
        """

    def check_quality(self, code: str, language: str) -> QualityReport:
        """
        Code quality metrics.

        Metrics:
        - Cyclomatic complexity
        - Code duplication
        - Function length
        - Parameter count
        - Nesting depth
        - Comment ratio
        """

    def check_performance(self, code: str, language: str) -> list[PerformanceFinding]:
        """
        Performance anti-patterns.

        Patterns:
        - N+1 query patterns
        - Inefficient loops
        - Unnecessary allocations
        - Missing indexes (SQL)
        - Blocking calls in async
        """

    def check_documentation(self, code: str, language: str) -> DocumentationReport:
        """
        Documentation completeness.

        Checks:
        - Docstring presence
        - Parameter documentation
        - Return type documentation
        - Example presence
        - Type hints (Python, TypeScript)
        """

    def check_test_coverage(self, code: str, tests: str, language: str) -> CoverageReport:
        """
        Test coverage analysis.

        Coverage:
        - Line coverage
        - Branch coverage
        - Function coverage
        - Critical path coverage
        """
```

**Implementation Details**:
- **pedantic_raven**: Use maze.integrations.pedantic_raven package
- **Security rules**: OWASP Top 10 patterns
- **Quality metrics**: Standard code metrics (cyclomatic complexity, etc.)
- **Performance patterns**: Language-specific anti-patterns
- **Documentation**: Parse docstrings/comments
- **Coverage**: Run coverage tools (coverage.py, nyc, tarpaulin)

**Test Coverage**: 10 tests
- Detect security vulnerabilities
- Calculate quality metrics
- Detect performance anti-patterns
- Check documentation completeness
- Calculate test coverage
- Custom rule configuration

---

### Component 4.8: Validation Pipeline

**Purpose**: Orchestrate multi-level validation with early exit.

**Responsibilities**:
- Run validators in order (syntax → types → tests → lint)
- Early exit on success
- Collect comprehensive diagnostics on failure
- Parallel validation where safe
- Cache results

**Interface**:
```python
class ValidationPipeline:
    """Multi-level validation pipeline with early exit."""

    def __init__(
        self,
        syntax_validator: SyntaxValidator,
        type_validator: TypeValidator,
        test_validator: TestValidator,
        lint_validator: LintValidator,
        pedantic_raven: Optional[PedanticRavenIntegration] = None,
        parallel_validation: bool = True
    ):
        """
        Initialize validation pipeline.

        Args:
            syntax_validator: Syntax validator
            type_validator: Type validator
            test_validator: Test validator
            lint_validator: Lint validator
            pedantic_raven: Optional final quality gate
            parallel_validation: Run syntax and lint in parallel
        """
        self.syntax_validator = syntax_validator
        self.type_validator = type_validator
        self.test_validator = test_validator
        self.lint_validator = lint_validator
        self.pedantic_raven = pedantic_raven
        self.parallel_validation = parallel_validation

    def validate(
        self,
        code: str,
        language: str,
        context: ValidationContext,
        stages: Optional[list[str]] = None
    ) -> ValidationResult:
        """
        Run validation pipeline.

        Args:
            code: Source code to validate
            language: Programming language
            context: Validation context (types, tests, rules)
            stages: Stages to run (default: all)

        Returns:
            Combined validation result

        Example:
            >>> pipeline = ValidationPipeline(syntax, types, tests, lint)
            >>> context = ValidationContext(
            ...     type_context=TypeContext(),
            ...     tests="def test_foo(): assert foo() == 42",
            ...     lint_rules=LintRules.default()
            ... )
            >>> result = pipeline.validate(code, "python", context)
            >>> assert result.success or len(result.diagnostics) > 0
        """

    def validate_syntax(self, code: str, language: str) -> list[Diagnostic]:
        """Quick syntax-only validation."""

    def validate_types(
        self,
        code: str,
        language: str,
        context: TypeContext
    ) -> list[Diagnostic]:
        """Type validation only."""

    def validate_tests(
        self,
        code: str,
        tests: str,
        language: str,
        timeout_ms: int = 5000
    ) -> TestResult:
        """Test execution only."""

    def validate_lint(
        self,
        code: str,
        language: str,
        rules: LintRules
    ) -> list[Diagnostic]:
        """Lint validation only."""

    def get_pipeline_stats(self) -> dict[str, Any]:
        """Get validation statistics."""
```

**Implementation Details**:
- **Execution order**: syntax → types → tests → lint → pedantic_raven
- **Early exit**: Stop at first success (all stages pass)
- **Parallel**: Run syntax + lint in parallel if enabled
- **Diagnostics**: Collect from all failed stages
- **Timing**: Track time per stage
- **Caching**: Delegate to individual validators

**Test Coverage**: 10 tests
- All stages pass
- Each stage fails independently
- Multiple stage failures
- Parallel validation
- Stage selection
- Performance (<500ms without tests)

---

## Data Structures

```python
from dataclasses import dataclass
from typing import Optional, Literal, Any
from enum import Enum

# Diagnostics

@dataclass
class Diagnostic:
    """Validation diagnostic (error, warning, info)."""
    level: Literal["error", "warning", "info"]
    message: str
    line: int
    column: int
    code: Optional[str] = None
    source: str = ""  # "syntax", "type", "test", "lint", "security"
    suggested_fix: Optional[str] = None
    context: Optional[str] = None  # Surrounding code

# Validation Results

@dataclass
class SyntaxValidationResult:
    """Result of syntax validation."""
    success: bool
    diagnostics: list[Diagnostic]
    parse_tree: Optional[Any] = None
    validation_time_ms: float = 0.0

@dataclass
class TypeValidationResult:
    """Result of type validation."""
    success: bool
    diagnostics: list[Diagnostic]
    type_errors: list[str]
    validation_time_ms: float = 0.0

@dataclass
class TestResults:
    """Parsed test results."""
    passed: int
    failed: int
    skipped: int
    errors: int
    failures: list[dict[str, Any]]  # name, message, traceback

@dataclass
class TestValidationResult:
    """Result of test validation."""
    success: bool
    diagnostics: list[Diagnostic]
    test_results: TestResults
    execution_time_ms: float = 0.0

@dataclass
class LintValidationResult:
    """Result of lint validation."""
    success: bool
    diagnostics: list[Diagnostic]
    auto_fixable: list[Diagnostic]
    validation_time_ms: float = 0.0

@dataclass
class ValidationResult:
    """Combined validation result."""
    success: bool
    diagnostics: list[Diagnostic]
    validation_time_ms: float
    stages_passed: list[str]  # ["syntax", "types", ...]
    stages_failed: list[str]

# Execution

@dataclass
class ResourceUsage:
    """Resource usage metrics."""
    cpu_time_ms: float
    memory_peak_mb: float
    syscalls: int

@dataclass
class ExecutionResult:
    """Sandboxed execution result."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: float
    resource_usage: ResourceUsage
    security_violations: list[str]
    timeout: bool = False

# Repair

class RepairStrategy(Enum):
    """Repair strategies."""
    CONSTRAINT_TIGHTENING = "constraint_tightening"
    TYPE_NARROWING = "type_narrowing"
    EXAMPLE_BASED = "example_based"
    TEMPLATE_FALLBACK = "template_fallback"
    SIMPLIFY = "simplify"

@dataclass
class FailureAnalysis:
    """Analysis of validation failures."""
    syntax_errors: list[Diagnostic]
    type_errors: list[Diagnostic]
    test_errors: list[Diagnostic]
    lint_errors: list[Diagnostic]
    root_causes: list[str]
    failure_patterns: list[str]
    severity: Literal["low", "medium", "high"]

@dataclass
class ConstraintRefinement:
    """Constraint refinement for repair."""
    original_grammar: str
    refined_grammar: str
    refinement_type: str  # "regex", "structure", "type", "example"
    description: str

@dataclass
class RepairResult:
    """Result of repair attempt."""
    success: bool
    repaired_code: Optional[str]
    attempts: int
    strategies_used: list[str]
    diagnostics_resolved: list[Diagnostic]
    diagnostics_remaining: list[Diagnostic]
    repair_time_ms: float
    constraint_refinements: list[ConstraintRefinement]
    learned_patterns: list[str]

# pedantic_raven

@dataclass
class SecurityFinding:
    """Security vulnerability finding."""
    category: str  # "injection", "xss", "auth", etc.
    severity: Literal["critical", "high", "medium", "low"]
    message: str
    line: int
    cwe_id: Optional[str] = None
    suggested_fix: Optional[str] = None

@dataclass
class PerformanceFinding:
    """Performance anti-pattern finding."""
    pattern: str  # "n_plus_one", "inefficient_loop", etc.
    impact: Literal["high", "medium", "low"]
    message: str
    line: int
    suggested_fix: Optional[str] = None

@dataclass
class QualityReport:
    """Code quality metrics."""
    cyclomatic_complexity: float
    code_duplication: float
    average_function_length: float
    max_nesting_depth: int
    comment_ratio: float
    quality_score: float  # 0-100

@dataclass
class DocumentationReport:
    """Documentation completeness."""
    functions_documented: int
    functions_total: int
    parameters_documented: int
    parameters_total: int
    return_types_documented: int
    returns_total: int
    examples_present: int
    completeness_score: float  # 0-100

@dataclass
class CoverageReport:
    """Test coverage metrics."""
    line_coverage: float  # 0-100
    branch_coverage: float  # 0-100
    function_coverage: float  # 0-100
    critical_path_coverage: float  # 0-100

@dataclass
class ReviewResult:
    """Comprehensive code review result."""
    passed: bool
    security_findings: list[SecurityFinding]
    performance_findings: list[PerformanceFinding]
    quality_report: QualityReport
    documentation_report: DocumentationReport
    coverage_report: Optional[CoverageReport]
    overall_score: float  # 0-100

# Contexts

@dataclass
class ValidationContext:
    """Context for validation."""
    type_context: TypeContext
    tests: Optional[str] = None
    lint_rules: Optional[LintRules] = None
    timeout_ms: int = 5000

@dataclass
class RepairContext:
    """Context for repair."""
    type_context: TypeContext
    validation_context: ValidationContext
    original_prompt: str
    max_attempts: int = 3

# Configuration

@dataclass
class LintRules:
    """Linting rules configuration."""
    max_line_length: int = 100
    max_complexity: int = 10
    require_docstrings: bool = True
    require_type_hints: bool = True
    custom_rules: dict[str, Any] = None

    @staticmethod
    def default() -> "LintRules":
        """Default lenient rules."""
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

@dataclass
class ReviewRules:
    """Code review rules configuration."""
    check_security: bool = True
    check_performance: bool = True
    check_quality: bool = True
    check_documentation: bool = True
    check_coverage: bool = False
    min_quality_score: float = 70.0
    min_coverage: float = 80.0
    block_on_critical_security: bool = True

    @staticmethod
    def strict() -> "ReviewRules":
        """Strict review rules."""
        return ReviewRules(
            check_security=True,
            check_performance=True,
            check_quality=True,
            check_documentation=True,
            check_coverage=True,
            min_quality_score=80.0,
            min_coverage=80.0,
            block_on_critical_security=True
        )

@dataclass
class RuneConfig:
    """RUNE sandbox configuration."""
    timeout_ms: int = 5000
    memory_limit_mb: int = 512
    cpu_limit_percent: int = 100
    network_enabled: bool = False
    allowed_syscalls: list[str] = None
```

## Test Plan

### Unit Tests (80+ tests)

**Component 4.1: SyntaxValidator (20 tests)**
- test_parse_valid_python
- test_parse_valid_typescript
- test_parse_valid_rust
- test_parse_valid_go
- test_parse_valid_zig
- test_detect_missing_semicolon
- test_detect_unmatched_braces
- test_detect_invalid_syntax
- test_extract_error_locations
- test_suggest_fix_missing_semicolon
- test_suggest_fix_unmatched_braces
- test_cache_hit
- test_cache_miss
- test_cache_eviction
- test_parse_performance_1000_lines
- test_multiple_syntax_errors
- test_unicode_handling
- test_multiline_errors
- test_tree_sitter_fallback
- test_clear_cache

**Component 4.2: TypeValidator (20 tests)**
- test_typescript_type_mismatch
- test_typescript_missing_annotation
- test_typescript_invalid_generic
- test_python_type_error_pyright
- test_python_missing_type_hint
- test_rust_type_error
- test_rust_lifetime_error
- test_go_type_mismatch
- test_zig_type_error
- test_parse_tsc_output
- test_parse_pyright_json
- test_parse_rust_analyzer_json
- test_suggest_type_annotation
- test_suggest_type_cast
- test_integration_with_phase3_types
- test_performance_500_lines
- test_multiple_type_errors
- test_generic_type_errors
- test_union_type_errors
- test_nullable_type_errors

**Component 4.3: TestValidator (15 tests)**
- test_run_passing_python_tests
- test_run_failing_python_tests
- test_run_passing_typescript_tests
- test_run_failing_rust_tests
- test_enforce_timeout
- test_enforce_memory_limit
- test_parse_pytest_json
- test_parse_jest_json
- test_parse_cargo_test_json
- test_extract_test_failures
- test_multiple_test_failures
- test_test_exception_handling
- test_sandbox_integration
- test_resource_limit_violation
- test_network_isolation

**Component 4.4: LintValidator (10 tests)**
- test_python_style_violations
- test_typescript_eslint_violations
- test_rust_clippy_warnings
- test_go_lint_violations
- test_zig_fmt_violations
- test_auto_fix_python
- test_auto_fix_typescript
- test_custom_rules
- test_cache_lint_results
- test_parse_ruff_output

**Component 4.5: RuneExecutor (10 tests)**
- test_execute_python_success
- test_execute_typescript_success
- test_timeout_enforcement
- test_memory_limit_enforcement
- test_cpu_limit_enforcement
- test_network_isolation
- test_filesystem_isolation
- test_security_violation_detection
- test_process_cleanup
- test_resource_usage_tracking

**Component 4.6: RepairOrchestrator (15 tests)**
- test_analyze_syntax_errors
- test_analyze_type_errors
- test_analyze_test_errors
- test_analyze_lint_errors
- test_select_constraint_tightening_strategy
- test_select_type_narrowing_strategy
- test_select_template_fallback_strategy
- test_refine_constraints_syntax
- test_refine_constraints_types
- test_learn_repair_pattern
- test_reuse_learned_pattern
- test_max_attempts_limit
- test_successful_repair_loop
- test_failed_repair_loop
- test_repair_stats

**Component 4.7: PedanticRavenIntegration (10 tests)**
- test_detect_sql_injection
- test_detect_xss_vulnerability
- test_detect_command_injection
- test_calculate_quality_metrics
- test_detect_performance_antipatterns
- test_check_documentation_completeness
- test_calculate_test_coverage
- test_custom_review_rules
- test_block_on_critical_security
- test_overall_review_score

**Component 4.8: ValidationPipeline (10 tests)**
- test_all_stages_pass
- test_syntax_stage_fails
- test_type_stage_fails
- test_test_stage_fails
- test_lint_stage_fails
- test_multiple_stage_failures
- test_parallel_validation
- test_stage_selection
- test_pipeline_performance
- test_comprehensive_diagnostics

### Integration Tests (25+ tests)

**End-to-End Validation (10 tests)**
- test_validate_valid_python_e2e
- test_validate_invalid_python_e2e
- test_validate_valid_typescript_e2e
- test_validate_invalid_rust_e2e
- test_full_pipeline_with_pedantic_raven
- test_validation_with_all_stages
- test_validation_performance_target
- test_cross_language_validation
- test_large_codebase_validation
- test_incremental_validation

**Repair Loop Integration (10 tests)**
- test_repair_syntax_error
- test_repair_type_error
- test_repair_test_failure
- test_repair_lint_violation
- test_multi_stage_repair
- test_repair_with_constraint_learning
- test_repair_max_attempts
- test_repair_strategy_progression
- test_repair_with_pedantic_raven
- test_repair_performance_target

**Sandbox Integration (5 tests)**
- test_rune_with_validators
- test_rune_resource_limits
- test_rune_security_enforcement
- test_rune_cleanup
- test_rune_multi_language

### Property Tests (10+ tests)

**Repair Properties (5 tests)**
- test_repair_idempotence (repaired code should validate)
- test_constraint_monotonicity (refinements should be stricter)
- test_repair_convergence (should not oscillate)
- test_repair_determinism (same input → same output)
- test_max_attempts_respected

**Validation Properties (5 tests)**
- test_valid_code_always_passes
- test_invalid_code_has_diagnostics
- test_validation_order_independence (parallel stages)
- test_diagnostic_completeness (all errors found)
- test_resource_bounds_respected

### Performance Tests (5+ tests)

- test_syntax_validation_50ms
- test_type_validation_200ms
- test_lint_validation_100ms
- test_full_pipeline_500ms (excluding tests)
- test_repair_iteration_2s

## Dependencies

### Phase Dependencies

**Phase 1: Context Indexer**
- Type context for validation
- API contracts for testing
- Style rules for linting

**Phase 2: Constraint Synthesis**
- Grammar refinement for repair
- Constraint tightening patterns
- Template generation

**Phase 3: Type System**
- TypeScript type validation
- Type narrowing for repair
- Type-aware error messages

### External Dependencies

**RUNE Sandbox**
- Package: `maze.integrations.rune`
- Purpose: Safe code execution
- Interface: `RuneExecutor`

**pedantic_raven**
- Package: `maze.integrations.pedantic_raven`
- Purpose: Code quality enforcement
- Interface: `PedanticRavenIntegration`

**Language Tools**
- Python: pyright, ruff
- TypeScript: tsc, eslint
- Rust: rust-analyzer, clippy
- Go: go build, golangci-lint
- Zig: zig ast-check, zig fmt

**Parsing**
- tree-sitter: Fast syntax parsing
- JSON parsers for tool output

## Traceability Matrix

| Requirement | Component | Implementation | Tests | Status |
|-------------|-----------|----------------|-------|--------|
| REQ-4.1: Multi-level validation | ValidationPipeline | src/maze/validation/pipeline.py | test_validation_integration.py | Pending |
| REQ-4.2: Syntax validation <50ms | SyntaxValidator | src/maze/validation/syntax.py | test_syntax.py | Pending |
| REQ-4.3: Type validation <200ms | TypeValidator | src/maze/validation/types.py | test_types.py | Pending |
| REQ-4.4: Test execution with limits | TestValidator | src/maze/validation/tests.py | test_tests.py | Pending |
| REQ-4.5: Style enforcement | LintValidator | src/maze/validation/lint.py | test_lint.py | Pending |
| REQ-4.6: Sandbox isolation | RuneExecutor | src/maze/integrations/rune/__init__.py | test_rune.py | Pending |
| REQ-4.7: Adaptive repair <3 attempts | RepairOrchestrator | src/maze/repair/orchestrator.py | test_repair.py | Pending |
| REQ-4.8: >90% repair success | RepairOrchestrator | src/maze/repair/orchestrator.py | test_repair_integration.py | Pending |
| REQ-4.9: Quality enforcement | PedanticRavenIntegration | src/maze/integrations/pedantic_raven/__init__.py | test_pedantic_raven.py | Pending |
| REQ-4.10: Security scanning | PedanticRavenIntegration | src/maze/integrations/pedantic_raven/__init__.py | test_security.py | Pending |

## Success Criteria

**Correctness**:
- All 115+ tests passing
- Validation detects all known error types
- Repair fixes >90% of errors within 3 attempts
- No false positives in security scanning

**Performance**:
- Syntax validation: <50ms
- Type validation: <200ms
- Lint validation: <100ms
- Full pipeline: <500ms (excluding tests)
- Repair iteration: <2s
- Total repair: <10s

**Quality**:
- Code coverage: >85%
- Type coverage: 100%
- Documentation: Complete
- Integration: All components work together

## Edge Cases

**Validation**:
- Empty code
- Very large files (>10k lines)
- Unicode and special characters
- Multiple error locations
- Cascading errors
- Ambiguous error messages

**Repair**:
- Unrepairable errors (logic bugs)
- Conflicting constraints
- Timeout during repair
- Memory limits during regeneration
- No learned patterns available

**Sandbox**:
- Infinite loops
- Fork bombs
- Memory leaks
- File descriptor exhaustion
- Syscall flooding

**pedantic_raven**:
- False positives
- Context-dependent vulnerabilities
- Performance trade-offs
- Documentation standards variation

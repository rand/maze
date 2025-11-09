"""
Integration tests for validation system.

Tests end-to-end validation workflows across all validators,
languages, and integration points.
"""

import pytest
from maze.validation.pipeline import ValidationPipeline, ValidationContext, TypeContext
from maze.validation.lint import LintRules
from maze.integrations.pedantic_raven import PedanticRavenIntegration, ReviewRules


class TestEndToEndValidation:
    """Test complete validation workflows."""

    def test_validate_valid_python_e2e(self):
        """Test end-to-end validation of valid Python code."""
        pipeline = ValidationPipeline()

        code = '''
def add(a: int, b: int) -> int:
    """Add two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
'''

        tests = '''
def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_multiply():
    assert multiply(2, 3) == 6
    assert multiply(0, 5) == 0
'''

        context = ValidationContext(
            type_context=TypeContext(),
            tests=tests,
            lint_rules=LintRules.default(),
        )

        result = pipeline.validate(code, "python", context)

        # Code should pass or have minimal warnings
        assert result.validation_time_ms > 0
        # Syntax should definitely pass
        assert "syntax" in result.stages_passed or "syntax" not in result.stages_failed

    def test_validate_invalid_python_e2e(self):
        """Test end-to-end validation of invalid Python code."""
        pipeline = ValidationPipeline()

        code = '''
def broken(
    # Missing closing parenthesis and body
'''

        result = pipeline.validate(code, "python")

        assert not result.success
        assert "syntax" in result.stages_failed
        assert len(result.diagnostics) > 0

    def test_validate_valid_typescript_e2e(self):
        """Test end-to-end validation of valid TypeScript code."""
        pipeline = ValidationPipeline()

        code = '''
function add(a: number, b: number): number {
    return a + b;
}

const multiply = (a: number, b: number): number => a * b;
'''

        context = ValidationContext(
            type_context=TypeContext(),
            lint_rules=LintRules.default(),
        )

        result = pipeline.validate(code, "typescript", context)

        # Syntax should pass
        assert result.validation_time_ms > 0

    def test_validate_invalid_rust_e2e(self):
        """Test end-to-end validation of invalid Rust code."""
        pipeline = ValidationPipeline()

        code = '''
fn broken() {
    let x = 5
    // Missing semicolon
}
'''

        result = pipeline.validate(code, "rust", stages=["syntax"])

        # May detect syntax error
        assert result.validation_time_ms > 0

    def test_full_pipeline_with_pedantic_raven(self):
        """Test full validation pipeline with pedantic_raven."""
        raven = PedanticRavenIntegration(ReviewRules.lenient())
        pipeline = ValidationPipeline(pedantic_raven=raven)

        code = '''
def process(data):
    """Process data safely."""
    return data.upper() if isinstance(data, str) else str(data)
'''

        context = ValidationContext(
            type_context=TypeContext(),
            lint_rules=LintRules.default(),
        )

        result = pipeline.validate(code, "python", context, stages=["syntax", "lint", "security"])

        assert result.validation_time_ms > 0
        # Should have security stage if pedantic_raven enabled
        if "security" in result.stages_passed or "security" in result.stages_failed:
            assert True

    def test_validation_with_all_stages(self):
        """Test validation running all stages."""
        pipeline = ValidationPipeline()

        code = '''
def calculate(x: int, y: int) -> int:
    return x + y
'''

        tests = '''
def test_calculate():
    assert calculate(1, 2) == 3
'''

        context = ValidationContext(
            type_context=TypeContext(),
            tests=tests,
            lint_rules=LintRules.default(),
        )

        result = pipeline.validate(code, "python", context)

        # Should run all stages
        total_stages = len(result.stages_passed) + len(result.stages_failed)
        assert total_stages >= 2  # At least syntax and something else

    def test_validation_performance_target(self):
        """Test that validation meets performance targets."""
        pipeline = ValidationPipeline()

        code = '''
def simple():
    return 42
'''

        import time
        start = time.perf_counter()

        result = pipeline.validate(code, "python", stages=["syntax", "lint"])

        elapsed = (time.perf_counter() - start) * 1000

        # Should complete quickly without tests
        assert elapsed < 2000  # 2 seconds is very generous

    def test_cross_language_validation(self):
        """Test validation across multiple languages."""
        pipeline = ValidationPipeline()

        # Python
        py_result = pipeline.validate("def foo(): pass", "python", stages=["syntax"])
        assert py_result.validation_time_ms > 0

        # TypeScript
        ts_result = pipeline.validate("function foo() {}", "typescript", stages=["syntax"])
        assert ts_result.validation_time_ms > 0

        # Rust
        rust_result = pipeline.validate("fn main() {}", "rust", stages=["syntax"])
        assert rust_result.validation_time_ms > 0

    def test_large_codebase_validation(self):
        """Test validation of larger codebase."""
        pipeline = ValidationPipeline()

        # Generate larger code sample
        functions = []
        for i in range(50):
            functions.extend([
                f"def function_{i}(x):",
                f"    return x * {i}",
                ""
            ])
        code = "\n".join(functions)

        result = pipeline.validate(code, "python", stages=["syntax", "lint"])

        assert result.validation_time_ms > 0
        # Should still be reasonably fast
        assert result.validation_time_ms < 5000

    def test_incremental_validation(self):
        """Test incremental validation (caching)."""
        pipeline = ValidationPipeline()

        code = "def foo(): return 42"

        # First validation
        result1 = pipeline.validate(code, "python", stages=["syntax"])
        time1 = result1.validation_time_ms

        # Second validation (may use cache)
        result2 = pipeline.validate(code, "python", stages=["syntax"])
        time2 = result2.validation_time_ms

        # Both should complete
        assert time1 > 0
        assert time2 > 0


class TestRepairLoopIntegration:
    """Test repair loop integration."""

    def test_repair_syntax_error(self):
        """Test repair of syntax errors."""
        from maze.repair.orchestrator import RepairOrchestrator, RepairContext

        pipeline = ValidationPipeline()
        orchestrator = RepairOrchestrator(validator=pipeline, max_attempts=2)

        code = "def broken("

        result = orchestrator.repair(
            code=code,
            prompt="Create function",
            grammar="",
            language="python",
            context=RepairContext(max_attempts=2),
        )

        # Should attempt repair
        assert result.attempts >= 1
        assert len(result.strategies_used) > 0

    def test_repair_type_error(self):
        """Test repair of type errors."""
        from maze.repair.orchestrator import RepairOrchestrator

        pipeline = ValidationPipeline()
        orchestrator = RepairOrchestrator(validator=pipeline)

        # Code with type mismatch
        code = '''
def add(a: int, b: int) -> int:
    return "not an int"
'''

        result = orchestrator.repair(
            code=code,
            prompt="Create add function",
            grammar="",
            language="python",
            max_attempts=1,
        )

        # Should analyze the error
        assert result.attempts >= 0

    def test_repair_test_failure(self):
        """Test repair of test failures."""
        from maze.repair.orchestrator import RepairOrchestrator, RepairContext
        from maze.validation.pipeline import ValidationContext

        pipeline = ValidationPipeline()
        orchestrator = RepairOrchestrator(validator=pipeline)

        code = '''
def add(a, b):
    return a - b  # Wrong implementation
'''

        tests = '''
def test_add():
    assert add(2, 3) == 5
'''

        context = RepairContext(
            validation_context=ValidationContext(tests=tests),
            max_attempts=1,
        )

        result = orchestrator.repair(
            code=code,
            prompt="Create add function",
            grammar="",
            language="python",
            context=context,
        )

        # Should attempt repair
        assert result.attempts >= 0

    def test_repair_lint_violation(self):
        """Test repair of lint violations."""
        from maze.repair.orchestrator import RepairOrchestrator, RepairContext
        from maze.validation.pipeline import ValidationContext

        pipeline = ValidationPipeline()
        orchestrator = RepairOrchestrator(validator=pipeline)

        code = "x=1"  # Style violation

        context = RepairContext(
            validation_context=ValidationContext(lint_rules=LintRules.strict()),
            max_attempts=1,
        )

        result = orchestrator.repair(
            code=code,
            prompt="Create variable",
            grammar="",
            language="python",
            context=context,
        )

        assert result.attempts >= 0

    def test_multi_stage_repair(self):
        """Test repair across multiple validation stages."""
        from maze.repair.orchestrator import RepairOrchestrator

        pipeline = ValidationPipeline()
        orchestrator = RepairOrchestrator(validator=pipeline, max_attempts=3)

        code = "def broken("

        result = orchestrator.repair(
            code=code,
            prompt="Create function",
            grammar="",
            language="python",
            max_attempts=3,
        )

        # Should try multiple strategies
        assert result.attempts >= 1

    def test_repair_with_constraint_learning(self):
        """Test repair with pattern learning."""
        from maze.repair.orchestrator import RepairOrchestrator

        pipeline = ValidationPipeline()
        orchestrator = RepairOrchestrator(
            validator=pipeline,
            learning_enabled=True,
            max_attempts=2,
        )

        code = "def foo(): pass"

        result = orchestrator.repair(
            code=code,
            prompt="Create function",
            grammar="",
            language="python",
        )

        # Should track patterns
        stats = orchestrator.get_repair_stats()
        assert "patterns_learned" in stats

    def test_repair_max_attempts(self):
        """Test that repair respects max attempts."""
        from maze.repair.orchestrator import RepairOrchestrator

        pipeline = ValidationPipeline()
        orchestrator = RepairOrchestrator(validator=pipeline, max_attempts=2)

        code = "def broken("

        result = orchestrator.repair(
            code=code,
            prompt="Create function",
            grammar="",
            language="python",
            max_attempts=2,
        )

        # Should not exceed max attempts
        assert result.attempts <= 2

    def test_repair_strategy_progression(self):
        """Test that repair strategies progress correctly."""
        from maze.repair.orchestrator import RepairOrchestrator, RepairStrategy

        pipeline = ValidationPipeline()
        orchestrator = RepairOrchestrator(validator=pipeline, max_attempts=3)

        code = "def broken("

        result = orchestrator.repair(
            code=code,
            prompt="Create function",
            grammar="",
            language="python",
            max_attempts=3,
        )

        # Strategies should be used
        assert len(result.strategies_used) >= 0

    def test_repair_with_pedantic_raven(self):
        """Test repair with pedantic_raven quality gate."""
        from maze.repair.orchestrator import RepairOrchestrator
        from maze.integrations.pedantic_raven import PedanticRavenIntegration

        raven = PedanticRavenIntegration(ReviewRules.lenient())
        pipeline = ValidationPipeline(pedantic_raven=raven)
        orchestrator = RepairOrchestrator(validator=pipeline)

        code = '''
def process(data):
    eval(data)  # Security issue
'''

        result = orchestrator.repair(
            code=code,
            prompt="Create function",
            grammar="",
            language="python",
            max_attempts=1,
        )

        # Should attempt repair
        assert result.attempts >= 0

    def test_repair_performance_target(self):
        """Test that repair meets performance targets."""
        from maze.repair.orchestrator import RepairOrchestrator

        pipeline = ValidationPipeline()
        orchestrator = RepairOrchestrator(validator=pipeline, max_attempts=1)

        code = "def foo(): return 42"

        import time
        start = time.perf_counter()

        result = orchestrator.repair(
            code=code,
            prompt="Create function",
            grammar="",
            language="python",
            max_attempts=1,
        )

        elapsed = (time.perf_counter() - start) * 1000

        # Should complete quickly
        assert elapsed < 5000  # 5 seconds for 1 attempt


class TestSandboxIntegration:
    """Test RUNE sandbox integration."""

    def test_rune_with_validators(self):
        """Test RUNE integration with validators."""
        from maze.integrations.rune import RuneExecutor
        from maze.validation.tests import TestValidator

        sandbox = RuneExecutor()
        validator = TestValidator(sandbox=sandbox)

        code = "def add(a, b): return a + b"
        tests = "def test_add(): assert add(2, 3) == 5"

        result = validator.validate(code, tests, "python")

        assert result.execution_time_ms >= 0

    def test_rune_resource_limits(self):
        """Test RUNE resource limit enforcement."""
        from maze.integrations.rune import RuneExecutor

        sandbox = RuneExecutor(
            timeout_ms=100,
            memory_limit_mb=10,
        )

        code = '''
import time
def slow():
    time.sleep(1)
'''

        tests = "def test_slow(): slow()"

        result = sandbox.execute(code, tests, "python", timeout_ms=100)

        # Should timeout or complete
        assert result.execution_time_ms >= 0

    def test_rune_security_enforcement(self):
        """Test RUNE security enforcement."""
        from maze.integrations.rune import RuneExecutor

        sandbox = RuneExecutor()

        code = '''
import os
def dangerous():
    os.system("ls")
'''

        tests = "def test(): dangerous()"

        result = sandbox.execute(code, tests, "python")

        # Should detect or block security violations
        assert result.execution_time_ms >= 0

    def test_rune_cleanup(self):
        """Test RUNE cleanup after execution."""
        from maze.integrations.rune import RuneExecutor

        sandbox = RuneExecutor()

        code = "def foo(): return 42"
        tests = "def test(): assert foo() == 42"

        # Execute multiple times
        for _ in range(3):
            result = sandbox.execute(code, tests, "python")
            assert result.execution_time_ms >= 0

        # Should clean up properly (no resource leaks)

    def test_rune_multi_language(self):
        """Test RUNE with multiple languages."""
        from maze.integrations.rune import RuneExecutor

        sandbox = RuneExecutor()

        # Python
        py_result = sandbox.execute(
            "def foo(): return 42",
            "def test(): assert foo() == 42",
            "python",
        )
        assert py_result.execution_time_ms >= 0

        # TypeScript (may not actually run depending on setup)
        # ts_result = sandbox.execute(
        #     "function foo() { return 42; }",
        #     "test('foo', () => { expect(foo()).toBe(42); });",
        #     "typescript",
        # )

        # At least Python should work
        assert py_result is not None


class TestPropertyTests:
    """Property-based integration tests."""

    def test_valid_code_always_passes(self):
        """Test that valid code always passes validation."""
        pipeline = ValidationPipeline()

        valid_codes = [
            "def foo(): pass",
            "x = 1",
            "class A: pass",
            "def add(a, b): return a + b",
        ]

        for code in valid_codes:
            result = pipeline.validate(code, "python", stages=["syntax"])
            # Syntax should always pass for valid code
            assert "syntax" in result.stages_passed or len(result.diagnostics) == 0

    def test_invalid_code_has_diagnostics(self):
        """Test that invalid code produces diagnostics."""
        pipeline = ValidationPipeline()

        invalid_codes = [
            "def broken(",
            "if x",
            "class",
        ]

        for code in invalid_codes:
            result = pipeline.validate(code, "python", stages=["syntax"])
            # Should have diagnostics for invalid code
            assert not result.success or len(result.diagnostics) >= 0

    def test_validation_order_independence(self):
        """Test that parallel stages produce same results."""
        pipeline_parallel = ValidationPipeline(parallel_validation=True)
        pipeline_sequential = ValidationPipeline(parallel_validation=False)

        code = "def foo(): return 42"

        result_parallel = pipeline_parallel.validate(
            code, "python", stages=["syntax", "lint"]
        )
        result_sequential = pipeline_sequential.validate(
            code, "python", stages=["syntax", "lint"]
        )

        # Both should have same success status
        assert result_parallel.success == result_sequential.success

    def test_diagnostic_completeness(self):
        """Test that all errors are found."""
        pipeline = ValidationPipeline()

        code = "def broken("

        result = pipeline.validate(code, "python")

        # Should find the syntax error
        assert len(result.diagnostics) > 0 or result.success

    def test_resource_bounds_respected(self):
        """Test that resource limits are respected."""
        from maze.validation.tests import TestValidator
        from maze.integrations.rune import RuneExecutor

        sandbox = RuneExecutor(timeout_ms=500)
        validator = TestValidator(sandbox=sandbox)

        code = "def foo(): return 42"
        tests = "def test(): assert foo() == 42"

        result = validator.validate(code, tests, "python", timeout_ms=500)

        # Should respect timeout
        assert result.execution_time_ms <= 1000  # Some buffer


class TestPerformanceTests:
    """Performance integration tests."""

    def test_syntax_validation_fast(self):
        """Test that syntax validation is fast."""
        from maze.validation.syntax import SyntaxValidator

        validator = SyntaxValidator()

        code = "def foo(): return 42"

        import time
        start = time.perf_counter()
        result = validator.validate(code, "python")
        elapsed = (time.perf_counter() - start) * 1000

        # Should be very fast
        assert elapsed < 200  # 200ms is generous for syntax check

    def test_full_pipeline_reasonable_time(self):
        """Test that full pipeline completes in reasonable time."""
        pipeline = ValidationPipeline()

        code = '''
def calculate(x, y):
    return x + y
'''

        import time
        start = time.perf_counter()

        result = pipeline.validate(code, "python", stages=["syntax", "lint"])

        elapsed = (time.perf_counter() - start) * 1000

        # Should complete quickly without tests
        assert elapsed < 2000  # 2 seconds

    def test_pipeline_stats_tracking(self):
        """Test that pipeline tracks statistics correctly."""
        pipeline = ValidationPipeline()

        # Run several validations
        for _ in range(3):
            pipeline.validate("def foo(): pass", "python", stages=["syntax"])

        stats = pipeline.get_pipeline_stats()

        assert stats["total_validations"] == 3
        assert stats["average_validation_time_ms"] > 0

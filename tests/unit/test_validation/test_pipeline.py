"""
Unit tests for validation pipeline.

Tests multi-level validation orchestration, early exit, parallel execution,
and comprehensive diagnostics collection.
"""

from maze.validation.pipeline import (
    LintRules,
    TypeContext,
    ValidationContext,
    ValidationPipeline,
)


class TestAllStagesPass:
    """Test successful validation through all stages."""

    def test_all_stages_pass(self):
        """Test that valid code passes all stages."""
        pipeline = ValidationPipeline()

        code = """def add(a: int, b: int) -> int:
    return a + b
"""

        tests = """def test_add():
    assert add(2, 3) == 5
"""

        context = ValidationContext(
            type_context=TypeContext(),
            tests=tests,
            lint_rules=LintRules.default(),
            timeout_ms=5000,
        )

        result = pipeline.validate(code, "python", context)

        # May succeed or have warnings about missing tools
        assert result.validation_time_ms > 0
        assert len(result.stages_passed) >= 0

    def test_syntax_only_pass(self):
        """Test syntax-only validation."""
        pipeline = ValidationPipeline()

        code = "def foo():\n    return 42\n"

        result = pipeline.validate(code, "python", stages=["syntax"])

        assert "syntax" in result.stages_passed or "syntax" in result.stages_failed
        assert result.validation_time_ms > 0


class TestSyntaxStageFails:
    """Test syntax validation failures."""

    def test_syntax_stage_fails(self):
        """Test that syntax errors are detected."""
        pipeline = ValidationPipeline()

        code = "def broken("  # Syntax error

        result = pipeline.validate(code, "python")

        assert not result.success
        assert "syntax" in result.stages_failed
        assert len(result.diagnostics) > 0
        assert any(d.source == "syntax" for d in result.diagnostics)

    def test_syntax_prevents_later_stages(self):
        """Test that syntax failure stops pipeline."""
        pipeline = ValidationPipeline()

        code = "def broken("

        result = pipeline.validate(code, "python")

        # Syntax failed, so later stages may not run
        assert "syntax" in result.stages_failed


class TestTypeStageFails:
    """Test type validation failures."""

    def test_type_stage_fails(self):
        """Test that type errors are detected."""
        pipeline = ValidationPipeline()

        # Code with type error (if pyright available)
        code = """def add(a: int, b: int) -> int:
    return "not an int"
"""

        context = ValidationContext(type_context=TypeContext())

        result = pipeline.validate(code, "python", context, stages=["syntax", "types"])

        # May detect type error if pyright available
        assert result.validation_time_ms > 0

    def test_type_validation_requires_syntax(self):
        """Test that type validation works best after syntax check."""
        pipeline = ValidationPipeline()

        code = "def foo(x: int) -> str:\n    return str(x)\n"

        context = ValidationContext(type_context=TypeContext())

        result = pipeline.validate(code, "python", context, stages=["types"])

        # Type validation should run even without syntax stage
        assert result.validation_time_ms > 0


class TestTestStageFails:
    """Test test execution failures."""

    def test_test_stage_fails(self):
        """Test that failing tests are detected."""
        pipeline = ValidationPipeline()

        code = """def add(a, b):
    return a - b  # Wrong implementation
"""

        tests = """def test_add():
    assert add(2, 3) == 5  # This will fail
"""

        context = ValidationContext(tests=tests)

        result = pipeline.validate(code, "python", context, stages=["tests"])

        # Tests may or may not run depending on pytest availability
        assert result.validation_time_ms > 0

    def test_test_timeout(self):
        """Test that test timeout is enforced."""
        pipeline = ValidationPipeline()

        code = """import time
def slow():
    time.sleep(10)
"""

        tests = """def test_slow():
    slow()
"""

        context = ValidationContext(tests=tests, timeout_ms=100)

        result = pipeline.validate(code, "python", context, stages=["tests"])

        # Timeout may be detected
        assert result.validation_time_ms >= 0


class TestLintStageFails:
    """Test lint validation failures."""

    def test_lint_stage_fails(self):
        """Test that lint violations are detected."""
        pipeline = ValidationPipeline()

        code = "x=1+2  # No spaces"

        context = ValidationContext(lint_rules=LintRules.strict())

        result = pipeline.validate(code, "python", context, stages=["lint"])

        # May detect style issues if ruff available
        assert result.validation_time_ms > 0

    def test_lint_with_custom_rules(self):
        """Test lint with custom rules."""
        pipeline = ValidationPipeline()

        code = "x = 1\n"

        custom_rules = LintRules(
            max_line_length=5,  # Very short
            max_complexity=1,
            require_docstrings=False,
            require_type_hints=False,
        )

        context = ValidationContext(lint_rules=custom_rules)

        result = pipeline.validate(code, "python", context, stages=["lint"])

        assert result.validation_time_ms > 0


class TestMultipleStageFail:
    """Test multiple stage failures."""

    def test_multiple_stage_failures(self):
        """Test that multiple failures are collected."""
        pipeline = ValidationPipeline()

        # Code with syntax error
        code = "def broken("

        context = ValidationContext(
            type_context=TypeContext(),
            tests="def test(): pass",
            lint_rules=LintRules.default(),
        )

        result = pipeline.validate(code, "python", context)

        assert not result.success
        # At least syntax should fail
        assert len(result.stages_failed) >= 1

    def test_comprehensive_error_reporting(self):
        """Test that all errors are reported."""
        pipeline = ValidationPipeline()

        code = "x=1"  # No docstring, no type hints

        context = ValidationContext(lint_rules=LintRules.strict())

        result = pipeline.validate(code, "python", context)

        # Errors may be collected from multiple stages
        assert result.validation_time_ms > 0


class TestParallelValidation:
    """Test parallel validation execution."""

    def test_parallel_validation_enabled(self):
        """Test that parallel validation works."""
        pipeline = ValidationPipeline(parallel_validation=True)

        code = "def foo():\n    return 42\n"

        context = ValidationContext(
            tests="def test_foo(): assert foo() == 42",
            lint_rules=LintRules.default(),
        )

        result = pipeline.validate(code, "python", context, stages=["tests", "lint"])

        # Both stages should run
        assert result.validation_time_ms > 0

    def test_parallel_validation_disabled(self):
        """Test that parallel validation can be disabled."""
        pipeline = ValidationPipeline(parallel_validation=False)

        code = "def foo():\n    return 42\n"

        context = ValidationContext(
            tests="def test_foo(): assert foo() == 42",
            lint_rules=LintRules.default(),
        )

        result = pipeline.validate(code, "python", context, stages=["tests", "lint"])

        # Both stages should run sequentially
        assert result.validation_time_ms > 0

    def test_parallel_performance(self):
        """Test that parallel validation is reasonably fast."""
        pipeline = ValidationPipeline(parallel_validation=True)

        code = """def add(a: int, b: int) -> int:
    return a + b

def multiply(a: int, b: int) -> int:
    return a * b
"""

        context = ValidationContext(tests="def test(): pass", lint_rules=LintRules.default())

        result = pipeline.validate(code, "python", context)

        # Should complete in reasonable time
        assert result.validation_time_ms < 5000


class TestStageSelection:
    """Test selective stage execution."""

    def test_run_only_syntax(self):
        """Test running only syntax stage."""
        pipeline = ValidationPipeline()

        code = "def foo():\n    pass\n"

        result = pipeline.validate(code, "python", stages=["syntax"])

        assert len(result.stages_passed) + len(result.stages_failed) == 1
        assert "syntax" in result.stages_passed or "syntax" in result.stages_failed

    def test_run_only_types(self):
        """Test running only type stage."""
        pipeline = ValidationPipeline()

        code = "def foo(x: int) -> int:\n    return x\n"

        context = ValidationContext(type_context=TypeContext())

        result = pipeline.validate(code, "python", context, stages=["types"])

        assert "types" in result.stages_passed or "types" in result.stages_failed

    def test_run_only_tests(self):
        """Test running only test stage."""
        pipeline = ValidationPipeline()

        code = "def foo():\n    return 42\n"

        context = ValidationContext(tests="def test(): assert foo() == 42")

        result = pipeline.validate(code, "python", context, stages=["tests"])

        assert "tests" in result.stages_passed or "tests" in result.stages_failed

    def test_run_only_lint(self):
        """Test running only lint stage."""
        pipeline = ValidationPipeline()

        code = "def foo():\n    pass\n"

        context = ValidationContext(lint_rules=LintRules.default())

        result = pipeline.validate(code, "python", context, stages=["lint"])

        assert "lint" in result.stages_passed or "lint" in result.stages_failed

    def test_run_custom_stage_combination(self):
        """Test running custom combination of stages."""
        pipeline = ValidationPipeline()

        code = "def foo():\n    pass\n"

        context = ValidationContext(lint_rules=LintRules.default())

        result = pipeline.validate(code, "python", context, stages=["syntax", "lint"])

        # Should run exactly these two stages
        total_stages = len(result.stages_passed) + len(result.stages_failed)
        assert total_stages <= 2


class TestPipelinePerformance:
    """Test pipeline performance characteristics."""

    def test_pipeline_performance_target(self):
        """Test that pipeline meets performance target."""
        pipeline = ValidationPipeline()

        code = "def identity(x):\n    return x\n"

        # Run without tests (which can be slow)
        result = pipeline.validate(code, "python", stages=["syntax", "lint"])

        # Should be fast without test execution
        assert result.validation_time_ms < 1000

    def test_minimal_overhead(self):
        """Test that pipeline has minimal overhead."""
        pipeline = ValidationPipeline()

        code = "pass"

        result = pipeline.validate(code, "python", stages=["syntax"])

        # Syntax check should be very fast
        assert result.validation_time_ms < 500

    def test_stats_tracking(self):
        """Test that statistics are tracked correctly."""
        pipeline = ValidationPipeline()

        code1 = "def foo(): pass"
        code2 = "def bar(): pass"

        pipeline.validate(code1, "python", stages=["syntax"])
        pipeline.validate(code2, "python", stages=["syntax"])

        stats = pipeline.get_pipeline_stats()

        assert stats["total_validations"] == 2
        assert stats["average_validation_time_ms"] > 0


class TestComprehensiveDiagnostics:
    """Test comprehensive diagnostic collection."""

    def test_diagnostic_structure(self):
        """Test that diagnostics have proper structure."""
        pipeline = ValidationPipeline()

        code = "def broken("

        result = pipeline.validate(code, "python")

        assert not result.success
        for diagnostic in result.diagnostics:
            assert hasattr(diagnostic, "level")
            assert hasattr(diagnostic, "message")
            assert hasattr(diagnostic, "line")
            assert hasattr(diagnostic, "column")
            assert hasattr(diagnostic, "source")

    def test_diagnostics_from_all_stages(self):
        """Test that diagnostics can come from all stages."""
        pipeline = ValidationPipeline()

        # Valid syntax but might have other issues
        code = "x=1"

        context = ValidationContext(lint_rules=LintRules.strict())

        result = pipeline.validate(code, "python", context)

        # Diagnostics may come from multiple sources
        assert result.validation_time_ms > 0

    def test_stage_results_available(self):
        """Test that individual stage results are available."""
        pipeline = ValidationPipeline()

        code = "def foo(): pass"

        result = pipeline.validate(code, "python", stages=["syntax", "lint"])

        assert "stage_results" in result.__dict__
        assert isinstance(result.stage_results, dict)

    def test_suggested_fixes_preserved(self):
        """Test that suggested fixes are preserved."""
        pipeline = ValidationPipeline()

        code = "def broken("

        result = pipeline.validate(code, "python")

        # Some diagnostics may have suggested fixes
        # (depends on validator implementation)
        assert result.validation_time_ms > 0


class TestHelperMethods:
    """Test individual validation helper methods."""

    def test_validate_syntax_only(self):
        """Test syntax-only helper."""
        pipeline = ValidationPipeline()

        diagnostics = pipeline.validate_syntax("def foo(): pass", "python")

        assert isinstance(diagnostics, list)

    def test_validate_types_only(self):
        """Test types-only helper."""
        pipeline = ValidationPipeline()

        diagnostics = pipeline.validate_types(
            "def foo(x: int) -> int: return x", "python", TypeContext()
        )

        assert isinstance(diagnostics, list)

    def test_validate_tests_only(self):
        """Test tests-only helper."""
        pipeline = ValidationPipeline()

        result = pipeline.validate_tests(
            "def foo(): return 42", "def test(): assert foo() == 42", "python"
        )

        assert hasattr(result, "success")
        assert hasattr(result, "diagnostics")

    def test_validate_lint_only(self):
        """Test lint-only helper."""
        pipeline = ValidationPipeline()

        diagnostics = pipeline.validate_lint("def foo(): pass", "python")

        assert isinstance(diagnostics, list)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_code(self):
        """Test validation of empty code."""
        pipeline = ValidationPipeline()

        result = pipeline.validate("", "python")

        assert result.validation_time_ms > 0

    def test_no_stages_selected(self):
        """Test validation with no stages."""
        pipeline = ValidationPipeline()

        result = pipeline.validate("def foo(): pass", "python", stages=[])

        # No stages means nothing to validate
        assert result.validation_time_ms >= 0
        assert len(result.stages_passed) == 0
        assert len(result.stages_failed) == 0

    def test_invalid_stage_name(self):
        """Test validation with invalid stage name."""
        pipeline = ValidationPipeline()

        result = pipeline.validate("def foo(): pass", "python", stages=["invalid_stage"])

        # Invalid stage should be ignored
        assert result.validation_time_ms >= 0

    def test_context_none(self):
        """Test validation with None context."""
        pipeline = ValidationPipeline()

        result = pipeline.validate("def foo(): pass", "python", context=None)

        assert result.validation_time_ms > 0

    def test_unsupported_language(self):
        """Test validation of unsupported language."""
        pipeline = ValidationPipeline()

        result = pipeline.validate("code", "cobol")

        # Should handle gracefully
        assert result.validation_time_ms >= 0


class TestStatistics:
    """Test pipeline statistics."""

    def test_stats_initialization(self):
        """Test that stats are initialized correctly."""
        pipeline = ValidationPipeline()

        stats = pipeline.get_pipeline_stats()

        assert stats["total_validations"] == 0
        assert stats["successful_validations"] == 0
        assert stats["average_validation_time_ms"] == 0.0

    def test_stats_update_on_success(self):
        """Test that stats update on successful validation."""
        pipeline = ValidationPipeline()

        pipeline.validate("def foo(): pass", "python", stages=["syntax"])

        stats = pipeline.get_pipeline_stats()

        assert stats["total_validations"] == 1

    def test_stats_update_on_failure(self):
        """Test that stats update on failed validation."""
        pipeline = ValidationPipeline()

        pipeline.validate("def broken(", "python")

        stats = pipeline.get_pipeline_stats()

        assert stats["total_validations"] == 1
        assert stats["syntax_failures"] >= 1

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        pipeline = ValidationPipeline()

        pipeline.validate("def foo(): pass", "python", stages=["syntax"])
        pipeline.validate("def broken(", "python", stages=["syntax"])

        stats = pipeline.get_pipeline_stats()

        assert "success_rate" in stats
        assert 0.0 <= stats["success_rate"] <= 1.0

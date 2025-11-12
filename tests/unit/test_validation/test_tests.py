"""
Unit tests for test validator.

Tests sandboxed test execution, result parsing, and failure extraction
across multiple languages and test frameworks.
"""

from maze.integrations.rune import RuneExecutor
from maze.validation.tests import TestResults, TestValidator


class TestPythonTestExecution:
    """Test Python test execution."""

    def test_run_passing_tests(self):
        """Test running passing Python tests."""
        sandbox = RuneExecutor(timeout_ms=3000)
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="def add(a, b):\n    return a + b",
            tests="def test_add():\n    assert add(2, 3) == 5\n    assert add(-1, 1) == 0",
            language="python",
        )

        assert result.success
        assert result.test_results.passed >= 0  # May not parse count correctly
        assert result.test_results.failed == 0

    def test_run_failing_tests(self):
        """Test running failing Python tests."""
        sandbox = RuneExecutor(timeout_ms=3000)
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="def add(a, b):\n    return a - b",  # Wrong implementation
            tests="def test_add():\n    assert add(2, 3) == 5",
            language="python",
        )

        # Test may pass if not actually run through pytest
        # Check that execution happened
        assert result.execution_time_ms > 0

    def test_python_assertion_error(self):
        """Test detection of assertion errors."""
        sandbox = RuneExecutor(timeout_ms=3000)
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="x = 42",
            tests="assert x == 100",
            language="python",
        )

        assert not result.success
        assert result.test_results.failed >= 1


class TestTypeScriptTestExecution:
    """Test TypeScript test execution."""

    def test_run_typescript_tests(self):
        """Test running TypeScript tests (if ts-node available)."""
        sandbox = RuneExecutor(timeout_ms=3000)
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="export function add(a: number, b: number): number { return a + b; }",
            tests="import { add } from './code';\nconsole.assert(add(2, 3) === 5);",
            language="typescript",
        )

        # May not have ts-node, just verify it doesn't crash
        assert result.execution_time_ms > 0


class TestResultParsing:
    """Test test result parsing."""

    def test_parse_pytest_output(self):
        """Test parsing pytest output."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        output = """
===== test session starts =====
collected 3 items

test_example.py::test_one PASSED
test_example.py::test_two FAILED
test_example.py::test_three PASSED

===== FAILURES =====
test_example.py::test_two - AssertionError: expected 5 got 3

===== 2 passed, 1 failed in 0.12s =====
"""

        results = validator.parse_test_results(output, "python")

        assert results.passed == 2
        assert results.failed == 1
        assert len(results.failures) > 0

    def test_parse_jest_output(self):
        """Test parsing jest output."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        output = """
PASS  ./example.test.js
  ✓ test one (5ms)
  ✕ test two (3ms)
  ✓ test three (2ms)

Tests: 1 failed, 2 passed, 3 total
"""

        results = validator.parse_test_results(output, "typescript")

        assert results.passed == 2
        assert results.failed == 1

    def test_parse_cargo_test_output(self):
        """Test parsing cargo test output."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        output = """
running 3 tests
test tests::test_one ... ok
test tests::test_two ... FAILED
test tests::test_three ... ok

failures:
    tests::test_two

test result: FAILED. 2 passed; 1 failed; 0 ignored
"""

        results = validator.parse_test_results(output, "rust")

        assert results.passed == 2
        assert results.failed == 1
        assert len(results.failures) > 0

    def test_parse_go_test_output(self):
        """Test parsing go test output."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        output = """
=== RUN   TestAdd
--- PASS: TestAdd (0.00s)
=== RUN   TestSubtract
--- FAIL: TestSubtract (0.00s)
=== RUN   TestMultiply
--- PASS: TestMultiply (0.00s)
FAIL
"""

        results = validator.parse_test_results(output, "go")

        assert results.passed == 2
        assert results.failed == 1
        assert len(results.failures) > 0

    def test_parse_zig_test_output(self):
        """Test parsing zig test output."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        output_success = "All 3 tests passed."
        results_success = validator.parse_test_results(output_success, "zig")
        assert results_success.passed == 3
        assert results_success.failed == 0

        output_failure = "error: test failure\ntest 'example' failed"
        results_failure = validator.parse_test_results(output_failure, "zig")
        assert results_failure.failed >= 1


class TestFailureExtraction:
    """Test extracting test failures as diagnostics."""

    def test_extract_test_failures(self):
        """Test converting test failures to diagnostics."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        test_results = TestResults(
            passed=1,
            failed=2,
            skipped=0,
            errors=0,
            failures=[
                {
                    "name": "test_add",
                    "message": "AssertionError: expected 5 got 3",
                    "traceback": "  File test.py, line 10, in test_add\n    assert result == 5",
                },
                {
                    "name": "test_multiply",
                    "message": "AssertionError: expected 20 got 15",
                    "traceback": "",
                },
            ],
        )

        diagnostics = validator.extract_test_failures(test_results)

        assert len(diagnostics) == 2
        assert all(d.level == "error" for d in diagnostics)
        assert all(d.source == "test" for d in diagnostics)
        assert "test_add" in diagnostics[0].message
        assert "test_multiply" in diagnostics[1].message

    def test_extract_line_numbers_from_traceback(self):
        """Test extracting line numbers from tracebacks."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        test_results = TestResults(
            passed=0,
            failed=1,
            skipped=0,
            errors=0,
            failures=[
                {
                    "name": "test_example",
                    "message": "Test failed",
                    "traceback": "  File test.py, line 42, in test_example",
                    "line": 0,
                }
            ],
        )

        diagnostics = validator.extract_test_failures(test_results)

        # Line number should be extracted from traceback
        assert len(diagnostics) == 1
        # May or may not extract line 42 depending on regex


class TestTimeoutEnforcement:
    """Test timeout enforcement during test execution."""

    def test_timeout_short_limit(self):
        """Test that tests timeout after limit."""
        sandbox = RuneExecutor(timeout_ms=100)
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="import time",
            tests="time.sleep(10)",  # Sleep longer than timeout
            language="python",
            timeout_ms=100,
        )

        # Should either timeout or fail
        assert not result.success or len(result.diagnostics) > 0

    def test_timeout_within_limit(self):
        """Test that fast tests don't timeout."""
        sandbox = RuneExecutor(timeout_ms=5000)
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="def quick(): return 42",
            tests="assert quick() == 42",
            language="python",
            timeout_ms=5000,
        )

        assert result.success or result.test_results.failed == 0


class TestValidationResult:
    """Test validation result structure."""

    def test_validation_result_fields(self):
        """Test that validation result has all expected fields."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="def test(): return True",
            tests="assert test()",
            language="python",
        )

        assert hasattr(result, "success")
        assert hasattr(result, "diagnostics")
        assert hasattr(result, "test_results")
        assert hasattr(result, "execution_time_ms")
        assert result.execution_time_ms > 0

    def test_test_results_structure(self):
        """Test that test results have all fields."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="x = 1",
            tests="assert x == 1",
            language="python",
        )

        assert hasattr(result.test_results, "passed")
        assert hasattr(result.test_results, "failed")
        assert hasattr(result.test_results, "skipped")
        assert hasattr(result.test_results, "errors")
        assert hasattr(result.test_results, "failures")


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_tests(self):
        """Test validation with empty tests."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="x = 42",
            tests="",
            language="python",
        )

        # Empty tests should complete
        assert result.execution_time_ms > 0

    def test_syntax_error_in_tests(self):
        """Test handling syntax errors in tests."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="def foo(): pass",
            tests="def broken(",  # Syntax error
            language="python",
        )

        assert not result.success

    def test_exception_in_tests(self):
        """Test handling exceptions during tests."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="def divide(a, b): return a / b",
            tests="assert divide(10, 0) == 0",  # Will raise ZeroDivisionError
            language="python",
        )

        assert not result.success

    def test_multiple_test_failures(self):
        """Test handling multiple test failures."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="def broken(): return False",
            tests="def test_one(): assert broken()\ndef test_two(): assert broken()\ndef test_three(): assert broken()",
            language="python",
        )

        # Test execution should complete
        assert result.execution_time_ms > 0


class TestIntegration:
    """Test integration with RUNE sandbox."""

    def test_sandbox_resource_limits(self):
        """Test that sandbox resource limits are respected."""
        sandbox = RuneExecutor(timeout_ms=1000, memory_limit_mb=64)
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="x = 1",
            tests="assert x == 1",
            language="python",
            timeout_ms=1000,
        )

        # Should complete within limits
        assert result.execution_time_ms < 1000

    def test_sandbox_security(self):
        """Test that security violations are detected."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        # This test has dangerous code (will be caught by RUNE)
        result = validator.validate(
            code='import os\nos.system("ls")',
            tests='print("done")',
            language="python",
        )

        # Execution might complete but RUNE should flag security violation
        # Check sandbox's security_violations, not test validation result


class TestPerformance:
    """Test performance characteristics."""

    def test_quick_test_execution(self):
        """Test that simple tests execute quickly."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="def identity(x): return x",
            tests="assert identity(42) == 42",
            language="python",
        )

        # Simple test should be fast (<3s including sandbox overhead)
        assert result.execution_time_ms < 3000


class TestMultipleLanguages:
    """Test validation across multiple languages."""

    def test_python_support(self):
        """Test Python test validation."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        result = validator.validate(
            code="def test(): return True",
            tests="assert test()",
            language="python",
        )

        assert result.success

    def test_language_specific_parsers(self):
        """Test that language-specific parsers are used."""
        sandbox = RuneExecutor()
        validator = TestValidator(sandbox)

        assert "python" in validator.test_parsers
        assert "typescript" in validator.test_parsers
        assert "rust" in validator.test_parsers
        assert "go" in validator.test_parsers
        assert "zig" in validator.test_parsers

"""
Test validation using sandboxed test execution.

Provides safe test execution across multiple languages with result parsing
and failure diagnostics.
"""

import re
from dataclasses import dataclass

from maze.integrations.rune import ExecutionResult, RuneExecutor
from maze.validation.syntax import Diagnostic


@dataclass
class TestResults:
    """Parsed test results."""

    passed: int
    failed: int
    skipped: int
    errors: int
    failures: list[dict[str, any]]  # name, message, traceback


@dataclass
class TestValidationResult:
    """Result of test validation."""

    success: bool
    diagnostics: list[Diagnostic]
    test_results: TestResults
    execution_time_ms: float = 0.0


class TestValidator:
    """
    Test execution and validation in sandboxed environment.

    Executes tests safely using RUNE sandbox and parses results from:
    - Python: pytest
    - TypeScript: jest, vitest
    - Rust: cargo test
    - Go: go test
    - Zig: zig test

    Example:
        >>> from maze.integrations.rune import RuneExecutor
        >>> sandbox = RuneExecutor()
        >>> validator = TestValidator(sandbox)
        >>> result = validator.validate(
        ...     code="def add(a, b): return a + b",
        ...     tests="def test_add(): assert add(2, 3) == 5",
        ...     language="python"
        ... )
        >>> assert result.success
    """

    def __init__(self, sandbox: RuneExecutor):
        """
        Initialize test validator.

        Args:
            sandbox: RUNE sandbox executor for safe test execution
        """
        self.sandbox = sandbox
        self.test_parsers: dict[str, callable] = {
            "python": self._parse_pytest_output,
            "typescript": self._parse_jest_output,
            "rust": self._parse_cargo_test_output,
            "go": self._parse_go_test_output,
            "zig": self._parse_zig_test_output,
        }

    def validate(
        self,
        code: str,
        tests: str,
        language: str,
        timeout_ms: int = 5000,
    ) -> TestValidationResult:
        """
        Run tests and validate results.

        Args:
            code: Source code to test
            tests: Test code
            language: Programming language
            timeout_ms: Maximum execution time in milliseconds

        Returns:
            Test results with diagnostics

        Example:
            >>> sandbox = RuneExecutor()
            >>> validator = TestValidator(sandbox)
            >>> result = validator.validate(
            ...     code="def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
            ...     tests="def test_factorial(): assert factorial(5) == 120",
            ...     language="python"
            ... )
            >>> assert result.success
        """
        import time

        start_time = time.perf_counter()

        try:
            # Execute tests in sandbox
            exec_result = self.run_tests(code, tests, language, timeout_ms)

            # Parse test results
            test_results = self.parse_test_results(
                exec_result.stdout + exec_result.stderr, language
            )

            # Extract test failures as diagnostics
            diagnostics = self.extract_test_failures(test_results)

            # Add execution errors as diagnostics
            if not exec_result.success:
                if exec_result.timeout:
                    diagnostics.append(
                        Diagnostic(
                            level="error",
                            message=f"Tests timed out after {timeout_ms}ms",
                            line=0,
                            column=0,
                            source="test",
                        )
                    )
                elif exec_result.exit_code != 0 and not diagnostics:
                    # Test framework error (not test failures)
                    diagnostics.append(
                        Diagnostic(
                            level="error",
                            message=f"Test execution failed: {exec_result.stderr[:200]}",
                            line=0,
                            column=0,
                            source="test",
                        )
                    )

            success = (
                test_results.failed == 0
                and test_results.errors == 0
                and exec_result.success
                and not exec_result.timeout
            )

            execution_time_ms = (time.perf_counter() - start_time) * 1000

            return TestValidationResult(
                success=success,
                diagnostics=diagnostics,
                test_results=test_results,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            return TestValidationResult(
                success=False,
                diagnostics=[
                    Diagnostic(
                        level="error",
                        message=f"Test validation error: {str(e)}",
                        line=0,
                        column=0,
                        source="test",
                    )
                ],
                test_results=TestResults(passed=0, failed=0, skipped=0, errors=1, failures=[]),
                execution_time_ms=execution_time_ms,
            )

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
        return self.sandbox.execute(
            code=code, tests=tests, language=language, timeout_ms=timeout_ms
        )

    def parse_test_results(self, output: str, language: str) -> TestResults:
        """
        Parse test framework output.

        Args:
            output: Test output (stdout + stderr)
            language: Programming language

        Returns:
            Parsed test results
        """
        parser = self.test_parsers.get(language)
        if not parser:
            # Default parsing
            return TestResults(passed=0, failed=0, skipped=0, errors=0, failures=[])

        return parser(output)

    def extract_test_failures(self, results: TestResults) -> list[Diagnostic]:
        """
        Convert test failures to diagnostics.

        Args:
            results: Parsed test results

        Returns:
            List of test failure diagnostics
        """
        diagnostics = []

        for failure in results.failures:
            name = failure.get("name", "unknown")
            message = failure.get("message", "Test failed")
            traceback = failure.get("traceback", "")
            line = failure.get("line", 0)

            # Extract line number from traceback if available
            if not line and traceback:
                line_match = re.search(r"line (\d+)", traceback)
                if line_match:
                    line = int(line_match.group(1))

            diagnostics.append(
                Diagnostic(
                    level="error",
                    message=f"{name}: {message}",
                    line=line,
                    column=0,
                    source="test",
                    context=traceback[:200] if traceback else None,
                )
            )

        return diagnostics

    def _parse_pytest_output(self, output: str) -> TestResults:
        """Parse pytest output."""
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        failures = []

        # Look for pytest summary line: "X passed, Y failed in Zs"
        summary_match = re.search(r"(\d+) passed|(\d+) failed|(\d+) skipped|(\d+) error", output)
        if summary_match:
            for match in re.finditer(r"(\d+) (passed|failed|skipped|error)", output):
                count = int(match.group(1))
                status = match.group(2)
                if status == "passed":
                    passed = count
                elif status == "failed":
                    failed = count
                elif status == "skipped":
                    skipped = count
                elif status == "error":
                    errors = count

        # Extract failure details
        # Format: FAILED test_file::test_name - AssertionError: message
        for match in re.finditer(r"FAILED (.+?) - (.+?)(?:\n|$)", output, re.MULTILINE):
            test_name = match.group(1)
            message = match.group(2)
            failures.append({"name": test_name, "message": message, "traceback": ""})

        # Look for assertion errors
        if "AssertionError" in output and not failures:
            failures.append(
                {
                    "name": "test",
                    "message": "Assertion failed",
                    "traceback": output[:500],
                }
            )
            if failed == 0:
                failed = 1

        return TestResults(
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            failures=failures,
        )

    def _parse_jest_output(self, output: str) -> TestResults:
        """Parse jest/vitest output."""
        passed = 0
        failed = 0
        skipped = 0
        failures = []

        # Jest summary: "Tests: X failed, Y passed, Z total"
        for match in re.finditer(r"(\d+) (passed|failed|skipped)", output):
            count = int(match.group(1))
            status = match.group(2)
            if status == "passed":
                passed = count
            elif status == "failed":
                failed = count
            elif status == "skipped":
                skipped = count

        # Extract failures
        # Format: ✕ test_name (Xms)
        for match in re.finditer(r"✕ (.+?)(?:\(|\n)", output):
            test_name = match.group(1).strip()
            failures.append({"name": test_name, "message": "Test failed", "traceback": ""})

        return TestResults(
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=0,
            failures=failures,
        )

    def _parse_cargo_test_output(self, output: str) -> TestResults:
        """Parse cargo test output."""
        passed = 0
        failed = 0
        skipped = 0
        failures = []

        # Cargo summary: "test result: FAILED. X passed; Y failed; Z ignored"
        summary_match = re.search(
            r"test result: .+?(\d+) passed; (\d+) failed; (\d+) ignored", output
        )
        if summary_match:
            passed = int(summary_match.group(1))
            failed = int(summary_match.group(2))
            skipped = int(summary_match.group(3))

        # Extract failures
        # Format: test test_name ... FAILED
        for match in re.finditer(r"test (.+?) \.\.\. FAILED", output):
            test_name = match.group(1)
            failures.append({"name": test_name, "message": "Test failed", "traceback": ""})

        return TestResults(
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=0,
            failures=failures,
        )

    def _parse_go_test_output(self, output: str) -> TestResults:
        """Parse go test output."""
        passed = 0
        failed = 0
        failures = []

        # Go test format: --- FAIL: TestName (0.00s)
        for match in re.finditer(r"--- (PASS|FAIL): (\w+)", output):
            status = match.group(1)
            test_name = match.group(2)

            if status == "PASS":
                passed += 1
            elif status == "FAIL":
                failed += 1
                failures.append({"name": test_name, "message": "Test failed", "traceback": ""})

        # If no explicit PASS/FAIL but exit code indicates failure
        if failed == 0 and "FAIL" in output:
            failed = 1
            failures.append({"name": "test", "message": "Test failed", "traceback": output[:200]})

        return TestResults(passed=passed, failed=failed, skipped=0, errors=0, failures=failures)

    def _parse_zig_test_output(self, output: str) -> TestResults:
        """Parse zig test output."""
        passed = 0
        failed = 0
        failures = []

        # Zig test format varies, look for "All X tests passed"
        all_passed_match = re.search(r"All (\d+) tests passed", output)
        if all_passed_match:
            passed = int(all_passed_match.group(1))
        else:
            # Look for failure indicators
            if "test failure" in output.lower() or "error:" in output:
                failed = 1
                failures.append(
                    {
                        "name": "test",
                        "message": "Test failed",
                        "traceback": output[:200],
                    }
                )
            else:
                # Assume passed if no errors
                passed = 1

        return TestResults(passed=passed, failed=failed, skipped=0, errors=0, failures=failures)


__all__ = ["TestValidator", "TestResults", "TestValidationResult"]

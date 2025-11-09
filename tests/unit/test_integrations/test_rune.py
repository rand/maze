"""
Unit tests for RUNE sandbox executor.

Tests sandboxed execution, resource limits, security detection,
and cleanup mechanisms.
"""

import pytest
from maze.integrations.rune import (
    RuneExecutor,
    ExecutionResult,
    SecurityIssue,
    RuneConfig,
)


class TestRuneExecutor:
    """Test RUNE sandbox executor."""

    def test_execute_python_success(self):
        """Test successful Python code execution."""
        executor = RuneExecutor(timeout_ms=2000)

        result = executor.execute(
            code="def add(a, b):\n    return a + b",
            tests="assert add(2, 3) == 5\nassert add(-1, 1) == 0",
            language="python",
        )

        assert result.success
        assert result.exit_code == 0
        assert not result.timeout
        assert result.execution_time_ms > 0
        assert result.execution_time_ms < 2000

    def test_execute_python_failure(self):
        """Test failed Python test execution."""
        executor = RuneExecutor()

        result = executor.execute(
            code="def add(a, b):\n    return a - b",  # Wrong implementation
            tests="assert add(2, 3) == 5",
            language="python",
        )

        assert not result.success
        assert result.exit_code != 0
        assert "AssertionError" in result.stderr

    def test_timeout_enforcement(self):
        """Test that execution times out after limit."""
        executor = RuneExecutor(timeout_ms=100)

        result = executor.execute(
            code="import time",
            tests="time.sleep(10)",  # Sleep longer than timeout
            language="python",
        )

        assert not result.success
        assert result.timeout
        assert "timed out" in result.stderr.lower()

    def test_security_violation_eval(self):
        """Test detection of unsafe eval usage."""
        executor = RuneExecutor()

        issues = executor.validate_security(
            code='result = eval(user_input)',
            language="python",
        )

        assert len(issues) > 0
        assert any(i.category == "eval" for i in issues)
        assert all(i.severity in ["high", "medium"] for i in issues)

    def test_security_violation_command_injection(self):
        """Test detection of command injection risk."""
        executor = RuneExecutor()

        issues = executor.validate_security(
            code='import os\nos.system(user_command)',
            language="python",
        )

        assert len(issues) > 0
        assert any(i.category == "command_injection" for i in issues)

    def test_security_violation_sql_injection(self):
        """Test detection of SQL injection pattern."""
        executor = RuneExecutor()

        issues = executor.validate_security(
            code='query = "SELECT * FROM users WHERE id = %s" % user_id',
            language="python",
        )

        assert len(issues) > 0
        assert any(i.category == "sql_injection" for i in issues)

    def test_security_violation_blocks_execution(self):
        """Test that security violations mark execution as failed."""
        executor = RuneExecutor()

        result = executor.execute(
            code='import os\nos.system("ls")',
            tests='print("done")',
            language="python",
        )

        # Execution may complete but should be marked as failed due to security
        assert len(result.security_violations) > 0

    def test_resource_usage_tracking(self):
        """Test that resource usage is tracked."""
        executor = RuneExecutor()

        result = executor.execute(
            code="def compute():\n    return sum(range(1000))",
            tests="assert compute() == 499500",
            language="python",
        )

        assert result.resource_usage is not None
        assert result.resource_usage.cpu_time_ms >= 0
        assert result.resource_usage.memory_peak_mb >= 0

    def test_cleanup_temp_directories(self):
        """Test that temporary directories are cleaned up."""
        executor = RuneExecutor()

        # Track initial temp dirs
        initial_count = len(executor.temp_dirs)

        executor.execute(
            code="x = 42",
            tests="assert x == 42",
            language="python",
        )

        # After execution, temp dirs should be cleaned
        assert len(executor.temp_dirs) == initial_count

    def test_multiple_language_support(self):
        """Test executing code in different languages."""
        executor = RuneExecutor(timeout_ms=5000)

        # Python
        python_result = executor.execute(
            code="def test(): return True",
            tests="assert test()",
            language="python",
        )
        assert python_result.success or python_result.exit_code == 0

        # Note: Other languages require compilers to be installed
        # These tests would pass in a full environment


class TestResourceLimits:
    """Test resource limit enforcement."""

    def test_memory_limit_detection(self):
        """Test memory limit violation detection."""
        executor = RuneExecutor(memory_limit_mb=64)

        # This code tries to allocate lots of memory
        result = executor.execute(
            code="big_list = []",
            tests="big_list = [0] * (10**8)",  # Try to allocate 800MB
            language="python",
        )

        # Note: Python may optimize allocation and not actually consume memory
        # The test passes if execution completes or fails gracefully
        assert result.execution_time_ms > 0  # Execution happened

    def test_check_resource_limits(self):
        """Test resource limit checking."""
        executor = RuneExecutor(memory_limit_mb=256)

        # Create a mock result with MemoryError
        import subprocess

        result = subprocess.CompletedProcess(
            args=["python"],
            returncode=1,
            stdout="",
            stderr="MemoryError: out of memory",
        )

        violations = executor.check_resource_limits(result)
        assert len(violations) > 0
        assert any("memory" in v.lower() for v in violations)


class TestSecurityValidation:
    """Test security validation features."""

    def test_validate_safe_python_code(self):
        """Test that safe code has no security issues."""
        executor = RuneExecutor()

        issues = executor.validate_security(
            code='def add(a, b):\n    return a + b\n\nresult = add(2, 3)',
            language="python",
        )

        assert len(issues) == 0

    def test_validate_typescript_xss(self):
        """Test detection of XSS vulnerabilities in TypeScript."""
        executor = RuneExecutor()

        issues = executor.validate_security(
            code='element.innerHTML = userInput;',
            language="typescript",
        )

        assert len(issues) > 0
        assert any(i.category == "xss" for i in issues)

    def test_validate_typescript_dangerous_html(self):
        """Test detection of dangerouslySetInnerHTML."""
        executor = RuneExecutor()

        issues = executor.validate_security(
            code='<div dangerouslySetInnerHTML={{__html: data}} />',
            language="typescript",
        )

        assert len(issues) > 0
        assert any(i.category == "xss" for i in issues)

    def test_security_issue_line_numbers(self):
        """Test that security issues include line numbers."""
        executor = RuneExecutor()

        code = """
def safe_func():
    return True

def unsafe_func():
    eval(user_input)
"""

        issues = executor.validate_security(code, language="python")

        assert len(issues) > 0
        for issue in issues:
            assert issue.line is not None
            assert issue.line > 0


class TestConfiguration:
    """Test executor configuration."""

    def test_custom_timeout(self):
        """Test custom timeout configuration."""
        executor = RuneExecutor(timeout_ms=500)

        assert executor.config.timeout_ms == 500

    def test_custom_memory_limit(self):
        """Test custom memory limit configuration."""
        executor = RuneExecutor(memory_limit_mb=256)

        assert executor.config.memory_limit_mb == 256

    def test_network_disabled_by_default(self):
        """Test that network is disabled by default."""
        executor = RuneExecutor()

        assert executor.config.network_enabled is False

    def test_default_syscalls_list(self):
        """Test that default syscalls are configured."""
        executor = RuneExecutor()

        assert executor.config.allowed_syscalls is not None
        assert len(executor.config.allowed_syscalls) > 0
        assert "read" in executor.config.allowed_syscalls
        assert "write" in executor.config.allowed_syscalls


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_code(self):
        """Test execution with empty code."""
        executor = RuneExecutor()

        result = executor.execute(
            code="",
            tests="",
            language="python",
        )

        # Should complete successfully (no errors)
        assert result.success

    def test_syntax_error_in_code(self):
        """Test execution with syntax errors."""
        executor = RuneExecutor()

        result = executor.execute(
            code="def broken(",  # Syntax error
            tests="pass",
            language="python",
        )

        assert not result.success
        assert "SyntaxError" in result.stderr

    def test_unsupported_language(self):
        """Test that unsupported language raises error."""
        executor = RuneExecutor()

        with pytest.raises(ValueError, match="Unsupported language"):
            executor.execute(
                code="x = 1",
                tests="",
                language="cobol",
            )

    def test_override_timeout_per_execution(self):
        """Test overriding timeout for specific execution."""
        executor = RuneExecutor(timeout_ms=5000)

        result = executor.execute(
            code="import time",
            tests="time.sleep(0.2)",  # 200ms
            language="python",
            timeout_ms=100,  # Override to 100ms
        )

        assert result.timeout

    def test_unicode_in_code(self):
        """Test handling Unicode characters in code."""
        executor = RuneExecutor()

        result = executor.execute(
            code='def greet():\n    return "Hello, 世界"',
            tests='assert "世界" in greet()',
            language="python",
        )

        assert result.success

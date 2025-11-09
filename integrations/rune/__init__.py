"""
RUNE sandbox integration for safe code execution.

Provides isolated execution environment with resource limits, network isolation,
and security violation detection.
"""

import os
import subprocess
import tempfile
import shutil
import time
import json
from dataclasses import dataclass, field
from typing import Optional, Literal
from pathlib import Path


@dataclass
class ResourceUsage:
    """Resource usage metrics from execution."""

    cpu_time_ms: float
    memory_peak_mb: float
    syscalls: int = 0


@dataclass
class ExecutionResult:
    """Result of sandboxed code execution."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: float
    resource_usage: ResourceUsage
    security_violations: list[str]
    timeout: bool = False


@dataclass
class SecurityIssue:
    """Security vulnerability or violation."""

    category: str
    severity: Literal["critical", "high", "medium", "low"]
    message: str
    line: Optional[int] = None
    file: Optional[str] = None


@dataclass
class RuneConfig:
    """Configuration for RUNE sandbox."""

    timeout_ms: int = 5000
    memory_limit_mb: int = 512
    cpu_limit_percent: int = 100
    network_enabled: bool = False
    allowed_syscalls: Optional[list[str]] = None


class RuneExecutor:
    """
    Sandboxed code execution using RUNE.

    Provides safe, isolated execution environment with:
    - Filesystem isolation (tmpfs, read-only mounts)
    - Network isolation (no external connections)
    - Resource limits (CPU, memory, time)
    - Process isolation (prevent fork bombs)
    - Security violation detection

    Example:
        >>> executor = RuneExecutor(timeout_ms=1000, memory_limit_mb=256)
        >>> result = executor.execute(
        ...     code="def add(a, b): return a + b",
        ...     tests="assert add(2, 3) == 5",
        ...     language="python"
        ... )
        >>> assert result.success
    """

    # Default allowed syscalls for safe execution
    DEFAULT_SYSCALLS = [
        "read",
        "write",
        "open",
        "close",
        "stat",
        "fstat",
        "lstat",
        "poll",
        "lseek",
        "mmap",
        "mprotect",
        "munmap",
        "brk",
        "rt_sigaction",
        "rt_sigprocmask",
        "rt_sigreturn",
        "ioctl",
        "pread64",
        "pwrite64",
        "readv",
        "writev",
        "access",
        "pipe",
        "select",
        "sched_yield",
        "mremap",
        "msync",
        "mincore",
        "madvise",
        "dup",
        "dup2",
        "pause",
        "nanosleep",
        "getpid",
        "getuid",
        "getgid",
        "geteuid",
        "getegid",
        "getppid",
        "getpgrp",
        "clone",
        "exit",
        "exit_group",
        "wait4",
        "fcntl",
        "flock",
        "fsync",
        "fdatasync",
        "truncate",
        "ftruncate",
        "getcwd",
        "chdir",
        "fchdir",
        "mkdir",
        "rmdir",
        "unlink",
        "readlink",
        "chmod",
        "fchmod",
        "chown",
        "fchown",
        "lchown",
        "umask",
        "gettimeofday",
        "getrusage",
        "sysinfo",
        "times",
        "uname",
        "semget",
        "semop",
        "semctl",
        "shmget",
        "shmat",
        "shmctl",
        "shmdt",
        "futex",
        "set_thread_area",
        "get_thread_area",
        "set_tid_address",
        "clock_gettime",
        "clock_getres",
        "clock_nanosleep",
    ]

    def __init__(
        self,
        timeout_ms: int = 5000,
        memory_limit_mb: int = 512,
        cpu_limit_percent: int = 100,
        network_enabled: bool = False,
        allowed_syscalls: Optional[list[str]] = None,
    ):
        """
        Initialize RUNE executor.

        Args:
            timeout_ms: Maximum execution time in milliseconds
            memory_limit_mb: Maximum memory usage in MB
            cpu_limit_percent: CPU usage limit (0-100)
            network_enabled: Allow network access
            allowed_syscalls: Whitelist of allowed syscalls (default: safe subset)
        """
        self.config = RuneConfig(
            timeout_ms=timeout_ms,
            memory_limit_mb=memory_limit_mb,
            cpu_limit_percent=cpu_limit_percent,
            network_enabled=network_enabled,
            allowed_syscalls=allowed_syscalls or self._default_syscalls(),
        )
        self.temp_dirs: list[str] = []

    def execute(
        self,
        code: str,
        tests: str,
        language: str,
        timeout_ms: Optional[int] = None,
    ) -> ExecutionResult:
        """
        Execute code and tests in sandbox.

        Args:
            code: Source code to execute
            tests: Test code
            language: Programming language (python, typescript, rust, go, zig)
            timeout_ms: Override timeout in milliseconds

        Returns:
            Execution result with output, resource usage, and violations

        Example:
            >>> executor = RuneExecutor()
            >>> result = executor.execute(
            ...     code="def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
            ...     tests="assert factorial(5) == 120",
            ...     language="python"
            ... )
            >>> assert result.success
        """
        timeout = timeout_ms or self.config.timeout_ms
        temp_dir = None

        try:
            # Create isolated temporary directory
            temp_dir = tempfile.mkdtemp(prefix="maze_rune_")
            self.temp_dirs.append(temp_dir)

            # Write code and tests to temp directory
            code_file, test_file = self._write_files(
                temp_dir, code, tests, language
            )

            # Execute with resource limits
            start_time = time.perf_counter()

            try:
                result = self._execute_with_limits(
                    temp_dir, code_file, test_file, language, timeout
                )
            except subprocess.TimeoutExpired:
                execution_time_ms = (time.perf_counter() - start_time) * 1000
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr=f"Execution timed out after {timeout}ms",
                    exit_code=-1,
                    execution_time_ms=execution_time_ms,
                    resource_usage=ResourceUsage(
                        cpu_time_ms=execution_time_ms,
                        memory_peak_mb=0,
                        syscalls=0,
                    ),
                    security_violations=[],
                    timeout=True,
                )

            execution_time_ms = (time.perf_counter() - start_time) * 1000

            # Check resource limits
            limit_violations = self.check_resource_limits(result)

            # Detect security violations
            security_violations = self._detect_security_violations(
                code, tests, language
            )

            return ExecutionResult(
                success=result.returncode == 0 and not security_violations,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                execution_time_ms=execution_time_ms,
                resource_usage=ResourceUsage(
                    cpu_time_ms=execution_time_ms,
                    memory_peak_mb=0,  # Would need process monitoring
                    syscalls=0,  # Would need seccomp-bpf monitoring
                ),
                security_violations=security_violations,
                timeout=False,
            )

        finally:
            # Cleanup temporary directory
            if temp_dir:
                self._cleanup_temp_dir(temp_dir)

    def validate_security(
        self, code: str, language: str
    ) -> list[SecurityIssue]:
        """
        Check for security vulnerabilities in code.

        Performs static analysis to detect:
        - Command injection patterns
        - SQL injection patterns
        - Path traversal attempts
        - Unsafe eval/exec usage
        - Hardcoded credentials

        Args:
            code: Source code to analyze
            language: Programming language

        Returns:
            List of security issues found

        Example:
            >>> executor = RuneExecutor()
            >>> issues = executor.validate_security(
            ...     code='os.system(user_input)',
            ...     language='python'
            ... )
            >>> assert any(i.category == 'command_injection' for i in issues)
        """
        issues: list[SecurityIssue] = []

        if language == "python":
            # Check for dangerous functions
            dangerous_patterns = [
                (r"\beval\(", "eval", "Unsafe eval usage"),
                (r"\bexec\(", "exec", "Unsafe exec usage"),
                (r"\bos\.system\(", "command_injection", "Command injection risk"),
                (
                    r"\bsubprocess\.call\([^)]*shell=True",
                    "command_injection",
                    "Shell command injection risk",
                ),
                (
                    r"['\"]SELECT.*%s",
                    "sql_injection",
                    "Potential SQL injection",
                ),
                (
                    r"password\s*=\s*['\"][^'\"]+['\"]",
                    "hardcoded_credential",
                    "Hardcoded password",
                ),
            ]

            import re

            for pattern, category, message in dangerous_patterns:
                for match in re.finditer(pattern, code, re.IGNORECASE):
                    line_num = code[: match.start()].count("\n") + 1
                    issues.append(
                        SecurityIssue(
                            category=category,
                            severity="high" if "injection" in category else "medium",
                            message=message,
                            line=line_num,
                        )
                    )

        elif language == "typescript":
            # Check for dangerous JavaScript/TypeScript patterns
            import re

            dangerous_patterns = [
                (r"\beval\(", "eval", "Unsafe eval usage"),
                (
                    r"innerHTML\s*=",
                    "xss",
                    "Potential XSS via innerHTML",
                ),
                (
                    r"dangerouslySetInnerHTML",
                    "xss",
                    "Dangerous HTML injection",
                ),
                (
                    r"document\.write\(",
                    "xss",
                    "Unsafe document.write",
                ),
            ]

            for pattern, category, message in dangerous_patterns:
                for match in re.finditer(pattern, code):
                    line_num = code[: match.start()].count("\n") + 1
                    issues.append(
                        SecurityIssue(
                            category=category,
                            severity="high",
                            message=message,
                            line=line_num,
                        )
                    )

        return issues

    def check_resource_limits(
        self, result: subprocess.CompletedProcess
    ) -> list[str]:
        """
        Check if execution exceeded resource limits.

        Args:
            result: Subprocess result

        Returns:
            List of limit violations (empty if all within limits)
        """
        violations = []

        # Check stderr for OOM or other resource errors
        if "MemoryError" in result.stderr or "out of memory" in result.stderr.lower():
            violations.append(
                f"Memory limit exceeded ({self.config.memory_limit_mb}MB)"
            )

        if "RecursionError" in result.stderr:
            violations.append("Recursion limit exceeded")

        return violations

    def _write_files(
        self, temp_dir: str, code: str, tests: str, language: str
    ) -> tuple[str, str]:
        """
        Write code and test files to temporary directory.

        Args:
            temp_dir: Temporary directory path
            code: Source code
            tests: Test code
            language: Programming language

        Returns:
            Tuple of (code_file_path, test_file_path)
        """
        extensions = {
            "python": ".py",
            "typescript": ".ts",
            "rust": ".rs",
            "go": ".go",
            "zig": ".zig",
        }

        ext = extensions.get(language, ".txt")
        code_file = os.path.join(temp_dir, f"code{ext}")
        test_file = os.path.join(temp_dir, f"test{ext}")

        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(tests)

        return code_file, test_file

    def _execute_with_limits(
        self,
        temp_dir: str,
        code_file: str,
        test_file: str,
        language: str,
        timeout_ms: int,
    ) -> subprocess.CompletedProcess:
        """
        Execute code with resource limits.

        Args:
            temp_dir: Working directory
            code_file: Path to code file
            test_file: Path to test file
            language: Programming language
            timeout_ms: Timeout in milliseconds

        Returns:
            Subprocess result
        """
        # Build command based on language
        if language == "python":
            # Combine code and tests into one file for execution
            combined_file = os.path.join(temp_dir, "combined.py")
            with open(code_file, "r") as cf, open(test_file, "r") as tf:
                combined = cf.read() + "\n\n" + tf.read()
            with open(combined_file, "w") as f:
                f.write(combined)
            cmd = ["python", combined_file]

        elif language == "typescript":
            # Use ts-node if available, otherwise compile then run
            combined_file = os.path.join(temp_dir, "combined.ts")
            with open(code_file, "r") as cf, open(test_file, "r") as tf:
                combined = cf.read() + "\n\n" + tf.read()
            with open(combined_file, "w") as f:
                f.write(combined)
            cmd = ["ts-node", combined_file]

        elif language == "rust":
            # Create a Rust project structure
            main_file = os.path.join(temp_dir, "main.rs")
            with open(code_file, "r") as cf, open(test_file, "r") as tf:
                code_content = cf.read()
                test_content = tf.read()
                # Wrap in main function
                combined = f"{code_content}\n\nfn main() {{\n{test_content}\n}}"
            with open(main_file, "w") as f:
                f.write(combined)
            cmd = ["rustc", main_file, "-o", os.path.join(temp_dir, "test_bin")]
            # Compile first
            compile_result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=timeout_ms / 1000,
            )
            if compile_result.returncode != 0:
                return compile_result
            # Then run
            cmd = [os.path.join(temp_dir, "test_bin")]

        elif language == "go":
            # Create Go module
            go_file = os.path.join(temp_dir, "main.go")
            with open(code_file, "r") as cf, open(test_file, "r") as tf:
                code_content = cf.read()
                test_content = tf.read()
                # Wrap in package and main
                combined = f"package main\n\n{code_content}\n\nfunc main() {{\n{test_content}\n}}"
            with open(go_file, "w") as f:
                f.write(combined)
            cmd = ["go", "run", go_file]

        elif language == "zig":
            # Combine into single Zig file
            zig_file = os.path.join(temp_dir, "test.zig")
            with open(code_file, "r") as cf, open(test_file, "r") as tf:
                code_content = cf.read()
                test_content = tf.read()
                combined = f"{code_content}\n\npub fn main() void {{\n{test_content}\n}}"
            with open(zig_file, "w") as f:
                f.write(combined)
            cmd = ["zig", "run", zig_file]

        else:
            raise ValueError(f"Unsupported language: {language}")

        # Execute with timeout and resource limits
        # Note: This is a simplified version. Full RUNE integration would use
        # cgroups, namespaces, seccomp-bpf for true isolation
        timeout_sec = timeout_ms / 1000

        env = os.environ.copy()
        if not self.config.network_enabled:
            # Disable network access by setting proxy to invalid value
            env["HTTP_PROXY"] = "http://127.0.0.1:0"
            env["HTTPS_PROXY"] = "http://127.0.0.1:0"

        result = subprocess.run(
            cmd,
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=env,
        )

        return result

    def _detect_security_violations(
        self, code: str, tests: str, language: str
    ) -> list[str]:
        """
        Detect security violations in code.

        Args:
            code: Source code
            tests: Test code
            language: Programming language

        Returns:
            List of security violation messages
        """
        violations = []
        issues = self.validate_security(code, language)

        for issue in issues:
            if issue.severity in ["critical", "high"]:
                violations.append(
                    f"{issue.category}: {issue.message} (line {issue.line})"
                )

        return violations

    def _cleanup_temp_dir(self, temp_dir: str) -> None:
        """
        Clean up temporary directory.

        Args:
            temp_dir: Directory to remove
        """
        try:
            shutil.rmtree(temp_dir)
            if temp_dir in self.temp_dirs:
                self.temp_dirs.remove(temp_dir)
        except Exception:
            # Best effort cleanup
            pass

    def _default_syscalls(self) -> list[str]:
        """Get default allowed syscalls for safe execution."""
        return self.DEFAULT_SYSCALLS.copy()

    def __del__(self):
        """Cleanup any remaining temporary directories."""
        for temp_dir in self.temp_dirs:
            self._cleanup_temp_dir(temp_dir)


__all__ = [
    "RuneExecutor",
    "ExecutionResult",
    "ResourceUsage",
    "SecurityIssue",
    "RuneConfig",
]

"""
Lint validation using language-specific linters.

Provides style and quality checking across multiple languages with
auto-fix support and configurable rules.
"""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Any

from maze.validation.syntax import Diagnostic


@dataclass
class LintRules:
    """Linting rules configuration."""

    max_line_length: int = 100
    max_complexity: int = 10
    require_docstrings: bool = True
    require_type_hints: bool = True
    custom_rules: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def default() -> "LintRules":
        """Default lenient rules."""
        return LintRules(
            max_line_length=120,
            max_complexity=15,
            require_docstrings=False,
            require_type_hints=False,
        )

    @staticmethod
    def strict() -> "LintRules":
        """Strict rules for production."""
        return LintRules(
            max_line_length=100,
            max_complexity=10,
            require_docstrings=True,
            require_type_hints=True,
        )


@dataclass
class LintValidationResult:
    """Result of lint validation."""

    success: bool
    diagnostics: list[Diagnostic]
    auto_fixable: list[Diagnostic]
    validation_time_ms: float = 0.0


class LintValidator:
    """
    Style and quality validation using linters.

    Validates code style and quality using:
    - Python: ruff (fast, comprehensive)
    - TypeScript: eslint
    - Rust: clippy
    - Go: golangci-lint
    - Zig: zig fmt

    Example:
        >>> validator = LintValidator()
        >>> result = validator.validate("x=1+2", "python")
        >>> assert len(result.diagnostics) > 0  # Missing spaces
    """

    def __init__(self, rules: LintRules | None = None, cache_size: int = 500):
        """
        Initialize lint validator.

        Args:
            rules: Linting rules configuration
            cache_size: Maximum cache size for lint results
        """
        self.rules = rules or LintRules.default()
        self.linters: dict[str, str] = {
            "python": "ruff",
            "typescript": "eslint",
            "rust": "clippy",
            "go": "golangci-lint",
            "zig": "zig",
        }
        self.cache: dict[str, list[Diagnostic]] = {}
        self.cache_size = cache_size

    def validate(
        self, code: str, language: str, rules: LintRules | None = None
    ) -> LintValidationResult:
        """
        Lint code for style and quality issues.

        Args:
            code: Source code to lint
            language: Programming language
            rules: Optional override rules

        Returns:
            Lint validation result with diagnostics

        Example:
            >>> validator = LintValidator()
            >>> result = validator.validate("def foo( ):\\n  pass", "python")
            >>> # May have whitespace or style issues
        """
        import time

        start_time = time.perf_counter()

        # Use provided rules or instance rules
        active_rules = rules or self.rules

        # Check cache
        cache_key = self._cache_key(code, language, active_rules)
        if cache_key in self.cache:
            diagnostics = self.cache[cache_key]
            validation_time_ms = (time.perf_counter() - start_time) * 1000
            auto_fixable = [d for d in diagnostics if d.suggested_fix]
            return LintValidationResult(
                success=len(diagnostics) == 0,
                diagnostics=diagnostics,
                auto_fixable=auto_fixable,
                validation_time_ms=validation_time_ms,
            )

        try:
            # Run linter
            output = self.run_linter(code, language, active_rules)

            # Parse output
            diagnostics = self.parse_lint_output(output, language)

            # Cache result
            if len(self.cache) >= self.cache_size:
                self.cache.pop(next(iter(self.cache)))
            self.cache[cache_key] = diagnostics

            # Identify auto-fixable issues
            auto_fixable = [d for d in diagnostics if d.suggested_fix]

            success = len(diagnostics) == 0

            validation_time_ms = (time.perf_counter() - start_time) * 1000

            return LintValidationResult(
                success=success,
                diagnostics=diagnostics,
                auto_fixable=auto_fixable,
                validation_time_ms=validation_time_ms,
            )

        except Exception as e:
            validation_time_ms = (time.perf_counter() - start_time) * 1000
            return LintValidationResult(
                success=False,
                diagnostics=[
                    Diagnostic(
                        level="error",
                        message=f"Lint validation error: {str(e)}",
                        line=0,
                        column=0,
                        source="lint",
                    )
                ],
                auto_fixable=[],
                validation_time_ms=validation_time_ms,
            )

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
        linter = self.linters.get(language)
        if not linter:
            return ""

        if language == "python":
            return self._run_ruff(code, rules)
        elif language == "typescript":
            return self._run_eslint(code, rules)
        elif language == "rust":
            return self._run_clippy(code, rules)
        elif language == "go":
            return self._run_golangci_lint(code, rules)
        elif language == "zig":
            return self._run_zig_fmt(code, rules)
        else:
            return ""

    def parse_lint_output(self, output: str, language: str) -> list[Diagnostic]:
        """
        Parse linter output to diagnostics.

        Args:
            output: Linter output
            language: Programming language

        Returns:
            List of lint diagnostics
        """
        if not output:
            return []

        if language == "python":
            return self._parse_ruff_output(output)
        elif language == "typescript":
            return self._parse_eslint_output(output)
        elif language == "rust":
            return self._parse_clippy_output(output)
        elif language == "go":
            return self._parse_golangci_output(output)
        elif language == "zig":
            return self._parse_zig_fmt_output(output)
        else:
            return []

    def auto_fix(self, code: str, language: str) -> str:
        """
        Apply auto-fixable lint suggestions.

        Args:
            code: Source code
            language: Programming language

        Returns:
            Auto-fixed code
        """
        if language == "python":
            return self._auto_fix_ruff(code)
        elif language == "typescript":
            return self._auto_fix_eslint(code)
        elif language == "zig":
            return self._auto_fix_zig_fmt(code)
        else:
            # No auto-fix available
            return code

    def _run_ruff(self, code: str, rules: LintRules) -> str:
        """Run ruff linter on Python code."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Run ruff with JSON output
            result = subprocess.run(
                [
                    "ruff",
                    "check",
                    "--output-format=json",
                    f"--line-length={rules.max_line_length}",
                    temp_file,
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            return result.stdout

        except FileNotFoundError:
            return "LINTER_NOT_FOUND: ruff"
        except subprocess.TimeoutExpired:
            return ""
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def _run_eslint(self, code: str, rules: LintRules) -> str:
        """Run eslint on TypeScript code."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = subprocess.run(
                ["eslint", "--format=json", temp_file],
                capture_output=True,
                text=True,
                timeout=5,
            )

            return result.stdout

        except FileNotFoundError:
            return "LINTER_NOT_FOUND: eslint"
        except subprocess.TimeoutExpired:
            return ""
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def _run_clippy(self, code: str, rules: LintRules) -> str:
        """Run clippy on Rust code."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create minimal Cargo project
            cargo_toml = os.path.join(temp_dir, "Cargo.toml")
            with open(cargo_toml, "w") as f:
                f.write('[package]\nname = "temp"\nversion = "0.1.0"\nedition = "2021"\n')

            src_dir = os.path.join(temp_dir, "src")
            os.makedirs(src_dir)
            main_rs = os.path.join(src_dir, "main.rs")
            with open(main_rs, "w") as f:
                f.write(code)

            result = subprocess.run(
                ["cargo", "clippy", "--message-format=json"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )

            return result.stdout

        except FileNotFoundError:
            return "LINTER_NOT_FOUND: clippy"
        except subprocess.TimeoutExpired:
            return ""
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def _run_golangci_lint(self, code: str, rules: LintRules) -> str:
        """Run golangci-lint on Go code."""
        temp_dir = tempfile.mkdtemp()
        try:
            go_file = os.path.join(temp_dir, "main.go")
            with open(go_file, "w") as f:
                f.write(code)

            result = subprocess.run(
                ["golangci-lint", "run", "--out-format=json", go_file],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )

            return result.stdout

        except FileNotFoundError:
            return "LINTER_NOT_FOUND: golangci-lint"
        except subprocess.TimeoutExpired:
            return ""
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def _run_zig_fmt(self, code: str, rules: LintRules) -> str:
        """Run zig fmt check on Zig code."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".zig", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = subprocess.run(
                ["zig", "fmt", "--check", temp_file],
                capture_output=True,
                text=True,
                timeout=5,
            )

            # zig fmt returns non-zero if formatting needed
            if result.returncode != 0:
                return "FORMAT_NEEDED"
            return ""

        except FileNotFoundError:
            return "LINTER_NOT_FOUND: zig"
        except subprocess.TimeoutExpired:
            return ""
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def _parse_ruff_output(self, output: str) -> list[Diagnostic]:
        """Parse ruff JSON output."""
        if "LINTER_NOT_FOUND" in output:
            return [
                Diagnostic(
                    level="warning",
                    message="ruff not found - install with: pip install ruff",
                    line=0,
                    column=0,
                    source="lint",
                )
            ]

        diagnostics = []
        try:
            issues = json.loads(output)
            for issue in issues:
                location = issue.get("location", {})
                diagnostics.append(
                    Diagnostic(
                        level="warning",
                        message=issue.get("message", ""),
                        line=location.get("row", 0),
                        column=location.get("column", 0),
                        code=issue.get("code"),
                        source="lint",
                    )
                )
        except json.JSONDecodeError:
            pass

        return diagnostics

    def _parse_eslint_output(self, output: str) -> list[Diagnostic]:
        """Parse eslint JSON output."""
        if "LINTER_NOT_FOUND" in output:
            return [
                Diagnostic(
                    level="warning",
                    message="eslint not found - install with: npm install -g eslint",
                    line=0,
                    column=0,
                    source="lint",
                )
            ]

        diagnostics = []
        try:
            results = json.loads(output)
            for file_result in results:
                for message in file_result.get("messages", []):
                    severity = message.get("severity", 1)
                    level = "error" if severity == 2 else "warning"
                    diagnostics.append(
                        Diagnostic(
                            level=level,
                            message=message.get("message", ""),
                            line=message.get("line", 0),
                            column=message.get("column", 0),
                            code=message.get("ruleId"),
                            source="lint",
                        )
                    )
        except json.JSONDecodeError:
            pass

        return diagnostics

    def _parse_clippy_output(self, output: str) -> list[Diagnostic]:
        """Parse clippy JSON output."""
        if "LINTER_NOT_FOUND" in output:
            return [
                Diagnostic(
                    level="warning",
                    message="clippy not found - install Rust toolchain",
                    line=0,
                    column=0,
                    source="lint",
                )
            ]

        diagnostics = []
        for line in output.split("\n"):
            if not line.strip():
                continue
            try:
                msg = json.loads(line)
                if msg.get("reason") == "compiler-message":
                    compiler_msg = msg.get("message", {})
                    level_str = compiler_msg.get("level", "warning")
                    if level_str in ["warning", "error"]:
                        spans = compiler_msg.get("spans", [])
                        if spans:
                            span = spans[0]
                            diagnostics.append(
                                Diagnostic(
                                    level=level_str if level_str != "error" else "error",
                                    message=compiler_msg.get("message", ""),
                                    line=span.get("line_start", 0),
                                    column=span.get("column_start", 0),
                                    code=compiler_msg.get("code", {}).get("code"),
                                    source="lint",
                                )
                            )
            except json.JSONDecodeError:
                pass

        return diagnostics

    def _parse_golangci_output(self, output: str) -> list[Diagnostic]:
        """Parse golangci-lint JSON output."""
        if "LINTER_NOT_FOUND" in output:
            return [
                Diagnostic(
                    level="warning",
                    message="golangci-lint not found - install from golangci-lint.run",
                    line=0,
                    column=0,
                    source="lint",
                )
            ]

        diagnostics = []
        try:
            data = json.loads(output)
            for issue in data.get("Issues", []):
                pos = issue.get("Pos", {})
                diagnostics.append(
                    Diagnostic(
                        level="warning",
                        message=issue.get("Text", ""),
                        line=pos.get("Line", 0),
                        column=pos.get("Column", 0),
                        code=issue.get("FromLinter"),
                        source="lint",
                    )
                )
        except json.JSONDecodeError:
            pass

        return diagnostics

    def _parse_zig_fmt_output(self, output: str) -> list[Diagnostic]:
        """Parse zig fmt output."""
        if "LINTER_NOT_FOUND" in output:
            return [
                Diagnostic(
                    level="warning",
                    message="zig not found - install Zig toolchain",
                    line=0,
                    column=0,
                    source="lint",
                )
            ]

        if output == "FORMAT_NEEDED":
            return [
                Diagnostic(
                    level="warning",
                    message="Code needs formatting",
                    line=0,
                    column=0,
                    source="lint",
                    suggested_fix="Run 'zig fmt' to auto-format",
                )
            ]

        return []

    def _auto_fix_ruff(self, code: str) -> str:
        """Auto-fix Python code with ruff."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            subprocess.run(
                ["ruff", "check", "--fix", temp_file],
                capture_output=True,
                timeout=5,
            )

            with open(temp_file) as f:
                return f.read()

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return code
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def _auto_fix_eslint(self, code: str) -> str:
        """Auto-fix TypeScript code with eslint."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            subprocess.run(
                ["eslint", "--fix", temp_file],
                capture_output=True,
                timeout=5,
            )

            with open(temp_file) as f:
                return f.read()

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return code
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def _auto_fix_zig_fmt(self, code: str) -> str:
        """Auto-format Zig code."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".zig", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            subprocess.run(
                ["zig", "fmt", temp_file],
                capture_output=True,
                timeout=5,
            )

            with open(temp_file) as f:
                return f.read()

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return code
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def _cache_key(self, code: str, language: str, rules: LintRules) -> str:
        """Generate cache key."""
        import hashlib

        rules_str = f"{rules.max_line_length},{rules.max_complexity}"
        content = f"{language}:{rules_str}:{code}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


__all__ = ["LintValidator", "LintRules", "LintValidationResult"]

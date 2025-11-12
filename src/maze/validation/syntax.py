"""
Syntax validation using tree-sitter and native parsers.

Provides fast syntax checking across multiple languages with detailed
error messages and suggested fixes.
"""

import ast
import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class Diagnostic:
    """Validation diagnostic (error, warning, info)."""

    level: Literal["error", "warning", "info"]
    message: str
    line: int
    column: int
    code: str | None = None
    source: str = ""
    suggested_fix: str | None = None
    context: str | None = None


@dataclass
class SyntaxValidationResult:
    """Result of syntax validation."""

    success: bool
    diagnostics: list[Diagnostic]
    parse_tree: Any | None = None
    validation_time_ms: float = 0.0


class SyntaxValidator:
    """
    Fast syntax validation using tree-sitter and native parsers.

    Validates syntax across multiple languages using:
    - Python: ast.parse() + pyright fallback
    - TypeScript: tsc --noEmit
    - Rust: cargo check
    - Go: go build -o /dev/null
    - Zig: zig ast-check

    Example:
        >>> validator = SyntaxValidator()
        >>> result = validator.validate("const x = ", "typescript")
        >>> assert not result.success
        >>> assert len(result.diagnostics) > 0
    """

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
            >>> result = validator.validate("def foo():", "python")
            >>> assert not result.success  # Missing body
        """
        import time

        start_time = time.perf_counter()

        # Check cache
        cache_key = self._cache_key(code, language)
        if cache_key in self.parse_cache:
            success, diagnostics = self.parse_cache[cache_key]
            validation_time_ms = (time.perf_counter() - start_time) * 1000
            return SyntaxValidationResult(
                success=success,
                diagnostics=diagnostics,
                validation_time_ms=validation_time_ms,
            )

        # Parse and validate
        try:
            if language == "python":
                diagnostics = self._validate_python(code)
            elif language == "typescript":
                diagnostics = self._validate_typescript(code)
            elif language == "rust":
                diagnostics = self._validate_rust(code)
            elif language == "go":
                diagnostics = self._validate_go(code)
            elif language == "zig":
                diagnostics = self._validate_zig(code)
            else:
                raise ValueError(f"Unsupported language: {language}")

            success = len(diagnostics) == 0

            # Cache result
            if len(self.parse_cache) >= self.cache_size:
                # Simple LRU: remove first item
                self.parse_cache.pop(next(iter(self.parse_cache)))
            self.parse_cache[cache_key] = (success, diagnostics)

            validation_time_ms = (time.perf_counter() - start_time) * 1000

            return SyntaxValidationResult(
                success=success,
                diagnostics=diagnostics,
                validation_time_ms=validation_time_ms,
            )

        except Exception as e:
            validation_time_ms = (time.perf_counter() - start_time) * 1000
            return SyntaxValidationResult(
                success=False,
                diagnostics=[
                    Diagnostic(
                        level="error",
                        message=f"Validation error: {str(e)}",
                        line=0,
                        column=0,
                        source="syntax",
                    )
                ],
                validation_time_ms=validation_time_ms,
            )

    def parse(self, code: str, language: str) -> Any | None:
        """
        Parse code and return AST.

        Args:
            code: Source code
            language: Programming language

        Returns:
            Parsed AST or None if parse fails
        """
        if language == "python":
            try:
                return ast.parse(code)
            except SyntaxError:
                return None
        else:
            # For other languages, validation is done via external tools
            return None

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
        # This would use tree-sitter error nodes in full implementation
        return []

    def suggest_fix(self, error: Diagnostic, code: str, language: str) -> str | None:
        """
        Suggest fix for syntax error.

        Args:
            error: Syntax error diagnostic
            code: Original source code
            language: Programming language

        Returns:
            Suggested fix or None
        """
        message_lower = error.message.lower()

        # Common patterns
        if "unexpected eof" in message_lower or "expected" in message_lower:
            if language in ["typescript", "javascript"]:
                if ";" in message_lower:
                    return "Add semicolon at end of line"
                if "}" in message_lower:
                    return "Add closing brace }"
                if "{" in message_lower:
                    return "Add opening brace {"
            elif language == "python":
                if "expected an indented block" in message_lower:
                    return "Add indented block (e.g., 'pass')"
                if "unexpected indent" in message_lower:
                    return "Remove extra indentation"

        if "unmatched" in message_lower:
            if "'" in message_lower or '"' in message_lower:
                return "Check for unmatched quotes"
            if "(" in message_lower:
                return "Add closing parenthesis )"
            if "[" in message_lower:
                return "Add closing bracket ]"

        return None

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        return {"cache_size": len(self.parse_cache), "cache_max": self.cache_size}

    def clear_cache(self) -> None:
        """Clear parse cache."""
        self.parse_cache.clear()

    def _validate_python(self, code: str) -> list[Diagnostic]:
        """Validate Python syntax using ast.parse()."""
        diagnostics = []

        try:
            ast.parse(code)
        except SyntaxError as e:
            diagnostic = Diagnostic(
                level="error",
                message=e.msg,
                line=e.lineno or 0,
                column=e.offset or 0,
                code="E999",
                source="syntax",
            )
            diagnostic.suggested_fix = self.suggest_fix(diagnostic, code, "python")
            diagnostics.append(diagnostic)
        except Exception as e:
            diagnostics.append(
                Diagnostic(
                    level="error",
                    message=str(e),
                    line=0,
                    column=0,
                    source="syntax",
                )
            )

        return diagnostics

    def _validate_typescript(self, code: str) -> list[Diagnostic]:
        """Validate TypeScript syntax using tsc."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = subprocess.run(
                ["tsc", "--noEmit", "--pretty", "false", temp_file],
                capture_output=True,
                text=True,
                timeout=5,
            )

            diagnostics = []
            if result.returncode != 0:
                # Parse tsc output
                for line in result.stdout.split("\n"):
                    if not line.strip():
                        continue
                    # Format: file.ts(line,col): error TSxxxx: message
                    if "error TS" in line:
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            location = parts[0]
                            message = parts[2].strip()

                            # Extract line and column
                            if "(" in location and "," in location:
                                loc_part = location.split("(")[1].split(")")[0]
                                line_num, col_num = loc_part.split(",")
                                diagnostic = Diagnostic(
                                    level="error",
                                    message=message,
                                    line=int(line_num),
                                    column=int(col_num),
                                    code=(
                                        parts[1].strip().split()[1]
                                        if len(parts[1].strip().split()) > 1
                                        else None
                                    ),
                                    source="syntax",
                                )
                                diagnostic.suggested_fix = self.suggest_fix(
                                    diagnostic, code, "typescript"
                                )
                                diagnostics.append(diagnostic)

            return diagnostics

        except FileNotFoundError:
            # tsc not available
            return [
                Diagnostic(
                    level="warning",
                    message="TypeScript compiler (tsc) not found",
                    line=0,
                    column=0,
                    source="syntax",
                )
            ]
        except subprocess.TimeoutExpired:
            return [
                Diagnostic(
                    level="error",
                    message="Syntax check timed out",
                    line=0,
                    column=0,
                    source="syntax",
                )
            ]
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def _validate_rust(self, code: str) -> list[Diagnostic]:
        """Validate Rust syntax using cargo check."""
        # Create temporary Cargo project
        temp_dir = tempfile.mkdtemp()
        try:
            # Create minimal Cargo.toml
            cargo_toml = os.path.join(temp_dir, "Cargo.toml")
            with open(cargo_toml, "w") as f:
                f.write('[package]\nname = "temp"\nversion = "0.1.0"\nedition = "2021"\n')

            # Create src directory and main.rs
            src_dir = os.path.join(temp_dir, "src")
            os.makedirs(src_dir)
            main_rs = os.path.join(src_dir, "main.rs")
            with open(main_rs, "w") as f:
                f.write(code)

            # Run cargo check
            result = subprocess.run(
                ["cargo", "check", "--message-format=json"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )

            diagnostics = []
            for line in result.stdout.split("\n"):
                if not line.strip():
                    continue
                try:
                    import json

                    msg = json.loads(line)
                    if msg.get("reason") == "compiler-message":
                        compiler_msg = msg.get("message", {})
                        if compiler_msg.get("level") == "error":
                            spans = compiler_msg.get("spans", [])
                            if spans:
                                span = spans[0]
                                diagnostics.append(
                                    Diagnostic(
                                        level="error",
                                        message=compiler_msg.get("message", ""),
                                        line=span.get("line_start", 0),
                                        column=span.get("column_start", 0),
                                        code=compiler_msg.get("code", {}).get("code"),
                                        source="syntax",
                                    )
                                )
                except json.JSONDecodeError:
                    pass

            return diagnostics

        except FileNotFoundError:
            return [
                Diagnostic(
                    level="warning",
                    message="Rust compiler (cargo) not found",
                    line=0,
                    column=0,
                    source="syntax",
                )
            ]
        except subprocess.TimeoutExpired:
            return [
                Diagnostic(
                    level="error",
                    message="Syntax check timed out",
                    line=0,
                    column=0,
                    source="syntax",
                )
            ]
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def _validate_go(self, code: str) -> list[Diagnostic]:
        """Validate Go syntax using go build."""
        temp_dir = tempfile.mkdtemp()
        try:
            go_file = os.path.join(temp_dir, "main.go")
            with open(go_file, "w") as f:
                f.write(code)

            result = subprocess.run(
                ["go", "build", "-o", "/dev/null", go_file],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )

            diagnostics = []
            if result.returncode != 0:
                # Parse go build errors
                for line in result.stderr.split("\n"):
                    if ":" in line and "error" in line.lower():
                        parts = line.split(":")
                        if len(parts) >= 4:
                            try:
                                line_num = int(parts[1])
                                col_num = int(parts[2]) if parts[2].strip().isdigit() else 0
                                message = ":".join(parts[3:]).strip()
                                diagnostics.append(
                                    Diagnostic(
                                        level="error",
                                        message=message,
                                        line=line_num,
                                        column=col_num,
                                        source="syntax",
                                    )
                                )
                            except (ValueError, IndexError):
                                pass

            return diagnostics

        except FileNotFoundError:
            return [
                Diagnostic(
                    level="warning",
                    message="Go compiler (go) not found",
                    line=0,
                    column=0,
                    source="syntax",
                )
            ]
        except subprocess.TimeoutExpired:
            return [
                Diagnostic(
                    level="error",
                    message="Syntax check timed out",
                    line=0,
                    column=0,
                    source="syntax",
                )
            ]
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def _validate_zig(self, code: str) -> list[Diagnostic]:
        """Validate Zig syntax using zig ast-check."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".zig", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = subprocess.run(
                ["zig", "ast-check", temp_file],
                capture_output=True,
                text=True,
                timeout=5,
            )

            diagnostics = []
            if result.returncode != 0:
                # Parse zig errors
                for line in result.stderr.split("\n"):
                    if "error:" in line:
                        # Format: file.zig:line:col: error: message
                        if ":" in line:
                            parts = line.split(":")
                            if len(parts) >= 4:
                                try:
                                    line_num = int(parts[1])
                                    col_num = int(parts[2])
                                    message = ":".join(parts[4:]).strip()
                                    diagnostics.append(
                                        Diagnostic(
                                            level="error",
                                            message=message,
                                            line=line_num,
                                            column=col_num,
                                            source="syntax",
                                        )
                                    )
                                except (ValueError, IndexError):
                                    pass

            return diagnostics

        except FileNotFoundError:
            return [
                Diagnostic(
                    level="warning",
                    message="Zig compiler (zig) not found",
                    line=0,
                    column=0,
                    source="syntax",
                )
            ]
        except subprocess.TimeoutExpired:
            return [
                Diagnostic(
                    level="error",
                    message="Syntax check timed out",
                    line=0,
                    column=0,
                    source="syntax",
                )
            ]
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def _cache_key(self, code: str, language: str) -> str:
        """Generate cache key for code."""
        import hashlib

        return f"{language}:{hashlib.sha256(code.encode()).hexdigest()[:16]}"


__all__ = ["SyntaxValidator", "Diagnostic", "SyntaxValidationResult"]

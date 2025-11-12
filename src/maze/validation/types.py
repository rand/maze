"""
Type validation using language-specific type checkers.

Provides type checking across multiple languages using native type checkers
and integration with Phase 3 type system for TypeScript.
"""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Any

from maze.validation.syntax import Diagnostic


@dataclass
class TypeValidationResult:
    """Result of type validation."""

    success: bool
    diagnostics: list[Diagnostic]
    type_errors: list[str]
    validation_time_ms: float = 0.0


class TypeValidator:
    """
    Type validation using language-specific type checkers.

    Validates types across multiple languages using:
    - TypeScript: Phase 3 type system + tsc fallback
    - Python: pyright
    - Rust: rust-analyzer / cargo check
    - Go: go build
    - Zig: zig build-obj

    Example:
        >>> from maze.core.types import Type, TypeContext
        >>> validator = TypeValidator()
        >>> context = TypeContext(variables={"x": Type("number")})
        >>> result = validator.validate('const y: string = x;', "typescript", context)
        >>> assert not result.success
    """

    def __init__(self, type_system: Any | None = None):
        """
        Initialize type validator.

        Args:
            type_system: Optional TypeSystemOrchestrator from Phase 3
        """
        self.type_system = type_system
        self.checkers: dict[str, callable] = {
            "typescript": self.check_typescript,
            "python": self.check_python,
            "rust": self.check_rust,
            "go": self.check_go,
            "zig": self.check_zig,
        }

    def validate(self, code: str, language: str, context: Any) -> TypeValidationResult:
        """
        Validate types in code.

        Args:
            code: Source code to validate
            language: Programming language
            context: Type context (TypeContext from Phase 3)

        Returns:
            Validation result with type diagnostics

        Example:
            >>> from maze.core.types import TypeContext
            >>> validator = TypeValidator()
            >>> result = validator.validate('x: number = "hello"', "typescript", TypeContext())
            >>> assert not result.success
        """
        import time

        start_time = time.perf_counter()

        try:
            checker = self.checkers.get(language)
            if not checker:
                raise ValueError(f"Unsupported language: {language}")

            diagnostics = checker(code, context)
            type_errors = [d.message for d in diagnostics if d.level == "error"]
            success = len(diagnostics) == 0

            validation_time_ms = (time.perf_counter() - start_time) * 1000

            return TypeValidationResult(
                success=success,
                diagnostics=diagnostics,
                type_errors=type_errors,
                validation_time_ms=validation_time_ms,
            )

        except Exception as e:
            validation_time_ms = (time.perf_counter() - start_time) * 1000
            return TypeValidationResult(
                success=False,
                diagnostics=[
                    Diagnostic(
                        level="error",
                        message=f"Type validation error: {str(e)}",
                        line=0,
                        column=0,
                        source="type",
                    )
                ],
                type_errors=[str(e)],
                validation_time_ms=validation_time_ms,
            )

    def check_typescript(self, code: str, context: Any) -> list[Diagnostic]:
        """
        TypeScript type checking using Phase 3 type system or tsc.

        First tries to use Phase 3 TypeSystemOrchestrator for fast checking,
        falls back to tsc if Phase 3 not available.
        """
        # Try Phase 3 type system first
        if self.type_system:
            try:
                # Use Phase 3 for basic type checking
                # This is a simplified integration - full implementation would
                # parse the code and check types using the type system
                diagnostics = []

                # For now, fall through to tsc for comprehensive checking
                # Full integration would involve parsing and type inference
            except Exception:
                pass

        # Use tsc for comprehensive type checking
        return self._check_with_tsc(code)

    def check_python(self, code: str, context: Any) -> list[Diagnostic]:
        """Python type checking using pyright."""
        with tempfile.TemporaryDirectory() as temp_dir:
            py_file = os.path.join(temp_dir, "check.py")
            with open(py_file, "w") as f:
                f.write(code)

            try:
                result = subprocess.run(
                    ["pyright", "--outputjson", py_file],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                return self.parse_type_errors(result.stdout, "python")

            except FileNotFoundError:
                return [
                    Diagnostic(
                        level="warning",
                        message="pyright not found - install with: pip install pyright",
                        line=0,
                        column=0,
                        source="type",
                    )
                ]
            except subprocess.TimeoutExpired:
                return [
                    Diagnostic(
                        level="error",
                        message="Type check timed out",
                        line=0,
                        column=0,
                        source="type",
                    )
                ]

    def check_rust(self, code: str, context: Any) -> list[Diagnostic]:
        """Rust type checking using cargo check."""
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
                    msg = json.loads(line)
                    if msg.get("reason") == "compiler-message":
                        compiler_msg = msg.get("message", {})
                        level = compiler_msg.get("level", "error")
                        if level in ["error", "warning"]:
                            spans = compiler_msg.get("spans", [])
                            if spans:
                                span = spans[0]
                                diagnostics.append(
                                    Diagnostic(
                                        level=level if level != "error" else "error",
                                        message=compiler_msg.get("message", ""),
                                        line=span.get("line_start", 0),
                                        column=span.get("column_start", 0),
                                        code=compiler_msg.get("code", {}).get("code"),
                                        source="type",
                                    )
                                )
                except json.JSONDecodeError:
                    pass

            return diagnostics

        except FileNotFoundError:
            return [
                Diagnostic(
                    level="warning",
                    message="cargo not found - install Rust toolchain",
                    line=0,
                    column=0,
                    source="type",
                )
            ]
        except subprocess.TimeoutExpired:
            return [
                Diagnostic(
                    level="error",
                    message="Type check timed out",
                    line=0,
                    column=0,
                    source="type",
                )
            ]
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def check_go(self, code: str, context: Any) -> list[Diagnostic]:
        """Go type checking using go build."""
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
                # Parse go build errors (includes type errors)
                for line in result.stderr.split("\n"):
                    if ":" in line:
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
                                        source="type",
                                    )
                                )
                            except (ValueError, IndexError):
                                pass

            return diagnostics

        except FileNotFoundError:
            return [
                Diagnostic(
                    level="warning",
                    message="go not found - install Go toolchain",
                    line=0,
                    column=0,
                    source="type",
                )
            ]
        except subprocess.TimeoutExpired:
            return [
                Diagnostic(
                    level="error",
                    message="Type check timed out",
                    line=0,
                    column=0,
                    source="type",
                )
            ]
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def check_zig(self, code: str, context: Any) -> list[Diagnostic]:
        """Zig type checking using zig build-obj."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".zig", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = subprocess.run(
                ["zig", "build-obj", temp_file, "--name", "temp"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            diagnostics = []
            if result.returncode != 0:
                # Parse zig errors (includes type errors)
                for line in result.stderr.split("\n"):
                    if "error:" in line:
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
                                            source="type",
                                        )
                                    )
                                except (ValueError, IndexError):
                                    pass

            return diagnostics

        except FileNotFoundError:
            return [
                Diagnostic(
                    level="warning",
                    message="zig not found - install Zig toolchain",
                    line=0,
                    column=0,
                    source="type",
                )
            ]
        except subprocess.TimeoutExpired:
            return [
                Diagnostic(
                    level="error",
                    message="Type check timed out",
                    line=0,
                    column=0,
                    source="type",
                )
            ]
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def parse_type_errors(self, output: str, language: str) -> list[Diagnostic]:
        """
        Parse type checker output into diagnostics.

        Args:
            output: Raw type checker output
            language: Programming language

        Returns:
            List of type diagnostics
        """
        diagnostics = []

        if language == "python":
            # Parse pyright JSON output
            try:
                data = json.loads(output)
                for diag in data.get("generalDiagnostics", []):
                    severity = diag.get("severity", "error")
                    level = "error" if severity == "error" else "warning"

                    range_info = diag.get("range", {})
                    start = range_info.get("start", {})

                    diagnostics.append(
                        Diagnostic(
                            level=level,
                            message=diag.get("message", ""),
                            line=start.get("line", 0) + 1,  # pyright uses 0-based
                            column=start.get("character", 0),
                            code=diag.get("rule"),
                            source="type",
                        )
                    )
            except json.JSONDecodeError:
                pass

        elif language == "typescript":
            # Parse tsc output
            for line in output.split("\n"):
                if not line.strip() or "error TS" not in line:
                    continue

                # Format: file.ts(line,col): error TSxxxx: message
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    location = parts[0]
                    message = parts[2].strip()

                    if "(" in location and "," in location:
                        loc_part = location.split("(")[1].split(")")[0]
                        line_num, col_num = loc_part.split(",")

                        code_match = parts[1].strip().split()
                        code = code_match[1] if len(code_match) > 1 else None

                        diagnostics.append(
                            Diagnostic(
                                level="error",
                                message=message,
                                line=int(line_num),
                                column=int(col_num),
                                code=code,
                                source="type",
                            )
                        )

        return diagnostics

    def suggest_type_fix(self, error: Diagnostic, code: str, context: Any) -> str | None:
        """
        Suggest fix for type error.

        Args:
            error: Type error diagnostic
            code: Original source code
            context: Type context

        Returns:
            Suggested type annotation or cast
        """
        message_lower = error.message.lower()

        # Type mismatch suggestions
        if "type" in message_lower and "not assignable" in message_lower:
            return "Check type compatibility or add type cast"

        if "cannot find name" in message_lower or "undefined" in message_lower:
            return "Declare variable or import required module"

        if "missing" in message_lower and "type" in message_lower:
            return "Add type annotation"

        if "expected" in message_lower and "arguments" in message_lower:
            return "Check function signature and argument count"

        return None

    def _check_with_tsc(self, code: str) -> list[Diagnostic]:
        """Check TypeScript code with tsc."""
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

            return self.parse_type_errors(result.stdout, "typescript")

        except FileNotFoundError:
            return [
                Diagnostic(
                    level="warning",
                    message="tsc not found - install TypeScript",
                    line=0,
                    column=0,
                    source="type",
                )
            ]
        except subprocess.TimeoutExpired:
            return [
                Diagnostic(
                    level="error",
                    message="Type check timed out",
                    line=0,
                    column=0,
                    source="type",
                )
            ]
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


__all__ = ["TypeValidator", "TypeValidationResult"]

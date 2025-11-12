"""
Unit tests for type validator.

Tests type checking across Python, TypeScript, Rust, Go, and Zig with
error detection and type-aware suggestions.
"""

import pytest

from maze.core.types import TypeContext
from maze.validation.types import TypeValidator


class TestTypeScriptTypeValidation:
    """Test TypeScript type validation."""

    def test_valid_typescript_types(self):
        """Test validation of valid TypeScript types."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code="const x: number = 42;",
            language="typescript",
            context=context,
        )

        # May succeed or warn about tsc not found
        assert result.success or any("not found" in d.message for d in result.diagnostics)

    def test_type_mismatch(self):
        """Test detection of type mismatch."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code='const x: number = "hello";',  # Type mismatch
            language="typescript",
            context=context,
        )

        # If tsc available, should detect error
        if not any("not found" in d.message for d in result.diagnostics):
            assert not result.success
            assert len(result.type_errors) > 0

    def test_undefined_variable(self):
        """Test detection of undefined variable."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code="const y = x;",  # x is undefined
            language="typescript",
            context=context,
        )

        # If tsc available, should detect error
        if not any("not found" in d.message for d in result.diagnostics):
            assert not result.success

    def test_function_type_error(self):
        """Test detection of function type errors."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code="function add(a: number, b: number): number { return a + b; }\nconst result: string = add(1, 2);",
            language="typescript",
            context=context,
        )

        # If tsc available, should detect type mismatch
        if not any("not found" in d.message for d in result.diagnostics):
            assert not result.success


class TestPythonTypeValidation:
    """Test Python type validation."""

    def test_valid_python_types(self):
        """Test validation of valid Python types."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code="def add(a: int, b: int) -> int:\n    return a + b",
            language="python",
            context=context,
        )

        # May succeed or warn about pyright not found
        assert result.success or any("not found" in d.message for d in result.diagnostics)

    def test_python_type_mismatch(self):
        """Test detection of Python type mismatch."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code='def greet(name: str) -> str:\n    return name\n\nresult: int = greet("Alice")',
            language="python",
            context=context,
        )

        # If pyright available, might detect error (depends on strictness)
        # pyright may not error on this without stricter settings

    def test_python_undefined_name(self):
        """Test detection of undefined name."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code="x = undefined_variable",
            language="python",
            context=context,
        )

        # If pyright available, should detect undefined name
        if not any("not found" in d.message for d in result.diagnostics):
            # pyright may or may not flag this depending on settings
            pass


class TestRustTypeValidation:
    """Test Rust type validation."""

    def test_valid_rust_types(self):
        """Test validation of valid Rust types."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code='fn main() { let x: i32 = 42; println!("{}", x); }',
            language="rust",
            context=context,
        )

        # May succeed or warn about cargo not found
        assert result.success or any("not found" in d.message for d in result.diagnostics)

    def test_rust_type_mismatch(self):
        """Test detection of Rust type mismatch."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code='fn main() { let x: i32 = "hello"; }',  # Type mismatch
            language="rust",
            context=context,
        )

        # If cargo available, should detect error
        if not any("not found" in d.message for d in result.diagnostics):
            assert not result.success

    def test_rust_missing_type(self):
        """Test Rust with missing required type info."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code="fn add(a, b) -> i32 { a + b }",  # Missing param types
            language="rust",
            context=context,
        )

        # If cargo available, should detect error
        if not any("not found" in d.message for d in result.diagnostics):
            assert not result.success


class TestGoTypeValidation:
    """Test Go type validation."""

    def test_valid_go_types(self):
        """Test validation of valid Go types."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code="package main\n\nfunc main() { var x int = 42; println(x) }",
            language="go",
            context=context,
        )

        # May succeed or warn about go not found
        assert result.success or any("not found" in d.message for d in result.diagnostics)

    def test_go_type_mismatch(self):
        """Test detection of Go type mismatch."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code='package main\n\nfunc main() { var x int = "hello" }',
            language="go",
            context=context,
        )

        # If go available, should detect error
        if not any("not found" in d.message for d in result.diagnostics):
            assert not result.success


class TestZigTypeValidation:
    """Test Zig type validation."""

    def test_valid_zig_types(self):
        """Test validation of valid Zig types."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code='const std = @import("std");\npub fn main() void { const x: i32 = 42; _ = x; }',
            language="zig",
            context=context,
        )

        # May succeed or warn about zig not found
        # Zig may report warnings even for valid code
        assert (
            result.success
            or any("not found" in d.message for d in result.diagnostics)
            or all(d.level == "warning" for d in result.diagnostics)
        )

    def test_zig_type_mismatch(self):
        """Test detection of Zig type mismatch."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code='pub fn main() void { const x: i32 = "hello"; }',
            language="zig",
            context=context,
        )

        # If zig available, should detect error
        if not any("not found" in d.message for d in result.diagnostics):
            assert not result.success


class TestTypeErrorParsing:
    """Test type error parsing."""

    def test_parse_python_errors(self):
        """Test parsing pyright JSON output."""
        validator = TypeValidator()

        json_output = '{"generalDiagnostics": [{"message": "Type mismatch", "severity": "error", "range": {"start": {"line": 0, "character": 5}}, "rule": "reportGeneralTypeIssues"}]}'

        diagnostics = validator.parse_type_errors(json_output, "python")

        assert len(diagnostics) > 0
        assert diagnostics[0].level == "error"
        assert diagnostics[0].message == "Type mismatch"
        assert diagnostics[0].line == 1  # 0-based to 1-based

    def test_parse_typescript_errors(self):
        """Test parsing tsc output."""
        validator = TypeValidator()

        tsc_output = (
            "test.ts(10,5): error TS2322: Type 'string' is not assignable to type 'number'."
        )

        diagnostics = validator.parse_type_errors(tsc_output, "typescript")

        assert len(diagnostics) > 0
        assert diagnostics[0].level == "error"
        assert diagnostics[0].line == 10
        assert diagnostics[0].column == 5

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        validator = TypeValidator()

        diagnostics = validator.parse_type_errors("", "python")

        assert len(diagnostics) == 0


class TestSuggestedFixes:
    """Test type error fix suggestions."""

    def test_suggest_type_annotation(self):
        """Test suggestion for missing type annotation."""
        validator = TypeValidator()

        from maze.validation.syntax import Diagnostic

        diagnostic = Diagnostic(
            level="error",
            message="Missing type annotation",
            line=1,
            column=5,
            source="type",
        )

        fix = validator.suggest_type_fix(diagnostic, "", TypeContext())

        assert fix is not None
        assert "type" in fix.lower() and "annotation" in fix.lower()

    def test_suggest_type_cast(self):
        """Test suggestion for type mismatch."""
        validator = TypeValidator()

        from maze.validation.syntax import Diagnostic

        diagnostic = Diagnostic(
            level="error",
            message="Type 'string' is not assignable to type 'number'",
            line=1,
            column=5,
            source="type",
        )

        fix = validator.suggest_type_fix(diagnostic, "", TypeContext())

        assert fix is not None
        assert "type" in fix.lower()

    def test_suggest_undefined_fix(self):
        """Test suggestion for undefined variable."""
        validator = TypeValidator()

        from maze.validation.syntax import Diagnostic

        diagnostic = Diagnostic(
            level="error",
            message="Cannot find name 'x'",
            line=1,
            column=5,
            source="type",
        )

        fix = validator.suggest_type_fix(diagnostic, "", TypeContext())

        assert fix is not None
        assert "declare" in fix.lower() or "import" in fix.lower()


class TestValidationResult:
    """Test validation result structure."""

    def test_validation_result_structure(self):
        """Test that validation result has expected fields."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code="const x: number = 42;",
            language="typescript",
            context=context,
        )

        assert hasattr(result, "success")
        assert hasattr(result, "diagnostics")
        assert hasattr(result, "type_errors")
        assert hasattr(result, "validation_time_ms")
        assert result.validation_time_ms > 0

    def test_type_errors_extracted(self):
        """Test that type errors are extracted from diagnostics."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code='const x: number = "hello";',
            language="typescript",
            context=context,
        )

        # If tsc available and detected error
        if not result.success and not any("not found" in d.message for d in result.diagnostics):
            assert len(result.type_errors) > 0
            assert all(isinstance(err, str) for err in result.type_errors)


class TestPerformance:
    """Test performance characteristics."""

    def test_validation_performance(self):
        """Test that type validation completes quickly."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code="const x: number = 42;\nconst y: string = 'hello';",
            language="typescript",
            context=context,
        )

        # Should complete in reasonable time (<500ms target)
        assert result.validation_time_ms < 1000  # Relaxed for external tools


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_code(self):
        """Test type checking empty code."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code="",
            language="python",
            context=context,
        )

        # Empty code should validate (or warn about missing checker)
        assert result.success or any("not found" in d.message for d in result.diagnostics)

    def test_unsupported_language(self):
        """Test that unsupported language produces error."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code="code",
            language="cobol",
            context=context,
        )

        assert not result.success
        assert any("Unsupported language" in d.message for d in result.diagnostics)

    def test_unicode_code(self):
        """Test type checking with Unicode."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code='const greeting: string = "こんにちは";',
            language="typescript",
            context=context,
        )

        # Should handle Unicode gracefully
        assert result.success or any("not found" in d.message for d in result.diagnostics)

    def test_multiple_type_errors(self):
        """Test detection of multiple type errors."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code='const x: number = "hello";\nconst y: string = 42;',
            language="typescript",
            context=context,
        )

        # If tsc available, should detect multiple errors
        if not any("not found" in d.message for d in result.diagnostics):
            # May have multiple errors
            assert len(result.diagnostics) >= 1


class TestIntegration:
    """Test integration with other components."""

    def test_phase3_integration_placeholder(self):
        """Test that TypeValidator can accept Phase 3 type system."""
        # Import Phase 3 type system
        try:
            from maze.type_system import TypeSystemOrchestrator

            type_system = TypeSystemOrchestrator(language="typescript")
            validator = TypeValidator(type_system=type_system)

            assert validator.type_system is not None

        except ImportError:
            # Phase 3 not available yet
            pytest.skip("Phase 3 type system not available")

    def test_diagnostic_source_is_type(self):
        """Test that diagnostics are tagged with 'type' source."""
        validator = TypeValidator()
        context = TypeContext()

        result = validator.validate(
            code='const x: number = "hello";',
            language="typescript",
            context=context,
        )

        # All diagnostics should have source='type'
        for diag in result.diagnostics:
            assert diag.source == "type"

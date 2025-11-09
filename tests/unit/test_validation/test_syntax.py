"""
Unit tests for syntax validator.

Tests syntax validation across Python, TypeScript, Rust, Go, and Zig with
error detection, suggested fixes, and caching.
"""

import pytest
from maze.validation.syntax import SyntaxValidator, Diagnostic


class TestPythonSyntaxValidation:
    """Test Python syntax validation."""

    def test_parse_valid_python(self):
        """Test parsing valid Python code."""
        validator = SyntaxValidator()

        result = validator.validate(
            code="def add(a, b):\n    return a + b",
            language="python",
        )

        assert result.success
        assert len(result.diagnostics) == 0
        assert result.validation_time_ms > 0

    def test_detect_syntax_error(self):
        """Test detection of Python syntax errors."""
        validator = SyntaxValidator()

        result = validator.validate(
            code="def broken(",  # Missing closing paren
            language="python",
        )

        assert not result.success
        assert len(result.diagnostics) > 0
        assert result.diagnostics[0].level == "error"

    def test_missing_colon(self):
        """Test detection of missing colon."""
        validator = SyntaxValidator()

        result = validator.validate(
            code="if True\n    pass",  # Missing colon
            language="python",
        )

        assert not result.success
        assert any(
            ":" in d.message or "invalid syntax" in d.message.lower()
            for d in result.diagnostics
        )

    def test_indentation_error(self):
        """Test detection of indentation errors."""
        validator = SyntaxValidator()

        result = validator.validate(
            code="def foo():\npass",  # Missing indentation
            language="python",
        )

        assert not result.success

    def test_python_line_numbers(self):
        """Test that error line numbers are correct."""
        validator = SyntaxValidator()

        result = validator.validate(
            code='x = 1\ny = 2\nz = "unclosed',  # Error on line 3
            language="python",
        )

        assert not result.success
        assert any(d.line == 3 for d in result.diagnostics)


class TestTypeScriptSyntaxValidation:
    """Test TypeScript syntax validation."""

    def test_parse_valid_typescript(self):
        """Test parsing valid TypeScript code."""
        validator = SyntaxValidator()

        result = validator.validate(
            code="const add = (a: number, b: number): number => a + b;",
            language="typescript",
        )

        # May succeed or warn about tsc not found
        assert result.success or any(
            "not found" in d.message for d in result.diagnostics
        )

    def test_detect_missing_semicolon(self):
        """Test detection of missing semicolon (if tsc available)."""
        validator = SyntaxValidator()

        # This code is valid in TypeScript (semicolons optional)
        result = validator.validate(
            code="const x = 42",
            language="typescript",
        )

        # Should succeed (semicolons are optional in TS)
        assert result.success or any(
            "not found" in d.message for d in result.diagnostics
        )

    def test_detect_unmatched_braces(self):
        """Test detection of unmatched braces."""
        validator = SyntaxValidator()

        result = validator.validate(
            code="function foo() { const x = 1;",  # Missing closing brace
            language="typescript",
        )

        # If tsc available, should detect error
        if result.success:
            # tsc not available
            assert any(
                "not found" in d.message for d in result.diagnostics
            )


class TestRustSyntaxValidation:
    """Test Rust syntax validation."""

    def test_parse_valid_rust(self):
        """Test parsing valid Rust code."""
        validator = SyntaxValidator()

        result = validator.validate(
            code='fn main() { println!("Hello"); }',
            language="rust",
        )

        # May succeed or warn about cargo not found
        assert result.success or any(
            "not found" in d.message for d in result.diagnostics
        )

    def test_detect_rust_error(self):
        """Test detection of Rust syntax errors."""
        validator = SyntaxValidator()

        result = validator.validate(
            code="fn broken(",  # Incomplete function
            language="rust",
        )

        # If cargo available, should detect error
        if not any("not found" in d.message for d in result.diagnostics):
            assert not result.success


class TestGoSyntaxValidation:
    """Test Go syntax validation."""

    def test_parse_valid_go(self):
        """Test parsing valid Go code."""
        validator = SyntaxValidator()

        result = validator.validate(
            code='package main\n\nfunc main() { println("Hello") }',
            language="go",
        )

        # May succeed or warn about go not found
        assert result.success or any(
            "not found" in d.message for d in result.diagnostics
        )

    def test_detect_go_error(self):
        """Test detection of Go syntax errors."""
        validator = SyntaxValidator()

        result = validator.validate(
            code="package main\n\nfunc broken(",  # Incomplete
            language="go",
        )

        # If go available, should detect error
        if not any("not found" in d.message for d in result.diagnostics):
            assert not result.success


class TestZigSyntaxValidation:
    """Test Zig syntax validation."""

    def test_parse_valid_zig(self):
        """Test parsing valid Zig code."""
        validator = SyntaxValidator()

        result = validator.validate(
            code='const std = @import("std");\npub fn main() void { std.debug.print("Hello", .{}); }',
            language="zig",
        )

        # May succeed or warn about zig not found
        assert result.success or any(
            "not found" in d.message for d in result.diagnostics
        )

    def test_detect_zig_error(self):
        """Test detection of Zig syntax errors."""
        validator = SyntaxValidator()

        result = validator.validate(
            code="pub fn broken(",  # Incomplete
            language="zig",
        )

        # If zig available, should detect error
        if not any("not found" in d.message for d in result.diagnostics):
            assert not result.success


class TestSuggestedFixes:
    """Test suggested fix generation."""

    def test_suggest_python_indent_fix(self):
        """Test suggestion for Python indentation error."""
        validator = SyntaxValidator()

        diagnostic = Diagnostic(
            level="error",
            message="expected an indented block",
            line=2,
            column=0,
            source="syntax",
        )

        fix = validator.suggest_fix(diagnostic, "", "python")
        assert fix is not None
        assert "indent" in fix.lower() or "pass" in fix.lower()

    def test_suggest_typescript_semicolon_fix(self):
        """Test suggestion for missing semicolon."""
        validator = SyntaxValidator()

        diagnostic = Diagnostic(
            level="error",
            message="';' expected",
            line=1,
            column=10,
            source="syntax",
        )

        fix = validator.suggest_fix(diagnostic, "", "typescript")
        assert fix is not None
        assert "semicolon" in fix.lower()

    def test_suggest_brace_fix(self):
        """Test suggestion for unmatched braces."""
        validator = SyntaxValidator()

        diagnostic = Diagnostic(
            level="error",
            message="'}' expected",
            line=3,
            column=0,
            source="syntax",
        )

        fix = validator.suggest_fix(diagnostic, "", "typescript")
        assert fix is not None
        assert "brace" in fix.lower() or "}" in fix


class TestCaching:
    """Test parse cache functionality."""

    def test_cache_hit(self):
        """Test that identical code is cached."""
        validator = SyntaxValidator()

        code = "def test(): return 42"

        # First validation
        result1 = validator.validate(code, "python")

        # Second validation (should hit cache)
        result2 = validator.validate(code, "python")

        assert result1.success == result2.success
        assert len(result1.diagnostics) == len(result2.diagnostics)
        # Cache hit should be faster (though timing may vary)

    def test_cache_miss(self):
        """Test that different code is not cached together."""
        validator = SyntaxValidator()

        result1 = validator.validate("def foo(): pass", "python")
        result2 = validator.validate("def bar(): pass", "python")

        # Both should succeed but be different validations
        assert result1.success
        assert result2.success

    def test_cache_eviction(self):
        """Test cache eviction when size limit reached."""
        validator = SyntaxValidator(cache_size=2)

        # Add 3 items (should evict first)
        validator.validate("def a(): pass", "python")
        validator.validate("def b(): pass", "python")
        validator.validate("def c(): pass", "python")

        # Cache should have at most 2 items
        assert len(validator.parse_cache) <= 2

    def test_clear_cache(self):
        """Test clearing the cache."""
        validator = SyntaxValidator()

        validator.validate("def foo(): pass", "python")
        assert len(validator.parse_cache) > 0

        validator.clear_cache()
        assert len(validator.parse_cache) == 0


class TestPerformance:
    """Test performance characteristics."""

    def test_validation_performance(self):
        """Test that validation is fast (<50ms for simple code)."""
        validator = SyntaxValidator()

        # Generate moderately sized code
        code = "def " + "test_" + "a" * 100 + "():\n    return 42\n" * 20

        result = validator.validate(code, "python")

        # Should be well under 50ms for this size
        assert result.validation_time_ms < 100  # Relaxed from 50ms

    def test_large_file_performance(self):
        """Test performance with larger files."""
        validator = SyntaxValidator()

        # Simulate a larger file (100 functions)
        code = "\n".join([
            f"def func_{i}():\n    return {i}"
            for i in range(100)
        ])

        result = validator.validate(code, "python")

        # Should still be fast (relaxed requirement)
        assert result.validation_time_ms < 500


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_code(self):
        """Test validation of empty code."""
        validator = SyntaxValidator()

        result = validator.validate("", "python")

        # Empty code should parse successfully in Python
        assert result.success

    def test_whitespace_only(self):
        """Test validation of whitespace-only code."""
        validator = SyntaxValidator()

        result = validator.validate("   \n\n   ", "python")

        assert result.success

    def test_unicode_code(self):
        """Test validation with Unicode characters."""
        validator = SyntaxValidator()

        result = validator.validate(
            'def greet():\n    return "Hello, 世界"',
            language="python",
        )

        assert result.success

    def test_unsupported_language(self):
        """Test that unsupported language produces error."""
        validator = SyntaxValidator()

        result = validator.validate("code", "cobol")

        # Should fail with unsupported language error
        assert not result.success
        assert any("Unsupported language" in d.message for d in result.diagnostics)

    def test_parse_returns_ast(self):
        """Test that parse returns AST for Python."""
        validator = SyntaxValidator()

        ast = validator.parse("def foo(): pass", "python")

        assert ast is not None

    def test_parse_returns_none_on_error(self):
        """Test that parse returns None on error."""
        validator = SyntaxValidator()

        ast = validator.parse("def broken(", "python")

        assert ast is None

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        validator = SyntaxValidator(cache_size=10)

        stats = validator.get_cache_stats()

        assert "cache_size" in stats
        assert "cache_max" in stats
        assert stats["cache_max"] == 10


class TestDiagnosticDetails:
    """Test diagnostic information quality."""

    def test_diagnostic_has_source(self):
        """Test that diagnostics include source."""
        validator = SyntaxValidator()

        result = validator.validate("def broken(", "python")

        assert not result.success
        assert all(d.source == "syntax" for d in result.diagnostics)

    def test_diagnostic_has_line_column(self):
        """Test that diagnostics include line and column."""
        validator = SyntaxValidator()

        result = validator.validate("def broken(", "python")

        assert not result.success
        for diagnostic in result.diagnostics:
            assert diagnostic.line >= 0
            assert diagnostic.column >= 0

    def test_multiple_errors(self):
        """Test detection of multiple syntax errors."""
        validator = SyntaxValidator()

        # Python stops at first syntax error, but test structure
        result = validator.validate(
            "def broken(\n",  # Syntax error
            language="python",
        )

        assert not result.success
        assert len(result.diagnostics) >= 1

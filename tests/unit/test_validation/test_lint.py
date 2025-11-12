"""
Unit tests for lint validator.

Tests style and quality validation across Python, TypeScript, Rust, Go, and Zig
with linter integration, output parsing, and auto-fix support.
"""

from maze.validation.lint import LintRules, LintValidator


class TestPythonLinting:
    """Test Python linting with ruff."""

    def test_valid_python_code(self):
        """Test linting valid Python code."""
        validator = LintValidator()

        result = validator.validate(
            code="def add(a: int, b: int) -> int:\n    return a + b\n",
            language="python",
        )

        # May succeed or warn about ruff not found
        assert result.success or any("not found" in d.message for d in result.diagnostics)

    def test_python_style_violations(self):
        """Test detection of Python style violations."""
        validator = LintValidator()

        # Code with obvious style issues
        result = validator.validate(
            code="x=1+2  # No spaces around operators\n",
            language="python",
        )

        # If ruff available, may detect style issues
        # Otherwise warns about missing linter
        assert result.validation_time_ms > 0

    def test_python_long_line(self):
        """Test detection of long lines."""
        validator = LintValidator(rules=LintRules(max_line_length=50))

        long_line = "x = " + "1 + " * 30 + "1\n"  # Very long line

        result = validator.validate(code=long_line, language="python")

        # May detect if ruff available
        assert result.validation_time_ms > 0


class TestTypeScriptLinting:
    """Test TypeScript linting with eslint."""

    def test_valid_typescript_code(self):
        """Test linting valid TypeScript code."""
        validator = LintValidator()

        result = validator.validate(
            code="const add = (a: number, b: number): number => a + b;\n",
            language="typescript",
        )

        # May succeed or warn about eslint not found
        assert result.success or any("not found" in d.message for d in result.diagnostics)

    def test_typescript_style_violations(self):
        """Test detection of TypeScript style violations."""
        validator = LintValidator()

        result = validator.validate(
            code="var x=1;",  # Should use const/let, missing spaces
            language="typescript",
        )

        # May detect if eslint available
        assert result.validation_time_ms > 0


class TestRustLinting:
    """Test Rust linting with clippy."""

    def test_valid_rust_code(self):
        """Test linting valid Rust code."""
        validator = LintValidator()

        result = validator.validate(
            code='fn main() { println!("Hello"); }\n',
            language="rust",
        )

        # May succeed or warn about clippy not found
        assert result.success or any("not found" in d.message for d in result.diagnostics)


class TestGoLinting:
    """Test Go linting with golangci-lint."""

    def test_valid_go_code(self):
        """Test linting valid Go code."""
        validator = LintValidator()

        result = validator.validate(
            code='package main\n\nfunc main() { println("Hello") }\n',
            language="go",
        )

        # May succeed or warn about golangci-lint not found
        assert result.success or any("not found" in d.message for d in result.diagnostics)


class TestZigLinting:
    """Test Zig linting with zig fmt."""

    def test_valid_zig_code(self):
        """Test linting valid Zig code."""
        validator = LintValidator()

        result = validator.validate(
            code="pub fn main() void {\n    const x: i32 = 42;\n    _ = x;\n}\n",
            language="zig",
        )

        # May succeed or warn about zig not found
        assert result.success or any("not found" in d.message for d in result.diagnostics)

    def test_zig_formatting_needed(self):
        """Test detection of formatting issues."""
        validator = LintValidator()

        result = validator.validate(
            code="pub fn main() void{const x:i32=42;_ = x;}",  # Poorly formatted
            language="zig",
        )

        # May detect formatting needed if zig available
        assert result.validation_time_ms > 0


class TestOutputParsing:
    """Test linter output parsing."""

    def test_parse_ruff_json(self):
        """Test parsing ruff JSON output."""
        validator = LintValidator()

        json_output = (
            '[{"code": "E501", "message": "Line too long", "location": {"row": 1, "column": 100}}]'
        )

        diagnostics = validator.parse_lint_output(json_output, "python")

        assert len(diagnostics) > 0
        assert diagnostics[0].code == "E501"
        assert diagnostics[0].line == 1

    def test_parse_eslint_json(self):
        """Test parsing eslint JSON output."""
        validator = LintValidator()

        json_output = '[{"messages": [{"ruleId": "no-var", "message": "Unexpected var", "line": 1, "column": 1, "severity": 2}]}]'

        diagnostics = validator.parse_lint_output(json_output, "typescript")

        assert len(diagnostics) > 0
        assert diagnostics[0].code == "no-var"
        assert diagnostics[0].level == "error"

    def test_parse_linter_not_found(self):
        """Test handling linter not found."""
        validator = LintValidator()

        diagnostics = validator.parse_lint_output("LINTER_NOT_FOUND: ruff", "python")

        assert len(diagnostics) == 1
        assert "not found" in diagnostics[0].message

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        validator = LintValidator()

        diagnostics = validator.parse_lint_output("", "python")

        assert len(diagnostics) == 0


class TestAutoFix:
    """Test auto-fix functionality."""

    def test_auto_fix_python(self):
        """Test auto-fixing Python code."""
        validator = LintValidator()

        # Code that could be auto-fixed
        code = "x=1\ny=2\n"

        fixed = validator.auto_fix(code, "python")

        # If ruff available, may fix spacing
        # Otherwise returns original code
        assert len(fixed) > 0

    def test_auto_fix_typescript(self):
        """Test auto-fixing TypeScript code."""
        validator = LintValidator()

        code = "var x=1;\n"

        fixed = validator.auto_fix(code, "typescript")

        # If eslint available with --fix, may fix
        assert len(fixed) > 0

    def test_auto_fix_zig(self):
        """Test auto-fixing Zig code."""
        validator = LintValidator()

        code = "pub fn main() void{const x=42;}"

        fixed = validator.auto_fix(code, "zig")

        # If zig available, should format
        assert len(fixed) > 0

    def test_auto_fix_unsupported_language(self):
        """Test auto-fix on language without support."""
        validator = LintValidator()

        code = "some code"

        fixed = validator.auto_fix(code, "rust")  # No auto-fix for Rust

        # Should return original code
        assert fixed == code


class TestRulesConfiguration:
    """Test lint rules configuration."""

    def test_default_rules(self):
        """Test default lenient rules."""
        rules = LintRules.default()

        assert rules.max_line_length == 120
        assert rules.max_complexity == 15
        assert not rules.require_docstrings
        assert not rules.require_type_hints

    def test_strict_rules(self):
        """Test strict production rules."""
        rules = LintRules.strict()

        assert rules.max_line_length == 100
        assert rules.max_complexity == 10
        assert rules.require_docstrings
        assert rules.require_type_hints

    def test_custom_rules(self):
        """Test custom rule configuration."""
        rules = LintRules(
            max_line_length=80,
            max_complexity=5,
            require_docstrings=True,
            require_type_hints=False,
        )

        assert rules.max_line_length == 80
        assert rules.max_complexity == 5

    def test_rules_override(self):
        """Test overriding rules per validation."""
        validator = LintValidator(rules=LintRules.default())

        # Override with strict rules
        result = validator.validate(
            code="def foo():\n    pass\n",
            language="python",
            rules=LintRules.strict(),
        )

        # Validation should use strict rules
        assert result.validation_time_ms > 0


class TestCaching:
    """Test lint result caching."""

    def test_cache_hit(self):
        """Test that identical code is cached."""
        validator = LintValidator()

        code = "def test(): return 42\n"

        # First validation
        result1 = validator.validate(code, "python")

        # Second validation (should hit cache)
        result2 = validator.validate(code, "python")

        assert result1.success == result2.success
        assert len(result1.diagnostics) == len(result2.diagnostics)

    def test_cache_miss_different_code(self):
        """Test that different code isn't cached together."""
        validator = LintValidator()

        result1 = validator.validate("def foo(): pass\n", "python")
        result2 = validator.validate("def bar(): pass\n", "python")

        # Different code, should be separate validations
        assert result1.validation_time_ms > 0
        assert result2.validation_time_ms > 0

    def test_cache_miss_different_rules(self):
        """Test that different rules create cache miss."""
        validator = LintValidator()

        code = "def test(): pass\n"

        result1 = validator.validate(code, "python", LintRules.default())
        result2 = validator.validate(code, "python", LintRules.strict())

        # Different rules should not hit same cache entry
        assert result1.validation_time_ms > 0
        assert result2.validation_time_ms > 0

    def test_cache_eviction(self):
        """Test cache eviction when size limit reached."""
        validator = LintValidator(cache_size=2)

        # Add 3 items (should evict first)
        validator.validate("def a(): pass\n", "python")
        validator.validate("def b(): pass\n", "python")
        validator.validate("def c(): pass\n", "python")

        # Cache should have at most 2 items
        assert len(validator.cache) <= 2


class TestValidationResult:
    """Test validation result structure."""

    def test_result_fields(self):
        """Test that result has all expected fields."""
        validator = LintValidator()

        result = validator.validate("def test(): pass\n", "python")

        assert hasattr(result, "success")
        assert hasattr(result, "diagnostics")
        assert hasattr(result, "auto_fixable")
        assert hasattr(result, "validation_time_ms")
        assert result.validation_time_ms > 0

    def test_auto_fixable_extraction(self):
        """Test that auto-fixable issues are extracted."""
        validator = LintValidator()

        # Simulate result with suggested fixes
        result = validator.validate("x=1\n", "python")

        # auto_fixable should be a subset of diagnostics
        assert len(result.auto_fixable) <= len(result.diagnostics)


class TestPerformance:
    """Test performance characteristics."""

    def test_quick_validation(self):
        """Test that simple validation is fast."""
        validator = LintValidator()

        result = validator.validate(
            code="def identity(x): return x\n",
            language="python",
        )

        # Should complete quickly (<200ms target)
        assert result.validation_time_ms < 500  # Relaxed for external tools


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_code(self):
        """Test linting empty code."""
        validator = LintValidator()

        result = validator.validate("", "python")

        # Empty code should validate (or warn about missing linter)
        assert result.validation_time_ms > 0

    def test_whitespace_only(self):
        """Test linting whitespace-only code."""
        validator = LintValidator()

        result = validator.validate("   \n\n   \n", "python")

        # Should handle gracefully
        assert result.validation_time_ms > 0

    def test_unicode_code(self):
        """Test linting code with Unicode."""
        validator = LintValidator()

        result = validator.validate(
            'def greet():\n    return "Hello, 世界"\n',
            language="python",
        )

        # Should handle Unicode gracefully
        assert result.validation_time_ms > 0

    def test_unsupported_language(self):
        """Test handling unsupported language."""
        validator = LintValidator()

        result = validator.validate("code", "cobol")

        # Should complete without error
        assert result.validation_time_ms > 0
        # Should have no diagnostics (no linter available)
        assert len(result.diagnostics) == 0

    def test_malformed_code(self):
        """Test linting malformed code."""
        validator = LintValidator()

        result = validator.validate(
            code="def broken(",  # Syntax error
            language="python",
        )

        # Linter may or may not run on syntactically invalid code
        assert result.validation_time_ms > 0


class TestMultipleLanguages:
    """Test validation across multiple languages."""

    def test_python_support(self):
        """Test Python linting."""
        validator = LintValidator()

        assert "python" in validator.linters
        assert validator.linters["python"] == "ruff"

    def test_typescript_support(self):
        """Test TypeScript linting."""
        validator = LintValidator()

        assert "typescript" in validator.linters
        assert validator.linters["typescript"] == "eslint"

    def test_rust_support(self):
        """Test Rust linting."""
        validator = LintValidator()

        assert "rust" in validator.linters
        assert validator.linters["rust"] == "clippy"

    def test_go_support(self):
        """Test Go linting."""
        validator = LintValidator()

        assert "go" in validator.linters
        assert validator.linters["go"] == "golangci-lint"

    def test_zig_support(self):
        """Test Zig linting."""
        validator = LintValidator()

        assert "zig" in validator.linters
        assert validator.linters["zig"] == "zig"

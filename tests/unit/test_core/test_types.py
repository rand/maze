"""
Unit tests for core type system.
"""

import pytest

from maze.core.types import (
    ConstraintLevel,
    Diagnostic,
    FunctionSignature,
    IndexedContext,
    Type,
    TypeContext,
    TypeParameter,
    ValidationResult,
)


class TestType:
    """Test the Type class."""

    def test_simple_type(self):
        """Test creation of simple types."""
        t = Type("string")
        assert t.name == "string"
        assert t.parameters == ()
        assert not t.nullable
        assert str(t) == "string"

    def test_nullable_type(self):
        """Test nullable type creation."""
        t = Type("string", nullable=True)
        assert t.nullable
        assert str(t) == "string?"

    def test_generic_type(self):
        """Test generic type with parameters."""
        t = Type("Array", (Type("number"),))
        assert t.name == "Array"
        assert len(t.parameters) == 1
        assert t.parameters[0].name == "number"
        assert str(t) == "Array<number>"

    def test_nested_generic_type(self):
        """Test nested generic types."""
        t = Type("Promise", (Type("Array", (Type("string"),)),))
        assert str(t) == "Promise<Array<string>>"

    def test_type_equality(self):
        """Test type equality and hashing."""
        t1 = Type("string")
        t2 = Type("string")
        t3 = Type("number")

        assert t1 == t2
        assert t1 != t3
        assert hash(t1) == hash(t2)
        assert hash(t1) != hash(t3)

    def test_is_primitive(self):
        """Test primitive type detection."""
        assert Type("string").is_primitive()
        assert Type("number").is_primitive()
        assert Type("boolean").is_primitive()
        assert not Type("Array", (Type("number"),)).is_primitive()
        assert not Type("CustomType").is_primitive()

    def test_is_function(self):
        """Test function type detection."""
        assert Type("function").is_function()
        assert not Type("string").is_function()

    def test_substitute(self):
        """Test type substitution."""
        t = Type("T")
        mapping = {"T": Type("string")}
        substituted = t.substitute(mapping)
        assert substituted.name == "string"

        # Test with generic type
        t2 = Type("Array", (Type("T"),))
        substituted2 = t2.substitute(mapping)
        assert substituted2.name == "Array"
        assert substituted2.parameters[0].name == "string"


class TestTypeContext:
    """Test the TypeContext class."""

    def test_context_creation(self):
        """Test TypeContext creation."""
        ctx = TypeContext(language="typescript")
        assert ctx.language == "typescript"
        assert ctx.strict_nulls
        assert ctx.strict_types
        assert len(ctx.variables) == 0
        assert len(ctx.functions) == 0

    def test_context_lookup(self):
        """Test symbol lookup in context."""
        ctx = TypeContext()
        ctx.variables["x"] = Type("number")
        ctx.functions["greet"] = FunctionSignature(
            name="greet", parameters=[], return_type=Type("string")
        )

        assert ctx.lookup("x") == Type("number")
        assert ctx.lookup("greet").name == "function"
        assert ctx.lookup("unknown") is None

    def test_context_copy(self):
        """Test context copying."""
        ctx = TypeContext()
        ctx.variables["x"] = Type("number")

        ctx_copy = ctx.copy()
        ctx_copy.variables["y"] = Type("string")

        assert "x" in ctx.variables
        assert "x" in ctx_copy.variables
        assert "y" not in ctx.variables
        assert "y" in ctx_copy.variables

    def test_context_merge(self):
        """Test context merging."""
        ctx1 = TypeContext()
        ctx1.variables["x"] = Type("number")

        ctx2 = TypeContext()
        ctx2.variables["y"] = Type("string")

        merged = ctx1.merge(ctx2)
        assert "x" in merged.variables
        assert "y" in merged.variables
        assert "y" not in ctx1.variables


class TestFunctionSignature:
    """Test the FunctionSignature class."""

    def test_simple_signature(self):
        """Test simple function signature."""
        sig = FunctionSignature(
            name="add",
            parameters=[
                TypeParameter("a", Type("number")),
                TypeParameter("b", Type("number")),
            ],
            return_type=Type("number"),
        )

        assert sig.name == "add"
        assert len(sig.parameters) == 2
        assert sig.return_type.name == "number"
        assert not sig.is_async
        assert str(sig) == "function add(a: number, b: number): number"

    def test_async_signature(self):
        """Test async function signature."""
        sig = FunctionSignature(
            name="fetchUser",
            parameters=[TypeParameter("id", Type("string"))],
            return_type=Type("Promise", (Type("User"),)),
            is_async=True,
        )

        assert sig.is_async
        assert "async" in str(sig)

    def test_optional_parameters(self):
        """Test optional parameters."""
        sig = FunctionSignature(
            name="greet",
            parameters=[
                TypeParameter("name", Type("string")),
                TypeParameter("greeting", Type("string"), optional=True),
            ],
            return_type=Type("string"),
        )

        assert sig.parameters[1].optional
        assert "?" in str(sig.parameters[1])

    def test_to_type_conversion(self):
        """Test conversion to Type."""
        sig = FunctionSignature(
            name="add",
            parameters=[
                TypeParameter("a", Type("number")),
                TypeParameter("b", Type("number")),
            ],
            return_type=Type("number"),
        )

        func_type = sig.to_type()
        assert func_type.name == "function"
        assert len(func_type.parameters) == 3  # 2 params + return type


class TestDiagnostic:
    """Test the Diagnostic class."""

    def test_error_diagnostic(self):
        """Test error diagnostic creation."""
        diag = Diagnostic(
            severity="error",
            category="type",
            message="Type 'string' is not assignable to type 'number'",
            file="test.ts",
            line=10,
            column=5,
            code="TS2322",
        )

        assert diag.severity == "error"
        assert diag.category == "type"
        assert "TS2322" in str(diag)

    def test_diagnostic_to_dict(self):
        """Test diagnostic serialization."""
        diag = Diagnostic(severity="warning", category="style", message="Line too long", line=20)

        d = diag.to_dict()
        assert d["severity"] == "warning"
        assert d["category"] == "style"
        assert d["message"] == "Line too long"
        assert d["line"] == 20


class TestValidationResult:
    """Test the ValidationResult class."""

    def test_passed_result(self):
        """Test passed validation result."""
        result = ValidationResult(passed=True)
        assert result.passed
        assert len(result.diagnostics) == 0

    def test_failed_result(self):
        """Test failed validation result."""
        result = ValidationResult(
            passed=False,
            diagnostics=[
                Diagnostic("error", "type", "Type error"),
                Diagnostic("warning", "style", "Style warning"),
            ],
        )

        assert not result.passed
        assert len(result.diagnostics) == 2
        assert len(result.get_errors()) == 1
        assert len(result.get_warnings()) == 1

    def test_combine_results(self):
        """Test combining validation results."""
        result1 = ValidationResult(passed=True, tests_run=5, tests_passed=5)

        result2 = ValidationResult(passed=False, tests_run=3, tests_passed=2, tests_failed=1)

        combined = ValidationResult.combine([result1, result2])
        assert not combined.passed  # One failed, so combined fails
        assert combined.tests_run == 8
        assert combined.tests_passed == 7
        assert combined.tests_failed == 1


class TestIndexedContext:
    """Test the IndexedContext class."""

    def test_context_creation(self):
        """Test IndexedContext creation."""
        ctx = IndexedContext(
            files=[{"path": "test.ts", "lang": "typescript"}],
            symbols=[{"name": "foo", "type": "string"}],
            schemas=[],
            style={"indent": 2},
            tests=[],
            constraints_candidates=[],
            language="typescript",
        )

        assert ctx.language == "typescript"
        assert len(ctx.files) == 1
        assert len(ctx.symbols) == 1

    def test_context_summary(self):
        """Test context summary generation."""
        ctx = IndexedContext(
            files=[{"path": "a.ts", "lang": "typescript"}, {"path": "b.ts", "lang": "typescript"}],
            symbols=[{"name": "x"}, {"name": "y"}, {"name": "z"}],
            schemas=[{"type": "object"}],
            style={},
            tests=[],
            constraints_candidates=[],
        )

        summary = ctx.to_summary()
        assert "typescript" in summary
        assert "3 symbols" in summary
        assert "1 schemas" in summary
        assert "2 files" in summary


class TestConstraintLevel:
    """Test the ConstraintLevel enum."""

    def test_constraint_levels(self):
        """Test constraint level ordering."""
        assert ConstraintLevel.SYNTACTIC.value < ConstraintLevel.TYPE.value
        assert ConstraintLevel.TYPE.value < ConstraintLevel.SEMANTIC.value
        assert ConstraintLevel.SEMANTIC.value < ConstraintLevel.CONTEXTUAL.value


# Performance tests (marked as slow)


@pytest.mark.performance
class TestTypePerformance:
    """Performance tests for type system."""

    def test_type_creation_performance(self, benchmark):
        """Test performance of type creation."""

        def create_types():
            types = []
            for i in range(1000):
                t = Type(f"Type{i}", (Type("string"), Type("number")))
                types.append(t)
            return types

        # Should complete in reasonable time
        types = benchmark(create_types)
        assert len(types) == 1000

    def test_type_hashing_performance(self, benchmark):
        """Test performance of type hashing."""
        types = [Type(f"Type{i}") for i in range(1000)]

        def hash_types():
            return {hash(t) for t in types}

        # Hashing should be fast
        hashes = benchmark(hash_types)
        assert len(hashes) == 1000  # All unique hashes

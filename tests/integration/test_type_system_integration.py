"""
Integration tests for type system.

Tests the complete type system pipeline from type inference through
grammar generation to hole filling.
"""

from maze.core.types import ClassType, FunctionSignature, Type, TypeContext, TypeParameter
from maze.type_system import TypeSystemOrchestrator


class TestTypeSystemIntegration:
    """Test type system integration."""

    def test_orchestrator_initialization(self):
        """Test creating orchestrator."""
        orchestrator = TypeSystemOrchestrator(language="typescript")

        assert orchestrator.language == "typescript"
        assert orchestrator.inference is not None
        assert orchestrator.inhabitation is not None
        assert orchestrator.converter is not None
        assert orchestrator.type_system is not None

    def test_parse_and_convert_simple_type(self):
        """Test parsing type and converting to grammar."""
        orchestrator = TypeSystemOrchestrator()

        # Parse type
        parsed = orchestrator.parse_type("string")
        assert parsed == Type("string")

        # Convert to grammar
        context = TypeContext()
        grammar = orchestrator.converter.convert(parsed, context)
        assert "string_value" in grammar

    def test_parse_complex_type(self):
        """Test parsing complex TypeScript type."""
        orchestrator = TypeSystemOrchestrator()

        # Parse Array<string | number>
        parsed = orchestrator.parse_type("Array<string | number>")

        assert parsed.name == "Array"
        assert parsed.parameters[0].name == "union"

    def test_type_assignability(self):
        """Test type assignability checking."""
        orchestrator = TypeSystemOrchestrator()

        # string is assignable to string
        assert orchestrator.is_assignable(Type("string"), Type("string"))

        # string is assignable to any
        assert orchestrator.is_assignable(Type("string"), Type("any"))

        # string is NOT assignable to number
        assert not orchestrator.is_assignable(Type("string"), Type("number"))

    def test_infer_type_from_expression(self):
        """Test type inference from expression."""
        orchestrator = TypeSystemOrchestrator()

        context = TypeContext(variables={"x": Type("number")})
        expr = {"kind": "identifier", "name": "x"}

        result = orchestrator.infer_type(expr, context)

        assert result.inferred_type == Type("number")

    def test_find_inhabitation_path(self):
        """Test finding type transformation path."""
        orchestrator = TypeSystemOrchestrator()

        context = TypeContext(variables={"x": Type("number")})

        # Find path from unknown to number (should use variable x)
        path = orchestrator.find_inhabitation_path(Type("unknown"), Type("number"), context)

        assert path is not None
        assert path.target == Type("number")

    def test_hole_identification(self):
        """Test identifying holes in code."""
        orchestrator = TypeSystemOrchestrator()

        code = "const x: number = /*__HOLE_value__*/"
        context = TypeContext()

        filled, results = orchestrator.fill_typed_holes(code, context)

        assert len(results) == 1
        assert results[0].hole.name == "value"

    def test_end_to_end_type_constrained_generation(self):
        """Test end-to-end type-constrained generation without provider."""
        orchestrator = TypeSystemOrchestrator()

        context = TypeContext()
        result = orchestrator.generate_with_type_constraints(
            prompt="Generate a number",
            context=context,
            expected_type=Type("number"),
            provider=None,  # No provider for test
        )

        # Should have grammar even without provider
        assert result.grammar_used is not None
        assert "number_value" in result.grammar_used
        assert result.success is False  # No provider

    def test_cache_statistics(self):
        """Test getting cache statistics."""
        orchestrator = TypeSystemOrchestrator()

        # Do some operations to populate cache
        context = TypeContext(variables={"x": Type("number")})
        expr = {"kind": "identifier", "name": "x"}
        orchestrator.infer_type(expr, context)

        # Get stats
        stats = orchestrator.get_cache_stats()

        assert "inference_cache_size" in stats
        assert "inhabitation_stats" in stats

    def test_clear_caches(self):
        """Test clearing all caches."""
        orchestrator = TypeSystemOrchestrator()

        # Populate caches
        context = TypeContext(variables={"x": Type("number")})
        expr = {"kind": "identifier", "name": "x"}
        orchestrator.infer_type(expr, context)

        # Clear caches
        orchestrator.clear_caches()

        # Caches should be empty
        stats = orchestrator.get_cache_stats()
        assert stats["inference_cache_size"] == 0


class TestComplexWorkflows:
    """Test complex type system workflows."""

    def test_object_type_workflow(self):
        """Test complete workflow with object types."""
        orchestrator = TypeSystemOrchestrator()

        # Create Person class type
        person = ClassType(
            name="Person", properties={"name": Type("string"), "age": Type("number")}, methods={}
        )

        context = TypeContext(classes={"Person": person})

        # Convert to grammar
        grammar = orchestrator.converter.convert(Type("Person"), context)

        assert "name" in grammar
        assert "age" in grammar

    def test_function_type_workflow(self):
        """Test workflow with function types."""
        orchestrator = TypeSystemOrchestrator()

        # Create function signature
        add = FunctionSignature(
            name="add",
            parameters=[TypeParameter("a", Type("number")), TypeParameter("b", Type("number"))],
            return_type=Type("number"),
        )

        context = TypeContext(functions={"add": add})

        # Infer function call type
        expr = {"kind": "call", "callee": {"kind": "identifier", "name": "add"}, "arguments": []}

        result = orchestrator.infer_type(expr, context)

        assert result.inferred_type == Type("number")

    def test_array_type_workflow(self):
        """Test workflow with array types."""
        orchestrator = TypeSystemOrchestrator()

        # Parse array type
        array_type = orchestrator.parse_type("Array<string>")

        # Convert to grammar
        context = TypeContext()
        grammar = orchestrator.converter.convert(array_type, context)

        assert "[" in grammar
        assert "string_value" in grammar

    def test_union_type_workflow(self):
        """Test workflow with union types."""
        orchestrator = TypeSystemOrchestrator()

        # Parse union type
        union_type = orchestrator.parse_type("string | number")

        # Check assignability
        assert orchestrator.is_assignable(Type("string"), union_type)
        assert orchestrator.is_assignable(Type("number"), union_type)

        # Convert to grammar
        context = TypeContext()
        grammar = orchestrator.converter.convert(union_type, context)

        assert "|" in grammar

    def test_nested_type_workflow(self):
        """Test workflow with nested generic types."""
        orchestrator = TypeSystemOrchestrator()

        # Parse nested array
        nested = orchestrator.parse_type("Array<Array<number>>")

        assert nested.name == "Array"
        assert nested.parameters[0].name == "Array"
        assert nested.parameters[0].parameters[0] == Type("number")


class TestPerformance:
    """Test performance characteristics."""

    def test_inference_caching(self):
        """Test that inference results are cached."""
        orchestrator = TypeSystemOrchestrator()

        context = TypeContext(variables={"x": Type("number")})
        expr = {"kind": "identifier", "name": "x"}

        # First inference
        result1 = orchestrator.infer_type(expr, context)

        # Second inference (should use cache)
        result2 = orchestrator.infer_type(expr, context)

        # Results should be the same object (cached)
        assert result1 is result2

    def test_inhabitation_caching(self):
        """Test that inhabitation paths are cached."""
        orchestrator = TypeSystemOrchestrator()

        context = TypeContext(variables={"x": Type("number")})

        # First search
        path1 = orchestrator.find_inhabitation_path(Type("unknown"), Type("number"), context)

        # Get cache stats
        stats = orchestrator.get_cache_stats()
        initial_hits = stats["inhabitation_stats"]["hits"]

        # Second search (should use cache)
        path2 = orchestrator.find_inhabitation_path(Type("unknown"), Type("number"), context)

        # Cache hits should increase
        stats_after = orchestrator.get_cache_stats()
        assert stats_after["inhabitation_stats"]["hits"] > initial_hits

    def test_multiple_operations(self):
        """Test performing multiple operations efficiently."""
        orchestrator = TypeSystemOrchestrator()

        context = TypeContext(
            variables={"x": Type("number"), "y": Type("string"), "z": Type("boolean")}
        )

        # Perform multiple inferences
        for var_name in ["x", "y", "z"]:
            expr = {"kind": "identifier", "name": var_name}
            result = orchestrator.infer_type(expr, context)
            assert result.inferred_type == context.variables[var_name]

        # All should be in cache
        stats = orchestrator.get_cache_stats()
        assert stats["inference_cache_size"] >= 3

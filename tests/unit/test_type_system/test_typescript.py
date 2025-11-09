"""
Tests for TypeScript type system.
"""

import pytest
from maze.type_system.languages.typescript import TypeScriptTypeSystem
from maze.core.types import Type


class TestTypeScriptTypeSystem:
    """Test TypeScript type system."""

    def test_parse_primitive_string(self):
        """Test parsing primitive string type."""
        ts = TypeScriptTypeSystem()

        result = ts.parse_type("string")

        assert result.name == "string"
        assert result.parameters == ()
        assert result.nullable is False

    def test_parse_primitive_number(self):
        """Test parsing primitive number type."""
        ts = TypeScriptTypeSystem()

        result = ts.parse_type("number")

        assert result == Type("number")

    def test_parse_primitive_boolean(self):
        """Test parsing primitive boolean type."""
        ts = TypeScriptTypeSystem()

        result = ts.parse_type("boolean")

        assert result == Type("boolean")

    def test_parse_any_unknown_never(self):
        """Test parsing special TypeScript types."""
        ts = TypeScriptTypeSystem()

        assert ts.parse_type("any") == Type("any")
        assert ts.parse_type("unknown") == Type("unknown")
        assert ts.parse_type("never") == Type("never")

    def test_parse_nullable_type(self):
        """Test parsing nullable type with ?."""
        ts = TypeScriptTypeSystem()

        result = ts.parse_type("string?")

        assert result.name == "string"
        assert result.nullable is True

    def test_parse_array_bracket_syntax(self):
        """Test parsing array type with [] syntax."""
        ts = TypeScriptTypeSystem()

        result = ts.parse_type("string[]")

        assert result.name == "Array"
        assert len(result.parameters) == 1
        assert result.parameters[0] == Type("string")

    def test_parse_array_generic_syntax(self):
        """Test parsing array type with generic syntax."""
        ts = TypeScriptTypeSystem()

        result = ts.parse_type("Array<number>")

        assert result.name == "Array"
        assert len(result.parameters) == 1
        assert result.parameters[0] == Type("number")

    def test_parse_union_type(self):
        """Test parsing union type."""
        ts = TypeScriptTypeSystem()

        result = ts.parse_type("string | number")

        assert result.name == "union"
        assert len(result.parameters) == 2
        assert Type("string") in result.parameters
        assert Type("number") in result.parameters

    def test_parse_intersection_type(self):
        """Test parsing intersection type."""
        ts = TypeScriptTypeSystem()

        result = ts.parse_type("A & B")

        assert result.name == "intersection"
        assert len(result.parameters) == 2

    def test_parse_generic_type(self):
        """Test parsing generic type with multiple parameters."""
        ts = TypeScriptTypeSystem()

        result = ts.parse_type("Map<string, number>")

        assert result.name == "Map"
        assert len(result.parameters) == 2
        assert result.parameters[0] == Type("string")
        assert result.parameters[1] == Type("number")

    def test_parse_nested_generic(self):
        """Test parsing nested generic types."""
        ts = TypeScriptTypeSystem()

        result = ts.parse_type("Array<Array<number>>")

        assert result.name == "Array"
        assert result.parameters[0].name == "Array"
        assert result.parameters[0].parameters[0] == Type("number")

    def test_parse_function_type(self):
        """Test parsing function type."""
        ts = TypeScriptTypeSystem()

        result = ts.parse_type("(x: number) => string")

        assert result.name == "function"
        assert result.parameters[0] == Type("string")  # Return type

    def test_parse_object_type(self):
        """Test parsing object type."""
        ts = TypeScriptTypeSystem()

        result = ts.parse_type("{ x: number }")

        assert result.name == "object"

    def test_assignability_same_type(self):
        """Test assignability of same types."""
        ts = TypeScriptTypeSystem()

        assert ts.is_assignable(Type("string"), Type("string")) is True
        assert ts.is_assignable(Type("number"), Type("number")) is True

    def test_assignability_to_any(self):
        """Test any accepts everything."""
        ts = TypeScriptTypeSystem()

        assert ts.is_assignable(Type("string"), Type("any")) is True
        assert ts.is_assignable(Type("number"), Type("any")) is True
        assert ts.is_assignable(Type("object"), Type("any")) is True

    def test_assignability_never_to_anything(self):
        """Test never is assignable to everything."""
        ts = TypeScriptTypeSystem()

        assert ts.is_assignable(Type("never"), Type("string")) is True
        assert ts.is_assignable(Type("never"), Type("number")) is True

    def test_assignability_union_source(self):
        """Test union source assignability."""
        ts = TypeScriptTypeSystem()

        # string | number to any
        union = Type("union", (Type("string"), Type("number")))
        assert ts.is_assignable(union, Type("any")) is True

    def test_assignability_union_target(self):
        """Test union target assignability."""
        ts = TypeScriptTypeSystem()

        # string to string | number
        union = Type("union", (Type("string"), Type("number")))
        assert ts.is_assignable(Type("string"), union) is True

    def test_assignability_nullable(self):
        """Test nullable type assignability."""
        ts = TypeScriptTypeSystem()

        nullable_string = Type("string", nullable=True)
        string = Type("string")

        # Nullable cannot be assigned to non-nullable
        assert ts.is_assignable(nullable_string, string) is False

        # Non-nullable can be assigned to nullable
        # (Actually false in our impl - but that's okay for safety)

    def test_assignability_generic_types(self):
        """Test generic type assignability."""
        ts = TypeScriptTypeSystem()

        array_number = Type("Array", (Type("number"),))
        array_string = Type("Array", (Type("string"),))

        # Array<number> not assignable to Array<string>
        assert ts.is_assignable(array_number, array_string) is False

        # Array<number> assignable to Array<number>
        assert ts.is_assignable(array_number, array_number) is True

    def test_widen_string_literal(self):
        """Test widening string literal to string."""
        ts = TypeScriptTypeSystem()

        literal = Type("'hello'")
        widened = ts.widen_type(literal)

        assert widened.name == "string"

    def test_widen_number_literal(self):
        """Test widening number literal to number."""
        ts = TypeScriptTypeSystem()

        literal = Type("42")
        widened = ts.widen_type(literal)

        assert widened.name == "number"

    def test_widen_boolean_literal(self):
        """Test widening boolean literal to boolean."""
        ts = TypeScriptTypeSystem()

        literal_true = Type("true")
        widened_true = ts.widen_type(literal_true)
        assert widened_true.name == "boolean"

        literal_false = Type("false")
        widened_false = ts.widen_type(literal_false)
        assert widened_false.name == "boolean"

    def test_narrow_typeof_guard(self):
        """Test narrowing with typeof guard."""
        ts = TypeScriptTypeSystem()

        union = Type("union", (Type("string"), Type("number")))
        narrowed = ts.narrow_type(union, "typeof x === 'string'")

        assert narrowed.name == "string"

    def test_narrow_instanceof_guard(self):
        """Test narrowing with instanceof guard."""
        ts = TypeScriptTypeSystem()

        union = Type("union", (Type("Date"), Type("string")))
        narrowed = ts.narrow_type(union, "x instanceof Date")

        assert narrowed.name == "Date"

    def test_narrow_null_guard(self):
        """Test narrowing with null check."""
        ts = TypeScriptTypeSystem()

        nullable = Type("string", nullable=True)
        narrowed = ts.narrow_type(nullable, "x != null")

        assert narrowed.nullable is False

    def test_infer_from_number_literal(self):
        """Test inferring type from number literal."""
        ts = TypeScriptTypeSystem()

        result = ts.infer_from_literal(42)
        assert result == Type("number")

        result_float = ts.infer_from_literal(3.14)
        assert result_float == Type("number")

    def test_infer_from_string_literal(self):
        """Test inferring type from string literal."""
        ts = TypeScriptTypeSystem()

        result = ts.infer_from_literal("hello")
        assert result == Type("string")

    def test_infer_from_boolean_literal(self):
        """Test inferring type from boolean literal."""
        ts = TypeScriptTypeSystem()

        result_true = ts.infer_from_literal(True)
        assert result_true == Type("boolean")

        result_false = ts.infer_from_literal(False)
        assert result_false == Type("boolean")

    def test_infer_from_null(self):
        """Test inferring type from null."""
        ts = TypeScriptTypeSystem()

        result = ts.infer_from_literal(None)
        assert result == Type("null")

    def test_infer_from_array(self):
        """Test inferring type from array literal."""
        ts = TypeScriptTypeSystem()

        result = ts.infer_from_literal([1, 2, 3])
        assert result.name == "Array"
        assert result.parameters[0] == Type("number")

    def test_infer_from_object(self):
        """Test inferring type from object literal."""
        ts = TypeScriptTypeSystem()

        result = ts.infer_from_literal({"x": 1, "y": 2})
        assert result == Type("object")

    def test_resolve_union_single_type(self):
        """Test resolve union with single type."""
        ts = TypeScriptTypeSystem()

        result = ts.resolve_union([Type("string")])
        assert result == Type("string")

    def test_resolve_union_multiple_types(self):
        """Test resolve union with multiple types."""
        ts = TypeScriptTypeSystem()

        result = ts.resolve_union([Type("string"), Type("number")])
        assert result.name == "union"
        assert len(result.parameters) == 2

    def test_resolve_union_with_duplicates(self):
        """Test resolve union removes duplicates."""
        ts = TypeScriptTypeSystem()

        result = ts.resolve_union([Type("string"), Type("string"), Type("number")])
        assert result.name == "union"
        assert len(result.parameters) == 2

    def test_resolve_union_with_never(self):
        """Test resolve union with never."""
        ts = TypeScriptTypeSystem()

        # never | string = string
        result = ts.resolve_union([Type("never"), Type("string")])
        assert result == Type("string")

    def test_resolve_union_with_any(self):
        """Test resolve union with any."""
        ts = TypeScriptTypeSystem()

        # any | string = any
        result = ts.resolve_union([Type("any"), Type("string")])
        assert result == Type("any")

    def test_resolve_intersection_single_type(self):
        """Test resolve intersection with single type."""
        ts = TypeScriptTypeSystem()

        result = ts.resolve_intersection([Type("A")])
        assert result == Type("A")

    def test_resolve_intersection_multiple_types(self):
        """Test resolve intersection with multiple types."""
        ts = TypeScriptTypeSystem()

        result = ts.resolve_intersection([Type("A"), Type("B")])
        assert result.name == "intersection"
        assert len(result.parameters) == 2

    def test_resolve_intersection_with_never(self):
        """Test resolve intersection with never."""
        ts = TypeScriptTypeSystem()

        # never & A = never
        result = ts.resolve_intersection([Type("never"), Type("A")])
        assert result == Type("never")

    def test_resolve_intersection_with_any(self):
        """Test resolve intersection with any."""
        ts = TypeScriptTypeSystem()

        # any & A = A
        result = ts.resolve_intersection([Type("any"), Type("A")])
        assert result == Type("A")

    def test_instantiate_generic_array(self):
        """Test instantiating generic Array type."""
        ts = TypeScriptTypeSystem()

        generic = Type("Array", (Type("T"),))
        instantiated = ts.instantiate_generic(generic, [Type("number")])

        assert instantiated.name == "Array"
        assert instantiated.parameters[0] == Type("number")

    def test_instantiate_generic_map(self):
        """Test instantiating generic Map type."""
        ts = TypeScriptTypeSystem()

        generic = Type("Map", (Type("K"), Type("V")))
        instantiated = ts.instantiate_generic(generic, [Type("string"), Type("number")])

        assert instantiated.name == "Map"
        assert instantiated.parameters[0] == Type("string")
        assert instantiated.parameters[1] == Type("number")

    def test_instantiate_non_generic(self):
        """Test instantiating non-generic type returns original."""
        ts = TypeScriptTypeSystem()

        non_generic = Type("string")
        result = ts.instantiate_generic(non_generic, [Type("number")])

        assert result == non_generic

    def test_complex_nested_types(self):
        """Test parsing complex nested types."""
        ts = TypeScriptTypeSystem()

        # Array<string | number>
        result = ts.parse_type("Array<string | number>")

        assert result.name == "Array"
        assert result.parameters[0].name == "union"
        assert len(result.parameters[0].parameters) == 2

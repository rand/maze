"""
Tests for type-to-grammar converter.
"""

from maze.core.types import ClassType, Type, TypeContext
from maze.type_system.grammar_converter import (
    TypeToGrammarConverter,
    create_grammar_for_type,
)


class TestTypeToGrammarConverter:
    """Test type-to-grammar converter."""

    def test_convert_string_primitive(self):
        """Test converting string type to grammar."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        grammar = converter.convert(Type("string"), context)

        assert "start" in grammar
        assert "string_value" in grammar

    def test_convert_number_primitive(self):
        """Test converting number type to grammar."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        grammar = converter.convert(Type("number"), context)

        assert "number_value" in grammar

    def test_convert_boolean_primitive(self):
        """Test converting boolean type to grammar."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        grammar = converter.convert(Type("boolean"), context)

        assert "boolean_value" in grammar

    def test_convert_null_type(self):
        """Test converting null type to grammar."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        grammar = converter.convert(Type("null"), context)

        assert '"null"' in grammar

    def test_convert_simple_object(self):
        """Test converting simple object type to grammar."""
        converter = TypeToGrammarConverter()

        person = ClassType(name="Person", properties={"name": Type("string")}, methods={})

        context = TypeContext(classes={"Person": person})

        grammar = converter.convert(Type("Person"), context)

        assert "{" in grammar
        assert "name" in grammar

    def test_convert_object_with_multiple_properties(self):
        """Test converting object with multiple properties."""
        converter = TypeToGrammarConverter()

        person = ClassType(
            name="Person", properties={"name": Type("string"), "age": Type("number")}, methods={}
        )

        context = TypeContext(classes={"Person": person})

        grammar = converter.convert(Type("Person"), context)

        assert "name" in grammar
        assert "age" in grammar
        assert "," in grammar

    def test_convert_array(self):
        """Test converting array type to grammar."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        grammar = converter.convert(Type("Array", (Type("number"),)), context)

        assert "[" in grammar
        assert "]" in grammar

    def test_convert_array_of_strings(self):
        """Test converting Array<string> to grammar."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        grammar = converter.convert(Type("Array", (Type("string"),)), context)

        assert "string_value" in grammar

    def test_convert_union(self):
        """Test converting union type to grammar."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        union = Type("union", (Type("string"), Type("number")))
        grammar = converter.convert(union, context)

        assert "string_value" in grammar
        assert "number_value" in grammar
        assert "|" in grammar

    def test_convert_nullable_type(self):
        """Test converting nullable type to grammar."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        nullable_string = Type("string", nullable=True)
        grammar = converter.convert(nullable_string, context)

        assert "string_value" in grammar
        assert '"null"' in grammar
        assert "|" in grammar

    def test_convert_nested_array(self):
        """Test converting nested array type."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        nested_array = Type("Array", (Type("Array", (Type("number"),)),))
        grammar = converter.convert(nested_array, context)

        # Should have nested brackets
        assert "[" in grammar

    def test_convert_generic_type(self):
        """Test converting generic type."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        # Array is the main generic we support
        array_type = Type("Array", (Type("string"),))
        grammar = converter.convert(array_type, context)

        assert "[" in grammar
        assert "string_value" in grammar

    def test_convert_function_type(self):
        """Test converting function type."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        func_type = Type("function", (Type("string"),))
        grammar = converter.convert(func_type, context)

        assert "function" in grammar

    def test_convert_any_type(self):
        """Test converting any type."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        grammar = converter.convert(Type("any"), context)

        assert "any_value" in grammar

    def test_convert_unknown_type(self):
        """Test converting unknown type."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        grammar = converter.convert(Type("unknown"), context)

        assert "any_value" in grammar

    def test_convert_object_generic_type(self):
        """Test converting generic object type."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        grammar = converter.convert(Type("object"), context)

        assert "object_value" in grammar

    def test_primitive_converter_methods(self):
        """Test individual primitive converter methods."""
        converter = TypeToGrammarConverter()

        assert "string_value" in converter.convert_primitive(Type("string"))
        assert "number_value" in converter.convert_primitive(Type("number"))
        assert "boolean_value" in converter.convert_primitive(Type("boolean"))

    def test_array_converter_method(self):
        """Test array converter method."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        rule = converter.convert_array(Type("number"), context)

        assert "[" in rule
        assert "]" in rule

    def test_union_converter_method(self):
        """Test union converter method."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        types = [Type("string"), Type("number")]
        rule = converter.convert_union(types, context)

        assert "|" in rule

    def test_create_grammar_for_type_function(self):
        """Test convenience function for creating grammar."""
        grammar = create_grammar_for_type(Type("string"))

        assert "start" in grammar
        assert "string_value" in grammar

    def test_create_grammar_with_custom_context(self):
        """Test creating grammar with custom context."""
        person = ClassType(name="Person", properties={"name": Type("string")}, methods={})

        context = TypeContext(classes={"Person": person})

        grammar = create_grammar_for_type(Type("Person"), context)

        assert "name" in grammar

    def test_grammar_builder_integration(self):
        """Test integration with GrammarBuilder."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        # Convert should use GrammarBuilder internally
        grammar = converter.convert(Type("string"), context)

        # Should have proper grammar structure
        assert "start:" in grammar or "start " in grammar


class TestComplexTypes:
    """Test converting complex nested types."""

    def test_array_of_objects(self):
        """Test converting Array<Person> to grammar."""
        converter = TypeToGrammarConverter()

        person = ClassType(name="Person", properties={"name": Type("string")}, methods={})

        context = TypeContext(classes={"Person": person})

        array_of_person = Type("Array", (Type("Person"),))
        grammar = converter.convert(array_of_person, context)

        assert "[" in grammar
        assert "name" in grammar

    def test_object_with_array_property(self):
        """Test converting object with array property."""
        converter = TypeToGrammarConverter()

        company = ClassType(
            name="Company", properties={"employees": Type("Array", (Type("string"),))}, methods={}
        )

        context = TypeContext(classes={"Company": company})

        grammar = converter.convert(Type("Company"), context)

        assert "employees" in grammar

    def test_union_of_arrays(self):
        """Test converting union of array types."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        union = Type("union", (Type("Array", (Type("string"),)), Type("Array", (Type("number"),))))

        grammar = converter.convert(union, context)

        assert "[" in grammar
        assert "|" in grammar

    def test_nullable_array(self):
        """Test converting nullable array type."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        nullable_array = Type("Array", (Type("number"),), nullable=True)
        grammar = converter.convert(nullable_array, context)

        assert "[" in grammar
        assert '"null"' in grammar

    def test_multiple_conversions(self):
        """Test multiple type conversions with same converter."""
        converter = TypeToGrammarConverter()
        context = TypeContext()

        # Multiple calls should work correctly
        grammar1 = converter.convert(Type("string"), context)
        grammar2 = converter.convert(Type("number"), context)

        assert "string_value" in grammar1
        assert "number_value" in grammar2

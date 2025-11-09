"""
Type-to-Grammar converter for type-constrained code generation.

Converts Maze Type representations to Lark grammars for use with llguidance.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from maze.core.types import Type, TypeContext, ClassType, FunctionSignature
from maze.synthesis.grammar_builder import GrammarBuilder


class TypeToGrammarConverter:
    """
    Convert types to Lark grammars.

    Generates Lark grammar rules that constrain generation to match
    specific types, enabling type-safe code generation.

    Performance target: <5ms per type
    """

    def __init__(self, language: str = "typescript"):
        """
        Initialize converter.

        Args:
            language: Target language (typescript, python, rust)
        """
        self.language = language
        self.builder = GrammarBuilder()
        self.rule_counter = 0

    def convert(self, type: Type, context: TypeContext) -> str:
        """
        Convert type to grammar.

        Args:
            type: Type to convert
            context: Type context for resolving references

        Returns:
            Lark grammar string

        Example:
            >>> converter = TypeToGrammarConverter()
            >>> context = TypeContext()
            >>> grammar = converter.convert(Type("string"), context)
            >>> print("string_value" in grammar)
            True
        """
        # Reset builder
        self.builder = GrammarBuilder()
        self.rule_counter = 0

        # Add start rule
        start_rule = self._convert_type(type, context)
        self.builder.add_rule("start", start_rule)

        # Build and return grammar
        return self.builder.build()

    def convert_primitive(self, type: Type) -> str:
        """
        Convert primitive type to grammar.

        Args:
            type: Primitive type

        Returns:
            Grammar rule body

        Example:
            >>> converter = TypeToGrammarConverter()
            >>> rule = converter.convert_primitive(Type("number"))
            >>> print("NUMBER" in rule)
            True
        """
        if type.name == "string":
            return 'string_value'
        elif type.name == "number":
            return 'number_value'
        elif type.name == "boolean":
            return 'boolean_value'
        elif type.name == "null":
            return '"null"'
        elif type.name == "undefined":
            return '"undefined"'
        elif type.name == "void":
            return '"void"'
        elif type.name == "any" or type.name == "unknown":
            return 'any_value'
        else:
            # Unknown primitive - accept any value
            return 'any_value'

    def convert_object(
        self,
        class_type: ClassType,
        context: TypeContext
    ) -> str:
        """
        Convert object/class type to grammar.

        Args:
            class_type: Class type definition
            context: Type context

        Returns:
            Grammar rule body

        Example:
            >>> converter = TypeToGrammarConverter()
            >>> person = ClassType("Person", {"name": Type("string")}, {})
            >>> rule = converter.convert_object(person, TypeContext())
            >>> print("{" in rule)
            True
        """
        if not class_type.properties:
            # Empty object
            return '"{" "}"'

        # Build property rules
        prop_parts = []
        for prop_name, prop_type in class_type.properties.items():
            prop_rule = self._convert_type(prop_type, context)
            prop_parts.append(f'"\\"" "{prop_name}" "\\"" ":" {prop_rule}')

        # Join with commas
        properties = ' "," '.join(prop_parts)

        return f'"{{" {properties} "}}"'

    def convert_array(
        self,
        element_type: Type,
        context: TypeContext
    ) -> str:
        """
        Convert array type to grammar.

        Args:
            element_type: Array element type
            context: Type context

        Returns:
            Grammar rule body

        Example:
            >>> converter = TypeToGrammarConverter()
            >>> rule = converter.convert_array(Type("number"), TypeContext())
            >>> print("[" in rule)
            True
        """
        element_rule = self._convert_type(element_type, context)

        # Array can be empty or have elements
        return f'"[" ({element_rule} ("," {element_rule})*)? "]"'

    def convert_union(
        self,
        types: List[Type],
        context: TypeContext
    ) -> str:
        """
        Convert union type to grammar (alternatives).

        Args:
            types: Union member types
            context: Type context

        Returns:
            Grammar rule body

        Example:
            >>> converter = TypeToGrammarConverter()
            >>> types = [Type("string"), Type("number")]
            >>> rule = converter.convert_union(types, TypeContext())
            >>> print("|" in rule)
            True
        """
        if not types:
            # Empty union - should not happen
            return '""'

        if len(types) == 1:
            return self._convert_type(types[0], context)

        # Generate rules for each type
        type_rules = [self._convert_type(t, context) for t in types]

        # Join with OR
        return ' | '.join(type_rules)

    def convert_function(
        self,
        signature: FunctionSignature,
        context: TypeContext
    ) -> str:
        """
        Convert function type to grammar.

        Args:
            signature: Function signature
            context: Type context

        Returns:
            Grammar rule body (simplified)
        """
        # Simplified function syntax
        # For now, just accept function keyword + identifier
        return '"function" IDENT'

    def convert_generic(
        self,
        type: Type,
        context: TypeContext
    ) -> str:
        """
        Convert generic type to grammar.

        Args:
            type: Generic type
            context: Type context

        Returns:
            Grammar rule body
        """
        if type.name == "Array":
            # Special handling for Array
            if type.parameters:
                return self.convert_array(type.parameters[0], context)
            else:
                return self.convert_array(Type("any"), context)

        # For other generics, just use the base type name
        return f'"{type.name}"'

    # Private helper methods

    def _convert_type(self, type: Type, context: TypeContext) -> str:
        """
        Convert a type to a grammar rule (dispatcher).

        Args:
            type: Type to convert
            context: Type context

        Returns:
            Grammar rule body
        """
        # Handle nullable types
        if type.nullable:
            non_null = Type(type.name, type.parameters, nullable=False)
            non_null_rule = self._convert_type(non_null, context)
            return f'({non_null_rule} | "null")'

        # Handle union types
        if type.name == "union":
            return self.convert_union(list(type.parameters), context)

        # Handle intersection types (simplified - treat as object merge)
        if type.name == "intersection":
            # For now, just use first type
            # Full implementation would merge object properties
            if type.parameters:
                return self._convert_type(type.parameters[0], context)
            return 'any_value'

        # Handle array types
        if type.name == "Array":
            if type.parameters:
                return self.convert_array(type.parameters[0], context)
            return self.convert_array(Type("any"), context)

        # Handle function types
        if type.name == "function":
            # Simplified - just keyword
            return '"function"'

        # Handle special types (any, unknown)
        if type.name in {"any", "unknown"}:
            return 'any_value'

        # Handle object type
        if type.name == "object":
            # Generic object - accept any JSON object
            return 'object_value'

        # Check if it's a class type
        if type.name in context.classes:
            class_type = context.classes[type.name]
            return self.convert_object(class_type, context)

        # Handle primitive types
        if type.is_primitive():
            return self.convert_primitive(type)

        # Generic type with parameters
        if type.parameters:
            return self.convert_generic(type, context)

        # Unknown type - use type name as identifier
        return f'"{type.name}"'

    def _generate_rule_name(self, prefix: str = "rule") -> str:
        """
        Generate unique rule name.

        Args:
            prefix: Rule name prefix

        Returns:
            Unique rule name
        """
        self.rule_counter += 1
        return f"{prefix}_{self.rule_counter}"


def create_grammar_for_type(
    type: Type,
    context: Optional[TypeContext] = None,
    language: str = "typescript"
) -> str:
    """
    Convenience function to create grammar for a type.

    Args:
        type: Type to convert
        context: Type context (default: empty context)
        language: Target language

    Returns:
        Lark grammar string

    Example:
        >>> from maze.core.types import Type
        >>> grammar = create_grammar_for_type(Type("number"))
        >>> print("number_value" in grammar)
        True
    """
    if context is None:
        context = TypeContext(language=language)

    converter = TypeToGrammarConverter(language=language)
    return converter.convert(type, context)


# Re-export for cleaner imports
__all__ = [
    "TypeToGrammarConverter",
    "create_grammar_for_type",
]

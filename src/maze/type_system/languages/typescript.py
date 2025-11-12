"""
TypeScript-specific type system implementation.

Handles TypeScript type parsing, assignability checking, type widening/narrowing,
and generic instantiation.
"""

from __future__ import annotations

import re
from typing import Any

from maze.core.types import Type


class TypeScriptTypeSystem:
    """
    TypeScript-specific type system.

    Implements TypeScript type operations including:
    - Type parsing from TypeScript syntax
    - Assignability (subtyping) rules
    - Type widening (literal -> primitive)
    - Type narrowing (type guards)
    - Union/intersection resolution
    - Generic instantiation
    """

    def __init__(self):
        """Initialize TypeScript type system."""
        self.primitive_types = {
            "string",
            "number",
            "boolean",
            "null",
            "undefined",
            "void",
            "any",
            "unknown",
            "never",
        }

    def parse_type(self, type_annotation: str) -> Type:
        """
        Parse TypeScript type annotation to Maze Type.

        Args:
            type_annotation: TypeScript type string

        Returns:
            Maze Type representation

        Examples:
            >>> ts = TypeScriptTypeSystem()
            >>> ts.parse_type("number")
            Type(name='number')
            >>> ts.parse_type("Array<string>")
            Type(name='Array', parameters=(Type(name='string'),))
            >>> ts.parse_type("string | number")
            Type(name='union', parameters=(Type(name='string'), Type(name='number')))
        """
        # Normalize whitespace
        type_annotation = type_annotation.strip()

        # Check for nullable (ends with ?)
        nullable = type_annotation.endswith("?")
        if nullable:
            type_annotation = type_annotation[:-1].strip()

        # Parse union types (A | B) - but not inside generics
        if " | " in type_annotation and not self._contains_generic_brackets(type_annotation):
            parts = [self.parse_type(p.strip()) for p in type_annotation.split(" | ")]
            return Type("union", tuple(parts), nullable=nullable)

        # Parse intersection types (A & B) - but not inside generics
        if " & " in type_annotation and not self._contains_generic_brackets(type_annotation):
            parts = [self.parse_type(p.strip()) for p in type_annotation.split(" & ")]
            return Type("intersection", tuple(parts), nullable=nullable)

        # Parse array types
        if type_annotation.endswith("[]"):
            element_type = self.parse_type(type_annotation[:-2].strip())
            return Type("Array", (element_type,), nullable=nullable)

        # Parse generic types (e.g., Array<T>, Map<K, V>)
        generic_match = re.match(r"(\w+)<(.+)>$", type_annotation)
        if generic_match:
            base_name = generic_match.group(1)
            params_str = generic_match.group(2)

            # Parse type parameters
            type_params = self._parse_type_params(params_str)

            return Type(base_name, tuple(type_params), nullable=nullable)

        # Parse function types (simplified)
        if "=>" in type_annotation:
            # Format: (param: Type) => ReturnType
            return self._parse_function_type(type_annotation, nullable)

        # Parse object types
        if type_annotation.startswith("{") and type_annotation.endswith("}"):
            # Simplified object type parsing
            return Type("object", nullable=nullable)

        # Primitive or named type
        return Type(type_annotation, nullable=nullable)

    def is_assignable(self, source: Type, target: Type) -> bool:
        """
        Check if source type is assignable to target type.

        Implements TypeScript's structural subtyping rules.

        Args:
            source: Source type
            target: Target type

        Returns:
            True if source is assignable to target

        Examples:
            >>> ts = TypeScriptTypeSystem()
            >>> ts.is_assignable(Type("string"), Type("string"))
            True
            >>> ts.is_assignable(Type("number"), Type("string"))
            False
            >>> ts.is_assignable(Type("string"), Type("any"))
            True
        """
        # Exact match
        if source == target:
            return True

        # any accepts everything, everything accepts never
        if target.name == "any" or source.name == "never":
            return True

        # unknown only accepts unknown, any, or never
        if target.name == "unknown":
            return source.name in {"unknown", "any", "never"}

        # null/undefined assignability
        if source.name in {"null", "undefined"}:
            return target.nullable or target.name in {"null", "undefined", "any", "unknown"}

        # Union types
        if source.name == "union":
            # All union members must be assignable to target
            return all(self.is_assignable(member, target) for member in source.parameters)

        if target.name == "union":
            # Source must be assignable to at least one union member
            return any(self.is_assignable(source, member) for member in target.parameters)

        # Intersection types
        if target.name == "intersection":
            # Source must be assignable to all intersection members
            return all(self.is_assignable(source, member) for member in target.parameters)

        # Generic types - must match structure
        if source.parameters and target.parameters:
            if source.name == target.name and len(source.parameters) == len(target.parameters):
                # Covariant parameter matching (simplified)
                return all(
                    self.is_assignable(s, t) for s, t in zip(source.parameters, target.parameters)
                )

        # Nullable handling
        if source.nullable and not target.nullable:
            # Cannot assign nullable to non-nullable
            return False

        return False

    def widen_type(self, type: Type) -> Type:
        """
        Widen literal types to their base types.

        TypeScript widens types in certain contexts (e.g., mutable variables).

        Args:
            type: Type to widen

        Returns:
            Widened type

        Examples:
            >>> ts = TypeScriptTypeSystem()
            >>> literal = Type("'hello'")
            >>> widened = ts.widen_type(literal)
            >>> print(widened.name)
            string
        """
        # String literals widen to string
        if type.name.startswith("'") or type.name.startswith('"'):
            return Type("string", nullable=type.nullable)

        # Number literals widen to number
        if type.name.isdigit() or (type.name.startswith("-") and type.name[1:].isdigit()):
            return Type("number", nullable=type.nullable)

        # Boolean literals widen to boolean
        if type.name in {"true", "false"}:
            return Type("boolean", nullable=type.nullable)

        # Widen template literal types to string
        if type.name.startswith("`") and type.name.endswith("`"):
            return Type("string", nullable=type.nullable)

        # Already widened
        return type

    def narrow_type(self, type: Type, guard: str) -> Type:
        """
        Narrow type based on type guard.

        TypeScript narrows types in control flow based on type guards.

        Args:
            type: Type to narrow
            guard: Type guard expression

        Returns:
            Narrowed type

        Examples:
            >>> ts = TypeScriptTypeSystem()
            >>> union = Type("union", (Type("string"), Type("number")))
            >>> narrowed = ts.narrow_type(union, "typeof x === 'string'")
            >>> print(narrowed.name)
            string
        """
        # typeof guard
        if "typeof" in guard:
            if "'string'" in guard or '"string"' in guard:
                return Type("string")
            elif "'number'" in guard or '"number"' in guard:
                return Type("number")
            elif "'boolean'" in guard or '"boolean"' in guard:
                return Type("boolean")
            elif "'object'" in guard or '"object"' in guard:
                return Type("object")

        # instanceof guard
        if "instanceof" in guard:
            match = re.search(r"instanceof\s+(\w+)", guard)
            if match:
                class_name = match.group(1)
                return Type(class_name)

        # Nullability narrowing (x != null, x !== undefined)
        if (
            "!= null" in guard
            or "!== null" in guard
            or "!= undefined" in guard
            or "!== undefined" in guard
        ):
            # Remove nullability
            return Type(type.name, type.parameters, nullable=False, metadata=type.metadata)

        # Union narrowing
        if type.name == "union":
            # Try to narrow to specific union member
            for member in type.parameters:
                if member.name in guard:
                    return member

        # No narrowing possible
        return type

    def infer_from_literal(self, literal: Any) -> Type:
        """
        Infer type from JavaScript literal value.

        Args:
            literal: JavaScript literal value

        Returns:
            Inferred type

        Examples:
            >>> ts = TypeScriptTypeSystem()
            >>> ts.infer_from_literal(42)
            Type(name='number')
            >>> ts.infer_from_literal("hello")
            Type(name='string')
        """
        if isinstance(literal, bool):
            return Type("boolean")
        elif isinstance(literal, int) or isinstance(literal, float):
            return Type("number")
        elif isinstance(literal, str):
            return Type("string")
        elif literal is None:
            return Type("null")
        elif isinstance(literal, list):
            if literal:
                element_type = self.infer_from_literal(literal[0])
                return Type("Array", (element_type,))
            else:
                return Type("Array", (Type("unknown"),))
        elif isinstance(literal, dict):
            return Type("object")
        else:
            return Type("unknown")

    def resolve_union(self, types: list[Type]) -> Type:
        """
        Create union type, simplifying if possible.

        Args:
            types: Types to union

        Returns:
            Union type or simplified type

        Examples:
            >>> ts = TypeScriptTypeSystem()
            >>> union = ts.resolve_union([Type("string"), Type("number")])
            >>> print(union.name)
            union
        """
        if not types:
            return Type("never")

        if len(types) == 1:
            return types[0]

        # Remove duplicates
        unique_types = []
        seen = set()

        for t in types:
            t_str = str(t)
            if t_str not in seen:
                seen.add(t_str)
                unique_types.append(t)

        if len(unique_types) == 1:
            return unique_types[0]

        # Check for never (never | T = T)
        unique_types = [t for t in unique_types if t.name != "never"]

        if not unique_types:
            return Type("never")

        if len(unique_types) == 1:
            return unique_types[0]

        # Check for any (any | T = any)
        if any(t.name == "any" for t in unique_types):
            return Type("any")

        return Type("union", tuple(unique_types))

    def resolve_intersection(self, types: list[Type]) -> Type:
        """
        Create intersection type, merging if possible.

        Args:
            types: Types to intersect

        Returns:
            Intersection type or merged type

        Examples:
            >>> ts = TypeScriptTypeSystem()
            >>> inter = ts.resolve_intersection([Type("A"), Type("B")])
            >>> print(inter.name)
            intersection
        """
        if not types:
            return Type("never")

        if len(types) == 1:
            return types[0]

        # Remove duplicates
        unique_types = []
        seen = set()

        for t in types:
            t_str = str(t)
            if t_str not in seen:
                seen.add(t_str)
                unique_types.append(t)

        if len(unique_types) == 1:
            return unique_types[0]

        # Check for never (never & T = never)
        if any(t.name == "never" for t in unique_types):
            return Type("never")

        # Check for any (any & T = T)
        unique_types = [t for t in unique_types if t.name != "any"]

        if not unique_types:
            return Type("any")

        if len(unique_types) == 1:
            return unique_types[0]

        return Type("intersection", tuple(unique_types))

    def instantiate_generic(self, generic: Type, type_args: list[Type]) -> Type:
        """
        Instantiate generic type with type arguments.

        Args:
            generic: Generic type
            type_args: Type arguments for instantiation

        Returns:
            Instantiated type

        Examples:
            >>> ts = TypeScriptTypeSystem()
            >>> generic = Type("Array", (Type("T"),))
            >>> instantiated = ts.instantiate_generic(generic, [Type("number")])
            >>> print(instantiated)
            Array<number>
        """
        if not generic.parameters:
            # Not a generic type
            return generic

        if len(type_args) != len(generic.parameters):
            # Mismatched type argument count
            return generic

        # Create substitution map
        subst = {}
        for param, arg in zip(generic.parameters, type_args):
            if param.name not in self.primitive_types:
                # Type parameter
                subst[param.name] = arg

        # Apply substitution
        instantiated_params = tuple(
            arg if i < len(type_args) else param
            for i, (param, arg) in enumerate(zip(generic.parameters, type_args))
        )

        return Type(
            generic.name, instantiated_params, nullable=generic.nullable, metadata=generic.metadata
        )

    # Private helper methods

    def _contains_generic_brackets(self, type_str: str) -> bool:
        """
        Check if type string contains generic angle brackets.

        Args:
            type_str: Type string to check

        Returns:
            True if contains < and >
        """
        return "<" in type_str and ">" in type_str

    def _parse_type_params(self, params_str: str) -> list[Type]:
        """
        Parse comma-separated type parameters.

        Handles nested generics correctly.
        """
        params = []
        depth = 0
        current = ""

        for char in params_str:
            if char == "<":
                depth += 1
                current += char
            elif char == ">":
                depth -= 1
                current += char
            elif char == "," and depth == 0:
                if current.strip():
                    params.append(self.parse_type(current.strip()))
                current = ""
            else:
                current += char

        if current.strip():
            params.append(self.parse_type(current.strip()))

        return params

    def _parse_function_type(self, type_annotation: str, nullable: bool) -> Type:
        """Parse function type annotation."""
        # Simplified function type parsing
        # Format: (param: Type) => ReturnType
        parts = type_annotation.split("=>")

        if len(parts) != 2:
            return Type("function", nullable=nullable)

        # Parse parameter types (simplified)
        params_str = parts[0].strip()
        return_str = parts[1].strip()

        # Parse return type
        return_type = self.parse_type(return_str)

        # For now, return generic function type
        # Full implementation would parse parameter types
        return Type("function", (return_type,), nullable=nullable)


# Re-export for cleaner imports
__all__ = [
    "TypeScriptTypeSystem",
]

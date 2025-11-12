"""
JSON Schema synthesis from type definitions.

This module provides utilities for converting type definitions from various
sources (Pydantic models, TypeScript interfaces, Maze types) into JSON Schema.
"""

from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass
from typing import Any, get_type_hints

from maze.core.types import ClassType, FunctionSignature, InterfaceType, Type

logger = logging.getLogger(__name__)


@dataclass
class SchemaBuilder:
    """
    Builder for constructing JSON Schema from type definitions.

    Supports conversion from:
    - Pydantic models (runtime introspection)
    - Python dataclasses (type hints)
    - Maze Type objects
    - Direct schema construction
    """

    strict: bool = True
    additional_properties: bool = False
    definitions: dict[str, Any] = None

    def __post_init__(self):
        """Initialize definitions storage."""
        if self.definitions is None:
            self.definitions = {}

    def from_pydantic(self, model: type) -> dict[str, Any]:
        """
        Convert Pydantic model to JSON Schema.

        Args:
            model: Pydantic model class

        Returns:
            JSON Schema dict

        Raises:
            ImportError: If pydantic not installed
            ValueError: If not a Pydantic model
        """
        try:
            from pydantic import BaseModel
        except ImportError:
            raise ImportError("pydantic not installed. Install with: uv add pydantic")

        if not (inspect.isclass(model) and issubclass(model, BaseModel)):
            raise ValueError(f"{model} is not a Pydantic BaseModel")

        # Use Pydantic's built-in schema generation
        schema = model.model_json_schema()

        # Optionally enforce strict mode
        if self.strict:
            schema["additionalProperties"] = self.additional_properties

        return schema

    def from_dataclass(self, cls: type) -> dict[str, Any]:
        """
        Convert Python dataclass to JSON Schema.

        Args:
            cls: Dataclass class

        Returns:
            JSON Schema dict

        Raises:
            ValueError: If not a dataclass
        """
        from dataclasses import fields, is_dataclass

        if not is_dataclass(cls):
            raise ValueError(f"{cls} is not a dataclass")

        properties = {}
        required = []

        # Get type hints
        hints = get_type_hints(cls)

        for field in fields(cls):
            field_name = field.name
            field_type = hints.get(field_name, field.type)

            # Convert type to JSON Schema type
            properties[field_name] = self._python_type_to_schema(field_type)

            # Check if field is required (no default)
            from dataclasses import MISSING

            if field.default is MISSING and field.default_factory is MISSING:
                required.append(field_name)

        schema = {
            "type": "object",
            "properties": properties,
            "required": required,
        }

        if self.strict:
            schema["additionalProperties"] = self.additional_properties

        return schema

    def from_maze_type(self, maze_type: Type) -> dict[str, Any]:
        """
        Convert Maze Type to JSON Schema.

        Args:
            maze_type: Maze Type object

        Returns:
            JSON Schema dict
        """
        # Handle nullable types first (wraps the base type)
        if maze_type.nullable:
            base_schema = self.from_maze_type(
                Type(maze_type.name, maze_type.parameters, nullable=False)
            )
            return {"anyOf": [base_schema, {"type": "null"}]}

        # Handle primitive types
        if maze_type.name in ("string", "str"):
            return {"type": "string"}
        elif maze_type.name in ("number", "int", "float"):
            return {"type": "number"}
        elif maze_type.name in ("boolean", "bool"):
            return {"type": "boolean"}
        elif maze_type.name in ("null", "None"):
            return {"type": "null"}
        elif maze_type.name == "any":
            return {}  # Empty schema = any type

        # Handle array types
        elif maze_type.name in ("Array", "List", "list"):
            if maze_type.parameters:
                item_schema = self.from_maze_type(maze_type.parameters[0])
                return {"type": "array", "items": item_schema}
            else:
                return {"type": "array"}

        # Handle object/dict types
        elif maze_type.name in ("Object", "Dict", "dict"):
            return {"type": "object"}

        # Generic/unknown types - use type name as reference
        else:
            return {"$ref": f"#/definitions/{maze_type.name}"}

    def from_class_type(self, class_type: ClassType) -> dict[str, Any]:
        """
        Convert Maze ClassType to JSON Schema.

        Args:
            class_type: ClassType object

        Returns:
            JSON Schema dict
        """
        properties = {}
        required = []

        for prop_name, prop_type in class_type.properties.items():
            properties[prop_name] = self.from_maze_type(prop_type)
            # Assume all properties are required unless explicitly optional
            if not prop_type.nullable:
                required.append(prop_name)

        schema = {
            "type": "object",
            "properties": properties,
        }

        if required:
            schema["required"] = required

        if self.strict:
            schema["additionalProperties"] = self.additional_properties

        return schema

    def from_interface_type(self, interface: InterfaceType) -> dict[str, Any]:
        """
        Convert Maze InterfaceType to JSON Schema.

        Args:
            interface: InterfaceType object

        Returns:
            JSON Schema dict
        """
        properties = {}
        required = []

        for method in interface.methods:
            # Represent methods as their signature
            properties[method.name] = self._function_signature_to_schema(method)

        schema = {
            "type": "object",
            "properties": properties,
        }

        if self.strict:
            schema["additionalProperties"] = self.additional_properties

        return schema

    def build_object_schema(
        self,
        properties: dict[str, dict[str, Any]],
        required: list[str] | None = None,
        additional_properties: bool | None = None,
    ) -> dict[str, Any]:
        """
        Build an object schema directly.

        Args:
            properties: Property name -> property schema mapping
            required: List of required property names
            additional_properties: Whether to allow additional properties

        Returns:
            JSON Schema dict
        """
        schema = {
            "type": "object",
            "properties": properties,
        }

        if required:
            schema["required"] = required

        if additional_properties is not None:
            schema["additionalProperties"] = additional_properties
        elif self.strict:
            schema["additionalProperties"] = self.additional_properties

        return schema

    def build_array_schema(
        self,
        items: dict[str, Any],
        min_items: int | None = None,
        max_items: int | None = None,
        unique_items: bool = False,
    ) -> dict[str, Any]:
        """
        Build an array schema.

        Args:
            items: Schema for array items
            min_items: Minimum number of items
            max_items: Maximum number of items
            unique_items: Whether items must be unique

        Returns:
            JSON Schema dict
        """
        schema = {
            "type": "array",
            "items": items,
        }

        if min_items is not None:
            schema["minItems"] = min_items
        if max_items is not None:
            schema["maxItems"] = max_items
        if unique_items:
            schema["uniqueItems"] = True

        return schema

    def build_enum_schema(self, values: list[Any]) -> dict[str, Any]:
        """
        Build an enum schema.

        Args:
            values: List of allowed values

        Returns:
            JSON Schema dict
        """
        return {"enum": values}

    def build_string_schema(
        self,
        pattern: str | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        format: str | None = None,
    ) -> dict[str, Any]:
        """
        Build a string schema with constraints.

        Args:
            pattern: Regex pattern
            min_length: Minimum length
            max_length: Maximum length
            format: String format (e.g., "email", "uri", "date-time")

        Returns:
            JSON Schema dict
        """
        schema = {"type": "string"}

        if pattern:
            schema["pattern"] = pattern
        if min_length is not None:
            schema["minLength"] = min_length
        if max_length is not None:
            schema["maxLength"] = max_length
        if format:
            schema["format"] = format

        return schema

    def build_number_schema(
        self,
        minimum: float | None = None,
        maximum: float | None = None,
        exclusive_minimum: float | None = None,
        exclusive_maximum: float | None = None,
        multiple_of: float | None = None,
        integer: bool = False,
    ) -> dict[str, Any]:
        """
        Build a number schema with constraints.

        Args:
            minimum: Minimum value (inclusive)
            maximum: Maximum value (inclusive)
            exclusive_minimum: Minimum value (exclusive)
            exclusive_maximum: Maximum value (exclusive)
            multiple_of: Number must be multiple of this value
            integer: Whether to use integer type

        Returns:
            JSON Schema dict
        """
        schema = {"type": "integer" if integer else "number"}

        if minimum is not None:
            schema["minimum"] = minimum
        if maximum is not None:
            schema["maximum"] = maximum
        if exclusive_minimum is not None:
            schema["exclusiveMinimum"] = exclusive_minimum
        if exclusive_maximum is not None:
            schema["exclusiveMaximum"] = exclusive_maximum
        if multiple_of is not None:
            schema["multipleOf"] = multiple_of

        return schema

    def _python_type_to_schema(self, python_type: Any) -> dict[str, Any]:
        """
        Convert Python type hint to JSON Schema.

        Args:
            python_type: Python type annotation

        Returns:
            JSON Schema dict
        """
        # Handle basic types
        if python_type == str:
            return {"type": "string"}
        elif python_type in (int, float):
            return {"type": "number"}
        elif python_type == bool:
            return {"type": "boolean"}
        elif python_type == type(None):
            return {"type": "null"}

        # Handle typing module types
        origin = getattr(python_type, "__origin__", None)

        if origin is list or origin is list:
            args = getattr(python_type, "__args__", ())
            if args:
                return {"type": "array", "items": self._python_type_to_schema(args[0])}
            return {"type": "array"}

        elif origin is dict or origin is dict:
            return {"type": "object"}

        # Default to any
        return {}

    def _function_signature_to_schema(self, sig: FunctionSignature) -> dict[str, Any]:
        """
        Convert function signature to schema representation.

        Args:
            sig: FunctionSignature object

        Returns:
            Schema describing the function
        """
        return {
            "type": "object",
            "properties": {
                "parameters": {
                    "type": "array",
                    "items": [{"type": "string", "const": param.name} for param in sig.parameters],
                },
                "returnType": self.from_maze_type(sig.return_type),
            },
        }


__all__ = [
    "SchemaBuilder",
]

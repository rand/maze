"""
Unit tests for JSON Schema synthesis.
"""

import pytest
from dataclasses import dataclass
from typing import List, Dict, Optional

from maze.synthesis.schema_builder import SchemaBuilder
from maze.core.types import Type, ClassType, InterfaceType, FunctionSignature, TypeParameter


class TestSchemaBuilderBasics:
    """Test basic schema builder functionality."""

    def test_builder_creation(self):
        """Test creating schema builder."""
        builder = SchemaBuilder()
        assert builder.strict is True
        assert builder.additional_properties is False
        assert builder.definitions == {}

    def test_builder_with_options(self):
        """Test creating builder with custom options."""
        builder = SchemaBuilder(strict=False, additional_properties=True)
        assert builder.strict is False
        assert builder.additional_properties is True


class TestMazeTypeConversion:
    """Test converting Maze Type objects to JSON Schema."""

    def test_string_type(self):
        """Test string type conversion."""
        builder = SchemaBuilder()
        schema = builder.from_maze_type(Type("string"))
        assert schema == {"type": "string"}

    def test_number_type(self):
        """Test number type conversion."""
        builder = SchemaBuilder()
        schema = builder.from_maze_type(Type("number"))
        assert schema == {"type": "number"}

    def test_boolean_type(self):
        """Test boolean type conversion."""
        builder = SchemaBuilder()
        schema = builder.from_maze_type(Type("boolean"))
        assert schema == {"type": "boolean"}

    def test_null_type(self):
        """Test null type conversion."""
        builder = SchemaBuilder()
        schema = builder.from_maze_type(Type("null"))
        assert schema == {"type": "null"}

    def test_any_type(self):
        """Test any type conversion."""
        builder = SchemaBuilder()
        schema = builder.from_maze_type(Type("any"))
        assert schema == {}  # Empty schema = any type

    def test_array_type(self):
        """Test array type conversion."""
        builder = SchemaBuilder()
        array_type = Type("Array", (Type("string"),))
        schema = builder.from_maze_type(array_type)

        assert schema == {
            "type": "array",
            "items": {"type": "string"}
        }

    def test_array_type_no_params(self):
        """Test array without type parameters."""
        builder = SchemaBuilder()
        schema = builder.from_maze_type(Type("Array"))
        assert schema == {"type": "array"}

    def test_object_type(self):
        """Test object type conversion."""
        builder = SchemaBuilder()
        schema = builder.from_maze_type(Type("Object"))
        assert schema == {"type": "object"}

    def test_nullable_type(self):
        """Test nullable type conversion."""
        builder = SchemaBuilder()
        nullable_string = Type("string", nullable=True)
        schema = builder.from_maze_type(nullable_string)

        assert "anyOf" in schema
        assert {"type": "string"} in schema["anyOf"]
        assert {"type": "null"} in schema["anyOf"]

    def test_custom_type_reference(self):
        """Test custom type creates reference."""
        builder = SchemaBuilder()
        schema = builder.from_maze_type(Type("CustomType"))

        assert schema == {"$ref": "#/definitions/CustomType"}


class TestClassTypeConversion:
    """Test converting ClassType to JSON Schema."""

    def test_simple_class(self):
        """Test simple class conversion."""
        builder = SchemaBuilder()

        class_type = ClassType(
            name="Person",
            properties={
                "name": Type("string"),
                "age": Type("number"),
            },
            methods={}
        )

        schema = builder.from_class_type(class_type)

        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]
        assert schema["properties"]["name"] == {"type": "string"}
        assert schema["properties"]["age"] == {"type": "number"}
        assert set(schema["required"]) == {"name", "age"}
        assert schema["additionalProperties"] is False

    def test_class_with_optional_fields(self):
        """Test class with optional fields."""
        builder = SchemaBuilder()

        class_type = ClassType(
            name="Person",
            properties={
                "name": Type("string"),
                "nickname": Type("string", nullable=True),
            },
            methods={}
        )

        schema = builder.from_class_type(class_type)

        # Only non-nullable fields should be required
        assert "required" in schema
        assert "name" in schema["required"]
        assert "nickname" not in schema["required"]


class TestDataclassConversion:
    """Test converting Python dataclasses to JSON Schema."""

    def test_simple_dataclass(self):
        """Test simple dataclass conversion."""
        @dataclass
        class Person:
            name: str
            age: int

        builder = SchemaBuilder()
        schema = builder.from_dataclass(Person)

        assert schema["type"] == "object"
        assert schema["properties"]["name"] == {"type": "string"}
        assert schema["properties"]["age"] == {"type": "number"}
        assert set(schema["required"]) == {"name", "age"}
        assert schema["additionalProperties"] is False

    def test_dataclass_with_defaults(self):
        """Test dataclass with default values."""
        @dataclass
        class Person:
            name: str
            age: int = 0

        builder = SchemaBuilder()
        schema = builder.from_dataclass(Person)

        # Fields with defaults are not required
        assert "name" in schema["required"]
        assert "age" not in schema["required"]

    def test_dataclass_with_list(self):
        """Test dataclass with list field."""
        @dataclass
        class Team:
            name: str
            members: List[str]

        builder = SchemaBuilder()
        schema = builder.from_dataclass(Team)

        assert schema["properties"]["members"] == {
            "type": "array",
            "items": {"type": "string"}
        }

    def test_not_a_dataclass(self):
        """Test error on non-dataclass."""
        class NotADataclass:
            pass

        builder = SchemaBuilder()

        with pytest.raises(ValueError, match="not a dataclass"):
            builder.from_dataclass(NotADataclass)


class TestPydanticConversion:
    """Test converting Pydantic models to JSON Schema."""

    def test_pydantic_model(self):
        """Test Pydantic model conversion."""
        try:
            from pydantic import BaseModel
        except ImportError:
            pytest.skip("pydantic not installed")

        class Person(BaseModel):
            name: str
            age: int

        builder = SchemaBuilder()
        schema = builder.from_pydantic(Person)

        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]

    def test_not_a_pydantic_model(self):
        """Test error on non-Pydantic class."""
        class NotPydantic:
            pass

        builder = SchemaBuilder()

        with pytest.raises(ValueError, match="not a Pydantic BaseModel"):
            builder.from_pydantic(NotPydantic)


class TestSchemaBuilders:
    """Test direct schema building methods."""

    def test_build_object_schema(self):
        """Test building object schema."""
        builder = SchemaBuilder()

        schema = builder.build_object_schema(
            properties={
                "name": {"type": "string"},
                "age": {"type": "number"}
            },
            required=["name"]
        )

        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]
        assert schema["required"] == ["name"]

    def test_build_array_schema(self):
        """Test building array schema."""
        builder = SchemaBuilder()

        schema = builder.build_array_schema(
            items={"type": "string"},
            min_items=1,
            max_items=10,
            unique_items=True
        )

        assert schema["type"] == "array"
        assert schema["items"] == {"type": "string"}
        assert schema["minItems"] == 1
        assert schema["maxItems"] == 10
        assert schema["uniqueItems"] is True

    def test_build_enum_schema(self):
        """Test building enum schema."""
        builder = SchemaBuilder()
        schema = builder.build_enum_schema(["red", "green", "blue"])

        assert schema == {"enum": ["red", "green", "blue"]}

    def test_build_string_schema(self):
        """Test building string schema with constraints."""
        builder = SchemaBuilder()

        schema = builder.build_string_schema(
            pattern="^[a-z]+$",
            min_length=3,
            max_length=20,
            format="email"
        )

        assert schema["type"] == "string"
        assert schema["pattern"] == "^[a-z]+$"
        assert schema["minLength"] == 3
        assert schema["maxLength"] == 20
        assert schema["format"] == "email"

    def test_build_number_schema(self):
        """Test building number schema with constraints."""
        builder = SchemaBuilder()

        schema = builder.build_number_schema(
            minimum=0,
            maximum=100,
            multiple_of=5,
            integer=True
        )

        assert schema["type"] == "integer"
        assert schema["minimum"] == 0
        assert schema["maximum"] == 100
        assert schema["multipleOf"] == 5

    def test_build_number_schema_exclusive(self):
        """Test exclusive min/max."""
        builder = SchemaBuilder()

        schema = builder.build_number_schema(
            exclusive_minimum=0,
            exclusive_maximum=1
        )

        assert schema["exclusiveMinimum"] == 0
        assert schema["exclusiveMaximum"] == 1


class TestComplexSchemas:
    """Test complex schema scenarios."""

    def test_nested_objects(self):
        """Test nested object schemas."""
        builder = SchemaBuilder()

        schema = builder.build_object_schema(
            properties={
                "user": builder.build_object_schema(
                    properties={
                        "name": {"type": "string"},
                        "email": {"type": "string"}
                    },
                    required=["name", "email"]
                ),
                "posts": builder.build_array_schema(
                    items=builder.build_object_schema(
                        properties={
                            "title": {"type": "string"},
                            "content": {"type": "string"}
                        }
                    )
                )
            }
        )

        assert schema["properties"]["user"]["type"] == "object"
        assert schema["properties"]["posts"]["type"] == "array"
        assert schema["properties"]["posts"]["items"]["type"] == "object"

    def test_strict_mode(self):
        """Test strict mode enforcement."""
        builder = SchemaBuilder(strict=True, additional_properties=False)

        schema = builder.build_object_schema(
            properties={"name": {"type": "string"}}
        )

        assert schema["additionalProperties"] is False

    def test_non_strict_mode(self):
        """Test non-strict mode."""
        builder = SchemaBuilder(strict=False)

        schema = builder.build_object_schema(
            properties={"name": {"type": "string"}}
        )

        assert "additionalProperties" not in schema

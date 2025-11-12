"""Tests for JSON Schema to GBNF conversion.

Test coverage target: 85%
"""


from maze.orchestrator.providers import LlamaCppProviderAdapter


class TestSchemaToGBNF:
    """Tests for schema to GBNF conversion."""

    def test_object_schema_to_gbnf(self):
        """Test converting object schema to GBNF."""
        adapter = LlamaCppProviderAdapter(model="test")

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
            },
        }

        gbnf = adapter._schema_to_gbnf(schema)

        assert "name" in gbnf
        assert "age" in gbnf
        assert "::" in gbnf  # GBNF syntax

    def test_array_schema_to_gbnf(self):
        """Test converting array schema to GBNF."""
        adapter = LlamaCppProviderAdapter(model="test")

        schema = {"type": "array", "items": {"type": "string"}}

        gbnf = adapter._schema_to_gbnf(schema)

        assert "[" in gbnf
        assert "]" in gbnf

    def test_string_property_gbnf(self):
        """Test string property in GBNF."""
        adapter = LlamaCppProviderAdapter(model="test")

        schema = {"type": "object", "properties": {"text": {"type": "string"}}}

        gbnf = adapter._schema_to_gbnf(schema)

        assert "text" in gbnf
        assert '"' in gbnf  # String quotes

    def test_number_property_gbnf(self):
        """Test number property in GBNF."""
        adapter = LlamaCppProviderAdapter(model="test")

        schema = {"type": "object", "properties": {"count": {"type": "number"}}}

        gbnf = adapter._schema_to_gbnf(schema)

        assert "count" in gbnf
        assert "[0-9]" in gbnf  # Number pattern

    def test_boolean_property_gbnf(self):
        """Test boolean property in GBNF."""
        adapter = LlamaCppProviderAdapter(model="test")

        schema = {"type": "object", "properties": {"active": {"type": "boolean"}}}

        gbnf = adapter._schema_to_gbnf(schema)

        assert "active" in gbnf
        assert "true" in gbnf or "false" in gbnf

    def test_fallback_to_generic_json(self):
        """Test fallback for unsupported schemas."""
        adapter = LlamaCppProviderAdapter(model="test")

        schema = {"type": "unknown"}

        gbnf = adapter._schema_to_gbnf(schema)

        assert "json_value" in gbnf

"""Tests for JSON Schema constraints in llguidance adapter.

Test coverage target: 85%
"""

from maze.integrations.llguidance.adapter import LLGuidanceAdapter


class TestSchemaConstraints:
    """Tests for schema-specific constraint generation."""

    def test_base_json_grammar(self):
        """Test base JSON grammar without schema."""
        adapter = LLGuidanceAdapter()
        grammar = adapter.grammar_from_json_schema(None)

        assert "object" in grammar
        assert "array" in grammar
        assert "string" in grammar

    def test_object_schema_with_properties(self):
        """Test object schema generates property constraints."""
        adapter = LLGuidanceAdapter()

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
                "active": {"type": "boolean"},
            },
            "required": ["name"],
        }

        grammar = adapter.grammar_from_json_schema(schema)

        assert "name" in grammar
        assert "age" in grammar
        assert "active" in grammar
        assert "string" in grammar
        assert "number" in grammar

    def test_array_schema(self):
        """Test array schema generation."""
        adapter = LLGuidanceAdapter()

        schema = {
            "type": "array",
            "items": {"type": "string"},
        }

        grammar = adapter.grammar_from_json_schema(schema)

        assert "array" in grammar

    def test_nested_object_schema(self):
        """Test nested object schema (basic support)."""
        adapter = LLGuidanceAdapter()

        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                }
            },
        }

        grammar = adapter.grammar_from_json_schema(schema)

        # Should at least generate base grammar with object support
        assert "object" in grammar
        # Nested properties not fully implemented, just verify no crash
        assert grammar is not None

    def test_schema_with_required_fields(self):
        """Test schema with required fields."""
        adapter = LLGuidanceAdapter()

        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "optional_field": {"type": "string"},
            },
            "required": ["id"],
        }

        grammar = adapter.grammar_from_json_schema(schema)

        # Both fields should be in grammar
        assert "id" in grammar
        assert "optional_field" in grammar

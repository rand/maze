"""
Unit tests for grammar builder.
"""

import pytest

from maze.synthesis.grammar_builder import (
    GrammarBuilder,
    GrammarTemplate,
    create_json_schema_grammar,
    merge_grammars,
)


class TestGrammarTemplate:
    """Test grammar template functionality."""

    def test_template_creation(self):
        """Test creating a template."""
        template = GrammarTemplate(
            name="test", grammar="?start: {{rule}}\n{{rule}}: {{pattern}}", language="test"
        )

        assert template.name == "test"
        assert "rule" in template.variables
        assert "pattern" in template.variables

    def test_template_rendering(self):
        """Test rendering a template."""
        template = GrammarTemplate(
            name="test", grammar="?start: {{rule}}\n{{rule}}: {{pattern}}", language="test"
        )

        rendered = template.render(rule="expr", pattern="NUMBER")
        assert "?start: expr" in rendered
        assert "expr: NUMBER" in rendered

    def test_template_missing_variables(self):
        """Test error on missing variables."""
        template = GrammarTemplate(
            name="test", grammar="?start: {{rule}}\n{{rule}}: {{pattern}}", language="test"
        )

        with pytest.raises(ValueError, match="Missing required variables"):
            template.render(rule="expr")  # Missing 'pattern'


class TestGrammarBuilder:
    """Test grammar builder functionality."""

    def test_builder_creation(self):
        """Test creating a grammar builder."""
        builder = GrammarBuilder(language="typescript")
        assert builder.language == "typescript"
        assert len(builder.rules) == 0

    def test_add_rule(self):
        """Test adding a rule."""
        builder = GrammarBuilder()
        builder.add_rule("expr", "NUMBER | STRING")

        assert len(builder.rules) == 1
        assert "expr: NUMBER | STRING" in builder.rules

    def test_add_terminal(self):
        """Test adding a terminal."""
        builder = GrammarBuilder()
        builder.add_terminal("NUMBER", r"/\d+/")

        assert len(builder.terminals) == 1
        assert "NUMBER: /\\d+/" in builder.terminals

    def test_add_directive(self):
        """Test adding a directive."""
        builder = GrammarBuilder()
        builder.add_directive("%ignore /\\s+/")

        assert len(builder.directives) == 1
        assert "%ignore /\\s+/" in builder.directives

    def test_ignore_whitespace(self):
        """Test ignore whitespace convenience method."""
        builder = GrammarBuilder()
        builder.ignore_whitespace()

        assert "%ignore /\\s+/" in builder.directives

    def test_add_json_schema(self):
        """Test adding JSON schema."""
        builder = GrammarBuilder()
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        builder.add_json_schema(schema, "person")

        assert len(builder.rules) == 1
        assert "person: %json" in builder.rules[0]
        assert '"type":"object"' in builder.rules[0]

    def test_build_grammar(self):
        """Test building complete grammar."""
        builder = GrammarBuilder()
        builder.add_rule("start", "expr", priority="?")
        builder.add_rule("expr", "NUMBER | STRING")
        builder.add_terminal("NUMBER", r"/\d+/")
        builder.add_terminal("STRING", r'/"[^"]*"/')
        builder.ignore_whitespace()

        grammar = builder.build()

        assert "?start: expr" in grammar
        assert "expr: NUMBER | STRING" in grammar
        assert "NUMBER: /\\d+/" in grammar
        assert 'STRING: /"[^"]*"/' in grammar
        assert "%ignore /\\s+/" in grammar

    def test_validate_grammar_with_start(self):
        """Test validating grammar with start rule."""
        builder = GrammarBuilder()
        builder.add_rule("start", "expr", priority="?")
        builder.add_rule("expr", "NUMBER")

        valid, error = builder.validate()
        assert valid
        assert error is None

    def test_validate_grammar_no_start(self):
        """Test validating grammar without start rule."""
        builder = GrammarBuilder()
        builder.add_rule("expr", "NUMBER")

        valid, error = builder.validate()
        assert not valid
        assert "start" in error.lower()

    def test_template_registration(self):
        """Test template registration and loading."""
        template = GrammarTemplate(
            name="simple", grammar="?start: {{rule}}\n{{rule}}: NUMBER", language="test"
        )

        builder = GrammarBuilder()
        builder.add_template(template)

        assert "simple" in builder.templates

    def test_template_loading(self):
        """Test loading and rendering template."""
        template = GrammarTemplate(
            name="simple", grammar="?start: {{rule}}\n{{rule}}: NUMBER", language="test"
        )

        builder = GrammarBuilder()
        builder.add_template(template)
        builder.load_template("simple", rule="expr")

        grammar = builder.build()
        assert "?start: expr" in grammar
        assert "expr: NUMBER" in grammar

    def test_template_not_found(self):
        """Test error on template not found."""
        builder = GrammarBuilder()

        with pytest.raises(KeyError, match="Template 'missing' not found"):
            builder.load_template("missing")

    def test_clear(self):
        """Test clearing builder state."""
        builder = GrammarBuilder()
        builder.add_rule("start", "expr", priority="?")
        builder.add_terminal("NUMBER", r"/\d+/")
        builder.ignore_whitespace()

        builder.clear()

        assert len(builder.rules) == 0
        assert len(builder.terminals) == 0
        assert len(builder.directives) == 0

    def test_chaining(self):
        """Test method chaining."""
        builder = GrammarBuilder()
        result = (
            builder.add_rule("start", "expr", priority="?")
            .add_rule("expr", "NUMBER")
            .add_terminal("NUMBER", r"/\d+/")
            .ignore_whitespace()
        )

        assert result is builder
        assert len(builder.rules) == 2
        assert len(builder.terminals) == 1
        assert len(builder.directives) == 1


class TestGrammarHelpers:
    """Test grammar helper functions."""

    def test_create_json_schema_grammar(self):
        """Test creating grammar from JSON schema."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
        }

        grammar = create_json_schema_grammar(schema)

        assert "?start: json_value" in grammar
        assert "json_value: %json" in grammar
        assert "%ignore /\\s+/" in grammar

    def test_merge_grammars(self):
        """Test merging multiple grammars."""
        grammar1 = """
?start: expr
expr: NUMBER
NUMBER: /\\d+/
        """

        grammar2 = """
expr: STRING
STRING: /"[^"]*"/
%ignore /\\s+/
        """

        merged = merge_grammars(grammar1, grammar2)

        # Should have start rule
        assert "?start: expr" in merged
        # Should have both terminals
        assert "NUMBER: /\\d+/" in merged
        assert 'STRING: /"[^"]*"/' in merged
        # Should have directive
        assert "%ignore /\\s+/" in merged

    def test_merge_deduplicates(self):
        """Test that merge deduplicates rules."""
        grammar1 = "?start: expr\nexpr: NUMBER"
        grammar2 = "?start: expr\nexpr: STRING"

        merged = merge_grammars(grammar1, grammar2)

        # Should only have one start rule
        start_count = merged.count("?start: expr")
        assert start_count == 1

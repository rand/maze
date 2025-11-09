"""
Tests for hole filling engine.
"""

import pytest
from maze.type_system.holes import (
    HoleFillingEngine,
    Hole,
    HoleFillResult,
)
from maze.type_system.inference import TypeInferenceEngine
from maze.type_system.grammar_converter import TypeToGrammarConverter
from maze.core.types import Type, TypeContext


class TestHoleFillingEngine:
    """Test hole filling engine."""

    def test_identify_single_hole(self):
        """Test identifying single hole in code."""
        engine = HoleFillingEngine(
            TypeInferenceEngine(),
            TypeToGrammarConverter()
        )

        code = "const x: number = /*__HOLE_value__*/"
        holes = engine.identify_holes(code)

        assert len(holes) == 1
        assert holes[0].name == "value"

    def test_identify_multiple_holes(self):
        """Test identifying multiple holes."""
        engine = HoleFillingEngine(
            TypeInferenceEngine(),
            TypeToGrammarConverter()
        )

        code = """
        const x = /*__HOLE_first__*/
        const y = /*__HOLE_second__*/
        """
        holes = engine.identify_holes(code)

        assert len(holes) == 2
        assert {h.name for h in holes} == {"first", "second"}

    def test_identify_no_holes(self):
        """Test identifying code with no holes."""
        engine = HoleFillingEngine(
            TypeInferenceEngine(),
            TypeToGrammarConverter()
        )

        code = "const x = 42"
        holes = engine.identify_holes(code)

        assert len(holes) == 0

    def test_infer_hole_type_from_context(self):
        """Test inferring hole type from context."""
        engine = HoleFillingEngine(
            TypeInferenceEngine(),
            TypeToGrammarConverter()
        )

        context = TypeContext(variables={"value": Type("string")})
        hole = Hole("value", (1, 1), None, context, "expression")

        inferred = engine.infer_hole_type(hole, context)

        assert inferred == Type("string")

    def test_infer_hole_type_unknown(self):
        """Test inferring unknown hole type."""
        engine = HoleFillingEngine(
            TypeInferenceEngine(),
            TypeToGrammarConverter()
        )

        context = TypeContext()
        hole = Hole("unknown_var", (1, 1), None, context, "expression")

        inferred = engine.infer_hole_type(hole, context)

        assert inferred == Type("unknown")

    def test_generate_grammar_for_hole(self):
        """Test generating grammar for hole."""
        engine = HoleFillingEngine(
            TypeInferenceEngine(),
            TypeToGrammarConverter()
        )

        hole = Hole("x", (1, 1), Type("number"), TypeContext(), "expression")
        grammar = engine.generate_grammar_for_hole(hole, Type("number"))

        assert "number_value" in grammar
        assert "start" in grammar

    def test_fill_hole_without_provider(self):
        """Test filling hole without provider fails gracefully."""
        engine = HoleFillingEngine(
            TypeInferenceEngine(),
            TypeToGrammarConverter(),
            provider=None
        )

        hole = Hole("x", (1, 1), Type("number"), TypeContext(), "expression")
        result = engine.fill_hole(hole)

        assert result.success is False
        assert result.error_message == "No provider configured"

    def test_fill_all_holes_empty_code(self):
        """Test filling holes in code with no holes."""
        engine = HoleFillingEngine(
            TypeInferenceEngine(),
            TypeToGrammarConverter()
        )

        code = "const x = 42"
        context = TypeContext()

        filled, results = engine.fill_all_holes(code, context)

        assert filled == code
        assert len(results) == 0

    def test_hole_fill_result_to_dict(self):
        """Test converting hole fill result to dictionary."""
        hole = Hole("x", (1, 1), Type("number"), TypeContext(), "expression")
        result = HoleFillResult(
            hole=hole,
            filled_code="42",
            inferred_type=Type("number"),
            grammar_used="start: number_value",
            success=True,
            attempts=1
        )

        result_dict = result.to_dict()

        assert result_dict["hole_name"] == "x"
        assert result_dict["filled_code"] == "42"
        assert result_dict["success"] is True
        assert result_dict["attempts"] == 1

    def test_hole_location_tracking(self):
        """Test that hole locations are tracked correctly."""
        engine = HoleFillingEngine(
            TypeInferenceEngine(),
            TypeToGrammarConverter()
        )

        code = "line1\nline2 /*__HOLE_test__*/"
        holes = engine.identify_holes(code)

        assert len(holes) == 1
        assert holes[0].location[0] == 2  # Line 2


class TestHoleDataclass:
    """Test Hole dataclass."""

    def test_hole_creation(self):
        """Test creating a hole."""
        hole = Hole(
            name="test",
            location=(10, 5),
            expected_type=Type("string"),
            context=TypeContext(),
            kind="expression"
        )

        assert hole.name == "test"
        assert hole.location == (10, 5)
        assert hole.expected_type == Type("string")
        assert hole.kind == "expression"

    def test_hole_with_original_code(self):
        """Test hole with original code stored."""
        hole = Hole(
            name="test",
            location=(1, 1),
            expected_type=None,
            context=TypeContext(),
            kind="expression",
            original_code="const x = /*__HOLE_test__*/"
        )

        assert hole.original_code == "const x = /*__HOLE_test__*/"

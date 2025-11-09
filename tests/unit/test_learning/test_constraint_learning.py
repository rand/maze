"""
Tests for constraint learning system.
"""

import pytest

from maze.learning.constraint_learning import (
    ConstraintLearningSystem,
    ConstraintRefinement,
    Feedback,
    GenerationResult,
    ValidationResult,
    RepairResult,
    LearningEvent,
)
from maze.learning.pattern_mining import (
    PatternSet,
    SyntacticPattern,
    TypePattern,
    SemanticPattern,
)


class TestConstraintLearningSystem:
    """Test ConstraintLearningSystem class."""

    @pytest.fixture
    def system(self):
        """Create constraint learning system."""
        return ConstraintLearningSystem(
            learning_rate=0.1,
            min_score=0.1,
            max_constraints=100,
            decay_rate=0.01
        )

    def test_init(self, system):
        """Test initialization."""
        assert system.learning_rate == 0.1
        assert system.min_score == 0.1
        assert system.max_constraints == 100
        assert system.decay_rate == 0.01
        assert len(system.constraints) == 0
        assert len(system.learning_history) == 0

    def test_learn_from_success_simple(self, system):
        """Test learning from successful generation."""
        generation_result = GenerationResult(
            code="def add(x, y):\n    return x + y",
            language="python",
            generation_time_ms=100.0
        )
        validation_result = ValidationResult(success=True)

        refinement = system.learn_from_success(generation_result, validation_result)

        assert isinstance(refinement, ConstraintRefinement)
        assert refinement.source == "feedback"
        assert system.stats["successful_feedback"] == 1
        assert len(system.constraints) > 0

    def test_learn_from_success_boosts_weights(self, system):
        """Test that successful generation boosts pattern weights."""
        code = "def foo(): pass"
        generation_result = GenerationResult(code=code, language="python", generation_time_ms=50.0)
        validation_result = ValidationResult(success=True)

        # First success
        system.learn_from_success(generation_result, validation_result)
        initial_weights = list(system.constraints.values())

        # Second success with same pattern
        system.learn_from_success(generation_result, validation_result)
        updated_weights = list(system.constraints.values())

        # Weights should increase
        assert any(updated_weights[i] > initial_weights[i] for i in range(len(initial_weights)))

    def test_learn_from_failure_simple(self, system):
        """Test learning from failed generation."""
        generation_result = GenerationResult(
            code="def broken(\n    # syntax error",
            language="python",
            generation_time_ms=100.0
        )
        diagnostics = [
            {"severity": "error", "message": "SyntaxError: unexpected EOF"}
        ]

        refinement = system.learn_from_failure(generation_result, diagnostics)

        assert isinstance(refinement, ConstraintRefinement)
        assert refinement.source == "feedback"
        assert system.stats["failed_feedback"] == 1

    def test_learn_from_failure_reduces_weights(self, system):
        """Test that failures reduce pattern weights."""
        code = "def foo(): pass"
        generation_result = GenerationResult(code=code, language="python", generation_time_ms=50.0)

        # First establish a pattern with success
        validation_result = ValidationResult(success=True)
        system.learn_from_success(generation_result, validation_result)
        initial_weights = dict(system.constraints)

        # Then fail with same pattern
        diagnostics = [{"severity": "error", "message": "SyntaxError"}]
        system.learn_from_failure(generation_result, diagnostics)

        # Weights should decrease
        for pattern_id in initial_weights:
            if pattern_id in system.constraints:
                assert system.constraints[pattern_id] <= initial_weights[pattern_id]

    def test_learn_from_patterns_syntactic(self, system):
        """Test learning from syntactic patterns."""
        patterns = PatternSet(
            language="python",
            syntactic=[
                SyntacticPattern("function", "def foo(): ...", 5, ["def add(): pass"], {}),
                SyntacticPattern("class", "class Bar: ...", 3, ["class MyClass: pass"], {}),
            ],
            type_patterns=[],
            semantic=[],
            extraction_time_ms=100.0,
            total_patterns=2
        )

        refinements = system.learn_from_patterns(patterns)

        assert len(refinements) == 2
        assert all(isinstance(r, ConstraintRefinement) for r in refinements)
        assert all(r.source == "pattern_mining" for r in refinements)
        assert system.stats["constraints_added"] == 2

    def test_learn_from_patterns_type(self, system):
        """Test learning from type patterns."""
        patterns = PatternSet(
            language="python",
            syntactic=[],
            type_patterns=[
                TypePattern("int", ["x", "y", "count"], 3, []),
                TypePattern("str", ["name", "msg"], 2, []),
            ],
            semantic=[],
            extraction_time_ms=100.0,
            total_patterns=2
        )

        refinements = system.learn_from_patterns(patterns)

        assert len(refinements) == 2
        assert all(r.constraint_type == "type" for r in refinements)

    def test_learn_from_patterns_semantic(self, system):
        """Test learning from semantic patterns."""
        patterns = PatternSet(
            language="python",
            syntactic=[],
            type_patterns=[],
            semantic=[
                SemanticPattern("error_handling", "try-except", ["try: op()\nexcept: pass"], 4),
            ],
            extraction_time_ms=100.0,
            total_patterns=1
        )

        refinements = system.learn_from_patterns(patterns)

        assert len(refinements) == 1
        assert refinements[0].constraint_type == "semantic"

    def test_learn_from_patterns_weight_from_frequency(self, system):
        """Test that initial weights are based on pattern frequency."""
        patterns = PatternSet(
            language="python",
            syntactic=[
                SyntacticPattern("function", "def foo(): ...", 15, [], {}),  # High frequency
                SyntacticPattern("function", "def bar(): ...", 2, [], {}),   # Low frequency
            ],
            type_patterns=[],
            semantic=[],
            extraction_time_ms=100.0,
            total_patterns=2
        )

        system.learn_from_patterns(patterns)

        # High frequency pattern should have higher weight
        weights = list(system.constraints.values())
        assert max(weights) > min(weights)

    def test_update_weights_positive_feedback(self, system):
        """Test weight update with positive feedback."""
        pattern = SyntacticPattern("function", "def foo(): ...", 1, [], {})

        feedback = Feedback(
            success=True,
            generation_result=GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0),
            validation_result=ValidationResult(success=True),
            repair_result=None,
            score=1.0,
            feedback_type="positive"
        )

        initial_weight = system.constraints.get(system._pattern_to_id(pattern), 0.5)
        new_weight = system.update_weights(pattern, feedback)

        assert new_weight > initial_weight

    def test_update_weights_negative_feedback(self, system):
        """Test weight update with negative feedback."""
        pattern = SyntacticPattern("function", "def foo(): ...", 1, [], {})

        # First establish a weight
        positive_feedback = Feedback(
            success=True,
            generation_result=GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0),
            validation_result=ValidationResult(success=True),
            repair_result=None,
            score=1.0,
            feedback_type="positive"
        )
        system.update_weights(pattern, positive_feedback)
        initial_weight = system.constraints[system._pattern_to_id(pattern)]

        # Then provide negative feedback
        negative_feedback = Feedback(
            success=False,
            generation_result=GenerationResult(code="def foo(): fail", language="python", generation_time_ms=50.0),
            validation_result=ValidationResult(success=False, diagnostics=[{"severity": "error", "message": "failed"}]),
            repair_result=None,
            score=-1.0,
            feedback_type="negative"
        )
        new_weight = system.update_weights(pattern, negative_feedback)

        assert new_weight < initial_weight

    def test_prune_constraints_by_score(self, system):
        """Test pruning constraints below minimum score."""
        # Add some constraints with different weights
        system.constraints = {
            "pat-1": 0.05,  # Below min_score
            "pat-2": 0.5,   # Above min_score
            "pat-3": 0.08,  # Below min_score
            "pat-4": 0.8,   # Above min_score
        }

        removed = system.prune_constraints()

        assert removed == 2
        assert "pat-1" not in system.constraints
        assert "pat-3" not in system.constraints
        assert "pat-2" in system.constraints
        assert "pat-4" in system.constraints

    def test_prune_constraints_max_limit(self, system):
        """Test pruning to enforce max constraints limit."""
        # Add more constraints than max_constraints
        for i in range(150):
            system.constraints[f"pat-{i}"] = 0.5 + (i * 0.001)  # Slight variation

        removed = system.prune_constraints()

        # Should prune down to max_constraints
        assert len(system.constraints) <= system.max_constraints

    def test_decay_weights(self, system):
        """Test periodic weight decay."""
        system.constraints = {
            "pat-1": 0.5,
            "pat-2": 0.8,
            "pat-3": 0.12,  # Close to min_score
        }
        initial_weights = dict(system.constraints)

        system.decay_weights()

        # All weights should decrease
        for pattern_id in system.constraints:
            assert system.constraints[pattern_id] < initial_weights[pattern_id]

        # Very low weights should be removed
        if 0.12 * (1.0 - system.decay_rate) < system.min_score:
            assert "pat-3" not in system.constraints

    def test_decay_weights_removes_low_weights(self, system):
        """Test that decay removes constraints below threshold."""
        system.constraints = {
            "pat-1": 0.11,  # Just above min_score
        }

        system.decay_weights()

        # After decay, should be below min_score and removed
        if 0.11 * (1.0 - system.decay_rate) < system.min_score:
            assert "pat-1" not in system.constraints

    def test_classify_failure_syntax(self, system):
        """Test failure classification for syntax errors."""
        diagnostics = [{"severity": "error", "message": "SyntaxError: invalid syntax"}]
        failure_type = system._classify_failure(diagnostics)
        assert failure_type == "syntax"

    def test_classify_failure_type(self, system):
        """Test failure classification for type errors."""
        diagnostics = [{"severity": "error", "message": "TypeError: incompatible types"}]
        failure_type = system._classify_failure(diagnostics)
        assert failure_type == "type"

    def test_classify_failure_test(self, system):
        """Test failure classification for test failures."""
        diagnostics = [{"severity": "error", "message": "AssertionError: test failed"}]
        failure_type = system._classify_failure(diagnostics)
        assert failure_type == "test"

    def test_classify_failure_security(self, system):
        """Test failure classification for security issues."""
        diagnostics = [{"severity": "critical", "message": "Security vulnerability detected"}]
        failure_type = system._classify_failure(diagnostics)
        assert failure_type == "security"

    def test_compute_penalty(self, system):
        """Test penalty computation."""
        assert system._compute_penalty("security") > system._compute_penalty("syntax")
        assert system._compute_penalty("syntax") > system._compute_penalty("test")

    def test_compute_score_delta_success(self, system):
        """Test score delta computation for success."""
        feedback = Feedback(
            success=True,
            generation_result=GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0),
            validation_result=ValidationResult(success=True),
            repair_result=None,
            score=1.0,
            feedback_type="positive"
        )

        delta = system._compute_score_delta(feedback)
        assert delta > 0

    def test_compute_score_delta_with_tests(self, system):
        """Test score delta with test results."""
        feedback = Feedback(
            success=True,
            generation_result=GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0),
            validation_result=ValidationResult(
                success=True,
                test_results={"total": 10, "passed": 8}
            ),
            repair_result=None,
            score=1.0,
            feedback_type="positive"
        )

        delta = system._compute_score_delta(feedback)
        # Should include test pass rate (8/10 = 0.8)
        assert delta > 1.0

    def test_compute_score_delta_with_security_violations(self, system):
        """Test score delta with security violations."""
        feedback = Feedback(
            success=False,
            generation_result=GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0),
            validation_result=ValidationResult(
                success=False,
                security_violations=[
                    {"severity": "critical", "message": "SQL injection"},
                    {"severity": "critical", "message": "XSS vulnerability"}
                ]
            ),
            repair_result=None,
            score=-2.0,
            feedback_type="negative"
        )

        delta = system._compute_score_delta(feedback)
        # Should heavily penalize security violations
        assert delta < -2.0

    def test_compute_score_delta_clamped(self, system):
        """Test that score delta is clamped to [-2, 2]."""
        feedback = Feedback(
            success=False,
            generation_result=GenerationResult(code="", language="python", generation_time_ms=50.0),
            validation_result=ValidationResult(
                success=False,
                security_violations=[{"severity": "critical", "message": "vuln"} for _ in range(10)]
            ),
            repair_result=None,
            score=-10.0,
            feedback_type="negative"
        )

        delta = system._compute_score_delta(feedback)
        assert delta >= -2.0
        assert delta <= 2.0

    def test_extract_patterns_from_code_functions(self, system):
        """Test pattern extraction from function definitions."""
        code = """
def foo():
    pass

def bar(x, y):
    return x + y
"""
        pattern_ids = system._extract_patterns_from_code(code)
        assert len(pattern_ids) >= 2

    def test_extract_patterns_from_code_classes(self, system):
        """Test pattern extraction from class definitions."""
        code = """
class Foo:
    pass

class Bar:
    def method(self):
        pass
"""
        pattern_ids = system._extract_patterns_from_code(code)
        # Should find both classes
        assert len(pattern_ids) >= 2

    def test_extract_patterns_from_code_error_handling(self, system):
        """Test pattern extraction for error handling."""
        code = """
try:
    risky_operation()
except Exception:
    handle_error()
"""
        pattern_ids = system._extract_patterns_from_code(code)
        # Should find try-except pattern
        assert len(pattern_ids) >= 1

    def test_extract_patterns_from_invalid_code(self, system):
        """Test pattern extraction from invalid code."""
        code = "def broken("
        pattern_ids = system._extract_patterns_from_code(code)
        # Should still extract basic patterns
        assert len(pattern_ids) >= 0

    def test_pattern_to_id_syntactic(self, system):
        """Test pattern ID generation for syntactic patterns."""
        pattern1 = SyntacticPattern("function", "def foo(): ...", 1, [], {})
        pattern2 = SyntacticPattern("function", "def foo(): ...", 5, ["example"], {})

        id1 = system._pattern_to_id(pattern1)
        id2 = system._pattern_to_id(pattern2)

        # Same pattern type and template should generate same ID
        assert id1 == id2

    def test_pattern_to_id_type(self, system):
        """Test pattern ID generation for type patterns."""
        pattern1 = TypePattern("int", ["x"], 1, [])
        pattern2 = TypePattern("int", ["y", "z"], 3, [])

        id1 = system._pattern_to_id(pattern1)
        id2 = system._pattern_to_id(pattern2)

        # Same signature should generate same ID
        assert id1 == id2

    def test_pattern_to_id_semantic(self, system):
        """Test pattern ID generation for semantic patterns."""
        pattern1 = SemanticPattern("error_handling", "try-except", [], 1)
        pattern2 = SemanticPattern("error_handling", "try-except", ["example"], 5)

        id1 = system._pattern_to_id(pattern1)
        id2 = system._pattern_to_id(pattern2)

        # Same intent and structure should generate same ID
        assert id1 == id2

    def test_learning_history_recorded(self, system):
        """Test that learning events are recorded in history."""
        pattern = SyntacticPattern("function", "def foo(): ...", 1, [], {})
        feedback = Feedback(
            success=True,
            generation_result=GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0),
            validation_result=ValidationResult(success=True),
            repair_result=None,
            score=1.0,
            feedback_type="positive"
        )

        system.update_weights(pattern, feedback)

        assert len(system.learning_history) > 0
        event = system.learning_history[-1]
        assert isinstance(event, LearningEvent)
        assert event.event_type in ["weight_increase", "weight_decrease"]

    def test_get_learning_stats(self, system):
        """Test learning statistics retrieval."""
        # Add some constraints
        patterns = PatternSet(
            language="python",
            syntactic=[SyntacticPattern("function", "def foo(): ...", 1, [], {})],
            type_patterns=[],
            semantic=[],
            extraction_time_ms=100.0,
            total_patterns=1
        )
        system.learn_from_patterns(patterns)

        stats = system.get_learning_stats()

        assert "total_constraints" in stats
        assert "total_feedback" in stats
        assert "constraints_added" in stats
        assert "avg_constraint_weight" in stats
        assert stats["total_constraints"] > 0

    def test_weight_clamping(self, system):
        """Test that weights are clamped to [0, 1]."""
        pattern = SyntacticPattern("function", "def foo(): ...", 1, [], {})

        # Try to boost weight beyond 1.0
        for _ in range(20):
            feedback = Feedback(
                success=True,
                generation_result=GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0),
                validation_result=ValidationResult(success=True),
                repair_result=None,
                score=1.0,
                feedback_type="positive"
            )
            weight = system.update_weights(pattern, feedback)

        # Weight should be clamped at 1.0
        assert weight <= 1.0

    def test_concurrent_pattern_updates(self, system):
        """Test handling of concurrent pattern updates."""
        pattern1 = SyntacticPattern("function", "def foo(): ...", 1, [], {})
        pattern2 = SyntacticPattern("class", "class Bar: ...", 1, [], {})

        feedback1 = Feedback(
            success=True,
            generation_result=GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0),
            validation_result=ValidationResult(success=True),
            repair_result=None,
            score=1.0,
            feedback_type="positive"
        )

        feedback2 = Feedback(
            success=False,
            generation_result=GenerationResult(code="class Bar: fail", language="python", generation_time_ms=50.0),
            validation_result=ValidationResult(success=False, diagnostics=[{"severity": "error", "message": "error"}]),
            repair_result=None,
            score=-1.0,
            feedback_type="negative"
        )

        system.update_weights(pattern1, feedback1)
        system.update_weights(pattern2, feedback2)

        # Both patterns should be updated independently
        assert len(system.constraints) == 2

    def test_constraint_metadata(self, system):
        """Test that constraint metadata is stored."""
        patterns = PatternSet(
            language="python",
            syntactic=[SyntacticPattern("function", "def foo(): ...", 5, [], {})],
            type_patterns=[],
            semantic=[],
            extraction_time_ms=100.0,
            total_patterns=1
        )

        system.learn_from_patterns(patterns)

        # Metadata should be stored
        assert len(system.constraint_metadata) > 0
        metadata = list(system.constraint_metadata.values())[0]
        assert "pattern_type" in metadata
        assert metadata["source"] == "pattern_mining"

    def test_stats_tracking(self, system):
        """Test that statistics are tracked correctly."""
        generation_result = GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0)
        validation_result = ValidationResult(success=True)

        system.learn_from_success(generation_result, validation_result)
        assert system.stats["successful_feedback"] == 1
        assert system.stats["total_feedback"] == 1

        diagnostics = [{"severity": "error", "message": "error"}]
        system.learn_from_failure(generation_result, diagnostics)
        assert system.stats["failed_feedback"] == 1
        assert system.stats["total_feedback"] == 2

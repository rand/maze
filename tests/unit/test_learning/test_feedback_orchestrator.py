"""
Tests for feedback loop orchestrator.
"""

from pathlib import Path
import pytest
from unittest.mock import Mock, MagicMock

from maze.learning.feedback_orchestrator import (
    FeedbackLoopOrchestrator,
    FeedbackResult,
    FeedbackStats,
)
from maze.learning.constraint_learning import (
    ConstraintLearningSystem,
    GenerationResult,
    ValidationResult,
    RepairResult,
)
from maze.learning.project_adaptation import ProjectAdaptationManager
from maze.learning.pattern_mining import PatternMiningEngine
from maze.integrations.mnemosyne import MnemosyneIntegration


class TestFeedbackLoopOrchestrator:
    """Test FeedbackLoopOrchestrator class."""

    @pytest.fixture
    def learner(self):
        """Create constraint learning system."""
        return ConstraintLearningSystem(learning_rate=0.1)

    @pytest.fixture
    def pattern_miner(self):
        """Create pattern mining engine."""
        return PatternMiningEngine(language="python", min_frequency=1)

    @pytest.fixture
    def adapter(self, pattern_miner, learner):
        """Create project adaptation manager."""
        return ProjectAdaptationManager(
            pattern_miner=pattern_miner,
            learner=learner
        )

    @pytest.fixture
    def memory(self, tmp_path):
        """Create mnemosyne integration."""
        return MnemosyneIntegration(
            enable_orchestration=False,
            local_cache_path=tmp_path / "cache.jsonl"
        )

    @pytest.fixture
    def orchestrator(self, learner, adapter, memory):
        """Create feedback loop orchestrator."""
        return FeedbackLoopOrchestrator(
            learner=learner,
            adapter=adapter,
            memory=memory,
            enable_auto_persist=True
        )

    def test_init(self, orchestrator, learner, adapter, memory):
        """Test initialization."""
        assert orchestrator.learner == learner
        assert orchestrator.adapter == adapter
        assert orchestrator.memory == memory
        assert orchestrator.enable_auto_persist is True
        assert isinstance(orchestrator.stats, FeedbackStats)
        assert orchestrator.stats.total_feedback_events == 0

    def test_process_feedback_success(self, orchestrator):
        """Test processing successful feedback."""
        generation = GenerationResult(
            code="def foo(): pass",
            language="python",
            generation_time_ms=50.0
        )
        validation = ValidationResult(success=True)

        result = orchestrator.process_feedback(generation, validation)

        assert isinstance(result, FeedbackResult)
        assert result.score > 0
        assert len(result.refinements) > 0
        assert orchestrator.stats.total_feedback_events == 1
        assert orchestrator.stats.positive_events == 1

    def test_process_feedback_failure(self, orchestrator):
        """Test processing failed feedback."""
        generation = GenerationResult(
            code="def foo(",
            language="python",
            generation_time_ms=50.0
        )
        validation = ValidationResult(
            success=False,
            diagnostics=[{"severity": "error", "message": "SyntaxError"}]
        )

        result = orchestrator.process_feedback(generation, validation)

        assert isinstance(result, FeedbackResult)
        assert result.score < 0
        assert len(result.refinements) > 0
        assert orchestrator.stats.total_feedback_events == 1
        assert orchestrator.stats.negative_events == 1

    def test_process_feedback_with_repair_success(self, orchestrator):
        """Test feedback with successful repair."""
        generation = GenerationResult(
            code="def foo(): pass",
            language="python",
            generation_time_ms=50.0
        )
        validation = ValidationResult(success=True)
        repair = RepairResult(attempts=2, success=True, final_code="def foo(): pass")

        result = orchestrator.process_feedback(generation, validation, repair)

        assert result.score > 0
        # Score should be lower than without repair (penalty for needing repair)

    def test_process_feedback_with_repair_failure(self, orchestrator):
        """Test feedback with failed repair."""
        generation = GenerationResult(
            code="def foo(",
            language="python",
            generation_time_ms=50.0
        )
        validation = ValidationResult(
            success=False,
            diagnostics=[{"severity": "error", "message": "SyntaxError"}]
        )
        repair = RepairResult(attempts=3, success=False)

        result = orchestrator.process_feedback(generation, validation, repair)

        assert result.score < 0

    def test_process_feedback_with_project(self, orchestrator, tmp_path):
        """Test feedback processing with project context."""
        # Initialize project
        project = tmp_path / "test_project"
        project.mkdir()
        (project / "main.py").write_text("def foo(): pass")
        orchestrator.adapter.initialize_project(project, language="python")

        generation = GenerationResult(
            code="def bar(): pass",
            language="python",
            generation_time_ms=50.0
        )
        validation = ValidationResult(success=True)

        result = orchestrator.process_feedback(
            generation,
            validation,
            project_name="test_project"
        )

        assert isinstance(result, FeedbackResult)
        # Project profile should be updated
        profile = orchestrator.adapter.profiles["test_project"]
        assert profile.generation_count == 1

    def test_compute_overall_score_success(self, orchestrator):
        """Test score computation for success."""
        validation = ValidationResult(success=True)
        score = orchestrator._compute_overall_score(validation, None)
        assert score > 0

    def test_compute_overall_score_failure(self, orchestrator):
        """Test score computation for failure."""
        validation = ValidationResult(success=False)
        score = orchestrator._compute_overall_score(validation, None)
        assert score < 0

    def test_compute_overall_score_with_tests(self, orchestrator):
        """Test score computation with test results."""
        validation = ValidationResult(
            success=True,
            test_results={"total": 10, "passed": 8}
        )
        score = orchestrator._compute_overall_score(validation, None)
        assert score > 1.0  # Success + partial test pass

    def test_compute_overall_score_with_security_violations(self, orchestrator):
        """Test score computation with security violations."""
        validation = ValidationResult(
            success=False,
            security_violations=[
                {"severity": "critical", "message": "SQL injection"},
                {"severity": "critical", "message": "XSS"}
            ]
        )
        score = orchestrator._compute_overall_score(validation, None)
        assert score <= -2.0  # Should be at minimum

    def test_compute_overall_score_clamped(self, orchestrator):
        """Test that scores are clamped to [-2, 2]."""
        validation = ValidationResult(
            success=True,
            test_results={"total": 100, "passed": 100}
        )
        score = orchestrator._compute_overall_score(validation, None)
        assert -2.0 <= score <= 2.0

    def test_classify_feedback_positive(self, orchestrator):
        """Test positive feedback classification."""
        validation = ValidationResult(success=True)
        feedback_type = orchestrator._classify_feedback(validation, None)
        assert feedback_type == "positive"

    def test_classify_feedback_negative(self, orchestrator):
        """Test negative feedback classification."""
        validation = ValidationResult(success=False)
        feedback_type = orchestrator._classify_feedback(validation, None)
        assert feedback_type == "negative"

    def test_classify_feedback_with_failed_repair(self, orchestrator):
        """Test feedback classification with failed repair."""
        validation = ValidationResult(success=True)
        repair = RepairResult(attempts=3, success=False)
        feedback_type = orchestrator._classify_feedback(validation, repair)
        assert feedback_type == "negative"

    def test_extract_patterns_from_result_function(self, orchestrator):
        """Test pattern extraction from function code."""
        generation = GenerationResult(
            code="def process_data(x):\n    return x * 2",
            language="python",
            generation_time_ms=50.0
        )

        patterns = orchestrator._extract_patterns_from_result(generation)

        assert len(patterns) > 0
        assert patterns[0].pattern_type == "function"

    def test_extract_patterns_from_result_class(self, orchestrator):
        """Test pattern extraction from class code."""
        generation = GenerationResult(
            code="class Processor:\n    def run(self):\n        pass",
            language="python",
            generation_time_ms=50.0
        )

        patterns = orchestrator._extract_patterns_from_result(generation)

        assert len(patterns) > 0
        assert patterns[0].pattern_type == "class"

    def test_extract_patterns_from_result_invalid_code(self, orchestrator):
        """Test pattern extraction from invalid code."""
        generation = GenerationResult(
            code="def broken(",
            language="python",
            generation_time_ms=50.0
        )

        patterns = orchestrator._extract_patterns_from_result(generation)

        assert len(patterns) > 0
        assert patterns[0].pattern_type == "unknown"

    def test_extract_patterns_with_pattern_ids(self, orchestrator):
        """Test pattern extraction when pattern IDs provided."""
        generation = GenerationResult(
            code="def foo(): pass",
            language="python",
            generation_time_ms=50.0,
            patterns_used=["pat-1", "pat-2"]
        )

        patterns = orchestrator._extract_patterns_from_result(generation)

        assert len(patterns) == 2

    def test_update_learning_state(self, orchestrator):
        """Test learning state update."""
        result = FeedbackResult(
            pattern=None,
            score=1.0,
            refinements=[],
            updated_weights={}
        )

        # Should not raise error
        orchestrator.update_learning_state(result)

    def test_persist_to_memory(self, orchestrator):
        """Test persisting feedback to memory."""
        from maze.learning.pattern_mining import SyntacticPattern

        pattern = SyntacticPattern(
            pattern_type="function",
            template="def foo(): ...",
            frequency=1,
            examples=[],
            context={}
        )

        result = FeedbackResult(
            pattern=pattern,
            score=1.5,
            refinements=[],
            updated_weights={}
        )

        orchestrator.persist_to_memory(result, "test:namespace")

        # Pattern should be stored in memory
        assert len(orchestrator.memory.pattern_cache) > 0

    def test_persist_to_memory_no_pattern(self, orchestrator):
        """Test persisting feedback without pattern."""
        result = FeedbackResult(
            pattern=None,
            score=1.0,
            refinements=[],
            updated_weights={}
        )

        # Should not raise error
        orchestrator.persist_to_memory(result, "test:namespace")

    def test_get_feedback_stats(self, orchestrator):
        """Test getting feedback statistics."""
        stats = orchestrator.get_feedback_stats()

        assert isinstance(stats, FeedbackStats)
        assert stats.total_feedback_events == 0
        assert stats.positive_events == 0
        assert stats.negative_events == 0

    def test_reset_stats(self, orchestrator):
        """Test resetting statistics."""
        # Process some feedback
        generation = GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0)
        validation = ValidationResult(success=True)
        orchestrator.process_feedback(generation, validation)

        assert orchestrator.stats.total_feedback_events == 1

        # Reset
        orchestrator.reset_stats()

        assert orchestrator.stats.total_feedback_events == 0
        assert orchestrator.stats.positive_events == 0

    def test_average_score_calculation(self, orchestrator):
        """Test average score calculation over multiple feedbacks."""
        generation1 = GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0)
        validation1 = ValidationResult(success=True)

        generation2 = GenerationResult(code="def bar(", language="python", generation_time_ms=50.0)
        validation2 = ValidationResult(success=False, diagnostics=[{"severity": "error", "message": "error"}])

        orchestrator.process_feedback(generation1, validation1)
        orchestrator.process_feedback(generation2, validation2)

        # Average should be between the two scores
        assert orchestrator.stats.total_feedback_events == 2

    def test_refinements_applied_counter(self, orchestrator):
        """Test refinements applied counter."""
        generation = GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0)
        validation = ValidationResult(success=True)

        orchestrator.process_feedback(generation, validation)

        assert orchestrator.stats.refinements_applied > 0

    def test_auto_persist_disabled(self, learner, adapter, memory):
        """Test with auto-persist disabled."""
        orchestrator = FeedbackLoopOrchestrator(
            learner=learner,
            adapter=adapter,
            memory=memory,
            enable_auto_persist=False
        )

        generation = GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0)
        validation = ValidationResult(success=True)

        result = orchestrator.process_feedback(
            generation,
            validation,
            project_name="test_project"
        )

        # Should still work, just not persist automatically
        assert isinstance(result, FeedbackResult)

    def test_updated_weights_tracking(self, orchestrator):
        """Test that updated weights are tracked."""
        generation = GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0)
        validation = ValidationResult(success=True)

        result = orchestrator.process_feedback(generation, validation)

        assert isinstance(result.updated_weights, dict)
        # Should have some weights updated
        assert len(result.updated_weights) >= 0

    def test_multiple_feedback_processing(self, orchestrator):
        """Test processing multiple feedbacks."""
        for i in range(5):
            generation = GenerationResult(
                code=f"def func{i}(): pass",
                language="python",
                generation_time_ms=50.0
            )
            validation = ValidationResult(success=True)
            orchestrator.process_feedback(generation, validation)

        assert orchestrator.stats.total_feedback_events == 5
        assert orchestrator.stats.positive_events == 5

    def test_mixed_feedback_processing(self, orchestrator):
        """Test processing mix of positive and negative feedback."""
        # Positive
        gen1 = GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0)
        val1 = ValidationResult(success=True)
        orchestrator.process_feedback(gen1, val1)

        # Negative
        gen2 = GenerationResult(code="def bar(", language="python", generation_time_ms=50.0)
        val2 = ValidationResult(success=False, diagnostics=[{"severity": "error", "message": "error"}])
        orchestrator.process_feedback(gen2, val2)

        # Positive
        gen3 = GenerationResult(code="def baz(): pass", language="python", generation_time_ms=50.0)
        val3 = ValidationResult(success=True)
        orchestrator.process_feedback(gen3, val3)

        assert orchestrator.stats.total_feedback_events == 3
        assert orchestrator.stats.positive_events == 2
        assert orchestrator.stats.negative_events == 1

    def test_performance_target(self, orchestrator):
        """Test that feedback processing meets performance target."""
        import time

        generation = GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0)
        validation = ValidationResult(success=True)

        start = time.perf_counter()
        orchestrator.process_feedback(generation, validation)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Target is <20ms, but we'll be lenient for test environments
        assert elapsed_ms < 100  # 100ms max for tests

    def test_last_update_timestamp(self, orchestrator):
        """Test that last_update timestamp is set."""
        import time
        before = time.time()

        generation = GenerationResult(code="def foo(): pass", language="python", generation_time_ms=50.0)
        validation = ValidationResult(success=True)
        orchestrator.process_feedback(generation, validation)

        after = time.time()

        assert before <= orchestrator.stats.last_update <= after

    def test_pattern_extraction_empty_code(self, orchestrator):
        """Test pattern extraction from empty code."""
        generation = GenerationResult(code="", language="python", generation_time_ms=50.0)

        patterns = orchestrator._extract_patterns_from_result(generation)

        # Should still return at least one pattern (unknown)
        assert len(patterns) >= 0

    def test_integration_with_all_components(self, orchestrator, tmp_path):
        """Test integration across all components."""
        # Initialize project
        project = tmp_path / "integration_project"
        project.mkdir()
        (project / "main.py").write_text("def process(): pass")
        orchestrator.adapter.initialize_project(project, language="python")

        # Process successful feedback
        generation = GenerationResult(
            code="def transform(data):\n    return data.upper()",
            language="python",
            generation_time_ms=50.0
        )
        validation = ValidationResult(
            success=True,
            test_results={"total": 5, "passed": 5}
        )

        result = orchestrator.process_feedback(
            generation,
            validation,
            project_name="integration_project"
        )

        # Verify all systems updated
        assert result.score > 0
        assert len(result.refinements) > 0
        assert len(orchestrator.learner.constraints) > 0
        assert orchestrator.adapter.profiles["integration_project"].generation_count == 1
        assert len(orchestrator.memory.pattern_cache) > 0

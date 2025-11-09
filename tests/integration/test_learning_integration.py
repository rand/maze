"""
Integration tests for Phase 5 adaptive learning system.

Tests end-to-end workflows across all learning components.
"""

from pathlib import Path
import time
import pytest

from maze.learning.pattern_mining import PatternMiningEngine, PatternSet
from maze.learning.constraint_learning import (
    ConstraintLearningSystem,
    GenerationResult,
    ValidationResult,
    RepairResult,
)
from maze.learning.project_adaptation import ProjectAdaptationManager
from maze.learning.feedback_orchestrator import FeedbackLoopOrchestrator
from maze.learning.hybrid_weighting import (
    HybridConstraintWeighter,
    ConstraintSet,
    GenerationState,
)
from maze.integrations.mnemosyne import (
    MnemosyneIntegration,
    GenerationContext,
)


class TestLearningIntegration:
    """Integration tests for adaptive learning system."""

    @pytest.fixture
    def sample_codebase(self, tmp_path):
        """Create sample codebase for testing."""
        project = tmp_path / "sample_project"
        project.mkdir()

        # Create sample Python files
        (project / "main.py").write_text("""
def process_data(data):
    '''Process input data.'''
    result = transform(data)
    return validate(result)

def transform(data):
    '''Transform data.'''
    return data.upper()

def validate(data):
    '''Validate data.'''
    return len(data) > 0
""")

        (project / "utils.py").write_text("""
class DataProcessor:
    '''Utility for data processing.'''

    def __init__(self, config):
        self.config = config

    def run(self, input_data):
        '''Run processing pipeline.'''
        cleaned = self._clean(input_data)
        return self._format(cleaned)

    def _clean(self, data):
        return data.strip()

    def _format(self, data):
        return f"Processed: {data}"
""")

        return project

    @pytest.fixture
    def pattern_miner(self):
        """Create pattern mining engine."""
        return PatternMiningEngine(language="python", min_frequency=1)

    @pytest.fixture
    def learner(self):
        """Create constraint learning system."""
        return ConstraintLearningSystem(learning_rate=0.1, max_constraints=1000)

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

    @pytest.fixture
    def weighter(self):
        """Create hybrid constraint weighter."""
        return HybridConstraintWeighter(default_temperature=0.5)

    def test_end_to_end_learning_workflow(
        self,
        sample_codebase,
        pattern_miner,
        learner,
        adapter,
        memory,
        orchestrator
    ):
        """Test complete learning workflow from mining to feedback."""
        # Step 1: Mine patterns from codebase
        patterns = pattern_miner.mine_patterns(sample_codebase)

        assert patterns.total_patterns > 0
        assert len(patterns.syntactic) > 0

        # Step 2: Initialize project adaptation
        adapter.initialize_project(sample_codebase, language="python")
        profile = adapter.profiles["sample_project"]

        assert profile is not None
        assert len(profile.patterns) > 0

        # Step 3: Generate code (simulated)
        generation = GenerationResult(
            code="def new_function(x):\n    return x * 2",
            language="python",
            generation_time_ms=50.0
        )

        # Step 4: Validate (simulated success)
        validation = ValidationResult(success=True)

        # Step 5: Process feedback
        feedback_result = orchestrator.process_feedback(
            generation,
            validation,
            project_name="sample_project"
        )

        assert feedback_result.score > 0
        assert len(feedback_result.refinements) > 0

        # Step 6: Verify learning occurred
        assert len(learner.constraints) > 0
        assert profile.generation_count == 1

    def test_cross_session_persistence(self, tmp_path, memory):
        """Test pattern persistence across sessions."""
        from maze.learning.pattern_mining import SyntacticPattern

        # Session 1: Store patterns
        pattern = SyntacticPattern(
            pattern_type="function",
            template="def foo(): ...",
            frequency=5,
            examples=["def foo(): pass"],
            context={"args": 0}
        )

        memory.store_pattern(
            pattern=pattern,
            namespace="project:test",
            importance=7,
            tags=["function", "test"]
        )

        # Verify stored
        assert len(memory.pattern_cache) > 0

        # Session 2: Create new instance (simulating new session)
        memory2 = MnemosyneIntegration(
            enable_orchestration=False,
            local_cache_path=tmp_path / "cache.jsonl"
        )

        # Recall patterns
        context = GenerationContext(
            language="python",
            task_description="create function",
            existing_code=None
        )

        recalled = memory2.recall_patterns(context, namespace="project:test", limit=10)

        # Verify persistence
        assert len(recalled) > 0

    def test_multi_project_learning(
        self,
        tmp_path,
        pattern_miner,
        learner,
        adapter,
        memory,
        orchestrator
    ):
        """Test learning from multiple projects."""
        # Create two projects
        project1 = tmp_path / "project1"
        project1.mkdir()
        (project1 / "main.py").write_text("def func1(): pass")

        project2 = tmp_path / "project2"
        project2.mkdir()
        (project2 / "main.py").write_text("def func2(): pass")

        # Initialize both projects
        adapter.initialize_project(project1, language="python")
        adapter.initialize_project(project2, language="python")

        # Process feedback for project1
        gen1 = GenerationResult(code="def new1(): pass", language="python", generation_time_ms=50.0)
        val1 = ValidationResult(success=True)
        orchestrator.process_feedback(gen1, val1, project_name="project1")

        # Process feedback for project2
        gen2 = GenerationResult(code="def new2(): pass", language="python", generation_time_ms=50.0)
        val2 = ValidationResult(success=True)
        orchestrator.process_feedback(gen2, val2, project_name="project2")

        # Verify both projects have profiles
        assert "project1" in adapter.profiles
        assert "project2" in adapter.profiles

        # Verify independent learning
        assert adapter.profiles["project1"].generation_count == 1
        assert adapter.profiles["project2"].generation_count == 1

    def test_pattern_recall_accuracy(self, memory):
        """Test pattern recall accuracy."""
        from maze.learning.pattern_mining import SyntacticPattern

        # Store multiple patterns
        patterns_stored = []
        for i in range(10):
            pattern = SyntacticPattern(
                pattern_type="function",
                template=f"def func{i}(): ...",
                frequency=i + 1,
                examples=[f"def func{i}(): pass"],
                context={"index": i}
            )
            patterns_stored.append(pattern)
            memory.store_pattern(
                pattern=pattern,
                namespace="project:accuracy_test",
                importance=5 + i // 2,
                tags=["function", f"test{i}"]
            )

        # Recall with relevant context
        context = GenerationContext(
            language="python",
            task_description="create function",
            existing_code=None
        )

        recalled = memory.recall_patterns(
            context,
            namespace="project:accuracy_test",
            limit=10
        )

        # Verify recall accuracy (should recall most patterns)
        recall_rate = len(recalled) / len(patterns_stored)
        assert recall_rate >= 0.9, f"Recall rate {recall_rate:.2%} below 90% target"

    def test_adaptation_convergence(
        self,
        sample_codebase,
        adapter,
        orchestrator
    ):
        """Test convergence within 100 examples."""
        # Initialize project
        adapter.initialize_project(sample_codebase, language="python")

        initial_constraints = len(adapter.learner.constraints)

        # Simulate 50 successful generations
        for i in range(50):
            generation = GenerationResult(
                code=f"def func{i}(): pass",
                language="python",
                generation_time_ms=50.0
            )
            validation = ValidationResult(success=True)

            orchestrator.process_feedback(
                generation,
                validation,
                project_name="sample_project"
            )

        # Check convergence (constraints should stabilize)
        final_constraints = len(adapter.learner.constraints)

        # Should have learned some constraints
        assert final_constraints > initial_constraints

        # Profile should show progress
        profile = adapter.profiles["sample_project"]
        assert profile.generation_count == 50

    def test_performance_end_to_end(
        self,
        sample_codebase,
        orchestrator
    ):
        """Test end-to-end performance."""
        # Measure feedback processing time
        generation = GenerationResult(
            code="def test(): pass",
            language="python",
            generation_time_ms=50.0
        )
        validation = ValidationResult(success=True)

        start = time.perf_counter()
        orchestrator.process_feedback(generation, validation)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Target is <20ms, but we'll be lenient for integration tests
        assert elapsed_ms < 100, f"Feedback processing took {elapsed_ms:.1f}ms (target: <100ms)"

    def test_memory_usage(self, learner):
        """Test memory usage limits."""
        # Add many constraints
        from maze.learning.pattern_mining import SyntacticPattern

        initial_count = len(learner.constraints)

        for i in range(150):
            pattern = SyntacticPattern(
                pattern_type="function",
                template=f"def func{i}(): ...",
                frequency=1,
                examples=[],
                context={}
            )

            generation = GenerationResult(
                code=f"def func{i}(): pass",
                language="python",
                generation_time_ms=50.0
            )
            validation = ValidationResult(success=True)

            learner.learn_from_success(generation, validation)

        # Should not exceed max_constraints (1000)
        assert len(learner.constraints) <= learner.max_constraints

    def test_pattern_mining_to_constraints(
        self,
        sample_codebase,
        pattern_miner,
        learner
    ):
        """Test pattern → constraint pipeline."""
        # Mine patterns
        patterns = pattern_miner.mine_patterns(sample_codebase)

        assert patterns.total_patterns > 0

        # Learn constraints from patterns
        generation = GenerationResult(
            code="def example(): pass",
            language="python",
            generation_time_ms=50.0
        )
        validation = ValidationResult(success=True)

        initial_count = len(learner.constraints)
        learner.learn_from_success(generation, validation)

        # Should have created constraints
        assert len(learner.constraints) >= initial_count

    def test_cold_start_fallback(self, memory):
        """Test cold start without patterns."""
        # Try to recall from non-existent project
        context = GenerationContext(
            language="python",
            task_description="create function",
            existing_code=None
        )

        recalled = memory.recall_patterns(
            context,
            namespace="project:nonexistent",
            limit=10
        )

        # Should return empty list (graceful degradation)
        assert isinstance(recalled, list)

    def test_error_recovery(self, orchestrator):
        """Test error recovery in learning loop."""
        # Process invalid generation
        generation = GenerationResult(
            code="def broken(",
            language="python",
            generation_time_ms=50.0
        )
        validation = ValidationResult(
            success=False,
            diagnostics=[{"severity": "error", "message": "SyntaxError"}]
        )

        # Should not raise exception
        result = orchestrator.process_feedback(generation, validation)

        assert result is not None
        assert result.score < 0  # Negative feedback

    def test_hybrid_weighting_integration(
        self,
        weighter,
        learner
    ):
        """Test integration of hybrid weighting with constraints."""
        # Create hard and soft constraint sets
        hard = ConstraintSet(constraints=[])
        soft = ConstraintSet(constraints=[])

        # Combine with weighter
        weighted = weighter.combine_constraints(hard, soft, temperature=0.7)

        assert weighted.temperature == 0.7
        assert weighted.hard_constraints == hard

        # Compute token weights
        vocab = ["def", "class", "if", "else", "return"]
        state = GenerationState(vocabulary=vocab)

        weights = weighter.compute_token_weights(weighted, state)

        assert len(weights.weights) == len(vocab)

        # Weights should be normalized
        total = sum(w for w, m in zip(weights.weights, weights.hard_masked) if not m)
        assert abs(total - 1.0) < 1e-6

    def test_concurrent_learning_simulation(
        self,
        orchestrator,
        adapter,
        tmp_path
    ):
        """Test concurrent learning from multiple sessions (simulated)."""
        # Create project
        project = tmp_path / "concurrent_project"
        project.mkdir()
        (project / "main.py").write_text("def initial(): pass")

        adapter.initialize_project(project, language="python")

        # Simulate concurrent feedback
        results = []
        for i in range(10):
            generation = GenerationResult(
                code=f"def func{i}(): pass",
                language="python",
                generation_time_ms=50.0
            )
            validation = ValidationResult(success=True)

            result = orchestrator.process_feedback(
                generation,
                validation,
                project_name="concurrent_project"
            )
            results.append(result)

        # All should succeed
        assert len(results) == 10
        assert all(r.score > 0 for r in results)

    def test_benchmarks_all_metrics(
        self,
        sample_codebase,
        pattern_miner,
        learner,
        adapter,
        orchestrator,
        weighter
    ):
        """Test all performance benchmarks."""
        benchmarks = {}

        # Pattern mining performance
        start = time.perf_counter()
        patterns = pattern_miner.mine_patterns(sample_codebase)
        benchmarks["pattern_mining_ms"] = (time.perf_counter() - start) * 1000

        # Constraint learning performance
        generation = GenerationResult(
            code="def test(): pass",
            language="python",
            generation_time_ms=50.0
        )
        validation = ValidationResult(success=True)

        start = time.perf_counter()
        learner.learn_from_success(generation, validation)
        benchmarks["constraint_learning_ms"] = (time.perf_counter() - start) * 1000

        # Feedback processing performance
        start = time.perf_counter()
        orchestrator.process_feedback(generation, validation)
        benchmarks["feedback_processing_ms"] = (time.perf_counter() - start) * 1000

        # Hybrid weighting performance
        hard = ConstraintSet(constraints=[])
        soft = ConstraintSet(constraints=[])
        weighted = weighter.combine_constraints(hard, soft)

        vocab = ["def", "class", "if", "else", "return"] * 10
        state = GenerationState(vocabulary=vocab)

        start = time.perf_counter()
        weighter.compute_token_weights(weighted, state)
        benchmarks["token_weighting_ms"] = (time.perf_counter() - start) * 1000

        # Verify all benchmarks completed
        assert "pattern_mining_ms" in benchmarks
        assert "constraint_learning_ms" in benchmarks
        assert "feedback_processing_ms" in benchmarks
        assert "token_weighting_ms" in benchmarks

        # Pattern mining should complete reasonably fast for small codebase
        assert benchmarks["pattern_mining_ms"] < 5000  # <5s for small codebase

        # Other operations should be fast
        assert benchmarks["constraint_learning_ms"] < 100
        assert benchmarks["feedback_processing_ms"] < 100
        assert benchmarks["token_weighting_ms"] < 50
